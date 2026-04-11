---
description: "Task list for PDF Upload and Arabic Transcript Parsing"
---

# Tasks: PDF Upload and Arabic Transcript Parsing

**Input**: Design documents from `specs/001-pdf-transcript-parsing/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Not requested in spec — test tasks are omitted from this list.

**Organization**: Tasks are grouped by user story to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in all descriptions

## Path Conventions

- Backend source: `backend/src/`
- Tests: `backend/tests/`
- Config: `docs/rules/academic_config.json`
- Sample PDFs: `data/sample_academic_record/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create backend directory structure: `backend/src/parsing/`, `backend/src/models/`, `backend/src/api/`, `backend/src/session/`, `backend/tests/integration/`, `backend/tests/unit/`
- [x] T002 Create `backend/requirements.txt` with pinned dependencies: pdfplumber, arabic-reshaper, python-bidi, Flask, SQLAlchemy, PyMySQL, pytest
- [x] T003 [P] Create `backend/src/__init__.py`, `backend/src/parsing/__init__.py`, `backend/src/models/__init__.py`, `backend/src/api/__init__.py`, `backend/src/session/__init__.py`
- [x] T004 [P] Create `backend/src/config.py` — load `docs/rules/academic_config.json` at startup; expose `GRADE_MAP`, `SEMESTER_LABEL_MAP`, `LEVEL_THRESHOLDS` as module-level constants
- [x] T005 [P] Create `backend/src/exceptions.py` — define `InvalidFileTypeError`, `PDFUnreadableError`, `TranscriptNotRecognizedError`, `MissingRequiredFieldsError` with descriptive messages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and normalization logic that every user story depends on

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete

- [x] T006 Create `backend/src/models/parse_warning.py` — `ParseWarning` dataclass with fields: `level` (str: "field"|"section"), `location` (str), `message` (str), `raw_value` (str|None)
- [x] T007 [P] Create `backend/src/models/student_record.py` — `StudentRecord` dataclass with fields: `cgpa` (float), `program` (str), `earned_hours` (int), `last_semester_gpa` (float), `level` (int), `admission_year` (int); `id` is NOT a field (assigned by DB)
- [x] T008 [P] Create `backend/src/models/course_record.py` — `CourseRecord` dataclass with fields: `course_code` (str), `course_grade` (str), `course_gpa` (float|None), `year` (int), `semester` (str); `enrollment_id` and `student_id` are NOT fields (assigned by DB)
- [x] T009 [P] Create `backend/src/models/semester_block.py` — `SemesterBlock` dataclass with fields: `semester_type` (str), `academic_year` (str), `semester_gpa` (float|None), `courses` (list[dict]), `parse_failed` (bool)
- [x] T010 [P] Create `backend/src/models/parse_result.py` — `ParseResult` dataclass with fields: `student` (StudentRecord), `enrollments` (list[CourseRecord]), `warnings` (list[ParseWarning]), `is_partial` (bool)
- [x] T011 Create `backend/src/parsing/normalizer.py` — implement `normalize_grade(raw: str) -> tuple[str, ParseWarning|None]` using `GRADE_MAP` from config; maps غ → Abs, returns ("Unknown", warning) for unrecognized values. Implement `normalize_semester_label(raw_arabic: str) -> str|None` using `SEMESTER_LABEL_MAP`; returns None if unrecognized
- [x] T012 Create `backend/src/parsing/validator.py` — implement `validate_student_record(student: StudentRecord) -> list[str]` returning list of missing mandatory field names; implement `derive_level(earned_hours: int) -> int` using `LEVEL_THRESHOLDS`; implement `validate_course_code(code: str) -> bool` using regex `^[A-Z]{2,5} \d{3}$`

**Checkpoint**: Foundation ready — all models, normalizer, and validator exist. User story work can now begin.

---

## Phase 3: User Story 1 — Upload Transcript and Receive Structured Academic Record (Priority: P1) 🎯 MVP

**Goal**: A student uploads a valid Arabic PDF and receives a complete, schema-conformant structured record of their academic history.

