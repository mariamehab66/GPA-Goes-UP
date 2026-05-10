"""
database.py

MySQL connection layer for GPA Goes UP.
All credentials are read from environment variables — never hardcode them.
See .env.example for the full list of required variables.
"""

import os

import mysql.connector
import pandas as pd

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", "3306")),
    "user":     os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "gpa_goes"),
    "charset":  "utf8mb4",
    # TiDB Cloud Serverless requires SSL; local MySQL works with ssl_disabled=True.
    "ssl_disabled": os.environ.get("DB_SSL", "true").lower() == "false",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_df(query: str, params=None) -> pd.DataFrame:
    """Execute a SELECT and return results as a DataFrame."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    finally:
        cur.close()
        conn.close()


def get_student_with_enrollments(student_id: int) -> dict | None:
    """Return the Student row merged with its full Enrollment history, or None."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM Student WHERE ID = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            return None

        cur.execute(
            """
            SELECT Enrollment_ID, Course_GPA, Course_Code, Grade,
                   Marks, Student_ID, Year, Semester
            FROM   Enrollment
            WHERE  Student_ID = %s
            """,
            (student_id,),
        )
        student["enrollments"] = cur.fetchall()
        return student
    finally:
        cur.close()
        conn.close()


def get_all_courses() -> list[dict]:
    """Return every row from the Course table as a list of dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Course")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def purge_student_session(student_id: int) -> None:
    """
    Delete the student and all their enrollment rows from the operational DB.

    The Enrollment table has ON DELETE CASCADE on Student_ID, so a single
    DELETE on Student removes everything in one round-trip.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Student WHERE ID = %s", (student_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_session_timestamp_column() -> None:
    """Add session_created_at to Student if not present (safe to call on every startup)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            ALTER TABLE Student
            ADD COLUMN session_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )
        conn.commit()
    except Exception:
        # Column already exists — normal on every run after the first.
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def get_stale_session_ids(max_age_hours: int = 24) -> list[int]:
    """Return Student IDs whose session_created_at is older than max_age_hours."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT ID FROM Student WHERE session_created_at < NOW() - INTERVAL %s HOUR",
            (max_age_hours,),
        )
        return [row["ID"] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


_ENROLLMENT_BATCH_SIZE = 100
_NULL_GPA_GRADES = {"P", "NP", "W", "I", "غ"}


def insert_student(student: dict) -> int:
    """Insert one Student row and return its AUTO_INCREMENT ID."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Student
                (CGPA, Program, Earned_Hours, Last_Semester_GPA, Level, Admission_Year)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                student.get("cgpa"),
                student.get("program"),
                student.get("earned_hours"),
                student.get("last_semester_gpa"),
                student.get("level"),
                student.get("admission_year"),
            ),
        )
        student_id = cur.lastrowid
        conn.commit()
        return student_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def insert_courses(courses: list, student_id: int) -> int:
    """
    Upsert Course rows (INSERT IGNORE) and batch-insert Enrollment rows.
    Returns count of enrollments inserted.
    """
    if not courses:
        return 0

    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    try:
        for course in courses:
            cur.execute(
                """
                INSERT IGNORE INTO Course
                    (Code, Credit_Hours, Type, Is_elective, Is_practical)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (course["code"], course.get("credits", 0), "Other", False, False),
            )

        enrollment_rows = []
        for course in courses:
            year  = course.get("year")
            if not year or year == "Unknown":
                year = None
            grade      = course.get("grade")
            gpa_points = None if grade in _NULL_GPA_GRADES else course.get("points")
            enrollment_rows.append((
                gpa_points,
                course.get("code"),
                grade,
                course.get("score"),
                student_id,
                year,
                course.get("semester"),
            ))

        for i in range(0, len(enrollment_rows), _ENROLLMENT_BATCH_SIZE):
            batch = enrollment_rows[i : i + _ENROLLMENT_BATCH_SIZE]
            cur.executemany(
                """
                INSERT INTO Enrollment
                    (Course_GPA, Course_Code, Grade, Marks, Student_ID, Year, Semester)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                batch,
            )
            inserted += len(batch)

        conn.commit()
        return inserted

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_prerequisites_map() -> dict[str, list[str]]:
    """Return {course_code: [prereq_code, ...]} built from the Prerequisite table."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT Course_Code, Prerequisite_Course_Code FROM Prerequisite")
        result: dict[str, list[str]] = {}
        for row in cur.fetchall():
            result.setdefault(row["Course_Code"], []).append(
                row["Prerequisite_Course_Code"]
            )
        return result
    finally:
        cur.close()
        conn.close()
