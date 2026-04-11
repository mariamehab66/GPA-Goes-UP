"""
transcript_parser.py — Structural parsing of extracted transcript text.
Functions operate on the list-of-strings output from pdf_extractor.extract_text().
"""
import re

import arabic_reshaper
from bidi.algorithm import get_display

from ..config import SEMESTER_LABEL_MAP
from ..models.semester_block import SemesterBlock

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# T023: Multiple patterns per field — tried in order, first match wins.
_CGPA_PATTERNS = [
    re.compile(r"(?:CGPA|المعدل\s*التراكمي)\s*[:\-]?\s*(\d+\.\d+)", re.IGNORECASE),
    re.compile(r"(\d+\.\d+)\s*(?:CGPA|المعدل\s*التراكمي)", re.IGNORECASE),
    # Standalone float on a line that also contains a GPA-related keyword
    re.compile(r"(?:تراكمي|cumulative)[^\d]*(\d+\.\d+)", re.IGNORECASE),
]
_EARNED_HOURS_PATTERNS = [
    re.compile(r"(?:Earned\s*Hours|الساعات\s*المكتسبة)\s*[:\-]?\s*(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*(?:Earned\s*Hours|ساعة\s*مكتسبة)", re.IGNORECASE),
    re.compile(r"(?:ساعات)[^\d]*(\d+)", re.IGNORECASE),
]
_PROGRAM_PATTERNS = [
    re.compile(r"(?:Program|البرنامج|التخصص)\s*[:\-]?\s*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:الدراسي|الشعبة|القسم)\s*[:\-]?\s*(.+?)(?:\n|$)", re.IGNORECASE),
]
_ACADEMIC_YEAR_PATTERN = re.compile(r"(\d{4})\s*[-–]\s*(\d{4})")
_FLOAT_PATTERN = re.compile(r"\d+\.\d+")
_COURSE_CODE_PATTERN = re.compile(r"^([A-Z]{2,5})\s+(\d{3})\b")

# T024: Known grade symbols for content-type identification
_KNOWN_GRADES = {
    "A", "A-", "A+", "B", "B-", "B+", "C", "C-", "C+",
    "D", "D-", "D+", "F", "W", "P", "I", "Abs", "غ",
}


