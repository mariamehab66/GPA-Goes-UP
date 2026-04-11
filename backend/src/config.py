"""
config.py — Load academic configuration constants from academic_config.json.
Exposes GRADE_MAP, SEMESTER_LABEL_MAP, and LEVEL_THRESHOLDS at module level.
"""
import json
import os

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "rules", "academic_config.json"
)

with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _config = json.load(_f)

# Grade map: grade symbol -> points (float or None) and counted_in_gpa flag
# Keyed by normalized grade string. Also includes raw Arabic aliases.
GRADE_MAP: dict = {
    entry["grade"]: entry
    for entry in _config["gpa_system"]["grade_map"]
}

# Arabic absent character alias
_ARABIC_ABSENT = _config["gpa_system"]["special_grade_handling"]["raw_arabic_absent_char"]
GRADE_MAP[_ARABIC_ABSENT] = GRADE_MAP["Abs"]

# Semester label normalization map: Arabic pattern -> English value
# Built from study_structure config
SEMESTER_LABEL_MAP: dict[str, str] = {
    # First semester (Fall)
    "الفصل الدراسي الأول": "Fall",
    "الخريف": "Fall",
    "خريف": "Fall",
    # Second semester (Spring)
    "الفصل الدراسي الثاني": "Spring",
    "الربيع": "Spring",
    "ربيع": "Spring",
    # Summer
    "الفصل الصيفي": "Summer",
    "صيف": "Summer",
    "صيفي": "Summer",
}

# Level thresholds: list of (min_hours, max_hours_inclusive_or_None, level_int)
# Derived from level_classification in config
_levels = _config["level_classification"]["levels"]
LEVEL_THRESHOLDS: list[tuple[int, int | None, int]] = [
    (_levels["freshman"]["min_hours"],  _levels["freshman"]["max_hours"],  1),
    (_levels["sophomore"]["min_hours"], _levels["sophomore"]["max_hours"], 2),
    (_levels["junior"]["min_hours"],    _levels["junior"]["max_hours"],    3),
    (_levels["senior"]["min_hours"],    _levels["senior"]["max_hours"],    4),
]
