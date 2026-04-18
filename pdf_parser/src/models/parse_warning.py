"""
parse_warning.py — ParseWarning dataclass for field-level and section-level warnings.
"""
from dataclasses import dataclass, field


@dataclass
class ParseWarning:
    level: str          # "field" or "section"
    location: str       # e.g. "Semester: Fall 2022-2023" or "Course: STAT 301, field: grade"
    message: str        # Human-readable description
    raw_value: str | None = field(default=None)  # Original extracted value that triggered the warning
