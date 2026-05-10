"""
Rule_Engine.py

Core academic logic engine for the GPA Goes UP recommendation system.
Pure business logic — no database connections, no SQL, no PDF parsing.

The Backend fetches data from MySQL, assembles clean Python structures,
and passes them into AcademicRuleEngine.process(). The returned payload
is forwarded directly to the ML model.

All thresholds and limits are read from Rule_Engine.json. Nothing is hardcoded.
"""

import json
from datetime import date


class AcademicRuleEngine:
    """
    Evaluates university academic rules and produces a course-recommendation
    payload ready for the ML ranking model.
    """

    # =========================================================================
    # PART 1: SETUP & INITIALIZATION
    # =========================================================================

    def __init__(self, json_config_path: str) -> None:
        """
        Load Rule_Engine.json and create named aliases for every key section
        so the rest of the class never re-indexes self.config directly.
        """
        with open(json_config_path, 'r', encoding='utf-8') as fh:
            self.config = json.load(fh)

        self.grad_req     = self.config['graduation_requirements']
        self.load_rules   = self.config['academic_load']
        self.delay_rules  = self.config['academic_delay']
        self.senior_rules = self.config['senior_exception']
        self.retake_rules = self.config['course_retake_rules']
        self.selection    = self.config['course_selection_strategy']
        self.gpa_cfg      = self.config['gpa_system']
        self.level_cfg    = self.config['level_classification']

        # grade string  ->  full grade-map entry dict
        self._grade_map: dict[str, dict] = {
            g['grade']: g for g in self.gpa_cfg['grade_map']
        }

        # raw alias  ->  canonical grade  (e.g. "gh" -> "Abs")
        self._alias_map: dict[str, str] = {
            g['raw_input_alias']: g['grade']
            for g in self.gpa_cfg['grade_map']
            if 'raw_input_alias' in g
        }

    # =========================================================================
    # PART 2: CORE HELPERS
    # =========================================================================

    def normalize_grade(self, raw: str | None) -> str:
        """
        Convert any raw grade token to its canonical form.
        Handles the Arabic absent character 'gh', the 'gh' alias, and
        any other raw_input_alias entries declared in Rule_Engine.json.
        Returns 'I' (Incomplete) when raw is None or empty.
        """
        if not raw:
            return 'I'

        raw = str(raw).strip()
        special = self.gpa_cfg.get('special_grade_handling', {})

        if raw == special.get('raw_arabic_absent_char', 'غ'):
            return special.get('normalize_to', 'Abs')

        if raw in self._alias_map:
            return self._alias_map[raw]

        return raw

    def is_passing_grade(self, grade: str) -> bool:
        """
        Return True if the canonical grade is a passing mark.
        'P' (pass/fail courses) is always passing.
        Numeric grades must meet the minimum pass grade defined in JSON.
        Grades with null points (W, I) are not passing.
        """
        grade = self.normalize_grade(grade)

        if grade == 'P':
            return True

        info = self._grade_map.get(grade)
        if info is None:
            return False

        points = info.get('points')
        if points is None:
            return False  # W, I — no numeric value

        min_pass_grade  = self.grad_req.get('minimum_pass_grade', 'D')
        min_pass_points = self._grade_map.get(min_pass_grade, {}).get('points', 2.0)
        return points >= min_pass_points

    def _get_latest_attempts(self, enrollments: list[dict]) -> dict[str, dict]:
        """
        For each course code, keep only the most recent enrollment record.
        Recency: higher Year wins; within the same year, semester order
        (fall=0, spring=1, summer=2) breaks the tie.
        """
        sem_order = {'fall': 0, 'spring': 1, 'summer': 2}
        latest: dict[str, dict] = {}

        for record in enrollments:
            code = record.get('Course_Code', '')
            if not code:
                continue

            year = record.get('Year', 0)
            sem  = sem_order.get(str(record.get('Semester', '')).lower(), -1)

            prev = latest.get(code)
            if prev is None:
                latest[code] = record
                continue

            p_year = prev.get('Year', 0)
            p_sem  = sem_order.get(str(prev.get('Semester', '')).lower(), -1)

            if year > p_year or (year == p_year and sem > p_sem):
                latest[code] = record

        return latest

    def get_passed_courses(self, enrollments: list[dict]) -> set[str]:
        """Return the set of course codes the student has passed (latest attempt only)."""
        return {
            code
            for code, rec in self._get_latest_attempts(enrollments).items()
            if self.is_passing_grade(self.normalize_grade(rec.get('Grade')))
        }

    def get_failed_courses(self, enrollments: list[dict]) -> set[str]:
        """
        Return the set of course codes whose latest-attempt grade is eligible
        for retake (F, Abs, W, I — as declared in Rule_Engine.json).
        """
        eligible: set[str] = set(self.retake_rules.get('eligible_grades_for_retake', []))
        return {
            code
            for code, rec in self._get_latest_attempts(enrollments).items()
            if self.normalize_grade(rec.get('Grade')) in eligible
        }

    # =========================================================================
    # PART 3: STATUS & CREDIT HOURS CALCULATION
    # =========================================================================

    def _level_from_hours(self, earned_hours: int) -> int:
        """Derive student level from earned credit hours using the JSON level map."""
        for label, bounds in self.level_cfg.get('levels', {}).items():
            if bounds['min_hours'] <= earned_hours <= bounds['max_hours']:
                return int(label.split()[-1])
        return 1

    def _expected_level(self, admission_year: int) -> int:
        """
        Expected level = academic years elapsed since admission, capped at 4.
        The academic year is assumed to begin in September.
        """
        today = date.today()
        academic_year = today.year if today.month >= 9 else today.year - 1
        elapsed = academic_year - admission_year
        return max(1, min(4, elapsed + 1))

    def calculate_academic_status(self, student_data: dict) -> dict:
        """
        Determine academic status and compute the maximum registrable credit hours.

        Status rules (evaluated in priority order):
          1. Probation  -- CGPA < minimum_cumulative_gpa   -> base = 12
          2. Delayed    -- actual_level < expected_level
                          AND actual_level < 4             -> base = 16
          3. Normal     -- everything else                 -> base = 18

        Bonus rule (+3, non-stacking):
          Senior exception takes precedence over the GPA bonus.
          Only one +3 bonus applies per semester.

        Returns:
          is_probation, is_delayed, is_senior_exception,
          actual_level, expected_level, status_label,
          max_credit_hours, warnings (list[str])
        """
        warnings: list[str] = []

        cgpa         = student_data.get('CGPA', 0.0)
        earned_hours = student_data.get('Earned_Hours', 0)
        admission_yr = student_data.get('Admission_Year', date.today().year)
        last_sem_gpa = student_data.get('Last_Semester_GPA', 0.0)

        actual_level   = student_data.get('Level') or self._level_from_hours(earned_hours)
        expected_level = self._expected_level(admission_yr)

        # Pull every threshold from JSON
        min_cgpa         = self.grad_req.get('minimum_cumulative_gpa', 2.0)
        total_grad_hours = self.senior_rules.get('total_graduation_hours', 140)
        senior_level     = self.senior_rules.get('eligible_level', 4)
        senior_threshold = self.senior_rules.get('max_remaining_hours_to_trigger', 21)
        senior_bonus     = self.senior_rules.get('bonus_hours', 3)

        reg           = self.load_rules['regular_semester']
        base_max      = reg.get('max_credit_hours', 18)
        probation_max = reg.get('academic_probation_max_credit_hours', 12)
        delayed_max   = self.delay_rules.get('max_credit_hours_when_delayed', 16)
        gpa_threshold = reg['gpa_bonus'].get('threshold', 3.0)
        gpa_bonus_hrs = reg['gpa_bonus'].get('bonus_hours', 3)

        # Evaluate conditions
        is_probation = cgpa < min_cgpa
        # Level 4 is NEVER classified as delayed (explicitly stated in JSON)
        is_delayed   = (actual_level < expected_level) and (actual_level < senior_level)
        remaining    = total_grad_hours - earned_hours
        is_senior    = (actual_level == senior_level) and (remaining <= senior_threshold)

        # Determine base credit hours
        if is_probation:
            base = probation_max
            warnings.append(
                f"Academic probation: CGPA {cgpa:.2f} is below the minimum {min_cgpa}. "
                f"Registration capped at {probation_max} credit hours."
            )
        elif is_delayed:
            base = delayed_max
            warnings.append(
                f"Academically delayed: current level {actual_level} is below "
                f"expected level {expected_level}. "
                f"Registration capped at {delayed_max} credit hours."
            )
        else:
            base = base_max

        # Apply single +3 bonus -- senior exception wins over GPA bonus (non-stacking)
        if is_senior:
            base += senior_bonus
            warnings.append(
                f"Senior exception: {remaining} hours remaining <= {senior_threshold}. "
                f"+{senior_bonus} bonus hours granted."
            )
        elif last_sem_gpa >= gpa_threshold:
            base += gpa_bonus_hrs
            warnings.append(
                f"GPA bonus: last semester GPA {last_sem_gpa:.2f} >= {gpa_threshold}. "
                f"+{gpa_bonus_hrs} bonus hours granted."
            )

        label = 'probation' if is_probation else ('delayed' if is_delayed else 'good_standing')

        return {
            'is_probation':        is_probation,
            'is_delayed':          is_delayed,
            'is_senior_exception': is_senior,
            'actual_level':        actual_level,
            'expected_level':      expected_level,
            'status_label':        label,
            'max_credit_hours':    base,
            'warnings':            warnings,
        }

    # =========================================================================
    # PART 4: THE SMART ENGINE (COURSE SELECTION)
    # =========================================================================

    def _bottleneck_weight(self, course_code: str, prerequisites_map: dict) -> int:
        """
        Count how many other courses list this course as a direct prerequisite.
        Higher weight means this course unlocks more future courses -- schedule it first.
        """
        return sum(1 for prereqs in prerequisites_map.values() if course_code in prereqs)

    def _filter_fulfilled_electives(
        self,
        candidates: list[dict],
        passed_courses: set[str],
        available_courses: list[dict],
    ) -> list[dict]:
        """
        Remove elective courses whose requirement group has already been satisfied.

        Grouping key: (Level, Semester, Type) — courses that share all three
        belong to the same 'pick one' slot in the curriculum.  If the student
        has passed ANY course from a group, every other un-taken course in that
        same group is excluded from the candidate list entirely and never
        reaches the ML model.

        Non-elective courses are always passed through unchanged.
        """
        course_lookup: dict[str, dict] = {
            c.get('Code', ''): c for c in available_courses
        }

        fulfilled_slots: set[tuple] = set()
        for code in passed_courses:
            course = course_lookup.get(code)
            if course and course.get('Is_elective'):
                slot = (
                    course.get('Level', 0),
                    str(course.get('Semester', '')).lower(),
                    str(course.get('Type', '')),
                )
                fulfilled_slots.add(slot)

        if not fulfilled_slots:
            return candidates

        filtered: list[dict] = []
        for c in candidates:
            if not c.get('Is_elective'):
                filtered.append(c)
                continue
            slot = (
                c.get('Level', 0),
                str(c.get('Semester', '')).lower(),
                str(c.get('Type', '')),
            )
            if slot not in fulfilled_slots:
                filtered.append(c)
        return filtered

    def _filter_by_prerequisites(
        self,
        courses: list[dict],
        passed_courses: set[str],
        prerequisites_map: dict,
        is_senior: bool,
    ) -> list[dict]:
        """
        Keep only courses whose prerequisites are fully satisfied.
        Level-4 students with the senior exception may register concurrently
        with unsatisfied prerequisites (requires admin approval per JSON config).
        """
        senior_cfg = (
            self.config
            .get('course_registration', {})
            .get('senior_exception', {})
        )
        senior_concurrent = senior_cfg.get('allow_concurrent_failed_prerequisite_registration', False)

        eligible = []
        for course in courses:
            prereqs = prerequisites_map.get(course.get('Code', ''), [])
            if all(p in passed_courses for p in prereqs):
                eligible.append(course)
            elif is_senior and senior_concurrent:
                eligible.append(course)
        return eligible

    def _guillotine(
        self,
        pool: list[dict],
        failed_courses: set[str],
        primary_level: int,
        prerequisites_map: dict,
        max_levels: int,
    ) -> list[dict]:
        """
        Trim the pool so it spans at most max_levels different course levels.

        The primary level (student's actual level) is always kept.
        Each additional slot is filled by the level with the highest score:
            score = sum(bottleneck_weight * 2  for each course in level)
                  + count of failed courses in that level
        """
        other_levels = sorted({
            c.get('Level', 0) for c in pool if c.get('Level') != primary_level
        })

        selected: set[int] = {primary_level}

        for _ in range(max_levels - 1):
            best_level, best_score = None, -1
            for lvl in other_levels:
                if lvl in selected:
                    continue
                lvl_courses = [c for c in pool if c.get('Level') == lvl]
                score = (
                    sum(
                        self._bottleneck_weight(c.get('Code', ''), prerequisites_map) * 2
                        for c in lvl_courses
                    )
                    + sum(1 for c in lvl_courses if c.get('Code', '') in failed_courses)
                )
                if score > best_score:
                    best_score, best_level = score, lvl
            if best_level is not None:
                selected.add(best_level)

        return [c for c in pool if c.get('Level', 0) in selected]

    def _build_pool(
        self,
        candidates: list[dict],
        passed_courses: set[str],
        failed_courses: set[str],
        actual_level: int,
        expected_level: int,
        max_hours: int,
        buffer_count: int,
        prerequisites_map: dict,
    ) -> list[dict]:
        """
        Full pipeline for building the sorted, annotated course pool:

          1. Scope filter        -- past uncompleted levels + current + expected
          2. Sequential borrowing -- if gathered hours < target, borrow from the
                                    immediately next level; repeat until satisfied
          3. Guillotine          -- trim to max_allowed_levels_per_semester if exceeded
          4. Annotate & sort     -- by (bottleneck DESC, is_failed DESC, is_past_gap DESC)
        """
        # Step 1 -- Scope
        allowed: set[int] = set(range(1, actual_level + 1)) | {expected_level}
        pool = [
            c for c in candidates
            if c.get('Code', '') not in passed_courses
            and c.get('Level', 0) in allowed
        ]

        # Step 2 -- Sequential borrowing
        # "hours for buffer courses" proxy: buffer_count * 3 (typical course size)
        target     = max_hours + buffer_count * 3
        pool_hours = sum(c.get('Credit_Hours', 0) for c in pool)

        if pool_hours < target:
            borrow_levels = sorted(
                lvl for lvl in {c.get('Level', 0) for c in candidates}
                if lvl > max(allowed)
            )
            for lvl in borrow_levels:
                if pool_hours >= target:
                    break
                extras = [
                    c for c in candidates
                    if c.get('Level') == lvl
                    and c.get('Code', '') not in passed_courses
                ]
                pool.extend(extras)
                pool_hours += sum(c.get('Credit_Hours', 0) for c in extras)
                allowed.add(lvl)

        # Step 3 -- Guillotine
        max_levels = self.selection.get('max_allowed_levels_per_semester', 2)
        if len({c.get('Level', 0) for c in pool}) > max_levels:
            pool = self._guillotine(
                pool, failed_courses, actual_level, prerequisites_map, max_levels
            )

        # Step 4 -- Annotate and sort
        annotated: list[dict] = []
        for course in pool:
            code        = course.get('Code', '')
            level       = course.get('Level', 0)
            is_failed   = code in failed_courses
            is_past_gap = level < actual_level and code not in passed_courses
            weight      = self._bottleneck_weight(code, prerequisites_map)

            annotated.append({
                **course,
                '_weight':   weight,
                '_failed':   is_failed,
                '_past_gap': is_past_gap,
            })

        annotated.sort(
            key=lambda c: (-c['_weight'], -int(c['_failed']), -int(c['_past_gap']))
        )
        return annotated

    def _truncate_to_payload(
        self,
        sorted_pool: list[dict],
        max_hours: int,
        buffer_count: int,
    ) -> list[dict]:
        """
        Greedily select courses up to max_hours, then append exactly buffer_count
        overflow courses. The combined list is the single payload for the ML model.

        The ML model decides which courses are top recommendations vs. alternatives.
        This engine does NOT split or categorize the list.
        """
        main: list[dict] = []
        hours_used = 0
        overflow: list[dict] = []

        for course in sorted_pool:
            hrs = course.get('Credit_Hours', 0)
            if hours_used + hrs <= max_hours:
                main.append(course)
                hours_used += hrs
            else:
                overflow.append(course)

        return main + overflow[:buffer_count]

    # =========================================================================
    # PART 5: THE MAESTRO (MAIN ENTRY POINT)
    # =========================================================================

    ###########################################################################
    ### BACKEND INTEGRATION NOTE ###
    ###
    ### Call AcademicRuleEngine.process() after fetching all required data.
    ###
    ### student_data (dict) -- one Student row + all Enrollment rows:
    ###   {
    ###     "ID":                str | int,
    ###     "CGPA":              float,
    ###     "Program":           str,
    ###     "Earned_Hours":      int,
    ###     "Last_Semester_GPA": float,
    ###     "Level":             int | None,   # None -> engine recalculates
    ###     "Admission_Year":    int,
    ###     "enrollments": [
    ###       {
    ###         "Course_Code": str,
    ###         "Grade":       str,   # Raw OK: "gh", "A-", "F", Arabic char ...
    ###         "Marks":       float,
    ###         "Year":        int,
    ###         "Semester":    str,   # "fall" | "spring" | "summer"
    ###         "Course_GPA":  float
    ###       }, ...
    ###     ]
    ###   }
    ###
    ### available_courses (list[dict]) -- full Course table dump:
    ###   [
    ###     {
    ###       "Code":         str,
    ###       "Course_Name":  str,
    ###       "Credit_Hours": int,
    ###       "Level":        int,
    ###       "Semester":     str,   # "fall" | "spring" | "both"
    ###       "Type":         str,
    ###       "Is_elective":  bool,
    ###       "Is_practical": bool
    ###     }, ...
    ###   ]
    ###
    ### prerequisites_map (dict) -- assembled from the Prerequisite table:
    ###   { "COURSE_CODE": ["PREREQ_1", "PREREQ_2"], ... }
    ###   Courses with no prerequisites may be absent or mapped to [].
    ###
    ### target_semester (str) -- "fall" | "spring" | "summer"
    ###########################################################################

    def process(
        self,
        student_data: dict,
        available_courses: list[dict],
        prerequisites_map: dict,
        target_semester: str,
    ) -> dict:
        """
        Main entry point. Orchestrates all rule evaluation and returns a
        structured payload ready for the ML ranking model.

        Return shape:
          {
            "student_id":               str | int,
            "target_semester":          str,
            "academic_status":          "probation" | "delayed" | "good_standing",
            "max_allowed_hours":        int,
            "warnings":                 list[str],
            "engine_suggested_courses": list[dict]  # single flat list for ML
          }
        """
        student_id      = student_data.get('ID', 'unknown')
        enrollments     = student_data.get('enrollments', [])
        target_semester = target_semester.lower().strip()

        passed_courses = self.get_passed_courses(enrollments)
        failed_courses = self.get_failed_courses(enrollments)
        status         = self.calculate_academic_status(student_data)
        buffer_count   = self.selection.get('suggestion_overflow_buffer_for_alternatives', 3)

        # ── Semester-specific course filtering ────────────────────────────────
        if target_semester == 'summer':
            # Summer: only courses the student is eligible to retake.
            # The course's Semester attribute is irrelevant for summer.
            summer_cfg      = self.config.get('summer_semester_registration', {})
            summer_eligible = set(summer_cfg.get('eligible_grades', []))
            latest          = self._get_latest_attempts(enrollments)
            retakeable      = {
                code for code, rec in latest.items()
                if self.normalize_grade(rec.get('Grade')) in summer_eligible
            }
            candidates = [
                c for c in available_courses
                if c.get('Code', '') in retakeable
            ]
            max_hours = self.load_rules.get('summer_semester', {}).get('max_credit_hours', 6)

        else:
            # Regular semester: keep only courses matching the target semester.
            candidates = [
                c for c in available_courses
                if c.get('Semester', '').lower() in (target_semester, 'both')
            ]
            max_hours = status['max_credit_hours']

        # ── Prerequisite gate ─────────────────────────────────────────────────
        candidates = self._filter_by_prerequisites(
            candidates, passed_courses, prerequisites_map,
            status['is_senior_exception'],
        )

        # ── Elective group gate (regular semesters only) ──────────────────────
        # Must run AFTER the prerequisite gate so the course_lookup is stable,
        # and only for regular semesters — summer is for retakes of failed
        # courses, so a failed elective stays retakeable even when a sibling
        # from the same group was passed earlier.
        if target_semester != 'summer':
            candidates = self._filter_fulfilled_electives(
                candidates, passed_courses, available_courses
            )

        # ── Build sorted course pool ──────────────────────────────────────────
        if target_semester == 'summer':
            # Summer needs no scope or guillotine logic -- annotate and sort only.
            annotated: list[dict] = []
            for course in candidates:
                code   = course.get('Code', '')
                weight = self._bottleneck_weight(code, prerequisites_map)
                annotated.append({
                    **course,
                    '_weight':   weight,
                    '_failed':   code in failed_courses,
                    '_past_gap': False,
                })
            annotated.sort(key=lambda c: (-c['_weight'], -int(c['_failed'])))
            pool = annotated

        else:
            pool = self._build_pool(
                candidates, passed_courses, failed_courses,
                status['actual_level'], status['expected_level'],
                max_hours, buffer_count, prerequisites_map,
            )

        # ── Truncate to ML payload ────────────────────────────────────────────
        payload = self._truncate_to_payload(pool, max_hours, buffer_count)

        # Strip internal annotation keys before handing off to the Backend
        clean = [
            {k: v for k, v in c.items() if not k.startswith('_')}
            for c in payload
        ]

        # Graduation roadmap: every course in the curriculum the student has not
        # yet passed.  No prerequisite gate, no semester constraint — this is the
        # complete picture of what remains until graduation, sorted naturally by
        # level then semester so the frontend can display it as-is.
        # Step 1: remove already-passed courses
        _roadmap = [
            c for c in available_courses
            if c.get('Code', '') not in passed_courses
        ]
        # Step 2: drop elective siblings whose slot is already fulfilled
        _roadmap = self._filter_fulfilled_electives(
            _roadmap, passed_courses, available_courses
        )
        # Step 3: annotate + sort by level → semester
        _sem_sort = {'fall': 0, 'spring': 1, 'summer': 2, 'both': 3}
        graduation_roadmap = sorted(
            [
                {**c, 'is_failed': c.get('Code', '') in failed_courses}
                for c in _roadmap
            ],
            key=lambda c: (
                c.get('Level', 0),
                _sem_sort.get(str(c.get('Semester', '')).lower(), 9),
            ),
        )

        return {
            'student_id':               student_id,
            'target_semester':          target_semester,
            'academic_status':          status['status_label'],
            'max_allowed_hours':        max_hours,
            'warnings':                 status['warnings'],
            'engine_suggested_courses': clean,
            'all_eligible_courses':     graduation_roadmap,
        }
