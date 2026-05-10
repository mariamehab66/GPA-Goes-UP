import csv
import os
import logging

log = logging.getLogger(__name__)

COURSE_MAP = {}


def load_courses(
    course_csv_path=None,
    prereq_csv_path=None
):

    global COURSE_MAP

    COURSE_MAP.clear()

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    # ---------------------------------------------------
    # Default paths
    # ---------------------------------------------------

    if course_csv_path is None:

        course_csv_path = os.path.join(
            base_dir,
            "data", "training", "course.csv"
        )

    if prereq_csv_path is None:

        prereq_csv_path = os.path.join(
            base_dir,
            "data", "training", "prerequisites.csv"
        )

    # ---------------------------------------------------
    # LOAD COURSE DATA
    # ---------------------------------------------------

    try:

        with open(course_csv_path, "r", encoding="utf-8") as f:

            reader = csv.reader(f)

            for row in reader:

                if len(row) < 8:
                    continue

                code = row[0].strip()

                if not code:
                    continue

                COURSE_MAP[code] = {

                    "code": code,

                    "type": row[1].strip(),

                    "name": row[2].strip(),

                    "credits": row[3].strip(),

                    "is_elective":
                        row[4].strip().upper() == "TRUE",

                    "is_practical":
                        row[5].strip().upper() == "TRUE",

                    "level": row[6].strip(),

                    "semester": row[7].strip(),

                    # filled later
                    "prerequisites": []
                }

        log.info(
            "Loaded %d courses",
            len(COURSE_MAP)
        )

    except Exception:
        log.exception("Failed to load course.csv")

    # ---------------------------------------------------
    # LOAD PREREQUISITES
    # ---------------------------------------------------

    try:

        with open(prereq_csv_path, "r", encoding="utf-8") as f:

            reader = csv.reader(f)

            for row in reader:

                if len(row) < 2:
                    continue

                course_code = row[0].strip()
                prereq_code = row[1].strip()

                if (
                    course_code not in COURSE_MAP
                    or not prereq_code
                ):
                    continue

                COURSE_MAP[course_code][
                    "prerequisites"
                ].append(prereq_code)

        log.info("Loaded prerequisites")

    except Exception:
        log.exception("Failed to load prerequisites.csv")


def get_course(code: str):

    return COURSE_MAP.get(code)


def get_course_name(code: str) -> str:

    c = COURSE_MAP.get(code)

    if not c:
        return code

    return f"{code} - {c['name']}"


def get_prerequisites(code: str):

    c = COURSE_MAP.get(code)

    if not c:
        return []

    return c.get("prerequisites", [])