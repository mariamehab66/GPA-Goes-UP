# Implementation Plan: PDF Upload and Arabic Transcript Parsing

**Branch**: `001-pdf-transcript-parsing` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pdf-transcript-parsing/spec.md`

## Summary

Parse Arabic-language PDF academic transcripts uploaded by students, extracting
structured student-level data and a complete semester-by-semester course enrollment
history. All Arabic content (grade symbols, semester labels) is normalized to English
equivalents using mappings from `academic_config.json`. Course names are mapped to
English via the course catalog (`data/database/courses.csv`). The output conforms
to the `Student` and `Enrollment` table schemas and is stored session-scoped, ready
for downstream rule-engine and ML processing. The parser must be robust to format
variations across real transcripts and handle partial parse failures gracefully.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pdfplumber (PDF text extraction), arabic-reshaper + python-bidi (Arabic text normalization), fuzzywuzzy or rapidfuzz (approximate course name matching), Flask or FastAPI (web endpoint), SQLAlchemy (ORM/session management)
**Storage**: MySQL (existing schema — `Student`, `Enrollment`, `Course`, `Prerequisite` tables); session-scoped only for this feature
**Testing**: pytest with sample PDFs from `data/sample_academic_record/`
**Target Platform**: Web service (backend module, Linux/Windows compatible)
**Project Type**: web-service — backend parsing module
**Performance Goals**: Full transcript parsed and output ready within 30 seconds of upload; error responses within 5 seconds
**Constraints**: Session-scoped storage (auto-delete on session end); no file size limit enforced at feature level; single file per session; no batch upload
**Scale/Scope**: One student per session; validates against `data/sample_academic_record/` samples

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applicability | Gate Status | Notes |
|-----------|--------------|-------------|-------|
| I. Academic Rules Supremacy | Partial | ✅ PASS | This feature is pre-rule-engine input. Output feeds the rule engine; accuracy of extraction directly enables rule enforcement downstream. |
| II. Rule Engine Before ML | Indirect | ✅ PASS | Parser output is the upstream data source for both rule engine and ML. No ML involvement in this feature. No violation possible. |
| III. Data Integrity & Accuracy | **Direct** | ✅ PASS | Grade symbols (غ → Abs) MUST be correctly normalized before storage (FR-007). Course name mapping uses catalog as source of truth (FR-008). GPA values extracted as-is from transcript, not recalculated here. Schema conformance enforced (FR-013, FR-015). |
| IV. Transparent AI Assistance | N/A | — | No AI/chatbot component in this feature. |
| V. Realistic Behavioral Modeling | N/A | — | No data generation in this feature. |
| Development Workflow | **Direct** | ✅ PASS | Constitution requires: "PDF extraction MUST correctly map all grade symbols and MUST be validated against real transcript samples before integration." Addressed by FR-007, FR-014, SC-001–SC-003, and validation against `data/sample_academic_record/`. |

**Constitution Check: PASSED.** No violations. Proceed to Phase 0.

*Post-Phase 1 re-check*: Confirmed — data model and contracts enforce schema integrity
(Principle III). Grade normalization is a required step in the parsing pipeline before
any record reaches storage. No new violations introduced by design.

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-transcript-parsing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── parse-transcript.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── parsing/
│   │   ├── pdf_extractor.py        # Raw text extraction from Arabic PDF
│   │   ├── transcript_parser.py    # Structure detection (header, semesters, courses)
│   │   ├── normalizer.py           # Grade + semester label normalization
│   │   ├── course_name_mapper.py   # Arabic → English course name mapping
│   │   └── validator.py            # Output schema validation + missing-field errors
│   ├── models/
│   │   ├── student_record.py       # StudentRecord dataclass
│   │   ├── semester_block.py       # SemesterBlock dataclass
│   │   ├── course_record.py        # CourseRecord dataclass
│   │   └── parse_result.py         # ParseResult (StudentRecord + [CourseRecord])
│   ├── api/
│   │   └── upload.py               # POST /upload-transcript endpoint
│   └── session/
│       └── session_store.py        # Session-scoped storage + auto-delete
└── tests/
    ├── integration/
    │   ├── test_parse_valid_transcripts.py   # Against all sample PDFs
    │   └── test_parse_format_variations.py   # Format robustness tests
    └── unit/
        ├── test_normalizer.py
        ├── test_course_name_mapper.py
        └── test_validator.py
```

**Structure Decision**: Web application backend module. Python backend with a dedicated
`parsing/` package — cleanly separates extraction, normalization, mapping, and
validation responsibilities. Source at `backend/src/`, tests at `backend/tests/`.
Frontend upload UI is out of scope for this feature spec.

## Complexity Tracking

> No Constitution Check violations. Table not applicable.
