"""Build `Flag` objects (Portal spec §2.6.4) for M5 findings.

Every flag carries the rule ID + version, APH clause + edition, the page and regions of the
evidence, the extracted and expected values with their sources, a confidence, and
`disposition: null`: an official records the decision (guard rail 1). IDs are deterministic per
document and finding.
"""

from dataclasses import dataclass
from typing import Any

from satya_affidavit.ids import stable_id
from satya_affidavit.rules import Rule, Ruleset

DOC_LABEL = "Affidavit 2 (sworn copy)"
TEXT_LAYER_CONFIDENCE = 0.98


def confidence_band(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"


@dataclass
class FlagFactory:
    ruleset: Ruleset
    doc_id: str
    doc_sha256: str

    def make(
        self,
        rule_id: str,
        key: str,
        *,
        page: int | None,
        regions: list[dict[str, float]],
        extracted: Any,
        expected: Any,
        expected_label: str,
        confidence: float,
        unit: str | None = None,
        delta: float | None = None,
        row: str | None = None,
    ) -> dict[str, Any]:
        rule: Rule = self.ruleset[rule_id]
        check_ref = f"m5:{rule_id}:{key}"
        confidence = round(min(max(confidence, 0.0), 1.0), 3)
        return {
            "flag_id": stable_id("flg", self.doc_sha256, check_ref, rule.version),
            "doc_id": self.doc_id,
            "page": page,
            "regions": regions,
            "rule_id": rule.rule_id,
            "rule_version": rule.version,
            "rule_text_key": rule.text_key,
            "aph_clause": rule.aph_clause,
            "aph_edition": rule.aph_edition,
            "extracted_value": extracted,
            "expected_value": expected,
            "value_unit": unit,
            "delta": None if delta is None else round(delta, 4),
            "extracted_source": {"doc_label": DOC_LABEL, "page": page, "row": row},
            "expected_source": {"label": expected_label},
            "confidence": confidence,
            "confidence_band": confidence_band(confidence),
            "label": rule.label,
            "provenance": "satya",
            "preliminary_indicator": rule.preliminary_indicator,
            "severity": rule.severity,
            "disposition": None,
            "check_ref": check_ref,
            "stage": "2",
            "institution_visible": rule.institution_visible,
            "evidence_sha256": self.doc_sha256,
        }
