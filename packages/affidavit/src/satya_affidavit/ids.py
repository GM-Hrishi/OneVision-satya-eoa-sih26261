"""Deterministic IDs, hashes, tokens and masks.

Runs are deterministic (Portal spec §2.11): the same sworn copy, draft and ruleset give the same
doc_id and flag IDs, so a replay can be compared byte for byte.
"""

import hashlib
import hmac

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    """`<prefix>_` + 26 Crockford base32 characters derived from the parts (ULID-shaped)."""
    digest = hashlib.sha256("\x1f".join(parts).encode()).digest()
    number = int.from_bytes(digest[:17], "big") >> 6  # 130 bits -> 26 chars
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[number & 31])
        number >>= 5
    return f"{prefix}_{''.join(reversed(chars))}"


def token(key: bytes, value: str, identifier: bool = False) -> str:
    """Keyed HMAC-SHA256 token of a T field (Portal spec §2.6.1), on the normalised value.

    Names keep single spaces; identifiers (deed document no.) drop every space, because a number
    wrapped inside a narrow table cell comes back from the text layer with a space in it.
    """
    joiner = "" if identifier else " "
    normalised = joiner.join(value.split()).casefold()
    return hmac.new(key, normalised.encode(), hashlib.sha256).hexdigest()


def mask(value: str | None, keep: int = 4) -> str | None:
    """Mask an identifier for display; only the last `keep` characters stay readable."""
    if value is None:
        return None
    compact = "".join(value.split())
    if len(compact) <= keep:
        return "•" * len(compact)
    return "•••" + compact[-keep:]
