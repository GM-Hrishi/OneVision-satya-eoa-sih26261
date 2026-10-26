"""X-SATYA-Signature verification (Portal spec §2.2).

Header: t=<unix>,kid=<key-id>,v1=<hex HMAC-SHA256 of "t.body">. Rejected when |now - t| > window
or the HMAC does not match (constant-time compare). The kid selects the secret, so two keys can be
valid at once during rotation.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass

from satya_api.problems import ProblemError

HEADER = "X-SATYA-Signature"


@dataclass(frozen=True)
class VerifiedSignature:
    kid: str
    timestamp: int


def sign(body: bytes, secret: bytes, kid: str, timestamp: int | None = None) -> str:
    """Build a header value. Used by tests and by tooling; the mock portal has its own TS copy."""
    t = int(time.time()) if timestamp is None else timestamp
    mac = hmac.new(secret, f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={t},kid={kid},v1={mac}"


def _parse(header: str) -> tuple[int, str, str]:
    parts: dict[str, str] = {}
    for item in header.split(","):
        key, sep, value = item.strip().partition("=")
        if not sep or key in parts:
            raise ValueError("malformed")
        parts[key] = value
    if set(parts) != {"t", "kid", "v1"} or not parts["t"].isdigit():
        raise ValueError("malformed")
    return int(parts["t"]), parts["kid"], parts["v1"]


def verify(
    header: str | None,
    body: bytes,
    keys: dict[str, bytes],
    window_s: int,
    now: float | None = None,
) -> VerifiedSignature:
    if not header or len(header) > 512:
        raise ProblemError(401, "SIGNATURE_INVALID", "Signature header missing.")
    try:
        t, kid, received = _parse(header)
    except ValueError:
        raise ProblemError(401, "SIGNATURE_INVALID", "Signature header malformed.") from None
    secret = keys.get(kid)
    expected = hmac.new(secret or b"", f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    # Compare before the key check so timing does not reveal which kids exist.
    matches = hmac.compare_digest(expected, received.lower())
    if secret is None or not matches:
        raise ProblemError(401, "SIGNATURE_INVALID")
    current = time.time() if now is None else now
    if abs(current - t) > window_s:
        raise ProblemError(401, "SIGNATURE_EXPIRED")
    return VerifiedSignature(kid=kid, timestamp=t)