**Independent Test**: Upload `data/sample_academic_record/academic_record1.pdf` → verify the returned `ParseResult` has a populated `StudentRecord` (all mandatory fields present) and a non-empty `enrollments` list with all Arabic grades and semester labels correctly normalized to English.

### Implementation for User Story 1

- [x] T014 [P] [US1] Create `backend/src/parsing/pdf_extractor.py` — implement `extract_text(pdf_bytes: bytes) -> list[str]` using pdfplumber; open PDF from bytes, extract text page by page as list of strings; raise `PDFUnreadableError` if pdfplumber raises or returns empty; raise `InvalidFileTypeError` if input bytes are not a valid PDF (check PDF header `%PDF`)
- [x] T015 [P] [US1] Create `backend/src/parsing/transcript_parser.py` — implement `parse_header(pages_text: list[str]) -> dict` to extract CGPA, earned hours, program from the first page/block; use regex patterns for float (CGPA), int (earned hours), and string (program); return dict with keys matching `StudentRecord` fields
- [x] T016 [US1] Add `detect_semester_blocks(pages_text: list[str]) -> list[SemesterBlock]` to `backend/src/parsing/transcript_parser.py` — scan all pages for Arabic semester anchor patterns from `SEMESTER_LABEL_MAP`; extract academic year via regex `\d{4}-\d{4}` on the anchor line; group lines between anchors as one semester block; set `parse_failed=True` on blocks where anchor is found but course rows cannot be extracted
- [x] T017 [US1] Add `extract_courses_from_block(block_lines: list[str]) -> list[dict]` to `backend/src/parsing/transcript_parser.py` — within each semester block, identify course rows by presence of course code pattern `^[A-Z]{2,5} \d{3}`; extract course code, raw grade, and course GPA from each row (course name is intentionally NOT extracted); extract semester GPA from terminal line of block matching float pattern after a known Arabic GPA label
- [x] T018 [US1] Add `extract_admission_year(blocks: list[SemesterBlock]) -> int` to `backend/src/parsing/transcript_parser.py` — return the year portion of the first semester block's `academic_year` (e.g., 2022 from "2022-2023")
- [x] T019 [US1] Create `backend/src/parsing/pipeline.py` — implement `TranscriptParser.parse(pdf_bytes: bytes) -> ParseResult`; orchestrate the full pipeline: `extract_text` → `parse_header` → `detect_semester_blocks` → `extract_courses_from_block` → `normalize_grade` (per course) → `normalize_semester_label` (per block) → `derive_level` → `validate_student_record`; assemble `StudentRecord`, list of `CourseRecord`, list of `ParseWarning`, and `is_partial`; raise `TranscriptNotRecognizedError` if no semester anchors found; raise `MissingRequiredFieldsError` if `validate_student_record` returns non-empty list
- [x] T020 [US1] Create `backend/src/session/session_store.py` — implement `SessionStore.save(session_id: str, result: ParseResult, db_session) -> tuple[int, list[int]]` that inserts one `Student` row and N `Enrollment` rows (using auto-increment IDs, never from PDF) tagged with `session_id`; implement `SessionStore.cleanup(session_id: str, db_session)` that deletes all `Student` and `Enrollment` rows for that `session_id`
- [x] T021 [US1] Create `backend/src/api/upload.py` — implement `POST /upload-transcript` endpoint; accept multipart `file` field; validate MIME type is `application/pdf` (raise `InvalidFileTypeError` if not); pass bytes to `TranscriptParser.parse()`; on success call `SessionStore.save()` and return JSON response with `status`, `is_partial`, `warnings`, `student`, and `enrollments` fields per contract; on exception return appropriate HTTP status and `error_code` per contract (400 for `InvalidFileTypeError`, 422 for all others); enforce 5-second timeout for error responses; target full pipeline completion within 30 seconds

**Checkpoint**: US1 complete — upload a valid transcript and receive a full structured record. Validate against `data/sample_academic_record/academic_record1.pdf`.

---

## Phase 4: User Story 2 — Robust Handling of Format Variations (Priority: P2)

