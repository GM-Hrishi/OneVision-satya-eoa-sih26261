"""Document label from its checks (Portal spec §2.6.3).

The label is the most severe check outcome, in the order
mismatch_detected > expired > manual_review_required > source_unavailable > verification_pending
> verified. `verified` also needs at least one authenticity check that passed: an issuer
signature or an official-source lookup. A valid uploader signature never makes a document verified
(decision #28), so a document whose only passing checks are the uploader signature and format
checks is `manual_review_required`: nothing vouches for its issuer yet.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from satya_shared_types.generated.constants import LABEL_PRECEDENCE

AUTHENTICITY_KINDS = frozenset({"issuer_signature", "source_lookup"})


def most_severe(outcomes: Iterable[str]) -> str | None:
    ranked = sorted(outcomes, key=LABEL_PRECEDENCE.index)
    return ranked[0] if ranked else None


def document_label(checks: Iterable[Mapping[str, Any]]) -> str:
    checks = list(checks)
    worst = most_severe(c["outcome"] for c in checks)
    if worst is None:
        return "verification_pending"
    if worst == "verified" and not any(
        c["kind"] in AUTHENTICITY_KINDS and c["outcome"] == "verified" for c in checks
    ):
        return "manual_review_required"
    return worst


def label_counts(labels: Iterable[str]) -> dict[str, int]:
    counts = dict.fromkeys(LABEL_PRECEDENCE, 0)
    for label in labels:
        if label in counts:
            counts[label] += 1
    return counts
