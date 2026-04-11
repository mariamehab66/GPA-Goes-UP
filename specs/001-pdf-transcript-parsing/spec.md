# Feature Specification: PDF Upload and Arabic Transcript Parsing

**Feature Branch**: `001-pdf-transcript-parsing`
**Created**: 2026-04-09
**Status**: Draft
**Input**: Arabic PDF academic transcript → structured student and enrollment records

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Transcript and Receive Structured Academic Record (Priority: P1)

A student uploads their Arabic-language PDF academic transcript. The system extracts
all relevant information — general student data and the full course enrollment history —
and returns a clean, structured record ready for downstream processing (rule engine,
ML scoring, GPA tools).

**Why this priority**: This is the foundational input step. Every downstream feature
(course recommendations, GPA simulation, chatbot) depends entirely on this data
being correctly parsed. Without it, no other feature can function.

**Independent Test**: A student uploads a valid Arabic transcript PDF and the system
returns a structured record containing student-level fields and a full semester-by-semester
enrollment list — verifiable by comparing extracted values against the known transcript content.

**Acceptance Scenarios**:

1. **Given** a valid Arabic PDF transcript, **When** the student uploads the file,
   **Then** the system extracts CGPA, earned hours, program, level, admission year,
   and all semester-course records with correct English-normalized values.

2. **Given** a transcript with the Arabic absent symbol غ in a grade field,
   **When** the system processes the grade, **Then** the value is stored as `Abs`
   in the output record.

3. **Given** a transcript containing semester labels in Arabic (e.g., الفصل الدراسي الأول),
   **When** the system processes the semester labels, **Then** each semester is mapped
   to the correct English value: `Fall`, `Spring`, or `Summer`.

4. **Given** a transcript spanning multiple academic years, **When** the system processes
   the document, **Then** the admission year is correctly inferred from the academic year
   label of the first semester (e.g., 2022 from "2022-2023").

5. **Given** a transcript where the latest semester is the most recent one listed,
   **When** the system determines the student's current level, **Then** the level
   classification (Freshman / Sophomore / Junior / Senior) is derived from total
   earned hours per the official threshold table.

---

### User Story 2 - Robust Handling of Format Variations (Priority: P2)

The system correctly parses transcripts that differ in layout, spacing, column order,
or formatting — as commonly seen across real academic records — without failing or
producing incorrect output.

**Why this priority**: Real transcripts from different years or departments vary in
formatting. The system must be production-ready for actual student uploads, not only
for a single controlled sample.

**Independent Test**: Upload multiple transcripts from `data/sample_academic_record/`
representing different format variants; all must produce valid structured output with
no missing required fields and no parsing errors.

**Acceptance Scenarios**:

1. **Given** two transcripts with different column orderings for course data,
   **When** each is uploaded, **Then** both produce correctly mapped records with
   all required course fields populated.

2. **Given** a transcript with extra whitespace, merged cells, or inconsistent line
   breaks, **When** it is processed, **Then** the system extracts data without
   truncation or misalignment errors.

---

### User Story 3 - Rejection and Clear Feedback for Invalid Inputs (Priority: P3)

When a student uploads a file that cannot be parsed as a valid Arabic academic
transcript, the system rejects it gracefully and provides actionable feedback.

**Why this priority**: Invalid uploads are an expected edge case. Clear error messages
prevent silent failures and guide the student to retry with the correct file.

**Independent Test**: Upload a non-PDF file, a blank PDF, and an unrelated PDF;
each must produce a specific, user-facing error message — no crash, no partial output.

**Acceptance Scenarios**:

1. **Given** a file that is not a PDF, **When** the student submits it,
   **Then** the system rejects it with a message indicating only PDF files are accepted.

2. **Given** a blank or corrupted PDF, **When** the student submits it,
   **Then** the system returns an error indicating the file could not be read.

3. **Given** a PDF that does not appear to contain an academic transcript structure,
   **When** the student submits it, **Then** the system returns an error indicating
   the expected transcript structure was not found.

