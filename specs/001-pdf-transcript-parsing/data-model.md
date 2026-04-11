# Data Model: PDF Upload and Arabic Transcript Parsing

**Branch**: `001-pdf-transcript-parsing` | **Date**: 2026-04-09

## Overview

This feature produces two output record types that map directly to the existing
database schema: `Student` (→ `studentt` table) and `Enrollment` (→ `enrollement`
table). Internally, the parsing pipeline uses three intermediate structures that
are never persisted: `SemesterBlock`, `ParseResult`, and `ParseWarning`.

---

## Persistent Output Records

### StudentRecord → `Student` table

Extracted once per uploaded transcript. Written to the `Student` table tagged
with the session ID for session-scoped cleanup.

| Field | Type | Source | Validation |
|-------|------|--------|-----------|
| `ID` | INT (auto-increment) | System-generated | Never from PDF |
| `CGPA` | FLOAT | Transcript header | 0.0 ≤ CGPA ≤ 4.0 |
| `Program` | VARCHAR(100) | Transcript header | Default: `"Statistics&Computer Science"` if absent |
| `Earned_Hours` | INT | Transcript header | ≥ 0 |
| `Last_Semester_GPA` | FLOAT | Most recent semester's GPA line | 0.0 ≤ value ≤ 4.0 |
| `Level` | INT | Derived from `Earned_Hours` | 1–4 per level classification thresholds |
| `Admission_Year` | INT | First semester academic year label | e.g., 2022 from "2022-2023" |

**Level derivation** (from `academic_config.json`):

| Earned Hours | Level |
|-------------|-------|
| 0 – 32 | 1 (Freshman) |
| 33 – 66 | 2 (Sophomore) |
| 67 – 100 | 3 (Junior) |
| ≥ 101 | 4 (Senior) |

---

### EnrollmentRecord → `Enrollment` table

One record per course per semester. Multiple records for the same course code are
allowed (retake scenario — FR-020). Written to `Enrollment` table tagged with session ID.

| Field | Type | Source | Validation |
|-------|------|--------|-----------|
| `Enrollment_ID` | INT (auto-increment) | System-generated | Never from PDF |
| `Student_ID` | INT | FK → StudentRecord.ID | Must reference a valid session student |
| `Course_Code` | VARCHAR(20) | Transcript course row | Must match pattern `[A-Z]{2,5} \d{3}` |
| `Course_Grade` | VARCHAR(10) | Transcript course row (normalized) | One of: A, A-, B+, B, C+, C, D, F, Abs, W, P, I, Unknown |
| `Course_GPA` | FLOAT | Transcript course row | 0.0 ≤ value ≤ 4.0; null if grade is W, P, or I |
| `Year` | INT | Semester section academic year label | e.g., 2022 from "2022-2023" |
| `Semester` | VARCHAR(20) | Semester section label (normalized) | One of: `Fall`, `Spring`, `Summer` |

**Note**: Course names are NOT extracted or stored by this feature. They are resolved
downstream from the `Course` table via the `Course_Code` FK when needed for display.

---

## Intermediate (Non-Persistent) Structures

### ParseWarning

Accumulated during parsing; included in `ParseResult.warnings`. Never persisted.

| Field | Type | Description |
|-------|------|-------------|
| `level` | str | `"field"` or `"section"` |
| `location` | str | e.g., `"Semester: Fall 2022-2023"` or `"Course: STAT 301, field: grade"` |
| `message` | str | Human-readable description of the issue |
| `raw_value` | str | The original extracted value that triggered the warning |

---

### SemesterBlock

Internal parsing unit. Not persisted. Decomposed into `EnrollmentRecord` entries.

| Field | Type | Description |
|-------|------|-------------|
| `semester_type` | str | Normalized: `Fall`, `Spring`, or `Summer` |
| `academic_year` | str | e.g., `"2022-2023"` |
| `semester_gpa` | float | Semester GPA from the terminal line of the block |
| `courses` | list[CourseRaw] | Raw extracted course rows before normalization |
| `parse_failed` | bool | True if this block could not be fully parsed |

---

### ParseResult

The complete output of one parsing operation. Passed to the storage layer.

| Field | Type | Description |
|-------|------|-------------|
| `student` | StudentRecord | Extracted + validated student-level data |
| `enrollments` | list[EnrollmentRecord] | All normalized course enrollment records |
| `warnings` | list[ParseWarning] | Field-level and section-level warnings |
| `is_partial` | bool | True if one or more semester sections failed to parse |

---

## Grade Normalization Map

Sourced from `academic_config.json → gpa_system.grade_map` and `special_grade_handling`.

| Raw Value in PDF | Stored Grade | GPA Impact | Counted in GPA |
|-----------------|-------------|-----------|---------------|
| A | A | 4.00 | Yes |
| A- | A- | 3.67 | Yes |
| B+ | B+ | 3.33 | Yes |
| B | B | 3.00 | Yes |
| C+ | C+ | 2.67 | Yes |
| C | C | 2.33 | Yes |
| D | D | 2.00 | Yes |
| F | F | 0.00 | Yes |
| غ | Abs | 0.00 | Yes |
| W | W | 0.00 | No (not counted) |
| P | P | — | No (excluded) |
| I | I | 0.00 | No |
| *(unrecognized)* | Unknown | — | Warning attached |

---

## Semester Label Normalization Map

Sourced from `academic_config.json → study_structure`.

| Arabic Label Pattern | Normalized Value |
|---------------------|-----------------|
| الفصل الدراسي الأول / الخريف / خريف | Fall |
| الفصل الدراسي الثاني / الربيع / ربيع | Spring |
| الفصل الصيفي / صيف / صيفي | Summer |

---

## Relationships

```
Student (1) ──< Enrollment (N)   [FK: Enrollment.Student_ID → Student.ID]
Course  (1) ──< Enrollment (N)   [FK: Enrollment.Course_Code → Course.Code]
```

The parser produces `Student` and `Enrollment` records. `Course` records already
exist in the database (from `courses.csv` seed data) and are not created by this
feature. The parser validates that each extracted `Course_Code` exists in the `Course`
table; if not found, it attaches a field-level warning but still writes the enrollment
record (to avoid blocking the student on a data-entry gap in the catalog).
