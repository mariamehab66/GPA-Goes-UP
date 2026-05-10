"""
ml/csv_appender.py

Anonymises a student's session data and appends it to the two permanent
training CSV files (student.csv, enrollment.csv) before the operational
DB is purged.

Anonymisation:
  - Student_ID and Enrollment_ID are replaced by new sequential IDs that
    continue from the last row already present in each CSV.
  - Everything else (CGPA, Earned_Hours, Level, Admission_Year, Program,
    all course codes, grades, marks, years, semesters) is kept unchanged.
  - No names, national IDs, or any other PII ever enter the CSV files.

Duplicate detection  (Q1 answer):
  Two students may share the same aggregate stats (CGPA, earned hours,
  admission year) but are astronomically unlikely to have identical
  course-by-course histories. The check compares the incoming student's
  first 10 chronological enrollment rows against every existing student
  block in enrollment.csv on five fields:
    Course_Code, Grade, Marks, Year, Semester
  If all compared rows match → duplicate → skip.

File locking:
  A shared FileLock (csv_lock.lock) is acquired by both this module
  (writer) and scheduler.py (reader/trainer). This prevents the scheduler
  from reading a half-written CSV during an append.

State tracking:
  ml/models/training_state.json records how many new students have been
  appended since the last retrain. The scheduler reads this to decide when
  to fire.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime

import pandas as pd
from filelock import FileLock, Timeout

from ml.data_loader import COURSE_CODE_FIXES, SEM_ORDER
from ml import r2_storage

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRAINING_DIR  = os.path.join(_BASE_DIR, "data", "training")
STUDENT_CSV    = os.path.join(_TRAINING_DIR, "student.csv")
ENROLLMENT_CSV = os.path.join(_TRAINING_DIR, "enrollment.csv")
_MODELS_DIR    = os.path.join(_BASE_DIR, "ml", "models")
STATE_FILE     = os.path.join(_MODELS_DIR, "training_state.json")
LOCK_FILE      = os.path.join(_MODELS_DIR, "csv_lock.lock")

# Shared lock — imported by scheduler.py so both processes use the same file.
LOCK = FileLock(LOCK_FILE, timeout=30)

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"new_students_since_last_retrain": 0, "last_retrain_timestamp": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"new_students_since_last_retrain": 0, "last_retrain_timestamp": None}


def _save_state(state: dict) -> None:
    os.makedirs(_MODELS_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


def get_new_student_count() -> int:
    """Return how many students have been appended since the last retrain."""
    return _load_state().get("new_students_since_last_retrain", 0)


def reset_new_student_count() -> None:
    """Called by the scheduler after a successful retrain."""
    state = _load_state()
    state["new_students_since_last_retrain"] = 0
    state["last_retrain_timestamp"] = datetime.now().isoformat()
    _save_state(state)


# ---------------------------------------------------------------------------
# Duplicate detection helpers
# ---------------------------------------------------------------------------

def _normalize_marks(value) -> str:
    """Convert any marks representation to a plain integer string: 112.0 → '112'."""
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value).strip()


def _build_fingerprint(enrollments: list[dict], n: int = 10) -> list[tuple]:
    """
    Sort the enrollment list chronologically and return the first *n* rows
    as (Course_Code, Grade, Marks, Year, Semester) tuples for comparison.
    Marks are normalised to plain integer strings to avoid float noise.
    """
    normalised = []
    for e in enrollments:
        code = str(e.get("Course_Code", ""))
        code = COURSE_CODE_FIXES.get(code, code)
        normalised.append({
            "Course_Code": code,
            "Grade":       str(e.get("Grade", "")).strip(),
            "Marks":       _normalize_marks(e.get("Marks", 0)),
            "Year":        str(e.get("Year", "")).strip(),
            "Semester":    str(e.get("Semester", "")).lower().strip(),
            "_year_int":   int(str(e.get("Year", "0")).split("-")[0]) if "-" in str(e.get("Year", "")) else 0,
            "_sem_int":    SEM_ORDER.get(str(e.get("Semester", "")).lower().strip(), 0),
        })

    normalised.sort(key=lambda r: (r["_year_int"], r["_sem_int"]))

    return [
        (r["Course_Code"], r["Grade"], r["Marks"], r["Year"], r["Semester"])
        for r in normalised[:n]
    ]


def _is_duplicate(new_fp: list[tuple]) -> bool:
    """
    Return True if *new_fp* matches the first-N rows of any existing student
    already in enrollment.csv.
    """
    if not new_fp or not os.path.exists(ENROLLMENT_CSV):
        return False

    try:
        df = pd.read_csv(ENROLLMENT_CSV, dtype=str)
    except Exception:
        return False

    if df.empty:
        return False

    # Normalise existing data for comparison
    df["Course_Code"] = df["Course_Code"].replace(COURSE_CODE_FIXES)
    df["Semester"]    = df["Semester"].str.lower().str.strip()
    df["Marks"]       = df["Marks"].apply(_normalize_marks)
    df["_year_int"]   = df["Year"].apply(
        lambda y: int(str(y).split("-")[0]) if "-" in str(y) else 0
    )
    df["_sem_int"] = df["Semester"].map(SEM_ORDER).fillna(0).astype(int)

    n = len(new_fp)

    for _, grp in df.groupby("Student_ID"):
        grp_sorted = grp.sort_values(["_year_int", "_sem_int"])
        existing_fp = list(zip(
            grp_sorted["Course_Code"].head(n),
            grp_sorted["Grade"].head(n),
            grp_sorted["Marks"].head(n),
            grp_sorted["Year"].head(n),
            grp_sorted["Semester"].head(n),
        ))
        # Only declare duplicate when we have enough rows to compare
        if len(existing_fp) >= n and existing_fp == new_fp:
            return True

    return False


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def _next_student_id() -> int:
    if not os.path.exists(STUDENT_CSV):
        return 1
    try:
        df = pd.read_csv(STUDENT_CSV, usecols=["ID"])
        return int(df["ID"].max()) + 1 if not df.empty else 1
    except Exception:
        return 1


def _next_enrollment_id() -> int:
    if not os.path.exists(ENROLLMENT_CSV):
        return 1
    try:
        df = pd.read_csv(ENROLLMENT_CSV, usecols=["Enrollment_ID"])
        return int(df["Enrollment_ID"].max()) + 1 if not df.empty else 1
    except Exception:
        return 1


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

STUDENT_FIELDS    = ["ID", "CGPA", "Program", "Earned_Hours",
                      "Last_Semester_GPA", "Level", "Admission_Year"]
ENROLLMENT_FIELDS = ["Enrollment_ID", "Course_GPA", "Course_Code", "Grade",
                      "Marks", "Student_ID", "Year", "Semester"]


def anonymize_and_append(student_data: dict) -> bool:
    """
    Anonymise *student_data* and append it to the two training CSV files.

    Args:
        student_data: The student dict fetched from MySQL during the session.
                      Must contain an 'enrollments' list.

    Returns:
        True  — data was appended and the retrain counter was incremented.
        False — skipped (duplicate, empty history, lock timeout, or any error).

    This function is intentionally exception-safe: it never raises, so a CSV
    failure cannot crash the Flask recommendation response.
    """
    enrollments = student_data.get("enrollments", [])
    if not enrollments:
        log.warning("[csv_appender] No enrollments found — skipping append.")
        return False

    # Build fingerprint before acquiring the lock (pure computation, fast).
    new_fp = _build_fingerprint(enrollments, n=10)
    if not new_fp:
        return False

    try:
        with LOCK:
            if _is_duplicate(new_fp):
                log.info("[csv_appender] Duplicate student detected — skipping append.")
                return False

            new_sid = _next_student_id()
            new_eid = _next_enrollment_id()

            # ── student.csv ───────────────────────────────────────────────
            student_row = {
                "ID":                new_sid,
                "CGPA":              student_data.get("CGPA", 0.0),
                "Program":           student_data.get("Program", ""),
                "Earned_Hours":      student_data.get("Earned_Hours", 0),
                "Last_Semester_GPA": student_data.get("Last_Semester_GPA", 0.0),
                "Level":             student_data.get("Level", 1),
                "Admission_Year":    student_data.get("Admission_Year", 2022),
            }
            needs_header = not os.path.exists(STUDENT_CSV)
            with open(STUDENT_CSV, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=STUDENT_FIELDS)
                if needs_header:
                    writer.writeheader()
                writer.writerow(student_row)

            # ── enrollment.csv ────────────────────────────────────────────
            needs_header = not os.path.exists(ENROLLMENT_CSV)
            with open(ENROLLMENT_CSV, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=ENROLLMENT_FIELDS)
                if needs_header:
                    writer.writeheader()
                for e in enrollments:
                    code = str(e.get("Course_Code", ""))
                    code = COURSE_CODE_FIXES.get(code, code)
                    writer.writerow({
                        "Enrollment_ID": new_eid,
                        "Course_GPA":    e.get("Course_GPA", 0.0),
                        "Course_Code":   code,
                        "Grade":         e.get("Grade", ""),
                        "Marks":         e.get("Marks", 0.0),
                        "Student_ID":    new_sid,
                        "Year":          e.get("Year", ""),
                        "Semester":      str(e.get("Semester", "")).lower().strip(),
                    })
                    new_eid += 1

            # ── increment state counter ───────────────────────────────────
            state = _load_state()
            state["new_students_since_last_retrain"] += 1
            _save_state(state)

            log.info(
                f"[csv_appender] Appended student {new_sid} "
                f"({len(enrollments)} enrollment rows). "
                f"New students since last retrain: "
                f"{state['new_students_since_last_retrain']}."
            )

            # ── persist to R2 so the next container restart is up-to-date ────
            r2_storage.upload_csvs()

            return True

    except Timeout:
        log.warning("[csv_appender] Could not acquire CSV lock — skipping append.")
        return False
    except Exception as exc:
        log.warning(f"[csv_appender] Append failed: {exc}")
        return False
