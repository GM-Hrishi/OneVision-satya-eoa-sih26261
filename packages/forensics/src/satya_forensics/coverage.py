"""Certificate coverage of the submission date (T5).

Pure date arithmetic over the validity a certificate prints. Settings live in
packages/rules/coverage.yaml. The statuses map to the existing labels: `expired_before_submission`
is `expired`; the other outcomes that need a person are `manual_review_required`; nothing new is
added. The result is an advisory indicator: a renewed certificate that was not uploaded would look
the same.
"""

from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

import yaml

from satya_affidavit.paths import rules_dir

COVERS = "covers"
EXPIRED = "expired_before_submission"
NOT_YET = "not_yet_valid"
UNKNOWN = "validity_unknown"

# status -> (rule id, outcome label, reason code)
OUTCOMES = {
    COVERS: (None, "verified", "CERT_COVERS_SUBMISSION"),
    EXPIRED: ("CERT-COVERAGE-EXPIRED", "expired", "CERT_EXPIRED_BEFORE_SUBMISSION"),
    NOT_YET: ("CERT-COVERAGE-NOT-YET", "manual_review_required", "CERT_NOT_YET_VALID"),
    UNKNOWN: ("CERT-COVERAGE-UNKNOWN", "manual_review_required", "CERT_VALIDITY_UNKNOWN"),
}


@dataclass(frozen=True)
class CoverageConfig:
    time_bound_types: tuple[str, ...]
    session_enabled: bool = False
    session_start: tuple[int, int] = (7, 1)
    session_end: tuple[int, int] = (6, 30)


def _month_day(text: str) -> tuple[int, int]:
    month, day = text.split("-")
    return int(month), int(day)


def load_config_file(path: Path) -> CoverageConfig:
    raw = yaml.safe_load(path.read_text("utf-8"))
    window = raw.get("session_window") or {}
    return CoverageConfig(
        time_bound_types=tuple(raw["time_bound_types"]),
        session_enabled=bool(window.get("enabled", False)),
        session_start=_month_day(str(window.get("start", "07-01"))),
        session_end=_month_day(str(window.get("end", "06-30"))),
    )


@cache
def load_config() -> CoverageConfig:
    return load_config_file(rules_dir() / "coverage.yaml")


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def certificate_coverage(
    valid_from: date | None, valid_to: date | None, submitted_on: date
) -> dict[str, Any]:
    """`{status, valid_from, valid_to, days_off}`; both ends of the validity are inclusive.

    `days_off`: days the validity ended before the submission date (`expired_before_submission`),
    days it starts after it (`not_yet_valid`), 0 when it covers, None when unknown.
    """
    out: dict[str, Any] = {"valid_from": _iso(valid_from), "valid_to": _iso(valid_to)}
    if valid_from and valid_to and valid_from > valid_to:
        return {**out, "status": UNKNOWN, "days_off": None}  # the printed dates contradict
    if valid_from and valid_from > submitted_on:
        return {**out, "status": NOT_YET, "days_off": (valid_from - submitted_on).days}
    if valid_to is None:
        return {**out, "status": UNKNOWN, "days_off": None}
    if valid_to < submitted_on:
        return {**out, "status": EXPIRED, "days_off": (submitted_on - valid_to).days}
    return {**out, "status": COVERS, "days_off": 0}


def session_end_of(ay: str, config: CoverageConfig) -> date:
    """Last day of the academic year `YYYY-YY`, from the configured month and day."""
    start_year = int(ay[:4])
    month, day = config.session_end
    return date(start_year + 1, month, day)


def session_coverage(
    valid_to: date | None, ay: str, config: CoverageConfig | None = None
) -> dict[str, Any] | None:
    """Whether the validity reaches the end of the session; None while the option is off."""
    config = config or load_config()
    if not config.session_enabled:
        return None
    end = session_end_of(ay, config)
    if valid_to is None:
        return {"status": UNKNOWN, "session_end": end.isoformat(), "days_short": None}
    short = (end - valid_to).days
    return {
        "status": "covers_session" if short <= 0 else "ends_before_session_end",
        "session_end": end.isoformat(),
        "days_short": max(short, 0),
    }


def is_time_bound(doc_type: str | None, config: CoverageConfig | None = None) -> bool:
    return doc_type in (config or load_config()).time_bound_types


def coverage_check(coverage: dict[str, Any], basis: str = "printed") -> dict[str, Any]:
    """A Check (kind `expiry`) for a coverage result, with an existing label as its outcome."""
    _, outcome, reason = OUTCOMES[coverage["status"]]
    check: dict[str, Any] = {
        "kind": "expiry",
        "outcome": outcome,
        "reason_code": reason,
        "basis": basis,
        "coverage": coverage,
    }
    for key in ("valid_from", "valid_to"):
        if coverage.get(key):
            check[key] = coverage[key]
    return check


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def printed_validity(checks: list[dict[str, Any]]) -> tuple[date | None, date | None]:
    """Validity dates from the document's own `expiry` check, when it has one."""
    for check in checks:
        if check.get("kind") == "expiry" and "coverage" not in check:
            return _date(check.get("valid_from")), _date(check.get("valid_to"))
    return None, None


def coverage_outcome(
    checks: list[dict[str, Any]],
    submitted_on: date,
    ay: str,
    factory: Any,
    config: CoverageConfig | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """(the coverage Check, the flags it raises) for one time-bound certificate.

    `factory` is a satya_forensics.flags.FlagFactory. A covering certificate raises no flag. Each
    flag carries `why_extra` with the dates its plain sentence needs; the API strips it.
    """
    config = config or load_config()
    valid_from, valid_to = printed_validity(checks)
    coverage = certificate_coverage(valid_from, valid_to, submitted_on)
    session = session_coverage(valid_to, ay, config) if coverage["status"] == COVERS else None
    if session:
        coverage["session"] = session
    check = coverage_check(coverage)
    submitted = submitted_on.isoformat()
    extra = {
        "valid_from": coverage["valid_from"] or "not printed",
        "valid_to": coverage["valid_to"] or "not printed",
        "days_off": coverage["days_off"] if coverage["days_off"] is not None else "unknown",
        "submitted": submitted,
    }
    flags: list[dict[str, Any]] = []
    rule_id = OUTCOMES[coverage["status"]][0]
    if rule_id:
        flags.append(
            _flag(factory, rule_id, "coverage", coverage["valid_to"], submitted, "submission date")
            | {"why_extra": extra}
        )
    elif session and session["status"] == "ends_before_session_end":
        flags.append(
            _flag(
                factory,
                "CERT-SESSION-GAP",
                "session",
                coverage["valid_to"],
                session["session_end"],
                "end of the academic session",
            )
            | {"why_extra": {**extra, "session_end": session["session_end"]}}
        )
    return check, flags


def _flag(
    factory: Any, rule_id: str, key: str, extracted: str | None, expected: str, label: str
) -> dict[str, Any]:
    flag: dict[str, Any] = factory.make(
        rule_id,
        key,
        page=None,
        regions=[],
        extracted=extracted,
        expected=expected,
        expected_label=label,
        confidence=0.9,
    )
    return flag
