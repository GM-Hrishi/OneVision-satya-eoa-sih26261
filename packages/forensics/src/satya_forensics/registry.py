"""Register of filings M6 compares reuse against: e-stamp certificate numbers and UDINs.

Within the prototype the register is the synthetic corpus: earlier filings
(data/synthetic/registry/prior-filings.json) plus the other current cases the gateway holds. A
number found under another application or year is a reuse finding; the same filing seen again is
not.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _norm(value: str) -> str:
    return "".join(value.split()).upper()


@dataclass(frozen=True)
class Filing:
    application_id: str | None
    permanent_id: str | None
    year: str  # AY for stamps, FY for UDINs


@dataclass
class Registry:
    stamps: dict[str, list[Filing]] = field(default_factory=dict)
    udins: dict[str, list[Filing]] = field(default_factory=dict)

    def add_stamp(self, number: str, application_id: str | None, ay: str) -> None:
        self.stamps.setdefault(_norm(number), []).append(Filing(application_id, None, ay))

    def add_udin(self, udin: str, permanent_id: str | None, fy: str) -> None:
        self.udins.setdefault(_norm(udin), []).append(Filing(None, permanent_id, fy))

    def stamp_reused(self, number: str, application_id: str, ay: str) -> list[Filing]:
        """Other filings with this certificate number (not this application in this AY)."""
        return [
            f
            for f in self.stamps.get(_norm(number), [])
            if not (f.application_id == application_id and f.year == ay)
        ]

    def udin_reused(self, udin: str, permanent_id: str, fy: str) -> list[Filing]:
        return [
            f
            for f in self.udins.get(_norm(udin), [])
            if not (f.permanent_id == permanent_id and f.year == fy)
        ]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Registry":
        reg = cls()
        for s in data.get("stamps", []):
            reg.add_stamp(s["certificate_no"], s.get("application_id"), s["ay"])
        for u in data.get("udins", []):
            reg.add_udin(u["udin"], u.get("permanent_id"), u["fy"])
        return reg

    @classmethod
    def from_file(cls, path: Path | None) -> "Registry":
        if path is None or not path.is_file():
            return cls()
        loaded: dict[str, Any] = json.loads(path.read_text("utf-8"))
        return cls.from_json(loaded)
