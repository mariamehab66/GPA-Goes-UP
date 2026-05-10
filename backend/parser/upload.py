import os
import uuid
import logging

from flask import Blueprint, request, jsonify, current_app
from pdf_parsing.transcript_parser import parse_transcript
from pdf_parsing.insert_data import insert_student, insert_courses
from pdf_parsing.db_connection import get_connection

log = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)

_PDF_MAGIC = b"%PDF"
_MAX_SIZE  = 16 * 1024 * 1024  # 16MB — must match app.config


@upload_bp.route("/upload-transcript", methods=["POST"])
def upload_transcript():

    # ── 1. File presence ──────────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files["file"]

    # ── 2. Filename extension ─────────────────────────────────────────────────
    if not uploaded.filename or \
       not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only .pdf files are accepted"}), 400

    # ── 3. Read and validate bytes ────────────────────────────────────────────
    pdf_bytes = uploaded.read()

    if not pdf_bytes:
        return jsonify({"error": "Uploaded file is empty"}), 400

    if len(pdf_bytes) > _MAX_SIZE:
        return jsonify({"error": "File exceeds 16MB limit"}), 413

    if pdf_bytes[:10].lstrip()[:4] != _PDF_MAGIC:
        return jsonify({"error": "File does not appear to be a valid PDF"}), 400

    # ── 4. Save temporarily ───────────────────────────────────────────────────
    file_path = None
    try:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        filename      = f"upload_{uuid.uuid4()}.pdf"
        file_path     = os.path.join(upload_folder, filename)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        # ── 5. Parse ──────────────────────────────────────────────────────────
        data = parse_transcript(file_path)

        # ── 6. Delete file immediately after parsing ──────────────────────────
        os.remove(file_path)
        file_path = None  # prevent finally from attempting it again

        if not isinstance(data, dict) or \
           not {"student", "courses"}.issubset(data):
            log.error("parse_transcript returned unexpected structure")
            return jsonify({"error": "Transcript parsing returned incomplete data"}), 422

        if not data["courses"]:
            return jsonify({"error": "No courses could be extracted"}), 422

        # ── 7. Insert into DB ─────────────────────────────────────────────────
        conn = get_connection()
        try:
            student_id = insert_student(data["student"], conn)
            insert_courses(data["courses"], student_id, conn)
            conn.commit()
            log.info(
                "Inserted student_id=%s with %d courses",
                student_id, len(data["courses"])
            )
        except Exception:
            conn.rollback()
            log.exception("DB insert failed")
            return jsonify({"error": "Database error during insert"}), 500
        finally:
            conn.close()

        # ── 8. Response ───────────────────────────────────────────────────────
        return jsonify({
            "status":           "ok",
            "courses_inserted": len(data["courses"])
        }), 200

    except Exception:
        log.exception("Unhandled error in upload_transcript")
        return jsonify({"error": "Failed to process transcript"}), 500

    finally:
        # Safety net only — file_path is None on the happy path
        # because step 6 already deleted it and reset it to None.
        # This only fires if parse_transcript raised before deletion.
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            log.debug("Temp file deleted in finally: %s", file_path)