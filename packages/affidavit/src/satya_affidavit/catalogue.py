"""Plain-language catalogue (packages/rules/catalogue/{en,hi}.yaml).

Limitation texts (`limitation.*`) and "why" templates (`why.<rule_id>`). Pure text lookup, no model.
Hindi entries carry `review: true`.
"""

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

from satya_affidavit.paths import rules_dir

LOCALES = ("en", "hi")
DEFAULT_LOCALE = "en"


@dataclass(frozen=True)
class Entry:
    text: str
    review: bool


@dataclass(frozen=True)
class Catalogue:
    locale: str
    limitation: dict[str, Entry]
    why: dict[str, Entry]


def _entries(raw: object) -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    for key, value in (raw or {}).items():  # type: ignore[attr-defined]
        if isinstance(value, dict):
            out[str(key)] = Entry(str(value["text"]), bool(value.get("review", False)))
        else:
            out[str(key)] = Entry(str(value), False)
    return out


def load_catalogue_file(path: Path) -> Catalogue:
    raw = yaml.safe_load(path.read_text("utf-8"))
    return Catalogue(
        locale=str(raw["locale"]),
        limitation=_entries(raw.get("limitation")),
        why=_entries(raw.get("why")),
    )


@cache
def load_catalogue(locale: str = DEFAULT_LOCALE) -> Catalogue:
    if locale not in LOCALES:
        locale = DEFAULT_LOCALE
    return load_catalogue_file(rules_dir() / "catalogue" / f"{locale}.yaml")


def limitation(key: str | None, locale: str = DEFAULT_LOCALE) -> dict[str, str] | None:
    """`{key, text}` for a limitation key, else None (also None for an unknown key)."""
    if not key:
        return None
    entry = load_catalogue(locale).limitation.get(key)
    if entry is None and locale != DEFAULT_LOCALE:
        entry = load_catalogue(DEFAULT_LOCALE).limitation.get(key)
    return None if entry is None else {"key": f"limitation.{key}", "text": entry.text}


class _Params(dict[str, str]):
    """Unknown placeholders stay readable instead of raising."""

    def __missing__(self, key: str) -> str:
        return "(not available)"


def why_text(
    rule_id: str, params: dict[str, str], locale: str = DEFAULT_LOCALE
) -> tuple[str, str] | None:
    """`(key, sentence)` from the `why.<rule_id>` template; None means the caller falls back."""
    entry = load_catalogue(locale).why.get(rule_id)
    if entry is None and locale != DEFAULT_LOCALE:
        entry = load_catalogue(DEFAULT_LOCALE).why.get(rule_id)
    if entry is None:
        return None
    return f"why.{rule_id}", entry.text.format_map(_Params(params)).replace("  ", " ")
