# Research: PDF Upload and Arabic Transcript Parsing

**Branch**: `001-pdf-transcript-parsing` | **Date**: 2026-04-09

## Decision Log

---

### 1. PDF Text Extraction Library

**Decision**: Use `pdfplumber`

**Rationale**: pdfplumber provides character-level and table-level extraction with
precise bounding-box information — critical for detecting tabular course rows even
when column alignment varies across transcript formats. It handles both text-based
and semi-structured PDFs reliably on Windows and Linux. It is pure Python with no
external binary dependencies, which simplifies deployment.

**Alternatives considered**:
- `PyMuPDF (fitz)`: Faster, lower-level; table extraction requires manual coordinate
  math. Better suited for image-heavy PDFs. Not needed here.
- `pdfminer.six`: Lower-level than pdfplumber; pdfplumber wraps it with a friendlier API.
- `camelot`: Excellent for lattice/stream tables but requires Ghostscript installation;
  adds deployment complexity with no benefit over pdfplumber for this use case.

---

### 2. Arabic Text Handling

**Decision**: Use `arabic-reshaper` + `python-bidi` for display normalization;
use standard Unicode string comparison for matching.

**Rationale**: Arabic text extracted from PDFs is often stored in visual (right-to-left)
order rather than logical order, causing string comparisons to fail. `arabic-reshaper`
reconstructs the logical character sequence; `python-bidi` handles bidirectional
display. Together they ensure extracted Arabic strings (semester labels, grade symbols,
course names) are comparable to the reference values in `academic_config.json` and
the course catalog.

**Alternatives considered**:
- CAMeL Tools (Arabic NLP): Full NLP toolkit — overkill for label/symbol normalization.
- Manual regex patterns: Brittle across different PDF encodings; not maintainable.

---

### 3. Course Name Mapping (Arabic → English)

**Decision**: Two-pass lookup against `data/database/courses.csv`:
  1. Exact match on extracted Arabic course name (after reshaping/normalization)
  2. If no exact match: fuzzy match using `rapidfuzz` (token_sort_ratio ≥ 85 threshold)
     to handle minor OCR errors, spacing differences, or encoding artifacts

**Rationale**: The course catalog (`courses.csv`) contains English course names keyed
by course code. Since `course_code` is always present in the transcript and is the
primary key in the catalog, the preferred mapping path is:
  **course_code → English name lookup** (direct, reliable, no fuzzy matching needed).
Arabic course name fuzzy matching is the fallback only when a course code is
unrecognized or missing from the catalog.

The `rapidfuzz` library is a Cython-accelerated replacement for `fuzzywuzzy` with
identical API, no GPL dependency, and significantly better performance.

**Alternatives considered**:
- Translation API (e.g., Google Translate): Requires internet, adds latency and cost,
  produces non-deterministic results that may not match official course names.
- Manual mapping dictionary: Already exists implicitly in `courses.csv`; no duplication needed.

---

### 4. Transcript Structure Detection Strategy

**Decision**: Section-based parsing with Arabic keyword anchors

**Rationale**: Real Ain Shams University transcripts follow a consistent structural
pattern despite surface formatting variation:
  1. **Header section**: Student info block at the top (CGPA, earned hours, program)
  2. **Semester sections**: Each begins with an Arabic semester label + academic year
  3. **Course table**: Rows of course code, name, grade, GPA within each semester
  4. **Semester GPA line**: Appears at the end of each semester block

Parsing strategy:
- Identify semester boundary anchors using a whitelist of known Arabic semester label
  patterns from `academic_config.json`
- Extract the academic year via regex on the line containing the semester label
- Within each semester block, identify course rows by the presence of a valid course
  code pattern (e.g., `[A-Z]{2,5} \d{3}`)
- Extract semester GPA from the terminal line of each block

**Alternatives considered**:
- Table-based extraction only: Fails when course data is not in strict grid layout.
- ML-based layout parsing: Disproportionate complexity for a well-structured domain.

---

### 5. Partial Parse Failure Handling

**Decision**: Best-effort parsing with per-semester error accumulation

**Rationale**: If a semester block cannot be parsed (garbled layout, missing anchor,
unexpected encoding), the parser:
  1. Logs the failed block with its detected academic year and semester type (if partially
     identifiable) or by its position in the document
  2. Continues to the next semester anchor
  3. Returns successfully parsed blocks + a `warnings` list in `ParseResult`

This matches FR-019 and SC-008. A `ParseResult` is always returned; it is never
replaced by an exception unless the header itself is unreadable (which triggers FR-017).

---

### 6. Unrecognized Grade Symbol Handling

**Decision**: Store as `"Unknown"` with field-level warning (per clarification Q1)

**Rationale**: Allows the parse to complete. The `"Unknown"` sentinel is detectable
downstream by the rule engine, which can flag the enrollment as requiring manual
review rather than blindly computing GPA with a zero or wrong value.

---

### 7. Session-Scoped Storage

**Decision**: Store parsed data in server-side session (Flask session / database rows
tagged with session ID), with cleanup triggered on session end or timeout.

**Rationale**: `academic_config.json` specifies `session_based_storage: true` and
`auto_delete_on_session_end: true`. The parsed `StudentRecord` and `CourseRecord`
entries are inserted into the `Student` and `Enrollment` tables with the session ID
as a foreign key or tag, then deleted on session teardown.

**Alternatives considered**:
- In-memory only (no DB write): Prevents downstream rule engine from querying records
  via SQL — not viable given the existing SQL-based schema.
- Permanent storage: Contradicts privacy policy in `academic_config.json`.

---

### 8. ID Generation

**Decision**: Auto-increment integer IDs (consistent with existing `Student.ID INT PRIMARY KEY` schema)

**Rationale**: The existing SQL schema uses `INT PRIMARY KEY` for both `Student.ID`
and `Enrollment.Enrollment_ID`. Auto-increment is the natural fit. UUIDs would require
schema changes. IDs are never extracted from the PDF (FR-011, FR-012).

---

## Resolved NEEDS CLARIFICATION Items

All Technical Context items were resolvable from project artifacts:

| Item | Resolution |
|------|-----------|
| Language/Version | Python 3.11 — standard for ML + web projects of this type |
| Primary Dependencies | pdfplumber, arabic-reshaper, python-bidi, rapidfuzz, Flask/FastAPI, SQLAlchemy |
| Storage | MySQL — confirmed from `data/database/database_codeCreation.sql` |
| Testing | pytest — standard Python testing; integration tests against sample PDFs |
| Target Platform | Web service backend — confirmed from README and system design |
| Performance Goals | 30s parse (SC-009), 5s error (SC-004) — confirmed from spec clarifications |
| Sample PDF location | `data/sample_academic_record/` (academic_record1.pdf, academic_record2.pdf) |
| Course catalog location | `data/database/courses.csv` — code, type, credits, is_elective, is_practical, name |