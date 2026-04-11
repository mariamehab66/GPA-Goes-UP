"""
semester_block.py — SemesterBlock dataclass.
Intermediate structure produced by the transcript parser for one semester section.
"""
from dataclasses import dataclass, field


@dataclass
class SemesterBlock:
    semester_type: str          # "Fall", "Spring", or "Summer"
    academic_year: str          # e.g. "2022-2023"
    semester_gpa: float | None  # None if not found or unparseable
    courses: list[dict] = field(default_factory=list)   # Raw extracted dicts before CourseRecord creation
    parse_failed: bool = False  # True if this block could not be parsed at all
