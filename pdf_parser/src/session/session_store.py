"""
session_store.py — Session-scoped storage for parsed transcript results.

Schema requirements (additions to the base SQL schema):
  ALTER TABLE Student ADD COLUMN session_id VARCHAR(64) NULL;
  ALTER TABLE Student MODIFY COLUMN ID INT NOT NULL AUTO_INCREMENT;
  ALTER TABLE Enrollment ADD COLUMN Course_Grade VARCHAR(10) NULL;
  ALTER TABLE Enrollment MODIFY COLUMN Enrollment_ID INT NOT NULL AUTO_INCREMENT;

These columns are required for session-scoped cleanup and grade persistence.
The base schema (database_codeCreation.sql) should be run first, then these
ALTER statements applied before using this feature.

T033: register_teardown() wires a Flask teardown_appcontext hook so that all
session IDs accumulated in Flask `g.session_ids` during a request are deleted
from the DB when the application context tears down (end of request or timeout).
"""
import logging

from sqlalchemy import text

from ..models.parse_result import ParseResult

log = logging.getLogger(__name__)


class SessionStore:
    """Handles inserting and cleaning up session-scoped Student/Enrollment rows."""

    def save(
        self, session_id: str, result: ParseResult, db_session
    ) -> tuple[int, list[int]]:
        """
        Insert one Student row and N Enrollment rows into the database.

        All rows are tagged with `session_id` for later cleanup.
        IDs are assigned by MySQL AUTO_INCREMENT; never derived from the PDF.

        Returns:
            (student_id, [enrollment_id, ...])
        """
        s = result.student

        student_insert = text(
            """
            INSERT INTO Student
                (CGPA, Program, Earned_Hours, Last_Semester_GPA, Level, Admission_Year, session_id)
            VALUES
                (:cgpa, :program, :earned_hours, :last_semester_gpa, :level, :admission_year, :session_id)
            """
        )
        db_session.execute(student_insert, {
            "cgpa": s.cgpa,
            "program": s.program,
            "earned_hours": s.earned_hours,
            "last_semester_gpa": s.last_semester_gpa,
            "level": s.level,
            "admission_year": s.admission_year,
            "session_id": session_id,
        })

        student_id: int = db_session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        enrollment_ids: list[int] = []
        enrollment_insert = text(
            """
            INSERT INTO Enrollment
                (Student_ID, Course_Code, Course_Grade, Course_GPA, Year, Semester)
            VALUES
                (:student_id, :course_code, :course_grade, :course_gpa, :year, :semester)
            """
        )
        for course in result.enrollments:
            db_session.execute(enrollment_insert, {
                "student_id": student_id,
                "course_code": course.course_code,
                "course_grade": course.course_grade,
                "course_gpa": course.course_gpa,
                "year": course.year,
                "semester": course.semester,
            })
            eid: int = db_session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            enrollment_ids.append(eid)

        db_session.commit()
        return student_id, enrollment_ids

    def cleanup(self, session_id: str, db_session) -> None:
        """
        Delete all Student and Enrollment rows associated with `session_id`.

        Enrollment rows are deleted first to satisfy FK constraints.
        """
        delete_enrollments = text(
            """
            DELETE e FROM Enrollment e
            INNER JOIN Student s ON e.Student_ID = s.ID
            WHERE s.session_id = :session_id
            """
        )
        db_session.execute(delete_enrollments, {"session_id": session_id})

        delete_student = text(
            "DELETE FROM Student WHERE session_id = :session_id"
        )
        db_session.execute(delete_student, {"session_id": session_id})
        db_session.commit()


def register_teardown(app, get_db_session_fn) -> None:
    """
    T033: Register a Flask teardown_appcontext hook for session-scoped cleanup.

    Call this once during app factory setup:
        register_teardown(app, lambda: g.get("db_session"))

    On every request teardown, deletes all Student/Enrollment rows whose
    session_id was recorded in g.session_ids during the request.

    Args:
        app:               Flask application instance.
        get_db_session_fn: Zero-argument callable returning the SQLAlchemy
                           session for the current app context, or None.
    """
    store = SessionStore()

    @app.teardown_appcontext
    def _cleanup_sessions(exc):  # noqa: ANN001
        from flask import g  # local import avoids circular dependency

        session_ids: list[str] = g.get("session_ids", [])
        if not session_ids:
            return

        db_session = get_db_session_fn()
        if db_session is None:
            return

        for sid in session_ids:
            try:
                store.cleanup(sid, db_session)
                log.debug("session_teardown: cleaned up session_id=%s", sid)
            except Exception:
                log.exception("session_teardown: cleanup failed for session_id=%s", sid)
