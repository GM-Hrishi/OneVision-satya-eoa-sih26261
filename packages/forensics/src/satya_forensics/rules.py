"""Versioned M6 rules (packages/rules/m6-signatures.yaml). Every flag and check cites rule_id,
rule_version, APH clause and edition from here (guard rail 6)."""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from satya_affidavit.paths import rules_dir

RULESET_FILE = "m6-signatures.yaml"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    version: str
    text_key: str
    aph_clause: str
    aph_edition: str
    check_kind: str
    reason_code: str
    pass_code: str
    severity: str
    label: str
    alert_type: str
    alert_subtype: str
    institution_visible: bool
    preliminary_indicator: bool
    retries: int = 0
    other_codes: tuple[tuple[str, str], ...] = ()
    max_year_gap: int = 0

    def code(self, name: str) -> str:
        return dict(self.other_codes)[name]


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

    def by_reason(self, reason_code: str) -> Rule:
        return next(r for r in self.rules.values() if r.reason_code == reason_code)


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
            check_kind=r["check_kind"],
            reason_code=r["reason_code"],
            pass_code=r["pass_code"],
            severity=r["severity"],
            label=r["label"],
            alert_type=r["alert"]["type"],
            alert_subtype=r["alert"]["subtype"],
            institution_visible=bool(r["institution_visible"]),
            preliminary_indicator=bool(r["preliminary_indicator"]),
            retries=int(r.get("retries", 0)),
            other_codes=tuple(sorted((r.get("other_codes") or {}).items())),
            max_year_gap=int(r.get("max_year_gap", 0)),
        )
        for r in raw["rules"]
    }
    return Ruleset(name=raw["ruleset"], version=str(raw["version"]), rules=rules)
