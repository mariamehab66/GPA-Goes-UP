"""
pdf_extractor.py — Low-level PDF text extraction using pdfplumber.
Accepts raw PDF bytes and returns a list of per-page text strings.
"""
import io

import pdfplumber

from ..exceptions import InvalidFileTypeError, PDFUnreadableError

_PDF_MAGIC = b"%PDF"


def extract_text(pdf_bytes: bytes) -> list[str]:
    """
    Extract text from a PDF given as raw bytes.

    Returns a list where each element is the text of one page (may be empty
    string for blank pages).

    Raises:
        InvalidFileTypeError: If the bytes do not start with the PDF magic header.
        PDFUnreadableError: If pdfplumber cannot open the file, or if every page
                            yields empty text (scanned/image-only PDF).
    """
    if not pdf_bytes or not pdf_bytes.lstrip().startswith(_PDF_MAGIC):
        raise InvalidFileTypeError()

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        raise PDFUnreadableError() from exc

    if all(t.strip() == "" for t in pages_text):
        raise PDFUnreadableError(
            "File appears to be blank or contains no extractable text."
        )

    return pages_text


def extract_with_fallback(pdf_bytes: bytes) -> list[str]:
    """
    Extract text with a per-page fallback strategy for robustness (T022/US2).

    For each page:
      1. Try pdfplumber table extraction — join cell values as whitespace-separated text.
      2. If table extraction yields no content, fall back to raw text extraction.

    This handles mixed-layout transcripts where some pages use embedded tables
    and others use plain text flow.

    Raises the same exceptions as extract_text().
    """
    if not pdf_bytes or not pdf_bytes.lstrip().startswith(_PDF_MAGIC):
        raise InvalidFileTypeError()

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text: list[str] = []
            for page in pdf.pages:
                # Attempt table-based extraction first
                table_text = _extract_page_via_table(page)
                if table_text.strip():
                    pages_text.append(table_text)
                else:
                    pages_text.append(page.extract_text() or "")
    except Exception as exc:
        raise PDFUnreadableError() from exc

    if all(t.strip() == "" for t in pages_text):
        raise PDFUnreadableError(
            "File appears to be blank or contains no extractable text."
        )

    return pages_text


def extract_page_rows(pdf_bytes: bytes) -> list[list[list[str]]]:
    """
    Positional word extraction for CID-font PDFs (T027 format fix).

    Returns pages → rows → tokens, where:
      - Each row is words on approximately the same horizontal line, sorted left→right.
      - CID-encoded tokens ((cid:NNNN)) are kept but flagged; callers may filter them.

    This preserves the spatial grouping needed for column-based field identification
    when Arabic characters are not Unicode-decodable.

    Raises:
        InvalidFileTypeError: Non-PDF bytes.
        PDFUnreadableError: Cannot open PDF.
    """
    if not pdf_bytes or not pdf_bytes.lstrip().startswith(_PDF_MAGIC):
        raise InvalidFileTypeError()

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            all_pages: list[list[list[str]]] = []
            for page in pdf.pages:
                words = page.extract_words(x_tolerance=4, y_tolerance=4)
                # Group words into rows by snapped y-coordinate
                rows_dict: dict[int, list[tuple[float, str]]] = {}
                for w in words:
                    row_key = round(w["top"] / 5) * 5
                    rows_dict.setdefault(row_key, []).append((w["x0"], w["text"]))
                # Sort rows top→bottom, tokens left→right within each row
                page_rows = [
                    [text for _, text in sorted(tokens)]
                    for _, tokens in sorted(rows_dict.items())
                ]
                all_pages.append(page_rows)
    except Exception as exc:
        raise PDFUnreadableError() from exc

    return all_pages


def _extract_page_via_table(page) -> str:
    """Join all table cell values from a pdfplumber page into a single string."""
    tables = page.extract_tables() or []
    rows: list[str] = []
    for table in tables:
        for row in table:
            if row:
                rows.append(" ".join(cell or "" for cell in row))
    return "\n".join(rows)
