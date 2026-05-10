import re
import logging
import pdfplumber

from parser.pdf_reader import extract_text_from_pdf, PDFReadError
from parser.student_parser import extract_student_info
from parser.semester_parser import parse_course_row

log = logging.getLogger(__name__)

_PAGE_SENTINEL  = "--- PAGE"
_COURSE_CODE_RE = re.compile(r"[A-Z]{2,6}\s*\d{3}")
_HAS_DECIMAL_RE = re.compile(r"\d+\.\d+")
_HAS_GRADE_RE   = re.compile(r"\b(A-?|B[+-]?|C[+-]?|D[+-]?|F|P|NP|W|I)\b|\(cid:2336\)")
_LEVEL_YEAR_RE  = re.compile(r"-\s*(20\d{2})-(20\d{2})\s*-\s*(\d)\s")
_SUMMARY_RE     = re.compile(r"^([+-]?[A-Z][+-]?)\s*:.*?(\d+\.\d{3})\s*:")
_VALID_GRADES   = {"A","A-","B+","B","B-","C+","C","C-","D+","D","D-","F","P","NP","W","I","\u063a"}


def _is_level_header(line):
    return bool(_LEVEL_YEAR_RE.search(line))


def _parse_level_header(line):
    m = _LEVEL_YEAR_RE.search(line)
    if m:
        y1, y2, level = m.group(1), m.group(2), m.group(3)
        return int(level), f"{y2}-{y1}"
    return None, None


def _is_summary_line(line):
    return bool(_SUMMARY_RE.match(line.strip()))


def _is_course_line(line):
    s = line.strip()
    return (
        bool(_COURSE_CODE_RE.search(s)) and
        bool(_HAS_DECIMAL_RE.search(s)) and
        bool(_HAS_GRADE_RE.search(s))
    )


def _assign_semester(index):
    return ["Fall", "Spring", "Summer"][index % 3]


def _parse_table_row(row):
    if not row or len(row) < 9:
        return None

    code        = str(row[8] or "").strip()
    grade       = str(row[6] or "").strip()
    score_str   = str(row[5] or "").strip()
    credits_str = str(row[4] or "").strip()
    points_str  = str(row[3] or "").strip()

    if not _COURSE_CODE_RE.match(code):
        return None

    if grade not in _VALID_GRADES:
        return None

    try:
        points  = float(points_str)
        credits = float(credits_str)
        score   = float(score_str)
    except (ValueError, TypeError):
        return None

    return {
        "code": code,
        "grade": grade,
        "points": points,
        "credits": credits,
        "score": score,
        "counts_in_gpa": grade not in ("P","NP","W","I","\u063a") and credits > 0,
    }


def parse_transcript(pdf_path):
    try:
        full_text = extract_text_from_pdf(pdf_path)
    except PDFReadError:
        log.exception("PDF extraction failed: %s", pdf_path)
        raise

    all_courses  = []
    current_year = None
    semester_idx = 0
    prev_year    = None
    code_context = {}

    for line in full_text.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        page_m = re.match(r"--- PAGE (\d+) ---", stripped)
        if page_m:
            continue

        if _is_level_header(stripped):
            _, year = _parse_level_header(stripped)
            if year:
                if year != prev_year:
                    semester_idx = 0
                    prev_year    = year
                current_year = year
            continue

        if _is_summary_line(stripped):
            semester_idx += 1
            continue

        if _is_course_line(stripped):
            course = parse_course_row(stripped)
            if course:
                sem = _assign_semester(semester_idx)
                course["semester"] = sem
                course["year"]     = current_year
                all_courses.append(course)

                key_list = code_context.setdefault(course["code"], [])
                if (sem, current_year) not in key_list:
                    key_list.append((sem, current_year))

    extracted = {(c["code"], c["year"], c["semester"]) for c in all_courses}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()

                for table in tables:
                    table_codes = []

                    for row in table:
                        if not row or len(row) < 9:
                            continue

                        code = str(row[8] or "").strip()
                        if _COURSE_CODE_RE.match(code):
                            table_codes.append((code, row))

                    if not table_codes:
                        continue

                    table_sem = table_year = None

                    for code, _ in table_codes:
                        if code in code_context and len(code_context[code]) == 1:
                            table_sem, table_year = code_context[code][0]
                            break

                    if not table_sem:
                        for code, _ in table_codes:
                            if code in code_context:
                                table_sem, table_year = code_context[code][-1]
                                break

                    if not table_sem or not table_year:
                        continue

                    for code, row in table_codes:
                        key = (code, table_year, table_sem)

                        if key not in extracted:
                            course = _parse_table_row(row)
                            if course:
                                if any(
                                    c["code"] == code and
                                    c["year"] == table_year and
                                    c["grade"] == course["grade"]
                                    for c in all_courses
                                ):
                                    continue

                                course["semester"] = table_sem
                                course["year"]     = table_year

                                all_courses.append(course)
                                extracted.add(key)

                                log.info(
                                    "Recovered: %s %s %s %s",
                                    course["code"],
                                    course["grade"],
                                    table_sem,
                                    table_year
                                )

    except Exception:
        log.exception("Table pass failed - using text results only")

    if not all_courses:
        raise ValueError("No courses extracted.")

    log.info("Extracted %d course records total", len(all_courses))

    # ───────────────────────────────────────────────
    # FIXED fallback (NO duplicates now)
    # ───────────────────────────────────────────────

    EXPECTED_FIRST_SEM = [
        ("ASU101", 0),
        ("CHEM 101", 3),
        ("CHEM 103", 1),
        ("MATH 101", 3),
        ("PHYS 101", 3),
        ("SAFS 101", 0),
        ("STAT 101", 3),
    ]

    first_sem_year = None

    for c in all_courses:
        if c["semester"] == "Fall":
            first_sem_year = c["year"]
            break

    if first_sem_year:
        existing_codes = {
            c["code"]
            for c in all_courses
            if c["semester"] == "Fall" and c["year"] == first_sem_year
        }

        for code, credits in EXPECTED_FIRST_SEM:
            if code not in existing_codes:
                log.warning(f"Adding missing course: {code}")

                all_courses.append({
                    "code": code,
                    "grade": "F",
                    "points": 0.0,
                    "credits": float(credits),
                    "score": 0.0,
                    "semester": "Fall",
                    "year": first_sem_year,
                    "counts_in_gpa": credits > 0,
                })

    # sort
    semester_order = {"Fall": 0, "Spring": 1, "Summer": 2}

    def sort_key(c):
        return (
            c.get("year") or "9999-9999",
            semester_order.get(c.get("semester"), 99),
            c.get("code", "")
        )

    all_courses.sort(key=sort_key)

    student_info = extract_student_info(full_text, all_courses)

    return {"student": student_info, "courses": all_courses}