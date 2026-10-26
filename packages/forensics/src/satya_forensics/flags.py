"""Build `Flag` objects (Portal spec §2.6.4) for M6 findings.

Same shape as the M5 flags: rule ID + version, APH clause + edition, page and regions of the
evidence, extracted and expected values with their sources, confidence, `disposition: null` (an
official decides, guard rail 1) and a deterministic ID per document and finding.
"""

from dataclasses import dataclass
from typing import Any

from satya_affidavit.ids import stable_id
from satya_forensics.rules import Ruleset


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
    doc_label: str

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
    ) -> dict[str, Any]:
        rule = self.ruleset[rule_id]
        check_ref = f"m6:{rule_id}:{key}"
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
            "delta": None,
            "extracted_source": {"doc_label": self.doc_label, "page": page, "row": None},
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
