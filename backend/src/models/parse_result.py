"""
parse_result.py — ParseResult dataclass.
Top-level result returned by the parsing pipeline.
"""
from dataclasses import dataclass, field

from .student_record import StudentRecord
from .course_record import CourseRecord
from .parse_warning import ParseWarning


@dataclass
class ParseResult:
    student: StudentRecord
    enrollments: list[CourseRecord] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    is_partial: bool = False    # True when one or more semester blocks failed to parse
