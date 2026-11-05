"""Plain-language additions to flags: limitation text (T1) and "why" sentences (T2).

Deterministic and catalogue-driven (packages/rules/catalogue). No model, no clock, no network.
"""

from typing import Any

from satya_affidavit.catalogue import limitation as catalogue_limitation
from satya_affidavit.catalogue import why_text
from satya_affidavit.rules import load_ruleset as load_m5
from satya_forensics.rules import load_ruleset as load_m6


def rule_of(rule_id: str) -> Any | None:
    """The current rule (M5 or M6) for an id, else None."""
    for ruleset in (load_m5(), load_m6()):
        if rule_id in ruleset.rules:
            return ruleset.rules[rule_id]
    return None


def limitation_for(flag: dict[str, Any], locale: str = "en") -> dict[str, str] | None:
    """`{key, text}` of the flag's rule limitation, else None."""
    rule = rule_of(str(flag.get("rule_id")))
    return catalogue_limitation(getattr(rule, "limitation_key", None), locale) if rule else None


def rule_detail(rule_id: str, locale: str = "en") -> dict[str, Any] | None:
    rule = rule_of(rule_id)
    if rule is None:
        return None
    return {
        "rule_id": rule.rule_id,
        "rule_version": rule.version,
        "aph_clause": rule.aph_clause,
        "aph_edition": rule.aph_edition,
        "severity": rule.severity,
        "label": rule.label,
        "preliminary_indicator": rule.preliminary_indicator,
        "limitation_key": rule.limitation_key,
        "limitation": catalogue_limitation(rule.limitation_key, locale),
        "advisory": True,
    }


UNIT_LABELS = {"acre": "acres", "m2": "square metres"}
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}
MAX_WHY_SUMMARY = 3


def fmt_value(value: Any, unit: str | None = None) -> str:
    """A flag value as plain text: two decimals for measured values, short, never empty."""
    if value is None:
        return "nothing"
    if isinstance(value, float):
        return f"{value:.2f}" if unit else f"{value:g}"
    text = str(value)
    return text if len(text) <= 60 else text[:57] + "..."


def why_params(flag: dict[str, Any]) -> dict[str, str]:
    """Placeholder values for a flag's why template, from the flag's own fields only."""
    unit = flag.get("value_unit")
    params = {
        "extracted": fmt_value(flag.get("extracted_value"), unit),
        "expected": fmt_value(flag.get("expected_value"), unit),
        "unit_label": UNIT_LABELS.get(str(unit), str(unit or "")),
        "doc_title": str(flag.get("doc_title") or "the document"),
        "page": str(flag.get("page") or "?"),
        "clause": str(flag.get("aph_clause") or ""),
    }
    for key, value in (flag.get("why_extra") or {}).items():
        params[str(key)] = str(value)
    return params


def _first_sentence(text: str) -> str:
    head = text.strip().split(". ")[0].rstrip(".")
    return head


def generic_why(flag: dict[str, Any]) -> str:
    """Fallback built from the rule title and clause (never empty)."""
    rule = rule_of(str(flag.get("rule_id")))
    title = _first_sentence(getattr(rule, "description", "")) if rule else ""
    clause = flag.get("aph_clause") or (rule.aph_clause if rule else "")
    if title:
        return f"{title} (APH clause {clause})." if clause else f"{title}."
    return (
        f"A check against APH clause {clause} found a difference to review."
        if clause
        else ("A check found a difference to review.")
    )


def why_detail(flag: dict[str, Any], locale: str = "en") -> dict[str, Any]:
    """`{key, params, text}`: one plain sentence, from the catalogue or the generic fallback."""
    params = why_params(flag)
    found = why_text(str(flag.get("rule_id")), params, locale)
    if found is None:
        return {"key": "why.generic", "params": params, "text": generic_why(flag)}
    key, text = found
    return {"key": key, "params": params, "text": text}


def why_summary(flags: list[dict[str, Any]], locale: str = "en") -> list[str]:
    """Up to three distinct sentences for a case, most severe flags first."""
    ordered = sorted(
        flags,
        key=lambda f: (
            SEVERITY_ORDER.get(str(f.get("severity")), 3),
            str(f.get("rule_id")),
            str(f.get("flag_id")),
        ),
    )
    out: list[str] = []
    for flag in ordered:
        text = (flag.get("why_detail") or why_detail(flag, locale))["text"]
        if text not in out:
            out.append(text)
        if len(out) == MAX_WHY_SUMMARY:
            break
    return out
