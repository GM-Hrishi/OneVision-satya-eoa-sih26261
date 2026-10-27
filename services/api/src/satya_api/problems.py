"""RFC 9457 problem responses with the codes in Portal spec §2.13. No stack traces leave the API."""

from typing import Any

from fastapi.responses import JSONResponse

PROBLEM_TYPE = "urn:satya:problem:"

TITLES = {
    "VALIDATION_FAILED": "The request body failed validation.",
    "UNSUPPORTED_EVENT_TYPE": "This event type is not accepted here.",
    "SCHEMA_VERSION_UNSUPPORTED": "This event spec version is not supported.",
    "UNSUPPORTED_AY": "This academic year is not supported.",
    "SIGNATURE_INVALID": "The event signature is missing or invalid.",
    "SIGNATURE_EXPIRED": "The event signature timestamp is outside the allowed window.",
    "PERSONAL_DATA_REJECTED": "The request contains a field that must not be sent.",
    "AUTH_REQUIRED": "Sign-in is required.",
    "INVALID_TOKEN": "The access token is missing, expired or invalid.",
    "SCOPE_DENIED": "Not assigned to you.",
    "NOT_FOUND": "Not found.",
    "METHOD_NOT_ALLOWED": "Method not allowed.",
    "PAYLOAD_TOO_LARGE": "The request body is larger than allowed.",
    "UNSUPPORTED_MEDIA_TYPE": "The request body must be application/json.",
    "RATE_LIMITED": "Too many requests.",
    "UPLOAD_NAME_REJECTED": "The file name must end in .pdf and use plain characters.",
    "UPLOAD_SIZE_REJECTED": "The file is empty or larger than 5 MB.",
    "UPLOAD_CONTENT_REJECTED": "The file content is not a PDF.",
    "UPLOAD_SLOT_REJECTED": "Choose the affidavit or the audited accounts slot.",
    "UPLOAD_UNREADABLE": "The PDF could not be read. It was not stored.",
    "UPLOAD_NOT_CONFIGURED": "Uploads are not enabled on this server.",
    "DISPOSITION_ACTION_REJECTED": "Choose one of the five dispositions.",
    "DISPOSITION_REASON_REJECTED": "A reason of at least 10 characters is required.",
    "FLAG_NOT_FOUND": "That finding is not on this case.",
    "DEGRADED": "The service is degraded.",
    "INTERNAL_ERROR": "Something went wrong. The error has been logged.",
}


class ProblemError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        detail: str | None = None,
        errors: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.detail = detail
        self.errors = errors or []
        self.headers = headers or {}


def problem_body(
    status: int,
    code: str,
    trace_id: str,
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": PROBLEM_TYPE + code.lower(),
        "title": TITLES.get(code, "Error."),
        "status": status,
        "code": code,
        "trace_id": trace_id,
    }
    if detail:
        body["detail"] = detail
    if errors:
        body["errors"] = errors
    return body


def problem_response(
    status: int,
    code: str,
    trace_id: str,
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        problem_body(status, code, trace_id, detail, errors),
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
    )
