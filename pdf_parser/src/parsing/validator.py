"""
validator.py — Student record and course code validation.
Uses LEVEL_THRESHOLDS from config to classify academic level.
"""
import re

from ..config import LEVEL_THRESHOLDS
from ..exceptions import MissingRequiredFieldsError
from ..models.student_record import StudentRecord

_COURSE_CODE_PATTERN = re.compile(r"^[A-Z]{2,5} \d{3}$")


def derive_level(earned_hours: int) -> int:
    """
    Return the academic level integer (1–4) for a given earned-hours count.
    Uses LEVEL_THRESHOLDS from academic_config.json.
    Raises ValueError if no threshold matches (config gap).
    """
    for min_h, max_h, level in LEVEL_THRESHOLDS:
        if max_h is None:
            if earned_hours >= min_h:
                return level
        else:
            if min_h <= earned_hours <= max_h:
                return level
    raise ValueError(
        f"earned_hours={earned_hours} does not fall within any configured level threshold."
    )


_DEFAULT_PROGRAM = "Statistics&Computer Science"


def validate_student_record(data: dict) -> StudentRecord:
    """
    Validate and construct a StudentRecord from a raw extracted dict.

    Required keys: cgpa, earned_hours, last_semester_gpa, admission_year.
    program: optional — defaults to "Statistics&Computer Science" per data model if absent.
    Level is derived from earned_hours; must NOT be supplied by caller.
    Raises MissingRequiredFieldsError if any non-optional required field is absent or None.
    """
    required = ["cgpa", "earned_hours", "last_semester_gpa", "admission_year"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        raise MissingRequiredFieldsError(missing)

    program = data.get("program") or _DEFAULT_PROGRAM

    return StudentRecord(
        cgpa=float(data["cgpa"]),
        program=str(program),
        earned_hours=int(data["earned_hours"]),
        last_semester_gpa=float(data["last_semester_gpa"]),
        level=derive_level(int(data["earned_hours"])),
        admission_year=int(data["admission_year"]),
    )


def validate_course_code(code: str) -> bool:
    """Return True if code matches the expected pattern (e.g. 'STAT 301')."""
    return bool(_COURSE_CODE_PATTERN.match(code.strip()))
