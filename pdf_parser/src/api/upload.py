"""
upload.py — POST /upload-transcript endpoint.
Accepts a multipart PDF file, parses it, saves the result, and returns JSON.

T028/T030: Strict MIME + magic-byte validation. Full structured error mapping.
T031: Session cleanup on error if save() was partially invoked.
"""
import dataclasses
import logging
import uuid

from flask import Blueprint, g, jsonify, request

from ..exceptions import (
    InvalidFileTypeError,
    MissingRequiredFieldsError,
    PDFUnreadableError,
    TranscriptNotRecognizedError,
)
from ..parsing.pipeline import TranscriptParser
from ..session.session_store import SessionStore

log = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)

_PDF_MAGIC = b"%PDF"


@upload_bp.post("/upload-transcript")
def upload_transcript():
    """
    POST /upload-transcript

    Multipart form field: `file` (PDF)

    Success response (200):
    {
      "status": "ok",
      "is_partial": false,
      "warnings": [...],
      "student": { ... },
      "enrollments": [ { ... }, ... ]
    }

    Error responses:
      400 — InvalidFileTypeError (wrong file type)
      422 — PDFUnreadableError | TranscriptNotRecognizedError | MissingRequiredFieldsError
    """
    if "file" not in request.files:
        return jsonify({"status": "error", "error_code": "MISSING_FILE",
                        "message": "No file field in request."}), 400

    uploaded = request.files["file"]

    # T028: MIME type check
    mime = (uploaded.content_type or "").lower()
    if mime and mime != "application/pdf" and not mime.startswith("application/octet"):
        return _error_response(InvalidFileTypeError(), 400)

    pdf_bytes = uploaded.read()

    # T028: Magic-byte check — catches mis-labelled non-PDFs
    if not pdf_bytes or not pdf_bytes.lstrip().startswith(_PDF_MAGIC):
        return _error_response(InvalidFileTypeError(), 400)

    session_id = str(uuid.uuid4())
    db_session = _get_db_session()
    save_attempted = False

    try:
        result = TranscriptParser().parse(pdf_bytes)
    except InvalidFileTypeError as exc:
        return _error_response(exc, 400)
    except (PDFUnreadableError, TranscriptNotRecognizedError, MissingRequiredFieldsError) as exc:
        return _error_response(exc, 422)

    # T031: Wrap DB save in its own try/except so we can clean up on failure
    if db_session is not None:
        store = SessionStore()
        try:
            save_attempted = True
            student_id, _ = store.save(session_id, result, db_session)
            g.setdefault("session_ids", []).append(session_id)
        except Exception as exc:
            # T031: rollback any partial rows already written
            if save_attempted:
                try:
                    store.cleanup(session_id, db_session)
                except Exception:
                    pass  # best-effort cleanup; don't mask original error
            log.exception("DB save failed for session %s", session_id)
            return jsonify({
                "status": "error",
                "error_code": "STORAGE_ERROR",
                "message": "Parsed successfully but could not save to database.",
            }), 500

    warnings_payload = [
        {
            "level": w.level,
            "location": w.location,
            "message": w.message,
            "raw_value": w.raw_value,
        }
        for w in result.warnings
    ]

    return jsonify({
        "status": "ok",
        "is_partial": result.is_partial,
        "warnings": warnings_payload,
        "student": dataclasses.asdict(result.student),
        "enrollments": [dataclasses.asdict(e) for e in result.enrollments],
    }), 200


def _error_response(exc: Exception, http_status: int):
    error_code = getattr(exc, "error_code", "UNKNOWN_ERROR")
    payload = {"status": "error", "error_code": error_code, "message": str(exc)}
    # T030: include missing_fields list for MissingRequiredFieldsError
    if isinstance(exc, MissingRequiredFieldsError):
        payload["missing_fields"] = exc.missing_fields
    return jsonify(payload), http_status


def _get_db_session():
    """Return SQLAlchemy session from Flask g, or None if not configured."""
    return getattr(g, "db_session", None)
