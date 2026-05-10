from collections import defaultdict


def build_student_insights(
    enrollment_history: list
) -> dict:
    """
    Analyze a student's academic history
    and generate structured insights.

    Returns:
        {
            active_failed_courses: [],
            recovered_courses: [],
            repeated_courses: [],
            total_failed_courses: int,
            risk_level: str
        }
    """

    # ============================================================
    # TRACK COURSE ATTEMPTS
    # ============================================================

    course_attempts = defaultdict(list)

    for enrollment in enrollment_history:

        code = enrollment.get(
            "Course_Code",
            ""
        )

        grade = enrollment.get(
            "Grade",
            ""
        )

        course_attempts[code].append(
            grade
        )

    # ============================================================
    # DETECT FAILURES / RECOVERIES
    # ============================================================

    active_failed_courses = []

    recovered_courses = []

    repeated_courses = []

    fail_grades = {
        "F",
        "FA",
        "غ"
    }

    passing_grades = {
        "D",
        "D+",
        "C",
        "C+",
        "B",
        "B+",
        "A",
        "A-"
    }

    for course_code, grades in course_attempts.items():

        # repeated course
        if len(grades) > 1:

            repeated_courses.append(
                course_code
            )

        has_failed = any(
            g in fail_grades
            for g in grades
        )

        has_passed = any(
            g in passing_grades
            for g in grades
        )

        # failed then passed later
        if has_failed and has_passed:

            recovered_courses.append(
                course_code
            )

        # failed and never passed
        elif has_failed and not has_passed:

            active_failed_courses.append(
                course_code
            )

    # ============================================================
    # DETERMINE RISK LEVEL
    # ============================================================

    total_active_failures = len(
        active_failed_courses
    )

    if total_active_failures >= 5:

        risk_level = "high"

    elif total_active_failures >= 2:

        risk_level = "moderate"

    else:

        risk_level = "low"

    # ============================================================
    # FINAL STRUCTURED INSIGHTS
    # ============================================================

    return {

        "active_failed_courses":
            sorted(active_failed_courses),

        "recovered_courses":
            sorted(recovered_courses),

        "repeated_courses":
            sorted(repeated_courses),

        "total_failed_courses":
            total_active_failures,

        "risk_level":
            risk_level
    }