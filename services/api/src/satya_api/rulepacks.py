"""Rule packs for replay (P-11): the current M5 + M6 rule files and archived earlier ones.

A pack id names both rule files: `m5-affidavit@<version>+m6-signatures@<version>`. The current pack
is built from packages/rules. Archived packs live in `<archive>/<pack id>/` with the two files under
their usual names. The allow-list is the current id plus the directory names found in the archive,
so a client can never make the service open a path of its choosing.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from satya_affidavit.paths import rules_dir
from satya_affidavit.rules import RULESET_FILE as M5_FILE
from satya_affidavit.rules import Ruleset as M5Ruleset
from satya_affidavit.rules import load_ruleset as load_m5
from satya_affidavit.rules import load_ruleset_file as load_m5_file
from satya_forensics.rules import RULESET_FILE as M6_FILE
from satya_forensics.rules import Ruleset as M6Ruleset
from satya_forensics.rules import load_ruleset as load_m6
from satya_forensics.rules import load_ruleset_file as load_m6_file

PACK_ID = re.compile(r"^m5-affidavit@[0-9A-Za-z.]{1,20}\+m6-signatures@[0-9A-Za-z.]{1,20}$")
UNKNOWN = "unknown"


@dataclass(frozen=True)
class RulePack:
    pack_id: str
    m5: M5Ruleset
    m6: M6Ruleset


def pack_id_of(m5: M5Ruleset, m6: M6Ruleset) -> str:
    return f"{m5.ref}+{m6.ref}"


def current_pack() -> RulePack:
    m5, m6 = load_m5(), load_m6()
    return RulePack(pack_id_of(m5, m6), m5, m6)


class RulePackCatalog:
    def __init__(self, archive: Path | None = None) -> None:
        self.archive = archive if archive is not None else rules_dir() / "archive"

    def available(self) -> list[str]:
        ids = [current_pack().pack_id]
        if self.archive.is_dir():
            ids += sorted(
                p.name
                for p in self.archive.iterdir()
                if p.is_dir() and PACK_ID.fullmatch(p.name) and p.name != ids[0]
            )
        return ids

    def resolve(self, pack_id: str) -> RulePack | None:
        """The pack for an allow-listed id, else None (also None when its files do not parse)."""
        if pack_id not in self.available():
            return None
        current = current_pack()
        if pack_id == current.pack_id:
            return current
        folder = self.archive / pack_id
        try:
            m5, m6 = load_m5_file(folder / M5_FILE), load_m6_file(folder / M6_FILE)
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if pack_id_of(m5, m6) != pack_id:
            return None
        return RulePack(pack_id, m5, m6)
