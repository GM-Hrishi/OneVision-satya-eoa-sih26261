"""Clause-level diff of the sworn declarations against the portal draft (design C3 step 2).

Declarations are aligned by content, not by number, so a dropped declaration (with the rest
renumbered) shows as one removal instead of a cascade of changes. Two declarations are equal when
their canonical forms match: whitespace, hyphen wraps, dashes and letter case ignored, names and IDs
substituted, and strike-through option groups resolved (any valid choice is not a change).
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from satya_affidavit.normalise import OPTION_MARKUP, canonical, clean, entity_substitute, squash
from satya_affidavit.parse import SwornDeclaration
from satya_affidavit.template import DraftDeclaration

MATCH_THRESHOLD = 0.45  # below this two declarations are unrelated (removed + added)


@dataclass
class Span:
    kind: str  # equal | insert | delete
    text: str


@dataclass
class DeclMatch:
    expected: DraftDeclaration | None
    sworn: SwornDeclaration | None
    similarity: float
    op: str  # equal | changed | removed | added
    spans: list[Span] = field(default_factory=list)
    selected: dict[str, list[str]] = field(default_factory=dict)
    expected_view: str = ""
    flag_id: str | None = None


def _loose(text: str, entities: dict[str, str]) -> list[str]:
    return clean(entity_substitute(clean(text), entities)).casefold().split()


def _similarity(a: list[str], b: list[str]) -> float:
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _align(sim: list[list[float]]) -> list[tuple[int | None, int | None]]:
    """Order-preserving alignment maximising total similarity (Needleman-Wunsch, zero gap cost)."""
    n, m = len(sim), len(sim[0]) if sim else 0
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = max(score[i - 1][j], score[i][j - 1])
            if sim[i - 1][j - 1] >= MATCH_THRESHOLD:
                best = max(best, score[i - 1][j - 1] + sim[i - 1][j - 1])
            score[i][j] = best
    pairs: list[tuple[int | None, int | None]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and sim[i - 1][j - 1] >= MATCH_THRESHOLD
            and abs(score[i][j] - (score[i - 1][j - 1] + sim[i - 1][j - 1])) < 1e-9
        ):
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i > 0 and (j == 0 or score[i][j] == score[i - 1][j]):
            pairs.append((i - 1, None))
            i -= 1
        else:
            pairs.append((None, j - 1))
            j -= 1
    pairs.reverse()
    return pairs


def _expected_view(decl: DraftDeclaration, selected: dict[str, list[str]]) -> str:
    """The draft text with each option group shown as the sworn copy's (valid) choice."""

    def repl(match: re.Match[str]) -> str:
        choices = [c.strip() for c in match[2].split("|")]
        chosen = [c for c in choices if c in selected.get(match[1], [])]
        return " / ".join(chosen or choices)

    text = OPTION_MARKUP.sub(repl, decl.markup)
    return clean(" ".join([text, *decl.bullets]))


def word_spans(expected: str, sworn: str) -> list[Span]:
    """Word-level spans: delete = in the draft only, insert = in the sworn copy only."""
    a, b = clean(expected).split(), clean(sworn).split()
    matcher = SequenceMatcher(
        None, [w.casefold() for w in a], [w.casefold() for w in b], autojunk=False
    )
    spans: list[Span] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            spans.append(Span("equal", " ".join(b[j1:j2])))
            continue
        if i2 > i1:
            spans.append(Span("delete", " ".join(a[i1:i2])))
        if j2 > j1:
            spans.append(Span("insert", " ".join(b[j1:j2])))
    return spans


def diff_declarations(
    expected: tuple[DraftDeclaration, ...],
    sworn: list[SwornDeclaration],
    entities: dict[str, str],
) -> list[DeclMatch]:
    exp_words = [_loose(d.display, entities) for d in expected]
    sw_words = [_loose(d.text, entities) for d in sworn]
    sim = [[_similarity(e, s) for s in sw_words] for e in exp_words]
    if not sworn:
        sim = [[] for _ in expected]
        pairs: list[tuple[int | None, int | None]] = [(i, None) for i in range(len(expected))]
    else:
        pairs = _align(sim)
    matches: list[DeclMatch] = []
    for ei, si in pairs:
        if ei is not None and si is not None:
            e, s = expected[ei], sworn[si]
            exp_canon, _ = canonical(e.tokenised, entities)
            sw_canon, selected = canonical(s.text, entities, e.groups)
            view = _expected_view(e, selected)
            if squash(exp_canon) == squash(sw_canon):
                matches.append(
                    DeclMatch(e, s, 1.0, "equal", [Span("equal", s.text)], selected, view)
                )
            else:
                spans = word_spans(view, s.text)
                matches.append(
                    DeclMatch(e, s, round(sim[ei][si], 4), "changed", spans, selected, view)
                )
        elif ei is not None:
            e = expected[ei]
            matches.append(
                DeclMatch(e, None, 0.0, "removed", [Span("delete", e.display)], {}, e.display)
            )
        elif si is not None:
            s = sworn[si]
            matches.append(DeclMatch(None, s, 0.0, "added", [Span("insert", s.text)], {}, ""))
    return matches
