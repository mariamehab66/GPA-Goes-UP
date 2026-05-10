import logging
import os

import pandas as pd
from flask import Blueprint, request, jsonify

import database
from chatbot.gemini_client import ask_gemini
from chatbot.prompt_builder import build_prompt
from chatbot.student_insights import build_student_insights
from rule_engine import AcademicRuleEngine
from ml.predict import recommend

log = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__)

# =====================================================
# LOAD RULE ENGINE
# =====================================================

_RULE_ENGINE_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "Rule_Engine.json"
)

_engine = AcademicRuleEngine(
    _RULE_ENGINE_JSON
)


# =====================================================
# HELPERS
# =====================================================

def _get_course_df() -> pd.DataFrame:
    df = pd.DataFrame(database.get_all_courses())
    if df.empty:
        return df
    for col in ("Is_elective", "Is_practical"):
        if col in df.columns:
            df[col] = df[col].astype(bool)
    if "Semester" in df.columns:
        df["Semester"] = df["Semester"].str.lower().str.strip()
    return df


# =====================================================
# DATABASE HELPERS
# =====================================================

def _fetch_student(conn, student_id: int) -> dict | None:

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Student WHERE ID = %s",
        (student_id,)
    )

    row = cursor.fetchone()

    cursor.close()

    return row


def _fetch_enrollments(conn, student_id: int) -> list:

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM Enrollment
        WHERE Student_ID = %s
        ORDER BY Year, Semester
        """,
        (student_id,)
    )

    rows = cursor.fetchall()

    cursor.close()

    return rows


def _fetch_prerequisites(conn) -> dict:

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            Course_Code,
            Prerequisite_Course_Code
        FROM Prerequisite
        """
    )

    rows = cursor.fetchall()

    cursor.close()

    prereqs = {}

    for row in rows:

        code = row["Course_Code"]

        prereq = row[
            "Prerequisite_Course_Code"
        ]

        prereqs.setdefault(
            code,
            []
        ).append(prereq)

    return prereqs


# =====================================================
# CHAT ROUTE
# =====================================================

@chatbot_bp.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.get_json()

    if not data:

        return jsonify({
            "error":
            "No JSON body provided"
        }), 400

    student_id = data.get(
        "student_id"
    )

    message = data.get(
        "message",
        ""
    ).strip()

    semester     = (data.get("semester")     or "fall").strip().lower()
    page_context = (data.get("page_context") or "").strip()

    if not student_id:

        return jsonify({
            "error":
            "student_id is required"
        }), 400

    if not message:

        return jsonify({
            "error":
            "message is required"
        }), 400

    conn = None

    try:

        conn = database.get_connection()

        # =====================================================
        # FETCH DATABASE DATA
        # =====================================================

        student = _fetch_student(
            conn,
            student_id
        )

        enrollments = _fetch_enrollments(
            conn,
            student_id
        )

        prerequisites = _fetch_prerequisites(
            conn
        )

        if not student:

            return jsonify({
                "error":
                f"Student {student_id} not found"
            }), 404

        # =====================================================
        # LOAD COURSE DATA FROM DATABASE
        # =====================================================

        course_df = _get_course_df()

        courses = database.get_all_courses()

        # =====================================================
        # BUILD STUDENT INSIGHTS
        # =====================================================

        insights = build_student_insights(
            enrollments
        )

        # =====================================================
        # PREPARE RULE ENGINE INPUT
        # =====================================================

        student_for_engine = dict(student)

        student_for_engine["enrollments"] = [

            {
                "Course_Code":
                    e["Course_Code"],

                "Grade":
                    e.get("Grade", ""),

                "Marks":
                    e.get("Marks", 0),

                "Year":
                    e.get("Year", ""),

                "Semester":
                    e.get("Semester", ""),

                "Course_GPA":
                    e.get("Course_GPA", 0),
            }

            for e in enrollments
        ]

        # =====================================================
        # RUN RULE ENGINE
        # =====================================================

        rule_result = None

        try:

            rule_result = _engine.process(

                student_data=student_for_engine,

                available_courses=courses,

                prerequisites_map=prerequisites,

                target_semester=semester,
            )

        except Exception:

            log.exception(
                "Rule engine failed "
                "for student %s",
                student_id
            )

        # =====================================================
        # RUN ML RECOMMENDATION ENGINE
        # =====================================================

        ml_result = None

        try:

            ml_result = recommend(

                student_data=student_for_engine,

                rule_engine_payload=rule_result,

                course_df=course_df,

                prerequisites_map=prerequisites,
            )

        except Exception:

            log.exception(
                "ML recommendation failed "
                "for student %s",
                student_id
            )

        # =====================================================
        # BUILD PROMPT
        # =====================================================

        # Off-topic guard — intercept before calling Gemini
        has_arabic = any("؀" <= c <= "ۿ" for c in message)
        academic_keywords = [
            "course", "register", "gpa", "grade", "credit", "hour", "semester",
            "prerequisite", "study", "exam", "subject", "level", "program",
            "cgpa", "sgpa", "fail", "pass", "retake", "stat", "comp", "math", "phys",
            "chem", "engl", "probability", "algorithm", "database", "academic",
            "graduation", "schedule", "recommend", "advise", "enroll",
            "simulator", "simulate", "calculator", "calculate", "planner", "plan",
            "milestone", "remaining", "result", "explain", "show", "target",
            "prediction", "difficulty", "score", "cumulative", "semester gpa",
            "مقرر", "دراسة",
            "تسجيل", "معدل",
            "فصل", "ساعة",
            "رسب", "نجح",
            "خطة", "برنامج",
            "محاكاة", "حاسبة", "مخطط", "نتيجة", "شرح",
        ]
        msg_lower = message.lower()
        is_academic = any(kw in msg_lower for kw in academic_keywords)

        if not is_academic:
            refusal = (
                "عذرًا، أنا "
                "متخصص فقط "
                "للإرشاد "
                "الأكاديمي. "
                "كيف يمكنني "
                "مساعدتك؟"
                if has_arabic else
                "Sorry, I'm only here to help with academic advising for this program. "
                "What can I help you with regarding your studies?"
            )
            return jsonify({
                "response": refusal,
                "rule_result": None,
                "ml_result": None,
                "student_insights": None,
                "student_id": student_id,
            }), 200

        prompt = build_prompt(
            student_data=student,
            enrollment_history=enrollments,
            rule_engine_result=rule_result,
            student_insights=insights,
            ml_result=ml_result,
            user_message=message,
            page_context=page_context,
        )

        # =====================================================
        # GEMINI RESPONSE
        # =====================================================

        response = ask_gemini(
            prompt
        )

        return jsonify({

            "response":
                response,

            "rule_result":
                rule_result,

            "ml_result":
                ml_result,

            "student_insights":
                insights,

            "student_id":
                student_id,

        }), 200

    except Exception:

        log.exception(
            "Chat endpoint error "
            "for student %s",
            student_id
        )

        return jsonify({
            "error":
            "Internal error "
            "processing your request"
        }), 500

    finally:

        if conn:

            conn.close()