**Goal**: The parser correctly handles all real transcript layouts in `data/sample_academic_record/` without failing or producing incomplete records.

**Independent Test**: Upload `data/sample_academic_record/academic_record2.pdf` (different format) → verify no `MissingRequiredFieldsError` and all mandatory fields are populated. Run both sample PDFs through the parser and confirm zero missing mandatory fields in either output.

### Implementation for User Story 2

- [x] T022 [P] [US2] Update `backend/src/parsing/pdf_extractor.py` — add `extract_with_fallback(pdf_bytes: bytes) -> list[str]`: first attempt pdfplumber table extraction per page; if table extraction returns no rows for a page, fall back to raw text extraction for that page; ensures mixed table/text layout pages are all captured
- [x] T023 [P] [US2] Update `backend/src/parsing/transcript_parser.py` `parse_header()` — make header extraction tolerant of varying field label positions: try multiple regex patterns per field (e.g., CGPA may appear as "المعدل التراكمي" followed by float, or as a float next to a known label on any line in the first 30 lines); add `parse_failed` flag to header result if any mandatory field not found
- [x] T024 [US2] Update `backend/src/parsing/transcript_parser.py` `extract_courses_from_block()` — handle column reordering: instead of fixed column-index parsing, identify each field by its content type (course code by regex, grade by membership in known grade set, GPA by float range 0.0–4.0); strip excess whitespace and normalize unicode spacing characters before field extraction; any remaining text tokens are ignored
- [x] T025 [US2] Update `backend/src/parsing/normalizer.py` `normalize_grade()` — add pre-normalization step using `arabic_reshaper.reshape()` + `bidi.get_display()` on all extracted Arabic text before matching; ensures visual-order Arabic characters extracted from PDFs match logical-order reference values in `academic_config.json`
- [x] T026 [US2] Update `backend/src/parsing/normalizer.py` `normalize_semester_label()` — apply arabic-reshaper + python-bidi before label matching; add partial-match fallback: if full label not found in `SEMESTER_LABEL_MAP`, try matching any key as a substring of the extracted label (handles extra trailing spaces or embedded year strings)
- [x] T027 [US2] Run both sample PDFs through the full pipeline manually (or via a quick script) and fix any parsing failures discovered in `backend/src/parsing/` modules; document any format-specific adjustments in comments

**Checkpoint**: US2 complete — both sample PDFs parse successfully with no missing mandatory fields. Robustness validated across known format variants.

---

## Phase 5: User Story 3 — Rejection and Clear Feedback for Invalid Inputs (Priority: P3)

**Goal**: Non-PDF files, blank PDFs, and unrelated PDFs all produce specific user-facing error messages within 5 seconds. No crash or silent failure.

**Independent Test**: Submit a `.docx` file, a blank PDF, and an unrelated PDF to `POST /upload-transcript`; verify each returns the correct HTTP status and `error_code` within 5 seconds.

### Implementation for User Story 3

- [x] T028 [P] [US3] Update `backend/src/api/upload.py` — add pre-parse MIME type validation before passing bytes to parser: check `file.content_type == "application/pdf"` and also verify PDF magic bytes (`%PDF` header in first 4 bytes); return `400 + INVALID_FILE_TYPE` immediately if either check fails (no timeout needed — returns in <1s)
- [x] T029 [P] [US3] Update `backend/src/parsing/pdf_extractor.py` `extract_text()` — add explicit check for empty extraction result (all pages return empty string after stripping whitespace); raise `PDFUnreadableError` with message "File appears to be blank or contains no extractable text"
- [x] T030 [US3] Update `backend/src/api/upload.py` — add structured exception handler mapping: `InvalidFileTypeError` → HTTP 400 + `INVALID_FILE_TYPE`; `PDFUnreadableError` → HTTP 422 + `PDF_UNREADABLE`; `TranscriptNotRecognizedError` → HTTP 422 + `TRANSCRIPT_NOT_RECOGNIZED`; `MissingRequiredFieldsError` → HTTP 422 + `MISSING_REQUIRED_FIELDS` (include `missing_fields` list in response); all error responses return within 5 seconds