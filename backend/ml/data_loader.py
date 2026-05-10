"""
ml/data_loader.py

All shared constants, CSV/DB loaders, and lightweight preprocessing.
Nothing here does feature engineering — that lives in features.py.
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Grade constants
# ---------------------------------------------------------------------------

# Known typos in the raw enrollment data that are normalised on load.
COURSE_CODE_FIXES: dict[str, str] = {
    "STATS 101": "STAT 101",
    "CHE 103":   "CHEM 103",
}

# Grades whose quality points count toward GPA.
GRADE_POINTS: dict[str, float] = {
    "A":   4.00,
    "A-":  3.67,
    "B+":  3.33,
    "B":   3.00,
    "C+":  2.67,
    "C":   2.33,
    "D":   2.00,
    "F":   0.00,
    "Abs": 0.00,
}
GPA_COUNTED: set[str] = set(GRADE_POINTS)

# Passing grades (D and above, plus P for pass/fail courses).
PASSING_GRADES: set[str] = {"A", "A-", "B+", "B", "C+", "C", "D", "P"}

# Pass/fail courses excluded from ML training (no letter grade to predict).
PASS_FAIL_COURSES: set[str] = {"ASU101", "INCO 102"}

# Semester sort index within an academic year.
SEM_ORDER: dict[str, int] = {"fall": 0, "spring": 1, "summer": 2}

# ---------------------------------------------------------------------------
# Grade-bucket mapping  (Q2: show both bucket and constituent grades)
# ---------------------------------------------------------------------------

GRADE_BUCKET_MAP: dict[str, str] = {
    "A":   "Excellent",  # A, A-  → GPA ≥ 3.67
    "A-":  "Excellent",
    "B+":  "Good",       # B+, B  → GPA 3.00–3.33
    "B":   "Good",
    "C+":  "Average",    # C+, C  → GPA 2.33–2.67
    "C":   "Average",
    "D":   "Low",        # D      → GPA 2.00  (barely passing)
    "F":   "Fail",       # F, Abs → GPA 0.00
    "Abs": "Fail",
}

# Ordered from best to worst — used for ranking and tolerance accuracy.
BUCKET_ORDER: list[str] = ["Excellent", "Good", "Average", "Low", "Fail"]

# Human-readable grade range shown in the API response alongside the bucket.
BUCKET_TO_GRADES: dict[str, str] = {
    "Excellent": "A, A-",
    "Good":      "B+, B",
    "Average":   "C+, C",
    "Low":       "D",
    "Fail":      "F",
}

# ---------------------------------------------------------------------------
# CSV loader
# ---------------------------------------------------------------------------

def load_csvs(data_dir: str = ".") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all four source CSVs from *data_dir*.
    Returns (enrollment, student, course, prerequisites).
    """
    enrollment = pd.read_csv(os.path.join(data_dir, "enrollment.csv"))
    student    = pd.read_csv(os.path.join(data_dir, "student.csv"))

    # course.csv has no header row in the original file.
    course = pd.read_csv(
        os.path.join(data_dir, "course.csv"),
        header=None,
        names=["Code", "Type", "Course_Name", "Credit_Hours",
               "Is_elective", "Is_practical", "Level", "Semester"],
    )

    prerequisites = pd.read_csv(
        os.path.join(data_dir, "prerequisites.csv"),
        header=None,
        names=["Course_Code", "Prerequisite_Course_Code"],
    )

    enrollment, student, course = _normalise(enrollment, student, course)
    return enrollment, student, course, prerequisites


# ---------------------------------------------------------------------------
# DB loader (used by the /api/admin/retrain endpoint)
# ---------------------------------------------------------------------------

def load_from_db() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Pull the same four tables from MySQL and return them as DataFrames.
    Applies the same normalisation as load_csvs.
    """
    import database  # imported here to avoid a hard dependency at module load

    enrollment    = database.fetch_df("SELECT * FROM Enrollment")
    student       = database.fetch_df("SELECT * FROM Student")
    course        = database.fetch_df("SELECT * FROM Course")
    prerequisites = database.fetch_df(
        "SELECT Course_Code, Prerequisite_Course_Code FROM Prerequisite"
    )

    enrollment, student, course = _normalise(enrollment, student, course)
    return enrollment, student, course, prerequisites


# ---------------------------------------------------------------------------
# Shared normalisation (runs for both CSV and DB paths)
# ---------------------------------------------------------------------------

def _normalise(
    enrollment: pd.DataFrame,
    student: pd.DataFrame,
    course: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Fix known typos in course codes.
    enrollment["Course_Code"] = enrollment["Course_Code"].replace(COURSE_CODE_FIXES)

    # Normalise boolean columns — CSV stores "TRUE"/"FALSE", DB stores 0/1.
    for col in ("Is_elective", "Is_practical"):
        if col in course.columns:
            raw = course[col]
            if raw.dtype == object:
                course[col] = raw.astype(str).str.upper().map(
                    {"TRUE": True, "FALSE": False}
                )
            else:
                course[col] = raw.astype(bool)

    # Uniform lowercase semester values.
    if "Semester" in course.columns:
        course["Semester"] = course["Semester"].str.lower().str.strip()

    return enrollment, student, course


# ---------------------------------------------------------------------------
# Preprocessing helpers shared across training and inference
# ---------------------------------------------------------------------------

def filter_training_rows(enrollment: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows with a GPA-counted letter grade
    (drops pass/fail courses and any grade not in GPA_COUNTED).
    Appends 'grade_bucket' and 'grade_points' columns.
    """
    df = enrollment[~enrollment["Course_Code"].isin(PASS_FAIL_COURSES)].copy()
    df = df[df["Grade"].isin(GPA_COUNTED)].copy()
    df["grade_bucket"] = df["Grade"].map(GRADE_BUCKET_MAP)
    df["grade_points"] = df["Grade"].map(GRADE_POINTS)
    return df.reset_index(drop=True)


def build_prerequisites_map(prerequisites: pd.DataFrame) -> dict[str, list[str]]:
    """Return {course_code: [prereq_code, ...]} from the prerequisites DataFrame."""
    result: dict[str, list[str]] = {}
    for _, row in prerequisites.iterrows():
        result.setdefault(row["Course_Code"], []).append(
            row["Prerequisite_Course_Code"]
        )
    return result


def semester_sort_key(year: str, semester: str) -> tuple[int, int]:
    """
    Convert ("2023-2024", "spring") → (2023, 1) for chronological sorting.
    The integer is the academic year start extracted from the "YYYY-YYYY" string.
    """
    try:
        year_int = int(str(year).split("-")[0])
    except (ValueError, AttributeError):
        year_int = 0
    return (year_int, SEM_ORDER.get(str(semester).lower().strip(), 0))
