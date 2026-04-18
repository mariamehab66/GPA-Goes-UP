"""
course_record.py — CourseRecord dataclass.
Represents one course row extracted from a semester block.
enrollment_id and student_id are NOT fields here; they are assigned by the database.
course_name is NOT included — handled by a separate downstream module.
"""
from dataclasses import dataclass


@dataclass
class CourseRecord:
    course_code: str
    course_grade: str       # Normalized grade symbol (e.g. "A+", "Abs", "Unknown")
    course_gpa: float | None
    year: int               # Academic year start (e.g. 2022 for "2022-2023")
    semester: str           # "Fall", "Spring", or "Summer"
