"""
app.py

Flask backend for GPA Goes UP.

Routes:
  POST /api/upload                → parse PDF transcript, persist student, set session
  GET  /api/session/student-id    → return student_id stored in Flask session
  POST /api/session/purge         → delete student from DB + clear session
  POST /api/recommend             → run Rule Engine + ML, return schedule + student stats
  POST /api/admin/retrain         → retrain ML model from CSVs, return CV metrics
  GET  /api/planner/autofill      → return stored academic data for planner form
  POST /api/planner/calculate     → run milestone projection

Dev-only:
  POST /api/dev/session/init      → seed Flask session with a student_id for testing
"""

from __future__ import annotations

import logging
import os
import uuid
from collections import Counter
from datetime import date

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import database
from ml import r2_storage
from parser.transcript_parser import parse_transcript
from parser.pdf_reader import PDFReadError, PDFEncryptedError
from rule_engine import AcademicRuleEngine
from ml import predict as ml_predict
from ml.train import train_and_save
from ml.csv_appender import LOCK as _CSV_LOCK, anonymize_and_append
from chatbot.chatbot_routes import chatbot_bp

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App + shared objects
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "gpa-goes-up-dev-secret-2025")

_allowed_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
CORS(app, origins=[_allowed_origin], supports_credentials=True)

app.register_blueprint(chatbot_bp, url_prefix="/api")

# Pull CSVs + trained model from Cloudflare R2 on every cold start so the
# ephemeral container filesystem is populated before the first request arrives.
r2_storage.sync_on_startup()

_RULE_ENGINE_PATH = os.path.join(os.path.dirname(__file__), "Rule_Engine.json")
RULE_ENGINE = AcademicRuleEngine(_RULE_ENGINE_PATH)

