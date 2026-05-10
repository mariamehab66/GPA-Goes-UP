"""
ml/features.py

Feature engineering for training and inference.

Training path  : build_training_features()
Inference path : build_inference_features()

Feature list (25 total)
  Numeric (23):
    cgpa_at_time, last_sem_gpa, earned_hours, level, is_probation,
    is_delayed, credit_hours, course_level, is_elective, is_practical,
    avg_grade_in_type, avg_grade_in_level, is_retake, prev_grade_points,
    prev_marks_normalized, num_prior_failures, level_gap, bottleneck_weight,
    gpa_trend, avg_prereq_grade_points, num_prereqs_passed_well,
    course_avg_grade, course_fail_rate
  Categorical (2):
    course_type, course_semester
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date

from ml.data_loader import (
    GPA_COUNTED,
    GRADE_POINTS,
    PASS_FAIL_COURSES,
    PASSING_GRADES,
    SEM_ORDER,
    semester_sort_key,
)

# ---------------------------------------------------------------------------
# Feature column lists  (imported by train.py and predict.py)
# ---------------------------------------------------------------------------

NUMERIC_FEATURES: list[str] = [
    "cgpa_at_time",
    "last_sem_gpa",
    "earned_hours",
    "level",
    "is_probation",
    "is_delayed",
    "credit_hours",
    "course_level",
    "is_elective",
    "is_practical",
    "avg_grade_in_type",
    "avg_grade_in_level",
    "is_retake",
    "prev_grade_points",
    "prev_marks_normalized",   # marks / max_marks_in_course (0 if first attempt)
    "num_prior_failures",
    "level_gap",
    "bottleneck_weight",
    "gpa_trend",               # last_sem_gpa − cgpa_at_time
    "avg_prereq_grade_points", # mean grade_points earned in prerequisites (0 if none)
    "num_prereqs_passed_well", # count of prereqs passed with grade ≥ B (grade_points ≥ 3.0)
    "course_avg_grade",        # historical avg grade_points for this course (fold-level)
    "course_fail_rate",        # fraction of students who failed this course (fold-level)
]

CATEGORICAL_FEATURES: list[str] = [
    "course_type",
    "course_semester",
]

ALL_FEATURES: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def compute_bottleneck_weights(
    prerequisites_map: dict[str, list[str]],
    all_course_codes: list[str],
) -> dict[str, int]:
    weights: dict[str, int] = {code: 0 for code in all_course_codes}
    for prereqs in prerequisites_map.values():
        for p in prereqs:
            if p in weights:
                weights[p] += 1
    return weights


def _level_from_hours(earned_hours: int | float) -> int:
    h = int(earned_hours)
    if h <= 32:
        return 1
    if h <= 66:
        return 2
    if h <= 100:
        return 3
    return 4


def _expected_level(admission_year: int, academic_year: int) -> int:
    elapsed = academic_year - admission_year
    return max(1, min(4, elapsed + 1))


def _compute_student_state(
    history: list[dict],
    admission_year: int,
    current_academic_year: int,
) -> dict:
    if not history:
        return {
            "cgpa": 0.0,
            "last_sem_gpa": 0.0,
            "earned_hours": 0,
            "level": 1,
            "is_probation": False,
            "is_delayed": False,
            "prev_sem_gpa": 0.0,
        }

    gpa_rows = [h for h in history if h["grade"] in GPA_COUNTED]
    if gpa_rows:
        total_qp = sum(h["grade_points"] * h["credit_hours"] for h in gpa_rows)
        total_ch = sum(h["credit_hours"] for h in gpa_rows)
        cgpa = total_qp / total_ch if total_ch > 0 else 0.0
    else:
        cgpa = 0.0

    earned_hours = int(sum(h["credit_hours"] for h in history if h["grade"] in PASSING_GRADES))

    all_sem_keys = sorted(set(h["sem_key"] for h in history))
    last_sem_key = all_sem_keys[-1]
    prev_sem_key = all_sem_keys[-2] if len(all_sem_keys) >= 2 else None

    ls_rows = [h for h in history if h["sem_key"] == last_sem_key and h["grade"] in GPA_COUNTED]
    if ls_rows:
        ls_qp = sum(h["grade_points"] * h["credit_hours"] for h in ls_rows)
        ls_ch = sum(h["credit_hours"] for h in ls_rows)
        last_sem_gpa = ls_qp / ls_ch if ls_ch > 0 else 0.0
    else:
        last_sem_gpa = 0.0

    if prev_sem_key is not None:
        ps_rows = [h for h in history if h["sem_key"] == prev_sem_key and h["grade"] in GPA_COUNTED]
        if ps_rows:
            ps_qp = sum(h["grade_points"] * h["credit_hours"] for h in ps_rows)
            ps_ch = sum(h["credit_hours"] for h in ps_rows)
            prev_sem_gpa = ps_qp / ps_ch if ps_ch > 0 else 0.0
        else:
            prev_sem_gpa = 0.0
    else:
        prev_sem_gpa = 0.0

    level = _level_from_hours(earned_hours)
    exp   = _expected_level(admission_year, current_academic_year)
    is_probation = (cgpa < 2.0) if gpa_rows else False
    is_delayed   = (level < exp) and (level < 4)

    return {
        "cgpa":          cgpa,
        "last_sem_gpa":  last_sem_gpa,
        "earned_hours":  earned_hours,
        "level":         level,
        "is_probation":  is_probation,
        "is_delayed":    is_delayed,
        "prev_sem_gpa":  prev_sem_gpa,
    }


def _course_row(
    code: str,
    course_info: dict,
    fallback: dict,
    student_level: int,
) -> tuple[float, int, str, bool, bool, str]:
    ci = course_info.get(code, fallback)
    credit_hours  = float(ci.get("Credit_Hours", fallback.get("Credit_Hours", 3)))
    course_level  = int(ci.get("Level", fallback.get("Level", student_level)))
    course_type   = str(ci.get("Type", fallback.get("Type", "REQ")))
    is_elective   = bool(ci.get("Is_elective", fallback.get("Is_elective", False)))
    is_practical  = bool(ci.get("Is_practical", fallback.get("Is_practical", False)))
    course_sem    = str(ci.get("Semester", fallback.get("Semester", "fall"))).lower()
    return credit_hours, course_level, course_type, is_elective, is_practical, course_sem


def _compute_marks_max(history: list[dict]) -> dict[str, float]:
    """Return {course_code: max_marks_seen} from the training history."""
    maxes: dict[str, float] = {}
    for h in history:
        code = h["code"]
        m = h.get("marks", 0.0) or 0.0
        if m > maxes.get(code, 0.0):
            maxes[code] = m
    return maxes


def _prereq_features(
    code: str,
    prerequisites_map: dict[str, list[str]],
    history: list[dict],
) -> tuple[float, int]:
    """
    Returns (avg_prereq_grade_points, num_prereqs_passed_well).
    Looks up all prerequisites of *code* and checks history for grades earned.
    """
    prereqs = prerequisites_map.get(code, [])
    if not prereqs:
        return 0.0, 0

    grade_pts = []
    passed_well = 0
    for prereq in prereqs:
        attempts = [h for h in history if h["code"] == prereq and h["grade"] in GPA_COUNTED]
        if not attempts:
            continue
        best_pts = max(h["grade_points"] for h in attempts)
        grade_pts.append(best_pts)
        if best_pts >= 3.0:
            passed_well += 1

    avg = float(np.mean(grade_pts)) if grade_pts else 0.0
    return avg, passed_well


# ---------------------------------------------------------------------------
# Training feature builder
# ---------------------------------------------------------------------------

def build_training_features(
    filtered_enrollment: pd.DataFrame,
    course_df: pd.DataFrame,
    prerequisites_map: dict[str, list[str]],
    admission_year: int = 2022,
    enrichment_stats: dict[str, dict] | None = None,
) -> pd.DataFrame:
    """
    Build one feature row per historical enrollment record.

    enrichment_stats: {course_code: {"avg_grade": float, "fail_rate": float}}
    When None (training without fold-level stats), placeholders (0.0) are used —
    train.py fills this per-fold using _compute_enrichment_stats().
    """
    course_info = course_df.set_index("Code").to_dict("index")
    all_codes   = list(course_df["Code"])
    bottleneck  = compute_bottleneck_weights(prerequisites_map, all_codes)

    if enrichment_stats is None:
        enrichment_stats = {}

    feature_rows: list[dict] = []

    for student_id, grp in filtered_enrollment.groupby("Student_ID"):
        grp = grp.copy()

        grp["_year_int"] = grp["Year"].apply(
            lambda y: int(str(y).split("-")[0]) if pd.notna(y) else 0
        )
        grp["_sem_int"] = grp["Semester"].str.lower().str.strip().map(SEM_ORDER).fillna(0).astype(int)
        grp["_sem_key"] = list(zip(grp["_year_int"].tolist(), grp["_sem_int"].tolist()))
        grp = grp.sort_values(["_year_int", "_sem_int"]).reset_index(drop=True)

        seen: set = set()
        ordered_sem_keys: list[tuple] = []
        for k in grp["_sem_key"]:
            if k not in seen:
                seen.add(k)
                ordered_sem_keys.append(k)

        history: list[dict] = []

        for sem_key in ordered_sem_keys:
            sem_mask = grp["_sem_key"] == sem_key
            sem_rows = grp[sem_mask]
            academic_year = sem_key[0]

            state = _compute_student_state(history, admission_year, academic_year)
            gpa_trend = state["last_sem_gpa"] - state["prev_sem_gpa"]

            type_gps:  dict[str, list[float]] = {}
            level_gps: dict[int, list[float]] = {}
            all_marks_for_code: dict[str, list[float]] = {}
            for h in history:
                if h["grade"] not in GPA_COUNTED:
                    continue
                type_gps.setdefault(h["course_type"], []).append(h["grade_points"])
                level_gps.setdefault(h["course_level"], []).append(h["grade_points"])
                m = h.get("marks", 0.0) or 0.0
                all_marks_for_code.setdefault(h["code"], []).append(m)

            for _, row in sem_rows.iterrows():
                code = row["Course_Code"]

                credit_hours, course_level, course_type, is_elective, is_practical, course_sem = (
                    _course_row(code, course_info, {}, state["level"])
                )

                avg_type  = float(np.mean(type_gps[course_type]))   if course_type  in type_gps  else state["cgpa"]
                avg_level = float(np.mean(level_gps[course_level]))  if course_level in level_gps else state["cgpa"]

                prev_attempts = [h for h in history if h["code"] == code]
                is_retake     = len(prev_attempts) > 0
                num_failures  = sum(1 for h in prev_attempts if h["grade"] in {"F", "Abs"})
                last_att      = prev_attempts[-1] if prev_attempts else None
                prev_grade_pts = float(last_att["grade_points"]) if last_att else 0.0

                # Normalized marks: prev_marks / max_marks_seen for this course globally
                if last_att:
                    raw_marks = float(last_att.get("marks", 0.0) or 0.0)
                    all_m = all_marks_for_code.get(code, [raw_marks])
                    max_m = max(all_m) if all_m else 0.0
                    prev_marks_norm = raw_marks / max_m if max_m > 0 else 0.0
                else:
                    prev_marks_norm = 0.0

                avg_prereq_gp, num_prereqs_well = _prereq_features(
                    code, prerequisites_map, history
                )

                es = enrichment_stats.get(code, {})
                course_avg_grade = float(es.get("avg_grade", 0.0))
                course_fail_rate = float(es.get("fail_rate", 0.0))

                feature_rows.append({
                    "student_id":              student_id,
                    "course_code":             code,
                    "cgpa_at_time":            state["cgpa"],
                    "last_sem_gpa":            state["last_sem_gpa"],
                    "earned_hours":            state["earned_hours"],
                    "level":                   state["level"],
                    "is_probation":            int(state["is_probation"]),
                    "is_delayed":              int(state["is_delayed"]),
                    "credit_hours":            credit_hours,
                    "course_level":            course_level,
                    "course_type":             course_type,
                    "is_elective":             int(is_elective),
                    "is_practical":            int(is_practical),
                    "course_semester":         course_sem,
                    "avg_grade_in_type":       avg_type,
                    "avg_grade_in_level":      avg_level,
                    "is_retake":               int(is_retake),
                    "prev_grade_points":       prev_grade_pts,
                    "prev_marks_normalized":   prev_marks_norm,
                    "num_prior_failures":      num_failures,
                    "level_gap":               course_level - state["level"],
                    "bottleneck_weight":       bottleneck.get(code, 0),
                    "gpa_trend":               gpa_trend,
                    "avg_prereq_grade_points": avg_prereq_gp,
                    "num_prereqs_passed_well": num_prereqs_well,
                    "course_avg_grade":        course_avg_grade,
                    "course_fail_rate":        course_fail_rate,
                    "grade_bucket":            row["grade_bucket"],
                })

                history.append({
                    "code":         code,
                    "grade":        row["Grade"],
                    "grade_points": float(row["grade_points"]),
                    "credit_hours": credit_hours,
                    "course_type":  course_type,
                    "course_level": course_level,
                    "sem_key":      sem_key,
                    "marks":        float(row.get("Marks", 0.0) or 0.0),
                })

    return pd.DataFrame(feature_rows)


# ---------------------------------------------------------------------------
# Inference feature builder
# ---------------------------------------------------------------------------

def build_inference_features(
    student_data: dict,
    eligible_courses: list[dict],
    course_df: pd.DataFrame,
    prerequisites_map: dict[str, list[str]],
    enrichment_stats: dict[str, dict] | None = None,
) -> pd.DataFrame:
    """
    Build one feature row per eligible course at inference time.

    enrichment_stats: {course_code: {"avg_grade": float, "fail_rate": float}}
    Loaded from the saved artifact by predict.py.
    """
    if enrichment_stats is None:
        enrichment_stats = {}

    course_info = course_df.set_index("Code").to_dict("index")
    all_codes   = list(course_df["Code"])
    bottleneck  = compute_bottleneck_weights(prerequisites_map, all_codes)

    current_cgpa  = float(student_data.get("CGPA",              0.0))
    last_sem_gpa  = float(student_data.get("Last_Semester_GPA", 0.0))
    earned_hours  = float(student_data.get("Earned_Hours",      0))
    level         = int(student_data.get("Level") or _level_from_hours(earned_hours))
    adm_year      = int(student_data.get("Admission_Year",      2022))

    today     = date.today()
    acad_year = today.year if today.month >= 9 else today.year - 1
    exp_level = _expected_level(adm_year, acad_year)
    is_probation = current_cgpa < 2.0
    is_delayed   = (level < exp_level) and (level < 4)

    raw_history = student_data.get("enrollments", [])
    history = [
        e for e in raw_history
        if e.get("Course_Code", "") not in PASS_FAIL_COURSES
        and e.get("Grade", "") in GPA_COUNTED
    ]

    type_gps:  dict[str, list[float]] = {}
    level_gps: dict[int, list[float]] = {}
    for e in history:
        ci  = course_info.get(e["Course_Code"], {})
        pts = GRADE_POINTS.get(e.get("Grade", ""), None)
        if pts is None:
            continue
        t  = str(ci.get("Type", "REQ"))
        lv = int(ci.get("Level", level))
        type_gps.setdefault(t, []).append(pts)
        level_gps.setdefault(lv, []).append(pts)

    history_sorted = sorted(
        history,
        key=lambda e: semester_sort_key(e.get("Year", ""), e.get("Semester", "")),
    )

    # Compute gpa_trend from the two most recent distinct semesters in enrollment history.
    sem_keys_seen: list[tuple] = []
    for e in history_sorted:
        sk = semester_sort_key(e.get("Year", ""), e.get("Semester", ""))
        if not sem_keys_seen or sem_keys_seen[-1] != sk:
            sem_keys_seen.append(sk)

    if len(sem_keys_seen) >= 2:
        prev_sk = sem_keys_seen[-2]
        prev_rows = [
            e for e in history_sorted
            if semester_sort_key(e.get("Year", ""), e.get("Semester", "")) == prev_sk
            and e.get("Grade", "") in GPA_COUNTED
        ]
        if prev_rows:
            ps_qp = sum(GRADE_POINTS[e["Grade"]] * float(course_info.get(e["Course_Code"], {}).get("Credit_Hours", 3)) for e in prev_rows)
            ps_ch = sum(float(course_info.get(e["Course_Code"], {}).get("Credit_Hours", 3)) for e in prev_rows)
            prev_sem_gpa = ps_qp / ps_ch if ps_ch > 0 else 0.0
        else:
            prev_sem_gpa = 0.0
        gpa_trend = last_sem_gpa - prev_sem_gpa
    else:
        gpa_trend = 0.0

    # Collect all marks per course for normalization reference.
    marks_per_code: dict[str, list[float]] = {}
    for e in history_sorted:
        code = e.get("Course_Code", "")
        m = float(e.get("Marks", 0.0) or 0.0)
        marks_per_code.setdefault(code, []).append(m)

    feature_rows: list[dict] = []

    for course in eligible_courses:
        code = course.get("Code", "")

        credit_hours, course_level, course_type, is_elective, is_practical, course_sem = (
            _course_row(code, course_info, course, level)
        )

        avg_type  = float(np.mean(type_gps[course_type]))   if course_type  in type_gps  else current_cgpa
        avg_level = float(np.mean(level_gps[course_level]))  if course_level in level_gps else current_cgpa

        prev_attempts = [e for e in history_sorted if e.get("Course_Code", "") == code]
        is_retake      = len(prev_attempts) > 0
        num_failures   = sum(1 for e in prev_attempts if e.get("Grade", "") in {"F", "Abs"})
        last_att       = prev_attempts[-1] if prev_attempts else None
        prev_grade_pts = GRADE_POINTS.get(last_att.get("Grade", ""), 0.0) if last_att else 0.0

        if last_att:
            raw_marks = float(last_att.get("Marks", 0.0) or 0.0)
            all_m = marks_per_code.get(code, [raw_marks])
            max_m = max(all_m) if all_m else 0.0
            prev_marks_norm = raw_marks / max_m if max_m > 0 else 0.0
        else:
            prev_marks_norm = 0.0

        avg_prereq_gp, num_prereqs_well = _prereq_features(
            code, prerequisites_map, [
                {"code": e.get("Course_Code", ""), "grade": e.get("Grade", ""),
                 "grade_points": GRADE_POINTS.get(e.get("Grade", ""), 0.0)}
                for e in history_sorted if e.get("Grade", "") in GPA_COUNTED
            ]
        )

        es = enrichment_stats.get(code, {})
        course_avg_grade = float(es.get("avg_grade", 0.0))
        course_fail_rate = float(es.get("fail_rate", 0.0))

        feature_rows.append({
            "course_code":             code,
            "cgpa_at_time":            current_cgpa,
            "last_sem_gpa":            last_sem_gpa,
            "earned_hours":            earned_hours,
            "level":                   level,
            "is_probation":            int(is_probation),
            "is_delayed":              int(is_delayed),
            "credit_hours":            credit_hours,
            "course_level":            course_level,
            "course_type":             course_type,
            "is_elective":             int(is_elective),
            "is_practical":            int(is_practical),
            "course_semester":         course_sem,
            "avg_grade_in_type":       avg_type,
            "avg_grade_in_level":      avg_level,
            "is_retake":               int(is_retake),
            "prev_grade_points":       prev_grade_pts,
            "prev_marks_normalized":   prev_marks_norm,
            "num_prior_failures":      num_failures,
            "level_gap":               course_level - level,
            "bottleneck_weight":       bottleneck.get(code, 0),
            "gpa_trend":               gpa_trend,
            "avg_prereq_grade_points": avg_prereq_gp,
            "num_prereqs_passed_well": num_prereqs_well,
            "course_avg_grade":        course_avg_grade,
            "course_fail_rate":        course_fail_rate,
        })

    return pd.DataFrame(feature_rows)
