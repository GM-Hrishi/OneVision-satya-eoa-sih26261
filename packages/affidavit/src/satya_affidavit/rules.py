"""Versioned M5 rules (packages/rules/m5-affidavit.yaml). Every flag cites rule_id, rule_version,
APH clause and edition from here (guard rail 6)."""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from satya_affidavit.paths import rules_dir

RULESET_FILE = "m5-affidavit.yaml"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    version: str
    text_key: str
    aph_clause: str
    aph_edition: str
    severity: str
    label: str
    alert_type: str
    alert_subtype: str
    institution_visible: bool
    preliminary_indicator: bool
    tolerance: float = 0.0


@dataclass(frozen=True)
class Ruleset:
    name: str
    version: str
    rules: dict[str, Rule]

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.version}"

    def __getitem__(self, rule_id: str) -> Rule:
        return self.rules[rule_id]


@cache
def load_ruleset() -> Ruleset:
    return load_ruleset_file(rules_dir() / RULESET_FILE)


def load_ruleset_file(path: Path) -> Ruleset:
    """Parse one rule file; replay (P-11) uses it for archived rule packs."""
    raw = yaml.safe_load(path.read_text("utf-8"))
    edition = str(raw["aph_edition"])
    rules = {
        r["rule_id"]: Rule(
            rule_id=r["rule_id"],
            version=str(r["version"]),
            text_key=r["text_key"],
            aph_clause=r["aph_clause"],
            aph_edition=edition,
            severity=r["severity"],
            label=r["label"],
            alert_type=r["alert"]["type"],
            alert_subtype=r["alert"]["subtype"],
            institution_visible=bool(r["institution_visible"]),
            preliminary_indicator=bool(r["preliminary_indicator"]),
            tolerance=float(r.get("tolerance", 0.0)),
        )
        for r in raw["rules"]
    }
    return Ruleset(name=raw["ruleset"], version=str(raw["version"]), rules=rules)
