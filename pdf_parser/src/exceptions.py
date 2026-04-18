"""
exceptions.py — Custom exceptions for the transcript parsing pipeline.
"""


class InvalidFileTypeError(Exception):
    """Raised when the uploaded file is not a valid PDF."""

    def __init__(self, message: str = "Only PDF files are accepted. Please upload a PDF version of your academic transcript."):
        super().__init__(message)
        self.error_code = "INVALID_FILE_TYPE"


class PDFUnreadableError(Exception):
    """Raised when a PDF exists but text cannot be extracted (blank, corrupted, or parse timeout)."""

    def __init__(self, message: str = "The uploaded file could not be read. It may be corrupted or password-protected."):
        super().__init__(message)
        self.error_code = "PDF_UNREADABLE"


class TranscriptNotRecognizedError(Exception):
    """Raised when no transcript structure (semester anchors) is found in the PDF."""

    def __init__(self, message: str = "The uploaded PDF does not appear to be an academic transcript. Please verify the file and try again."):
        super().__init__(message)
        self.error_code = "TRANSCRIPT_NOT_RECOGNIZED"


class MissingRequiredFieldsError(Exception):
    """Raised when one or more mandatory student-level fields cannot be extracted."""

    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        self.error_code = "MISSING_REQUIRED_FIELDS"
        super().__init__(
            f"Required student information could not be extracted from the transcript header. "
            f"Missing fields: {', '.join(missing_fields)}"
        )