_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(_UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"]      = _UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

_PDF_MAGIC = b"%PDF"


# ---------------------------------------------------------------------------
# TTL background cleanup — runs every 2 hours, purges sessions older than 24 h
# ---------------------------------------------------------------------------

def _cleanup_stale_sessions() -> None:
    stale_ids = database.get_stale_session_ids(max_age_hours=24)
    for sid in stale_ids:
        try:
            database.purge_student_session(sid)
            log.info("TTL cleanup: purged stale student session %s", sid)
        except Exception as exc:
            log.warning("TTL cleanup: failed to purge %s — %s", sid, exc)


_scheduler = BackgroundScheduler(daemon=True)
_scheduler.add_job(_cleanup_stale_sessions, "interval", hours=2, id="ttl_cleanup")
_scheduler.start()

# Ensure the session_created_at column exists (safe no-op if already present).
database.ensure_session_timestamp_column()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_course_df() -> pd.DataFrame:
    """Fetch the Course table and return a normalised DataFrame."""
    df = pd.DataFrame(database.get_all_courses())
    if df.empty:
        return df
    for col in ("Is_elective", "Is_practical"):
        if col in df.columns:
            df[col] = df[col].astype(bool)
    if "Semester" in df.columns:
        df["Semester"] = df["Semester"].str.lower().str.strip()
    return df


def _parse_year(raw) -> int:
    """Return the first 4-digit year from a value that may be '2022-2023' or a plain int."""
    try:
        return int(str(raw).split("-")[0])
    except (ValueError, AttributeError, TypeError):
        return 0


def _build_semester_history(enrollments: list[dict], courses: list[dict]) -> list[dict]:
    """
    Per-semester GPA history using credit-hour-weighted averages.
    Excludes special courses and grades not counted in GPA.
    Label format: "Fall '22-23", "Spring '22-23", "Summer '22-23"
    """
    credit_map    = {c["Code"]: float(c["Credit_Hours"]) for c in courses}
    special_codes = set(RULE_ENGINE.grad_req.get("special_courses", {}).get("codes", []))

    # groups maps (calendar_year, sem) → list of (gpa_points, credit_hours)
    groups: dict[tuple, list[tuple[float, float]]] = {}
    for rec in enrollments:
        code = rec.get("Course_Code", "")
        if code in special_codes:
            continue
        grade      = RULE_ENGINE.normalize_grade(rec.get("Grade", ""))
        grade_info = RULE_ENGINE._grade_map.get(grade)
        if not (grade_info and grade_info.get("counted_in_gpa", False)):
            continue
        gpa_val = rec.get("Course_GPA")
        if gpa_val is None:
            gpa_val = grade_info.get("points")
        if gpa_val is None:
            continue
        year = _parse_year(rec.get("Year"))
        sem  = str(rec.get("Semester") or "").lower().strip()
        if year <= 0 or not sem:
            continue
        ch = credit_map.get(code, 0.0)
        groups.setdefault((year, sem), []).append((float(gpa_val), ch))

    sem_order = {"fall": 0, "spring": 1, "summer": 2}
    history = []
    for (year, sem), pairs in sorted(
        groups.items(),
        key=lambda kv: (kv[0][0], sem_order.get(kv[0][1], 9)),
    ):
        total_ch = sum(ch for _, ch in pairs)
        if total_ch == 0:
            continue
        quality = sum(gpa * ch for gpa, ch in pairs)
        # year is the academic year start (e.g. 2022 from "2022-2023")
        # All seasons share the same academic year label
        label = f"{sem.capitalize()} '{str(year)[-2:]}-{str(year + 1)[-2:]}"
        history.append({"sem": label, "gpa": round(quality / total_ch, 3)})
    return history


# ---------------------------------------------------------------------------
# Planner helpers
# ---------------------------------------------------------------------------

def _retakeable_failed_hours(student_data: dict) -> int:
    """
    Count credit hours of courses that appear exactly once in enrollments
    with grade F or Abs — not-yet-retaken failures eligible for summer.
    """
    enrollments = student_data.get("enrollments", [])
    courses     = database.get_all_courses()
    credit_map  = {c["Code"]: float(c["Credit_Hours"]) for c in courses}

    counts = Counter(r.get("Course_Code", "") for r in enrollments)
    eligible = {"F", "Abs"}
    total = 0.0
    for rec in enrollments:
        code  = rec.get("Course_Code", "")
        grade = RULE_ENGINE.normalize_grade(rec.get("Grade", ""))
        if counts[code] == 1 and grade in eligible:
            total += credit_map.get(code, 0.0)
    return int(total)


_MILESTONE_EMOJIS = ["🌱", "📚", "🚀", "⭐", "🏆", "🎓", "🌟"]

# Academic calendar: what regular semester follows each semester type?
_NEXT_REGULAR = {"fall": "spring", "spring": "fall", "summer": "fall"}


def _last_sem_type_from_enrollments(enrollments: list[dict]) -> str:
    """
    Derive the type ('fall', 'spring', 'summer') of the student's most recent
    semester from enrollment rows. Falls back to 'spring'.
    """
    sem_order = {"fall": 0, "spring": 1, "summer": 2}
    latest_year  = -1
    latest_order = -1
    latest_type  = "spring"

    for rec in enrollments:
        year  = _parse_year(rec.get("Year"))
        sem   = str(rec.get("Semester", "")).lower().strip()
        order = sem_order.get(sem, -1)
        if order < 0:
            continue
        if year > latest_year or (year == latest_year and order > latest_order):
            latest_year  = year
            latest_order = order
            latest_type  = sem

    return latest_type


def _build_planner_milestones(
    cgpa: float,
    earned_hours: float,
    hours_for_grad: float,
    target_gpa: float,
    last_sem_gpa: float,
    admission_year: int,
    retakeable_hrs: float,
    last_sem_type: str = "spring",
) -> dict:
    """
    Iteratively project future semesters, consulting the Rule Engine each
    time to determine the student's maximum allowed credit hours.
    """
    remaining = hours_for_grad - earned_hours
    if remaining <= 0:
        return {"phase": "success", "milestones": [], "required_avg": round(cgpa, 2)}

    max_possible = min(4.0, round((cgpa * earned_hours + 4.0 * remaining) / hours_for_grad, 2))
    if target_gpa > max_possible + 0.005:
        return {"phase": "impossible", "max_gpa": max_possible}

    required_avg = round((target_gpa * hours_for_grad - cgpa * earned_hours) / remaining, 2)

    milestones: list[dict] = []
    cur_cgpa         = cgpa
    cur_earned       = earned_hours
    cur_last_sem_gpa = last_sem_gpa
    cur_retakeable   = float(retakeable_hrs)
    sem_num          = 1

    if last_sem_type == "spring" and cur_retakeable > 0:
        pending = "summer"
    else:
        pending = _NEXT_REGULAR.get(last_sem_type, "fall")

    while cur_earned < hours_for_grad:
        rem = hours_for_grad - cur_earned

        if pending == "summer":
            summer_hrs = min(6.0, cur_retakeable, rem)

            s_req    = min(4.0, round((target_gpa * hours_for_grad - cur_cgpa * cur_earned) / rem, 2))
            s_new_qp = cur_cgpa * cur_earned + s_req * summer_hrs
            s_earned = cur_earned + summer_hrs
            s_cgpa   = round(s_new_qp / s_earned, 2)
            s_last   = s_earned >= hours_for_grad

            milestones.append({
                "semNum":          sem_num,
                "type":            "summer",
                "creditHours":     summer_hrs,
                "requiredSemGPA":  s_req,
                "cumulativeGPA":   s_cgpa,
                "isLast":          s_last,
                "statusLabel":     "summer",
                "maxAllowedHours": 6,
                "warnings":        [
                    f"Summer retake window: {int(summer_hrs)} credit hour(s) of "
                    f"eligible failed courses available."
                ],
                "emoji":           "☀️",
            })

            cur_cgpa         = s_cgpa
            cur_earned       = s_earned
            cur_last_sem_gpa = s_req
            cur_retakeable  -= summer_hrs
            sem_num         += 1

            if s_last:
                break

            pending = "fall"

        else:
            status   = RULE_ENGINE.calculate_academic_status({
                "CGPA":              cur_cgpa,
                "Earned_Hours":      int(cur_earned),
                "Last_Semester_GPA": cur_last_sem_gpa,
                "Admission_Year":    admission_year,
                "Level":             None,
            })
            max_hrs  = status["max_credit_hours"]
            sem_hrs  = min(max_hrs, rem)

            sem_req  = min(4.0, round((target_gpa * hours_for_grad - cur_cgpa * cur_earned) / rem, 2))
            new_qp   = cur_cgpa * cur_earned + sem_req * sem_hrs
            new_earn = cur_earned + sem_hrs
            new_cgpa = round(new_qp / new_earn, 2)
            is_last  = new_earn >= hours_for_grad

            milestones.append({
                "semNum":          sem_num,
                "type":            "regular",
                "semesterType":    pending,
                "creditHours":     sem_hrs,
                "requiredSemGPA":  sem_req,
                "cumulativeGPA":   new_cgpa,
                "isLast":          is_last,
                "statusLabel":     status["status_label"],
                "maxAllowedHours": max_hrs,
                "warnings":        status["warnings"],
                "emoji":           _MILESTONE_EMOJIS[min(sem_num - 1, len(_MILESTONE_EMOJIS) - 1)],
            })

            cur_cgpa         = new_cgpa
            cur_earned       = new_earn
            cur_last_sem_gpa = sem_req
            sem_num         += 1

            if is_last:
                break

            if pending == "spring" and cur_retakeable > 0:
                pending = "summer"
            else:
                pending = _NEXT_REGULAR[pending]

    return {"phase": "success", "milestones": milestones, "required_avg": required_avg}


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16 MB."}), 413


@app.errorhandler(500)
def server_error(e):
    log.exception("Unhandled server error")
    return jsonify({"error": f"Server error: {e.original_exception}"}), 500


# ---------------------------------------------------------------------------
# Route: upload transcript
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload_transcript():
    """
    Accept a multipart PDF upload, parse it with pdf_parsing.transcript_parser,
    persist the student + enrollments via database.py, and store the new
    student_id in the Flask session.

    Request:  multipart/form-data  { file: <PDF> }
    Response: { "status": "ok", "courses_inserted": int }
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files["file"]

    if not uploaded.filename or not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only .pdf files are accepted"}), 400

    pdf_bytes = uploaded.read()

    if not pdf_bytes:
        return jsonify({"error": "Uploaded file is empty"}), 400

    if pdf_bytes[:10].lstrip()[:4] != _PDF_MAGIC:
        return jsonify({"error": "File does not appear to be a valid PDF"}), 400

    file_path = None
    try:
        filename  = f"upload_{uuid.uuid4()}.pdf"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        with open(file_path, "wb") as fh:
            fh.write(pdf_bytes)

        data = parse_transcript(file_path)

        os.remove(file_path)
        file_path = None  # prevent finally from re-attempting deletion

        if not isinstance(data, dict) or not {"student", "courses"}.issubset(data):
            log.error("parse_transcript returned unexpected structure")
            return jsonify({"error": "Transcript parsing returned incomplete data"}), 422

        if not data["courses"]:
            return jsonify({"error": "No courses could be extracted"}), 422

        # Purge any previous session before inserting new data
        old_id = session.get("student_id")
        if old_id:
            try:
                database.purge_student_session(int(old_id))
            except Exception as exc:
                log.warning("upload: failed to purge old session %s — %s", old_id, exc)
            session.clear()

        student_id = database.insert_student(data["student"])
        database.insert_courses(data["courses"], student_id)
        session["student_id"] = student_id

        log.info("Upload complete — student_id=%s courses=%d", student_id, len(data["courses"]))
        return jsonify({
            "status":           "ok",
            "courses_inserted": len(data["courses"]),
        }), 200

    except PDFEncryptedError as exc:
        return jsonify({"error": str(exc)}), 422
    except (PDFReadError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception:
        log.exception("Unhandled error in upload_transcript")
        return jsonify({"error": "Failed to process transcript"}), 500
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                log.debug("Temp file deleted in finally: %s", file_path)


# ---------------------------------------------------------------------------
# Route: session — student-id
# ---------------------------------------------------------------------------

@app.route("/api/session/student-id", methods=["GET"])
def session_student_id():
    """
    Return the student_id stored in the Flask session.

    Response (JSON):
        { "student_id": int }
    """
    student_id = session.get("student_id")
    if not student_id:
        return jsonify({"error": "No active student session. Please upload your transcript first."}), 401
    return jsonify({"student_id": student_id}), 200


# ---------------------------------------------------------------------------
# Route: session — purge
# ---------------------------------------------------------------------------

@app.route("/api/session/purge", methods=["POST"])
def session_purge():
    """
    Delete the student's data from the database and clear the Flask session.
    Called by the frontend via navigator.sendBeacon on tab close / page exit.

    Response (JSON):
        { "status": "purged" }  or  { "status": "no_session" }
    """
    student_id = session.get("student_id")
    if student_id:
        try:
            database.purge_student_session(int(student_id))
        except Exception as exc:
            log.warning("session_purge: failed to purge student %s — %s", student_id, exc)
        session.clear()
        return jsonify({"status": "purged"}), 200
    return jsonify({"status": "no_session"}), 200


# ---------------------------------------------------------------------------
# Route: planner — autofill
# ---------------------------------------------------------------------------

@app.route("/api/planner/autofill", methods=["GET"])
def planner_autofill():
    """
    Returns the student's stored academic data to pre-populate the planner form.

    Response (JSON):
        { "cgpa": float, "earnedHours": int, "hoursForGrad": int }
    """
    student_id = session.get("student_id")
    if not student_id:
        return jsonify({"error": "No active student session. Please upload your transcript first."}), 401

    student_data = database.get_student_with_enrollments(int(student_id))
    if not student_data:
        return jsonify({"error": "Student record not found."}), 404

    hours_for_grad = RULE_ENGINE.grad_req.get("total_credit_hours_required", 140)

    return jsonify({
        "cgpa":         round(float(student_data.get("CGPA", 0)), 2),
        "earnedHours":  int(student_data.get("Earned_Hours", 0)),
        "hoursForGrad": hours_for_grad,
    }), 200


# ---------------------------------------------------------------------------
# Route: planner — calculate
# ---------------------------------------------------------------------------

@app.route("/api/planner/calculate", methods=["POST"])
def planner_calculate():
    """
    Runs the dynamic Rule Engine planner simulation.

    Request body (JSON):
        { "cgpa": float, "earnedHours": float, "hoursForGrad": float, "targetGpa": float }

    Response (JSON):
        phase == "success":   { "phase": "success", "milestones": [...], "required_avg": float }
        phase == "impossible": { "phase": "impossible", "max_gpa": float }
    """
    body = request.get_json(silent=True) or {}

    try:
        cgpa           = float(body["cgpa"])
        earned_hours   = float(body["earnedHours"])
        hours_for_grad = float(body["hoursForGrad"])
        target_gpa     = float(body["targetGpa"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "cgpa, earnedHours, hoursForGrad and targetGpa are required."}), 400

    student_id     = session.get("student_id")
    last_sem_gpa   = 0.0
    admission_year = date.today().year
    retakeable_hrs = 0
    last_sem_type  = "spring"

    if student_id:
        student_data = database.get_student_with_enrollments(int(student_id))
        if student_data:
            last_sem_gpa   = float(student_data.get("Last_Semester_GPA") or 0.0)
            admission_year = int(student_data.get("Admission_Year") or date.today().year)
            retakeable_hrs = _retakeable_failed_hours(student_data)
            last_sem_type  = _last_sem_type_from_enrollments(
                student_data.get("enrollments", [])
            )

    result = _build_planner_milestones(
        cgpa, earned_hours, hours_for_grad, target_gpa,
        last_sem_gpa, admission_year, retakeable_hrs,
        last_sem_type=last_sem_type,
    )
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# Route: recommend
# ---------------------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend():
    """
    Request body (JSON):
        { "student_id": <int>, "target_semester": "fall" | "spring" | "summer" }

    Response (JSON):
        {
          "student_id":              int,
          "target_semester":         str,
          "academic_status":         str,
          "max_allowed_hours":       int,
          "warnings":                [str, …],
          "total_recommended_hours": float,
          "top_recommended":         [ {course + prediction fields}, … ],
          "alternative_courses":     [ {course + prediction fields}, … ],
          "student_stats": {
              "cgpa":             float,
              "earned_hours":     int,
              "total_hours":      int,
              "last_sem_gpa":     float,
              "semester_history": [ { "sem": str, "gpa": float }, … ]
          }
        }
    """
    body = request.get_json(silent=True) or {}

    student_id      = body.get("student_id")
    target_semester = str(body.get("target_semester", "")).lower().strip()

    if not student_id or not target_semester:
        return jsonify({"error": "student_id and target_semester are required"}), 400

    # ── Fetch data from DB ────────────────────────────────────────────────────
    student_data = database.get_student_with_enrollments(int(student_id))
    if not student_data:
        return jsonify({"error": f"Student {student_id} not found"}), 404

    available_courses = database.get_all_courses()
    prerequisites_map = database.get_prerequisites_map()
    course_df         = _get_course_df()

    # ── Capture student stats before any further processing ───────────────────
    total_hours = int(RULE_ENGINE.grad_req.get("total_credit_hours_required", 140))
    student_stats = {
        "cgpa":             round(float(student_data.get("CGPA", 0)), 2),
        "earned_hours":     int(student_data.get("Earned_Hours", 0)),
        "total_hours":      total_hours,
        "last_sem_gpa":     round(float(student_data.get("Last_Semester_GPA") or 0), 2),
        "semester_history": _build_semester_history(student_data.get("enrollments", []), available_courses),
    }

    # ── Graduation check (before anything else) ───────────────────────────────
    earned_hours = int(student_data.get("Earned_Hours", 0))
    if earned_hours >= total_hours:
        return jsonify({"error": "graduated"}), 422

    # ── Semester sequence check ───────────────────────────────────────────────
    enrollments = student_data.get("enrollments", [])
    last_sem    = _last_sem_type_from_enrollments(enrollments)
    valid_next  = _NEXT_REGULAR.get(last_sem)
    if target_semester not in (valid_next, last_sem):
        return jsonify({"error": "invalid-sequence"}), 422

    # ── Rule Engine ───────────────────────────────────────────────────────────
    rule_payload = RULE_ENGINE.process(
        student_data,
        available_courses,
        prerequisites_map,
        target_semester,
    )

    # ── Semester-completed check ──────────────────────────────────────────────
    if not rule_payload["engine_suggested_courses"]:
        return jsonify({"error": "semester-completed"}), 422

    # ── ML ranking + greedy selector ─────────────────────────────────────────
    try:
        result = ml_predict.recommend(
            student_data,
            rule_payload,
            course_df,
            prerequisites_map,
        )
    except FileNotFoundError as exc:
        return jsonify({
            "error": str(exc),
            "hint":  "POST /api/admin/retrain to train the model first.",
        }), 503

    # ── Anonymise + append to training CSVs ───────────────────────────────────
    # Student data is NOT purged here. It persists in the DB until the user
    # exits the page (sendBeacon → POST /api/session/purge) or the TTL job
    # removes it after 24 hours.
    anonymize_and_append(student_data)

    return jsonify({
        **result,
        "student_stats":        student_stats,
        "all_eligible_courses": rule_payload.get("all_eligible_courses", []),
    }), 200


# ---------------------------------------------------------------------------
# Route: admin retrain
# ---------------------------------------------------------------------------

@app.route("/api/admin/retrain", methods=["POST"])
def retrain():
    """
    Triggers a full retrain of the ML model from the CSV training dataset.

    Response (JSON):
        { "status": "success", "metrics": { … } }
    """
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")
        with _CSV_LOCK:
            metrics = train_and_save(data_dir=data_dir)
        return jsonify({"status": "success", "metrics": metrics}), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


# ---------------------------------------------------------------------------
# Dev-only route: seed Flask session with a student_id for testing
# Only registered when FLASK_ENV=development — never exposed in production.
# ---------------------------------------------------------------------------

if os.environ.get("FLASK_ENV", "production") == "development":
    @app.route("/api/dev/session/init", methods=["POST"])
    def dev_session_init():
        body       = request.get_json(silent=True) or {}
        student_id = body.get("student_id")
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        session["student_id"] = int(student_id)
        return jsonify({"status": "ok", "student_id": int(student_id)}), 200


# ---------------------------------------------------------------------------
# Dev server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, reloader_type="stat")
