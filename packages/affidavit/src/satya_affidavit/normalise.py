"""Text normalisation for the clause diff (design C3, D4).

Re-typeset sworn copies differ from the portal draft in ways that are not changes: whitespace and
line breaks, hyphen-wrapped words, struck-through option choices, letter case of names, and the date
order of the template year. Everything here is applied identically to the expected and the sworn
side.
"""

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date

_DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"), "-")
_QUOTES = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:)])")
_SPACE_AFTER_OPEN = re.compile(r"([(])\s+")
_WORD_EDGE_PUNCT = ".,;:()\"'"


def clean(text: str) -> str:
    """NFKC, ASCII dashes and quotes, single spaces, no space before punctuation."""
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).translate(_QUOTES)
    text = " ".join(text.split())
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    return _SPACE_AFTER_OPEN.sub(r"\1", text)


def squash(text: str) -> str:
    """Comparison key: cleaned, case-folded, every whitespace removed."""
    return "".join(clean(text).casefold().split())


def ay_long(ay: str) -> str:
    """'2026-27' -> '2026-2027' (the affidavit's AY line)."""
    start = int(ay[:4])
    return f"{start}-{start + 1}"


def ay_short(start: int, end: int) -> str | None:
    """(2026, 2027) -> '2026-27'; None when the years are not consecutive."""
    return f"{start}-{str(end)[2:]}" if end == start + 1 else None


def parse_number(text: str | None) -> float | None:
    if text is None:
        return None
    compact = clean(text).replace(",", "").replace(" ", "")
    try:
        return float(compact)
    except ValueError:
        return None


_DATE = re.compile(r"^\s*(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})\s*$")
_ISO = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def parse_date(text: str | None, order: str) -> tuple[date | None, bool]:
    """Parse a printed date in the template's order (design D4).

    Returns (date, fallback). An impossible month in the template order is retried in the other
    order and reported as a fallback; anything else unparseable is (None, False).
    """
    if not text:
        return None, False
    iso = _ISO.match(text)
    if iso:
        try:
            return date(int(iso[1]), int(iso[2]), int(iso[3])), False
        except ValueError:
            return None, False
    match = _DATE.match(clean(text))
    if not match:
        return None, False
    first, second, year = int(match[1]), int(match[2]), int(match[3])
    month, day = (first, second) if order == "MM/DD/YYYY" else (second, first)
    try:
        return date(year, month, day), False
    except ValueError:
        pass
    try:
        return date(year, day, month), True
    except ValueError:
        return None, False


def format_date(value: date, order: str) -> str:
    if order == "MM/DD/YYYY":
        return f"{value.month:02d}/{value.day:02d}/{value.year}"
    return f"{value.day:02d}/{value.month:02d}/{value.year}"


@dataclass(frozen=True)
class OptionGroup:
    name: str
    choices: tuple[str, ...]

    def pattern(self) -> re.Pattern[str]:
        """Any surviving subset of the choices, in any order, with leftover slashes."""
        alt = "|".join(re.escape(c) for c in sorted(self.choices, key=len, reverse=True))
        return re.compile(
            rf"(?<![\w])(?:/\s*)?(?:{alt})(?:\s*/\s*(?:{alt}))*(?:\s*/)?(?![\w])",
            re.IGNORECASE,
        )


OPTION_MARKUP = re.compile(r"\[\[(\w+):\s*([^\]]+)\]\]")


def option_token(name: str) -> str:
    return f"<opt:{name}>"


def resolve_options(text: str, groups: Iterable[OptionGroup]) -> tuple[str, dict[str, list[str]]]:
    """Replace each option group's surviving choices with a token; report what survived.

    The sworn copy keeps only the choice(s) the deponent did not strike through (struck characters
    are dropped at extraction). The expected side uses the same token, so a valid choice is not a
    change.
    """
    selected: dict[str, list[str]] = {}
    for group in groups:
        found: list[str] = []

        def repl(match: re.Match[str], group: OptionGroup = group, found: list[str] = found) -> str:
            span = match.group(0).casefold()
            for choice in group.choices:
                word = rf"(?<![\w]){re.escape(choice.casefold())}(?![\w])"
                if re.search(word, span) and choice not in found:
                    found.append(choice)
            return f" {option_token(group.name)} "

        text = group.pattern().sub(repl, text, count=1)
        selected[group.name] = found
    return clean(text), selected


def entity_substitute(text: str, entities: Mapping[str, str]) -> str:
    """Replace known names and IDs (institute, trust, AID, PID, AY) with tokens, ignoring case."""
    for name, value in sorted(entities.items(), key=lambda kv: len(kv[1]), reverse=True):
        if not value.strip():
            continue
        words = [re.escape(w) for w in clean(value).split()]
        pattern = re.compile(r"\s*".join(words), re.IGNORECASE)
        text = pattern.sub(f"<{name}>", text)
    return text


def canonical(
    text: str,
    entities: Mapping[str, str],
    groups: Iterable[OptionGroup] = (),
) -> tuple[str, dict[str, list[str]]]:
    """Cleaned, names substituted, options resolved, case-folded, single-spaced."""
    text = entity_substitute(clean(text), entities)
    text, selected = resolve_options(text, groups)
    return clean(text).casefold(), selected


def words_of(text: str) -> list[str]:
    return [
        w.strip(_WORD_EDGE_PUNCT).casefold()
        for w in clean(text).split()
        if w.strip(_WORD_EDGE_PUNCT)
    ]


def join_wrapped(previous: str, following: str, vocabulary: set[str]) -> tuple[str, bool]:
    """Join two text lines, re-joining a word hyphen-wrapped at the end of `previous`.

    "accor-" + "dance" -> "accordance"; "Self-" + "Financing" stays "Self-Financing" when the
    hyphenated form is in the vocabulary of the expected draft.
    Returns (joined, rejoined_without_hyphen).
    """
    previous = previous.rstrip()
    following = following.lstrip()
    if not previous:
        return following, False
    if not following:
        return previous, False
    if (
        previous.endswith("-")
        and len(previous) > 1
        and previous[-2].isalpha()
        and following[0].isalpha()
    ):
        left = previous[:-1].split()[-1] if previous[:-1].split() else ""
        right = following.split()[0]
        hyphenated = f"{left}-{right}".strip(_WORD_EDGE_PUNCT).casefold()
        if hyphenated in vocabulary:
            return previous + following, False
        return previous[:-1] + following, True
    return f"{previous} {following}", False
