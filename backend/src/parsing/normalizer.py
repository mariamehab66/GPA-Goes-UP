"""
normalizer.py — Grade and semester label normalization.
All normalization reads from config.py constants; no hard-coded values here.

T025/T026: arabic-reshaper + python-bidi are applied before matching so that
visual-order Arabic characters extracted from PDFs match the logical-order
reference values in academic_config.json and SEMESTER_LABEL_MAP.
"""
import arabic_reshaper
from bidi.algorithm import get_display

from ..config import GRADE_MAP, SEMESTER_LABEL_MAP
from ..models.parse_warning import ParseWarning


def _to_logical(text: str) -> str:
    """Convert visually-ordered Arabic PDF text to logical order for matching."""
    return get_display(arabic_reshaper.reshape(text))


def normalize_grade(raw: str, location: str) -> tuple[str, list[ParseWarning]]:
    """
    Normalize a raw grade string to a canonical grade symbol.

    T025: Applies arabic-reshaper + bidi before lookup so that the Arabic
    absent character غ (which may be extracted in visual order) maps correctly.

    Returns (normalized_grade, warnings).
    - Known grade or Arabic alias → canonical symbol (e.g. "A+", "Abs").
    - Unrecognized value → "Unknown" with a field-level warning.
    """
    warnings: list[ParseWarning] = []
    stripped = raw.strip() if raw else ""

    # Direct match (covers ASCII grade symbols)
    if stripped in GRADE_MAP:
        return GRADE_MAP[stripped]["grade"], warnings

    # Arabic reshaping pass (handles visually-ordered Arabic characters)
    logical = _to_logical(stripped)
    if logical in GRADE_MAP:
        return GRADE_MAP[logical]["grade"], warnings

    # Unrecognized
    warnings.append(ParseWarning(
        level="field",
        location=location,
        message="Unrecognized grade symbol; stored as 'Unknown'.",
        raw_value=stripped,
    ))
    return "Unknown", warnings


def normalize_semester_label(raw: str) -> str | None:
    """
    Map an Arabic semester label to its English equivalent.

    T026: Applies arabic-reshaper + bidi before matching; also tries partial
    (substring) match to handle labels with embedded year strings or extra chars.

    Returns "Fall", "Spring", or "Summer", or None if not recognized.
    """
    stripped = raw.strip()

    # Direct exact match
    if stripped in SEMESTER_LABEL_MAP:
        return SEMESTER_LABEL_MAP[stripped]

    # Direct substring match
    for arabic_key, english_val in SEMESTER_LABEL_MAP.items():
        if arabic_key in stripped:
            return english_val

    # Reshaping pass for visually-ordered Arabic from PDF
    logical = _to_logical(stripped)
    if logical in SEMESTER_LABEL_MAP:
        return SEMESTER_LABEL_MAP[logical]

    # Substring match on reshaped text
    for arabic_key, english_val in SEMESTER_LABEL_MAP.items():
        if arabic_key in logical:
            return english_val

    return None
