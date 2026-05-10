import logging
import pdfplumber

log = logging.getLogger(__name__)


class PDFReadError(Exception):
    """Raised when a PDF cannot be opened or yields no readable text."""


class PDFEncryptedError(PDFReadError):
    """Raised when a PDF is password-protected."""


def extract_text_from_pdf(pdf_path: str) -> str:
    pages_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            log.info("Opened PDF: %s (%d pages)", pdf_path, total_pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                # Do NOT use layout=True — this PDF uses embedded custom
                # fonts that produce cid codes with layout=True
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"--- PAGE {page_num} ---\n{text.strip()}")
                else:
                    log.warning("Page %d/%d yielded no text", page_num, total_pages)

    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise PDFEncryptedError(
                f"PDF is password-protected: {pdf_path}"
            ) from e
        raise PDFReadError(f"Unexpected error reading PDF: {pdf_path}") from e

    if not pages_text:
        raise PDFReadError(
            "PDF contains no readable text. "
            "It may be scanned and require OCR."
        )

    full_text = "\n\n".join(pages_text)
    log.info(
        "Extracted text from %d/%d pages (%d chars total)",
        len(pages_text), total_pages, len(full_text),
    )
    return full_text