---

### Edge Cases

- What happens when a semester section has no courses listed?
- What happens when CGPA is missing from the transcript header?
- When a grade field contains an unrecognized symbol: the grade is stored as `"Unknown"`, a field-level warning is attached to that course record, and parsing continues for the rest of the transcript.
- What if the same course code appears more than once across different semesters (retake scenario)?
- What if the last semester in the transcript contains zero enrolled courses?
- What if the program name is absent from the transcript header?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a single PDF file upload as input per session.
- **FR-002**: The system MUST extract from the transcript header: CGPA, earned hours,
  and program name (if present in the document).
- **FR-003**: The system MUST infer the student's admission year from the academic year
  label of the first semester in the transcript (e.g., "2022-2023" → admission year 2022).
- **FR-004**: The system MUST parse each semester section and extract: semester type,
  academic year, the list of courses in that semester, and the semester GPA.
- **FR-005**: For each course record, the system MUST extract: course code, course grade,
  and course GPA.
- **FR-006**: The system MUST normalize all Arabic semester labels to English equivalents
  (Fall, Spring, Summer) using the mappings defined in `academic_config.json`.
- **FR-007**: The system MUST normalize the Arabic absent grade symbol (غ) to `Abs`
  per the grade mapping in `academic_config.json`; all other grade normalization rules
  in the config MUST also be applied. If a grade value does not match any entry in the
  grade map, the system MUST store the grade as `"Unknown"`, attach a field-level warning
  to that course record, and continue parsing the remainder of the transcript without
  failing or dropping the course record.
- **FR-008**: The system MUST derive the student's current level (Freshman / Sophomore /
  Junior / Senior) from total earned hours using the level classification thresholds
  in `academic_config.json`.
- **FR-009**: The system MUST identify the most recent semester in the transcript as
  the student's current academic context, using its GPA as `Last_Semester_GPA`.
- **FR-010**: The system MUST NOT extract student IDs from the PDF; student IDs MUST
  be generated internally by the system and not sourced from transcript content.
- **FR-011**: The system MUST NOT extract enrollment IDs from the PDF; enrollment IDs
  MUST be generated internally per course enrollment record.
- **FR-012**: The structured output MUST conform to the schema defined in
  `academic_config.json`:
  - Student record fields: `CGPA`, `Program`, `Earned_Hours`, `Last_Semester_GPA`,
    `Level`, `Admission_Year`
  - Enrollment record fields per course: `course_code`, `course_grade`, `course_gpa`,
    `Year`, `Semester`
- **FR-013**: The system MUST be robust to format variations across transcripts;
  differences in spacing, column ordering, and layout MUST NOT cause extraction failure.
- **FR-014**: Before passing records downstream, the system MUST validate that all
  mandatory output fields are present; if a mandatory field cannot be extracted,
  the system MUST report a specific missing-field error rather than silently producing
  an incomplete record.
- **FR-015**: The system MUST reject non-PDF files with a clear, user-facing error message.
- **FR-016**: The system MUST reject PDFs that do not contain a recognizable transcript
  structure with a clear, user-facing error message.
- **FR-017**: All student data extracted from a transcript MUST be stored only for the
  duration of the active session and deleted automatically when the session ends,
  per `academic_config.json` data privacy settings.
- **FR-018**: If one or more semester sections cannot be parsed but the student-level
  header and at least one semester are successfully extracted, the system MUST return
  the successfully parsed data and include a warning that lists each semester section
  that failed extraction by its academic year and semester type. The student MUST be
  notified and may choose to proceed with the partial result or re-upload a cleaner file.
- **FR-019**: The system MUST preserve multiple occurrences of the same course code
  across semesters as separate enrollment records (retake scenario); no deduplication
  by course code is performed.

### Key Entities

