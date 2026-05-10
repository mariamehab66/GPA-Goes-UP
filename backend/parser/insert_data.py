import logging
from pdf_parsing.db_connection import get_connection

log = logging.getLogger(__name__)

_ENROLLMENT_BATCH_SIZE = 100


def _upsert_course(cursor, course: dict) -> None:
    """
    Insert course into Course table if it doesn't already exist.
    Type/Is_elective/Is_practical are unknown from transcript — safe defaults.
    """
    cursor.execute("""
        INSERT IGNORE INTO Course
            (Code, Credit_Hours, Type, Is_elective, Is_practical)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        course["code"],
        course.get("credits", 0),
        "Other",
        False,
        False,
    ))


def insert_student(student: dict, conn=None) -> int:
    """
    Insert one Student row. Returns the AUTO_INCREMENT generated ID.
    If conn is provided, caller manages commit/rollback.
    """
    close_conn = conn is None
    if close_conn:
        conn = get_connection()

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Student
                (CGPA, Program, Earned_Hours, Last_Semester_GPA,
                 Level, Admission_Year)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            student.get("cgpa"),
            student.get("program"),
            student.get("earned_hours"),
            student.get("last_semester_gpa"),
            student.get("level"),
            student.get("admission_year"),
        ))

        student_id = cursor.lastrowid
        log.info("Inserted Student ID=%s CGPA=%s", student_id, student.get("cgpa"))

        if close_conn:
            conn.commit()

        return student_id

    except Exception:
        if close_conn:
            conn.rollback()
        log.exception("Failed to insert student")
        raise

    finally:
        cursor.close()
        if close_conn:
            conn.close()


def insert_courses(courses: list, student_id: int, conn=None) -> int:
    """
    Insert Course rows (if new) and Enrollment rows for all courses.
    Returns count of enrollments inserted.
    If conn is provided, caller manages commit/rollback.
    """
    if not courses:
        log.warning("insert_courses called with empty list")
        return 0

    close_conn = conn is None
    if close_conn:
        conn = get_connection()

    cursor = conn.cursor()
    inserted = 0

    # Grades where Course_GPA should be NULL — not a numeric outcome
    _NULL_GPA_GRADES = {"P", "NP", "W", "I", "غ"}

    try:
        # ── Step 1: Upsert Course rows ────────────────────────────────────────
        for course in courses:
            _upsert_course(cursor, course)

        # ── Step 2: Build Enrollment rows ─────────────────────────────────────
        enrollment_rows = []
        for course in courses:
            year = course.get("year")
            if not year or year == "Unknown":
                year = None

            grade = course.get("grade")

            # Store NULL for Course_GPA on absent/pass-fail grades
            # so ML model distinguishes them from a genuine 0.0 (F grade)
            gpa_points = (
                None if grade in _NULL_GPA_GRADES
                else course.get("points")
            )

            enrollment_rows.append((
                gpa_points,              # Course_GPA (NULL for غ/P/NP/W/I)
                course.get("code"),      # Course_Code
                grade,                   # Grade
                course.get("score"),     # Marks
                student_id,              # Student_ID
                year,                    # Year
                course.get("semester"),  # Semester
            ))

        # ── Step 3: Batch insert Enrollment rows ──────────────────────────────
        for i in range(0, len(enrollment_rows), _ENROLLMENT_BATCH_SIZE):
            batch = enrollment_rows[i: i + _ENROLLMENT_BATCH_SIZE]
            cursor.executemany("""
                INSERT INTO Enrollment
                    (Course_GPA, Course_Code, Grade, Marks,
                     Student_ID, Year, Semester)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
            inserted += len(batch)
            log.debug("Inserted batch of %d enrollment rows", len(batch))

        log.info("Inserted %d enrollments for Student ID=%s", inserted, student_id)

        if close_conn:
            conn.commit()

        return inserted

    except Exception:
        if close_conn:
            conn.rollback()
        log.exception("Failed to insert courses for student_id=%s", student_id)
        raise

    finally:
        cursor.close()
        if close_conn:
            conn.close()