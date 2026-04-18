"""
pipeline.py — TranscriptParser orchestrates the full PDF → ParseResult pipeline.

Strategy (T027):
  1. Primary: positional word extraction (extract_page_rows) + positional parsing.
     Handles CID-encoded Arabic fonts where extract_text() returns garbage.
  2. Fallback: text-based extraction (extract_with_fallback) + regex parsing.
     For PDFs where Arabic text IS Unicode-decodable.

T032: Structured logging — parse start, completion, and exceptions with error_code.
T034: 30-second timeout guard on the full parse() call.
"""
import logging
import signal
import time

from ..exceptions import MissingRequiredFieldsError, PDFUnreadableError, TranscriptNotRecognizedError
from ..models.course_record import CourseRecord
from ..models.parse_result import ParseResult
from ..models.parse_warning import ParseWarning
from .normalizer import normalize_grade, normalize_semester_label
from .pdf_extractor import extract_page_rows, extract_with_fallback
from .transcript_parser import (
    detect_semester_blocks,
    detect_semester_blocks_from_rows,
    extract_admission_year,
    parse_header,
    parse_header_from_rows,
)
from .validator import validate_student_record

log = logging.getLogger(__name__)

_PARSE_TIMEOUT_SECONDS = 30


class TranscriptParser:
    """
    Entry point for the transcript parsing pipeline.
    Call `parse(pdf_bytes)` to get a `ParseResult`.
    """

    def parse(self, pdf_bytes: bytes, session_id: str = "") -> ParseResult:
        """
        Full pipeline: bytes → ParseResult.

        T032: Logs parse start (session_id, file size), completion (duration_ms,
              enrollment_count, warning_count, is_partial), and each raised exception.
        T034: Raises PDFUnreadableError if the parse exceeds 30 seconds.

        Raises:
            InvalidFileTypeError: Non-PDF bytes.
            PDFUnreadableError: PDF unreadable or parse exceeded timeout.
            TranscriptNotRecognizedError: No semester data found by either method.
            MissingRequiredFieldsError: Required header fields absent.
        """
        file_size = len(pdf_bytes) if pdf_bytes else 0
        log.info(
            "parse.start session_id=%s file_size_bytes=%d",
            session_id or "<none>",
            file_size,
        )
        t0 = time.monotonic()

        try:
            result = self._parse_with_timeout(pdf_bytes)
        except Exception as exc:
            error_code = getattr(exc, "error_code", type(exc).__name__)
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            log.warning(
                "parse.error session_id=%s error_code=%s elapsed_ms=%d msg=%s",
                session_id or "<none>",
                error_code,
                elapsed_ms,
                str(exc),
            )
            raise

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "parse.complete session_id=%s duration_ms=%d enrollments=%d warnings=%d is_partial=%s",
            session_id or "<none>",
            elapsed_ms,
            len(result.enrollments),
            len(result.warnings),
            result.is_partial,
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_with_timeout(self, pdf_bytes: bytes) -> ParseResult:
        """
        T034: Run _do_parse() with a 30-second wall-clock timeout.
        Uses SIGALRM on Unix; falls back to no timeout on Windows.
        """
        if hasattr(signal, "SIGALRM"):
            def _timeout_handler(signum, frame):
                raise PDFUnreadableError("Parse exceeded time limit of 30 seconds.")

            old = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(_PARSE_TIMEOUT_SECONDS)
            try:
                return self._do_parse(pdf_bytes)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        else:
            # Windows: no SIGALRM — rely on pdfplumber's own timeouts
            return self._do_parse(pdf_bytes)

    def _do_parse(self, pdf_bytes: bytes) -> ParseResult:
        """Core parsing logic, extracted for timeout wrapping."""
        # --- Attempt 1: Positional word extraction (CID-font PDFs) ---
        page_rows = extract_page_rows(pdf_bytes)
        semester_blocks = detect_semester_blocks_from_rows(page_rows)
        header_data = parse_header_from_rows(page_rows)

        # --- Attempt 2: Text-based fallback (Unicode PDFs) ---
        if not semester_blocks:
            pages_text = extract_with_fallback(pdf_bytes)
            header_text_data = parse_header(pages_text)
            semester_blocks = detect_semester_blocks(pages_text)
            for key in ("cgpa", "earned_hours", "program"):
                if header_data.get(key) is None:
                    header_data[key] = header_text_data.get(key)

        if not semester_blocks:
            raise TranscriptNotRecognizedError()

        warnings: list[ParseWarning] = []
        enrollments: list[CourseRecord] = []
        is_partial = False

        for block in semester_blocks:
            if block.parse_failed:
                is_partial = True
                warnings.append(ParseWarning(
                    level="section",
                    location=f"Semester: {block.semester_type} {block.academic_year}",
                    message="Semester block could not be fully parsed; skipped.",
                ))
                continue

            year_start = int(block.academic_year.split("-")[0]) if block.academic_year else 0
            semester_label = normalize_semester_label(block.semester_type) or block.semester_type

            for raw_course in block.courses:
                location = f"Course: {raw_course['course_code']}, field: grade"
                norm_grade, grade_warnings = normalize_grade(raw_course["raw_grade"], location)
                warnings.extend(grade_warnings)

                enrollments.append(CourseRecord(
                    course_code=raw_course["course_code"],
                    course_grade=norm_grade,
                    course_gpa=raw_course.get("course_gpa"),
                    year=year_start,
                    semester=semester_label,
                ))

        last_valid = next(
            (b for b in reversed(semester_blocks) if not b.parse_failed and b.semester_gpa is not None),
            None,
        )
        if last_valid:
            header_data["last_semester_gpa"] = last_valid.semester_gpa

        header_data["admission_year"] = extract_admission_year(semester_blocks)

        student = validate_student_record(header_data)

        return ParseResult(
            student=student,
            enrollments=enrollments,
            warnings=warnings,
            is_partial=is_partial,
        )