- **StudentRecord**: Represents student-level data extracted from the transcript header.
  Fields: `CGPA`, `Program`, `Earned_Hours`, `Last_Semester_GPA`, `Level`,
  `Admission_Year`. The `ID` field is system-generated, not extracted from the PDF.

- **SemesterBlock**: Represents one academic semester within the transcript.
  Fields: `semester_type` (Fall / Spring / Summer), `academic_year`
  (e.g., "2022-2023"), `semester_gpa`, and a list of associated course records.

- **CourseRecord**: Represents one course enrollment within a semester.
  Fields: `course_code`, `course_grade` (normalized), `course_gpa`, `Year`, `Semester`.
  The `enrollment_ID` and `student_id` are system-generated.

- **ParseResult**: The complete output of one parsing operation. Contains one
  `StudentRecord` and a flat list of `CourseRecord` entries (each tagged with
  their semester and academic year), ready for storage and downstream use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All required student-level fields (`CGPA`, `Earned_Hours`,
  `Last_Semester_GPA`, `Level`, `Admission_Year`) are correctly extracted from
  100% of sample transcripts in `data/sample_academic_record/`.
- **SC-002**: All Arabic grade symbols and semester labels are normalized to the
  correct English values with zero normalization errors across all sample files.
- **SC-003**: Transcripts with format variations (different layouts, spacing, column
  order) are parsed successfully for 100% of the provided sample files, with no
  missing mandatory fields in the output.
- **SC-004**: Invalid or non-transcript file uploads produce a user-facing error
  message within 5 seconds, with no application crash or silent failure.
- **SC-005**: A valid transcript is fully parsed and structured output is ready for
  downstream processing within 30 seconds of upload submission.
- **SC-006**: The structured output for every successfully parsed transcript is
  accepted without schema validation errors by the downstream storage layer.
- **SC-007**: Zero student IDs or enrollment IDs are sourced from PDF content;
  all IDs in the output are confirmed as system-generated.
- **SC-008**: No extracted student data persists beyond the end of the session in
  which it was uploaded, confirmed by post-session storage inspection.
- **SC-009**: When a transcript is partially parsed (one or more semester sections fail),
  the system produces a warning message identifying each failed section by academic year
  and semester type, with no silent omission of data.

## Clarifications

### Session 2026-04-09

- Q: When a grade field contains an unrecognized symbol not in the grade map, what should the system do? → A: Store the grade as `"Unknown"`, attach a field-level warning to that course record, and continue parsing.
- Q: If one or more semester sections fail to parse but the header and other semesters are readable, what should the system do? → A: Return the successfully parsed data with a warning listing which semester(s) could not be extracted; allow the student to proceed.
- Q: Should the system enforce a maximum file size for uploaded PDFs? → A: No file size limit is enforced by this feature.
- Q: What is the maximum acceptable time for a successful transcript parse? → A: 30 seconds.

## Assumptions

- Transcripts are issued by Ain Shams University Faculty of Science and follow the
  Arabic format described in this specification. Transcripts from other institutions
  are out of scope.
- The `sample_academic_records/` directory contains representative samples covering
  all known format variations; parser validation is performed against these files.
- `academic_config.json` (at `docs/rules/academic_config.json`) is the single
  authoritative source for grade mappings, semester label mappings, level
  classification thresholds, and output schema field definitions.
- Course names are NOT extracted or processed in this feature; they will be handled
  in a separate downstream module.
- Credit hours per course are not directly listed in the transcript and are therefore
  not extracted here; they are resolved downstream from the course catalog by course code.
- One student uploads one transcript per session; batch or multi-file upload is out
  of scope for this feature.
- No file size limit is enforced by this feature; file size constraints, if any, are
  delegated to the hosting platform or web server configuration.
- The `Program` field may not always be present in the transcript header; if absent,
  it is stored as "Statistics&Computer Science" and does not block the parsing process.
- The system operates as part of a web application where session lifecycle is managed
  by the platform; session-end data deletion is enforced at the application layer.