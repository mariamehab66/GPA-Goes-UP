import logging
from pdf_parsing.db_connection import get_connection

log = logging.getLogger(__name__)


def reset_database() -> None:
    """
    Wipe session data only (Enrollment + Student + Course).
    Prerequisite table is NEVER touched — it is static ML reference data.
    Course rows referenced by Prerequisite are preserved automatically
    by the ON DELETE RESTRICT foreign key in the schema.
    """
    conn   = None
    cursor = None

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # ── Audit counts before deletion ──────────────────────────────────────
        cursor.execute("SELECT COUNT(*) FROM Enrollment")
        enrollment_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Student")
        student_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Course")
        course_count = cursor.fetchone()[0]

        # ── Delete in FK-safe order ───────────────────────────────────────────

        # Enrollment first — references both Course and Student
        cursor.execute("DELETE FROM Enrollment")

        # Student next — safe once Enrollment is gone
        cursor.execute("DELETE FROM Student")

        # Course last — skip any codes referenced by Prerequisite.
        # ON DELETE RESTRICT on Prerequisite's FK would block those anyway,
        # but this explicit WHERE makes the intent clear and avoids a DB error.
        cursor.execute("""
            DELETE FROM Course
            WHERE Code NOT IN (
                SELECT DISTINCT Course_Code FROM Prerequisite
                UNION
                SELECT DISTINCT Prerequisite_Course_Code FROM Prerequisite
            )
        """)

        # ── Reset AUTO_INCREMENT ──────────────────────────────────────────────
        cursor.execute("ALTER TABLE Student    AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Enrollment AUTO_INCREMENT = 1")

        conn.commit()

        log.info(
            "Session reset complete — cleared %d enrollments, "
            "%d students, %d courses. Prerequisites preserved.",
            enrollment_count, student_count, course_count
        )

    except Exception:
        if conn:
            conn.rollback()
        log.exception("Database reset failed")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()