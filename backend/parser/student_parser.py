import re
import logging
from typing import Optional

log = logging.getLogger(__name__)

_CGPA_RE    = re.compile(r"CGPA:\s*([\d.]+)")
_HOURS_RE   = re.compile(r"^(\d{2,3})\s*:\s*\(cid")
_LEVEL_RE   = re.compile(r"-\s*20\d{2}-20\d{2}\s*-\s*(\d)\s")
_SUMMARY_RE = re.compile(r"^([+-]?[A-Z][+-]?)\s*:.*?(\d+\.\d{3})\s*:")
_PROGRAM    = "Statistcs&Computer Science"


def _safe_float(v):
    try:    return float(v)
    except: return None


def _safe_int(v):
    try:    return int(v)
    except: return None


def _weighted_gpa(courses):
    pts = crs = 0.0
    for c in courses:
        cr = c.get("credits") or 0
        pt = c.get("points")
        gr = c.get("grade", "")
        if gr in ("P","NP","W","I","غ") or cr == 0 or pt is None:
            continue
        pts += pt * cr
        crs += cr
    return round(pts / crs, 3) if crs else None


def extract_student_info(text, courses=None):
    if not text or not text.strip():
        raise ValueError("Empty text")

    student = {"program": _PROGRAM}

    # CGPA
    m = _CGPA_RE.search(text)
    student["cgpa"] = _safe_float(m.group(1)) if m else None

    # Earned hours — line starts with "114 :(cid..."
    student["earned_hours"] = None
    for line in text.splitlines():
        m = _HOURS_RE.match(line.strip())
        if m:
            student["earned_hours"] = _safe_int(m.group(1))
            break

    # Level — highest level number in year headers
    levels = [int(x) for x in _LEVEL_RE.findall(text)]
    # Level derived from earned hours using standard classification
    h = student.get("earned_hours") or 0
    if   h < 33:  student["level"] = 1  # Freshman
    elif h < 67:  student["level"] = 2  # Sophomore
    elif h < 101: student["level"] = 3  # Junior
    else:         student["level"] = 4  # Senior

    # Admission year
    student["admission_year"] = None
    if courses:
        years = []
        for c in courses:
            y = c.get("year")
            if y and y != "Unknown":
                try: years.append(int(y.split("-")[0]))
                except: pass
        if years:
            student["admission_year"] = min(years)

    # Last semester GPA — last summary line GPA value
    last_gpa = None
    for line in text.splitlines():
        m = _SUMMARY_RE.match(line.strip())
        if m:
            last_gpa = _safe_float(m.group(2))
    if last_gpa is not None:
        student["last_semester_gpa"] = last_gpa
    elif courses:
        seen = {}
        for c in courses:
            seen.setdefault((c.get("year"), c.get("semester")), []).append(c)
        student["last_semester_gpa"] = _weighted_gpa(list(seen.values())[-1]) if seen else None
    else:
        student["last_semester_gpa"] = None

    return student
