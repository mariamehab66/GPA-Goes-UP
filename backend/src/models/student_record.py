"""
student_record.py — StudentRecord dataclass.
Represents student-level data extracted from the transcript header.
ID is NOT a field here; it is assigned by the database (auto-increment).
"""
from dataclasses import dataclass


@dataclass
class StudentRecord:
    cgpa: float
    program: str
    earned_hours: int
    last_semester_gpa: float
    level: int           # 1=Freshman, 2=Sophomore, 3=Junior, 4=Senior
    admission_year: int