def _reshape(text: str) -> str:
    """Apply arabic-reshaper + bidi so Arabic text is in logical reading order."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def parse_header(pages_text: list[str]) -> dict:
    """
    Extract student-level fields from the transcript.

    T023: Tries multiple regex patterns per field and scans the first 30 lines
    before falling back to the full text. Tolerates varying label positions.

    Returns a dict with keys: cgpa, program, earned_hours, last_semester_gpa.
    Missing values are None; validator raises MissingRequiredFieldsError.
    """
    # Prioritise the first page for header fields; fall back to full text.
    first_page = pages_text[0] if pages_text else ""
    first_30_lines = "\n".join(first_page.splitlines()[:30])
    full_text = "\n".join(pages_text)

    cgpa = _extract_first_match_float(_CGPA_PATTERNS, first_30_lines) \
        or _extract_first_match_float(_CGPA_PATTERNS, full_text)

    earned_hours = _extract_first_match_int(_EARNED_HOURS_PATTERNS, first_30_lines) \
        or _extract_first_match_int(_EARNED_HOURS_PATTERNS, full_text)

    program = _extract_program(first_30_lines) or _extract_program(full_text)

    return {
        "cgpa": cgpa,
        "earned_hours": earned_hours,
        "program": program,
        "last_semester_gpa": None,  # filled later from the last semester block
    }


def detect_semester_blocks(pages_text: list[str]) -> list[SemesterBlock]:
    """
    Scan all pages and split the transcript into SemesterBlock objects.

    Each block spans from one Arabic semester anchor to the next.
    Returns an empty list if no anchors are found.
    """
    all_lines: list[str] = []
    for page in pages_text:
        all_lines.extend(page.splitlines())

    blocks: list[SemesterBlock] = []
    current_anchor_line: int | None = None
    current_semester_type: str | None = None
    current_academic_year: str | None = None

    for idx, line in enumerate(all_lines):
        reshaped = _reshape(line)
        semester_type = _match_semester_label(reshaped) or _match_semester_label(line)
        if semester_type:
            # Save previous block if any
            if current_anchor_line is not None:
                block_lines = all_lines[current_anchor_line:idx]
                block = _build_block(
                    block_lines, current_semester_type, current_academic_year
                )
                blocks.append(block)
            current_anchor_line = idx
            current_semester_type = semester_type
            year_match = _ACADEMIC_YEAR_PATTERN.search(line)
            current_academic_year = (
                f"{year_match.group(1)}-{year_match.group(2)}" if year_match else None
            )

    # Last block
    if current_anchor_line is not None:
        block_lines = all_lines[current_anchor_line:]
        block = _build_block(
            block_lines, current_semester_type, current_academic_year
        )
        blocks.append(block)

    return blocks


def extract_courses_from_block(block_lines: list[str]) -> list[dict]:
    """
    Extract raw course dicts from the text lines of one semester block.

    T024: Identifies each field by content type rather than fixed column index,
    making it robust against column reordering across different transcript formats:
      - course_code: token matching ^[A-Z]{2,5} \\d{3}$
      - raw_grade: token present in _KNOWN_GRADES set
      - course_gpa: float token in range [0.0, 4.0]
    Excess whitespace and unicode spacing chars are normalised before parsing.
    course_name is intentionally NOT extracted.

    Each dict has keys: course_code (str), raw_grade (str), course_gpa (float|None).
    """
    courses: list[dict] = []
    for line in block_lines:
        # Normalise unicode spacing (U+00A0, U+202F, etc.) to regular space
        normalised = line.replace("\u00a0", " ").replace("\u202f", " ").strip()
        if not normalised:
            continue
        # Check if line starts with a course code pattern
        if not _COURSE_CODE_PATTERN.match(normalised):
            continue
        tokens = normalised.split()
        course_code = f"{tokens[0]} {tokens[1]}"
        remaining = tokens[2:]

        raw_grade, course_gpa = _identify_grade_and_gpa_by_content(remaining)
        courses.append({
            "course_code": course_code,
            "raw_grade": raw_grade,
            "course_gpa": course_gpa,
        })
    return courses


def extract_admission_year(blocks: list[SemesterBlock]) -> int | None:
    """
    Return the starting year of the first semester block's academic_year.
    e.g. "2022-2023" → 2022.  Returns None if blocks is empty or year unparseable.
    """
    if not blocks:
        return None
    first_year = blocks[0].academic_year
    if not first_year:
        return None
    m = re.match(r"(\d{4})", first_year)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_first_match_float(patterns: list[re.Pattern], text: str) -> float | None:
    """Try each pattern in order; return the first successfully parsed float."""
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def _extract_first_match_int(patterns: list[re.Pattern], text: str) -> int | None:
    """Try each pattern in order; return the first successfully parsed int."""
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None


def _extract_program(text: str) -> str | None:
    for pattern in _PROGRAM_PATTERNS:
        m = pattern.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return None


def _match_semester_label(text: str) -> str | None:
    """Return English semester type if any Arabic anchor phrase is found in text."""
    for arabic_key, english_val in SEMESTER_LABEL_MAP.items():
        if arabic_key in text:
            return english_val
    return None


def _identify_grade_and_gpa_by_content(tokens: list[str]) -> tuple[str, float | None]:
    """
    T024: Identify grade and GPA from remaining tokens using content type, not position.

    - grade: first token that is a member of _KNOWN_GRADES (exact match after strip)
    - course_gpa: first float token in [0.0, 4.0] range that is NOT already the grade
    All other tokens (course name words, credit hours, etc.) are silently ignored.
    Falls back to scanning in reverse for a float if no grade is found explicitly.
    """
    grade = "Unknown"
    gpa: float | None = None

    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if grade == "Unknown" and tok in _KNOWN_GRADES:
            grade = tok
            continue
        float_match = _FLOAT_PATTERN.fullmatch(tok)
        if float_match and gpa is None:
            val = float(tok)
            if 0.0 <= val <= 4.0:
                gpa = val

    # Fallback: if grade still unknown, scan reversed tokens for a non-float
    if grade == "Unknown":
        for tok in reversed(tokens):
            tok = tok.strip()
            if tok and not _FLOAT_PATTERN.fullmatch(tok) and tok not in ("", "-"):
                grade = tok
                break

    return grade, gpa


def _build_block(
    lines: list[str],
    semester_type: str | None,
    academic_year: str | None,
) -> SemesterBlock:
    """Construct a SemesterBlock; set parse_failed if essential data is missing."""
    courses = extract_courses_from_block(lines)
    semester_gpa = _extract_semester_gpa(lines)
    parse_failed = (semester_type is None or academic_year is None)
    return SemesterBlock(
        semester_type=semester_type or "Unknown",
        academic_year=academic_year or "",
        semester_gpa=semester_gpa,
        courses=courses,
        parse_failed=parse_failed,
    )


def _extract_semester_gpa(lines: list[str]) -> float | None:
    """
    Extract the semester GPA from the terminal line(s) of a block.
    Looks for lines containing Arabic GPA labels followed by a float.
    """
    gpa_labels = ["المعدل الفصلي", "GPA", "معدل الفصل", "الفصل"]
    for line in reversed(lines):
        for label in gpa_labels:
            if label in line:
                m = _FLOAT_PATTERN.search(line)
                if m:
                    return float(m.group())
    return None


# ---------------------------------------------------------------------------
# Positional parsing for CID-encoded Arabic PDFs (T027)
# ---------------------------------------------------------------------------

# Year pattern in page headers: e.g. "2022-2023-1", "2025-2026-2"
_YEAR_SEMESTER_PATTERN = re.compile(r"(\d{4})-(\d{4})-(\d)")

# Map semester number to English type
_SEMESTER_NUM_MAP = {"1": "Fall", "2": "Spring", "3": "Summer", "4": "Summer"}

# Course code at the word level: two adjacent tokens "DEPT NNN"
_DEPT_PATTERN = re.compile(r"^[A-Z]{2,5}$")
_NUM_PATTERN = re.compile(r"^\d{3}$")

_CID_TOKEN = re.compile(r"^\(cid:\d+\)")


def _is_cid(token: str) -> bool:
    return bool(_CID_TOKEN.match(token))


def parse_header_from_rows(page_rows: list[list[list[str]]]) -> dict:
    """
    T027: Extract student header fields from positional word rows.

    Scans all rows across all pages for:
    - CGPA: token immediately after 'CGPA:' label, or isolated float on a row
      that also contains 'CGPA'
    - Earned hours: largest integer on a row containing 'CGPA' (cumulative total)
    - Program: row containing student ID pattern (long digit string)
    """
    cgpa: float | None = None
    earned_hours: int | None = None

    for page in page_rows:
        for row in page:
            ascii_tokens = [t for t in row if t.isascii() and t.strip()]
            row_str = " ".join(ascii_tokens)

            # CGPA: look for "CGPA:" followed by float
            for i, tok in enumerate(ascii_tokens):
                if tok.upper().startswith("CGPA") and i + 1 < len(ascii_tokens):
                    candidate = ascii_tokens[i + 1].rstrip(":")
                    if _FLOAT_PATTERN.fullmatch(candidate):
                        try:
                            cgpa = float(candidate)
                        except ValueError:
                            pass
                elif tok.upper() == "CGPA:" and i + 1 < len(ascii_tokens):
                    candidate = ascii_tokens[i + 1]
                    if _FLOAT_PATTERN.fullmatch(candidate):
                        try:
                            cgpa = float(candidate)
                        except ValueError:
                            pass

            # Earned hours: on CGPA row, look for pattern like "125 :"
            if cgpa is not None and earned_hours is None and "CGPA" in row_str.upper():
                for tok in ascii_tokens:
                    if INT_RE := re.fullmatch(r"\d{2,3}", tok):
                        val = int(INT_RE.string)
                        if val > 0 and (earned_hours is None or val > earned_hours):
                            earned_hours = val

    return {
        "cgpa": cgpa,
        "earned_hours": earned_hours,
        "program": None,        # Not reliably extractable from CID PDFs; use default
        "last_semester_gpa": None,
    }


def detect_semester_blocks_from_rows(
    page_rows: list[list[list[str]]],
) -> list[SemesterBlock]:
    """
    T027: Detect semester blocks from positional word rows.

    Each page = one semester. The academic year label (YYYY-YYYY-N) appears in
    the header area (row < 12) only for the first semester of each academic year
    (i.e., Fall). Other semesters are inferred by alternating Fall→Spring→Fall...

    Year labels in footer (row ≥ total_rows × 0.6) are ignored as document metadata.

    Course rows are extracted by positional content-type matching.
    """
    blocks: list[SemesterBlock] = []

    # First pass: collect header years per page (only header area rows)
    page_header_years: list[tuple[str, str] | None] = []  # (academic_year, semester_type) or None
    for page in page_rows:
        found = None
        header_limit = min(12, len(page))
        for row in page[:header_limit]:
            joined = "".join(row)
            m = _YEAR_SEMESTER_PATTERN.search(joined)
            if m:
                y1, y2 = int(m.group(1)), int(m.group(2))
                start_yr = min(y1, y2)
                end_yr = max(y1, y2)
                academic_year = f"{start_yr}-{end_yr}"
                found = (academic_year, "Fall")  # header label always = Fall
                break
        page_header_years.append(found)

    # Second pass: propagate years + alternate Fall/Spring for unlabeled pages
    current_year: int | None = None
    current_sem: str = "Fall"

    semester_assignments: list[tuple[str, str]] = []  # (academic_year, semester_type)
    for label in page_header_years:
        if label is not None:
            year_str, sem = label
            current_year = int(year_str.split("-")[0])
            current_sem = "Fall"
            semester_assignments.append((year_str, sem))
        elif current_year is not None:
            # Advance to next semester
            if current_sem == "Fall":
                current_sem = "Spring"
                semester_assignments.append((f"{current_year}-{current_year+1}", "Spring"))
            else:
                current_year += 1
                current_sem = "Fall"
                semester_assignments.append((f"{current_year}-{current_year+1}", "Fall"))
        else:
            semester_assignments.append(("", "Unknown"))

    # Third pass: extract courses per page
    for page_idx, page in enumerate(page_rows):
        academic_year, semester_type = semester_assignments[page_idx]

        courses: list[dict] = []
        semester_gpa: float | None = None

        for row in page:
            ascii_tokens = [t for t in row if t.strip() and not _is_cid(t)]
            if not ascii_tokens:
                continue

            course = _try_extract_course_from_row(ascii_tokens)
            if course:
                courses.append(course)
                continue

            # Semester summary row: grade + GPA float, no course code
            row_grades = [t for t in ascii_tokens if t in _KNOWN_GRADES]
            row_floats = [
                float(t) for t in ascii_tokens
                if _FLOAT_PATTERN.fullmatch(t) and 0.0 <= float(t) <= 4.0
            ]
            if row_grades and row_floats and semester_gpa is None:
                semester_gpa = row_floats[0]

        if not courses:
            continue  # Skip non-semester pages (e.g. summary page)

        blocks.append(SemesterBlock(
            semester_type=semester_type,
            academic_year=academic_year,
            semester_gpa=semester_gpa,
            courses=courses,
            parse_failed=(academic_year == ""),
        ))

    return blocks


_SINGLE_CODE_PATTERN = re.compile(r"^([A-Z]{2,5})(\d{3})$")


def _try_extract_course_from_row(ascii_tokens: list[str]) -> dict | None:
    """
    Try to extract a course dict from a row of ASCII tokens.

    Handles both two-token codes (DEPT NNN) and single-token codes (DEPTNNN).
    Identifies: course_code, grade (from known set), course_gpa (float ≤ 4.0).
    Returns None if no course code found.
    """
    course_code: str | None = None

    # Try two-token course code: 'COMP' '201'
    for i in range(len(ascii_tokens) - 1):
        if _DEPT_PATTERN.match(ascii_tokens[i]) and _NUM_PATTERN.match(ascii_tokens[i + 1]):
            course_code = f"{ascii_tokens[i]} {ascii_tokens[i + 1]}"
            break

    # Try single-token course code: 'COMP201' or 'ASU101'
    if not course_code:
        for tok in ascii_tokens:
            m = _SINGLE_CODE_PATTERN.match(tok)
            if m:
                course_code = f"{m.group(1)} {m.group(2)}"
                break

    if not course_code:
        return None

    grade = "Unknown"
    course_gpa: float | None = None

    for tok in ascii_tokens:
        clean = tok.strip("()")
        if clean in _KNOWN_GRADES and grade == "Unknown":
            grade = clean
        elif _FLOAT_PATTERN.fullmatch(tok):
            val = float(tok)
            if 0.0 <= val <= 4.0 and course_gpa is None:
                course_gpa = val

    return {"course_code": course_code, "raw_grade": grade, "course_gpa": course_gpa}
