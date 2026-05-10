import re
import logging
from typing import Optional

log = logging.getLogger(__name__)

_SEMESTER_KEYWORDS = {
    "الخريف": "Fall",
    "الربيع": "Spring",
    "الصيف":  "Summer",
    "سبتمبر": "Summer",
    "يناير":  "Fall",
    "يونيو":  "Spring",
}

GRADE_POINTS = {
    "A":  4.000, "A-": 3.670,
    "B+": 3.330, "B":  3.000, "B-": 2.670,
    "C+": 2.670, "C":  2.330, "C-": 2.000,
    "D+": 2.330, "D":  2.000, "D-": 1.670,
    "F":  0.000,
    "P":  None, "NP": None, "I": None, "W": None,
    "غ":  None,
}

# RTL layout columns: points  credits  score  grade  [arabic name]  code
# grade can be Latin letter, Arabic غ, or CID-encoded (cid:2336) for غ
_COURSE_RE = re.compile(
    r"(\d+(?:\.\d+)?)"
    r"\s+(\d+\.\d+)"
    r"\s+(\d+\.\d+)"
    r"\s+(A-?|B[+-]?|C[+-]?|D[+-]?|F|NP|P|W|I|غ|\(cid:2336\))"
    r".+?"
    r"\b([A-Z]{2,6}\s*\d{3}[A-Z]?)\s*$",
    re.UNICODE
)

_SEM_GPA_RE = re.compile(r"(\d+\.\d+)\s*:\s*(?:.*?)\s+(\d+\.\d+)\s*:\s*(?:.*?)\s+(\d+\.\d+)")
_YEAR_RE    = re.compile(r"(20\d{2})\s*[-/]\s*(20\d{2})")
_LEVEL_RE   = re.compile(r"مستوى\s+(\d+)")


def detect_semester_and_year(text: str) -> tuple:
    semester = "Unknown"
    for arabic_key, label in _SEMESTER_KEYWORDS.items():
        if arabic_key in text:
            semester = label
            break
    year = None
    m = _YEAR_RE.search(text)
    if m:
        year = f"{m.group(1)}-{m.group(2)}"
    return semester, year


def parse_course_row(line: str) -> Optional[dict]:
    m = _COURSE_RE.search(line)
    if not m:
        return None

    grade   = m.group(4).strip()
    credits = float(m.group(2))
    points  = float(m.group(1))
    score   = float(m.group(3))
    code    = m.group(5).strip()

    # Normalize CID-encoded absent grade to Arabic letter
    if grade == "(cid:2336)":
        grade = "غ"

    if grade == "غ":
        log.warning("Absent grade (غ) for course: %s", code)

    counts_in_gpa = grade not in ("P", "NP", "W", "I", "غ") and credits > 0

    return {
        "code":          code,
        "grade":         grade,
        "points":        points,
        "credits":       credits,
        "score":         score,
        "counts_in_gpa": counts_in_gpa,
    }


def parse_semester_block(block_text: str,
                         academic_year: Optional[str] = None) -> dict:
    semester, detected_year = detect_semester_and_year(block_text)
    year = detected_year or academic_year
    courses = []
    for line in block_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        course = parse_course_row(stripped)
        if course:
            courses.append(course)
    sem_gpa = None
    gpa_m = _SEM_GPA_RE.search(block_text)
    if gpa_m:
        try:
            sem_gpa = float(gpa_m.group(1))
        except ValueError:
            pass
    if not courses:
        log.warning("No courses parsed (year=%s sem=%s)", year, semester)
    return {
        "semester":     semester,
        "year":         year,
        "semester_gpa": sem_gpa,
        "courses":      courses,
    }


def extract_level_year(header_line: str) -> tuple:
    level = None
    lm = _LEVEL_RE.search(header_line)
    if lm:
        try:
            level = int(lm.group(1))
        except ValueError:
            pass
    year = None
    ym = _YEAR_RE.search(header_line)
    if ym:
        year = f"{ym.group(1)}-{ym.group(2)}"
    return level, year