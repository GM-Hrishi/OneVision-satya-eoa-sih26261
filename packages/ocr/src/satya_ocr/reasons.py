"""Reason codes and the fixed "why" sentences (no model; templates only).

Codes follow the repository convention (UPPER_SNAKE, module prefix as in SIG_IMAGE_ONLY) [ASSUMED:
the names are those of the slice prompt]. Each sentence has an i18n key `ocr.why.<variant>` in the
workbench messages (English complete, Hindi present and marked for review).
"""

SCAN_IMAGE_ONLY = "SCAN_IMAGE_ONLY"
OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
OCR_UNAVAILABLE = "OCR_UNAVAILABLE"
DOC_UNREADABLE = "DOC_UNREADABLE"

REASON_CODES = (SCAN_IMAGE_ONLY, OCR_LOW_CONFIDENCE, OCR_UNAVAILABLE, DOC_UNREADABLE)

# variant -> (reason code, sentence). Placeholders: {pages} {confidence} {threshold} {limit}
WHY: dict[str, tuple[str, str]] = {
    "scan_read": (
        SCAN_IMAGE_ONLY,
        "This file is a scan. {pages} read by OCR (confidence {confidence}%). "
        "A scan carries no digital signature, so an official must verify it.",
    ),
    "scan_not_attempted": (
        SCAN_IMAGE_ONLY,
        "This file is a scan and was not read by OCR. An official must read it.",
    ),
    "scan_timeout": (
        SCAN_IMAGE_ONLY,
        "This file is a scan and OCR did not finish in the time allowed. An official must read it.",
    ),
    "low_confidence": (
        OCR_LOW_CONFIDENCE,
        "This file is a scan and the text read by OCR is not reliable "
        "(confidence {confidence}%, needs {threshold}%). An official must read it.",
    ),
    "unavailable": (
        OCR_UNAVAILABLE,
        "This file is a scan and the OCR engine is not available on this system. "
        "An official must read it.",
    ),
    "encrypted": (
        DOC_UNREADABLE,
        "This file is password protected and cannot be opened. "
        "Ask the institution for an unprotected copy.",
    ),
    "corrupt": (
        DOC_UNREADABLE,
        "This file is damaged and cannot be opened. Ask the institution to upload it again.",
    ),
    "no_pages": (DOC_UNREADABLE, "This file has no pages. Ask the institution to upload it again."),
    "blank": (
        DOC_UNREADABLE,
        "Every page of this file is blank. Ask the institution to upload it again.",
    ),
    "too_large": (
        DOC_UNREADABLE,
        "This file is too large to read automatically ({limit}). An official must read it.",
    ),
}


def reason_for(variant: str) -> str:
    return WHY[variant][0]


def why_sentence(variant: str, **values: object) -> str:
    return WHY[variant][1].format(**values)
