"""Workbench API authentication: Keycloak OIDC access tokens (Portal spec §2.0, UI spec §1).

The workbench server sends the signed-in official's access token as a Bearer token. The gateway
verifies it on every request: RS256 signature against the realm's JWKS (fetched over the internal
network and cached), issuer, expiry and the authorised party (the workbench client). Roles come from
the realm-role mapper (`roles`), regions from group membership (`/regions/<name>`). Authorisation is
always decided here, never by the caller.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWK

from satya_api.problems import ProblemError

security = logging.getLogger("satya.security")

ROLES = ("RB", "SC", "EV", "HC", "RA", "AU", "INS")
JWKS_TTL_S = 600
JWKS_REFETCH_MIN_S = 30
LEEWAY_S = 10

JwksFetcher = Callable[[], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Principal:
    subject: str
    username: str
    roles: frozenset[str]
    regions: frozenset[str]

    def can_see_region(self, region: str) -> bool:
        return "national" in self.regions or region.casefold() in self.regions


class TokenVerifier:
    def __init__(self, issuer: str, audience_client: str, fetch_jwks: JwksFetcher) -> None:
        self.issuer = issuer
        self.audience_client = audience_client
        self._fetch = fetch_jwks
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at = 0.0
        self._lock = asyncio.Lock()

    async def _key(self, kid: str) -> PyJWK:
        now = time.monotonic()
        stale = now - self._fetched_at > JWKS_TTL_S
        unknown = kid not in self._keys and now - self._fetched_at > JWKS_REFETCH_MIN_S
        if stale or unknown or not self._keys:
            async with self._lock:
                if time.monotonic() - self._fetched_at > JWKS_REFETCH_MIN_S or not self._keys:
                    try:
                        jwks = await self._fetch()
                    except Exception as exc:
                        if not self._keys:
                            raise ProblemError(503, "DEGRADED") from exc
                    else:
                        self._keys = {
                            k["kid"]: PyJWK.from_dict(k)
                            for k in jwks.get("keys", [])
                            if k.get("use", "sig") == "sig" and "kid" in k
                        }
                        self._fetched_at = time.monotonic()
        if kid not in self._keys:
            raise ProblemError(401, "INVALID_TOKEN")
        return self._keys[kid]

    async def verify(self, authorization: str | None) -> Principal:
        if not authorization:
            raise ProblemError(401, "AUTH_REQUIRED", headers={"WWW-Authenticate": "Bearer"})
        scheme, _, raw = authorization.partition(" ")
        if scheme.casefold() != "bearer" or not raw.strip():
            raise ProblemError(401, "AUTH_REQUIRED", headers={"WWW-Authenticate": "Bearer"})
        raw = raw.strip()
        try:
            header = jwt.get_unverified_header(raw)
        except jwt.PyJWTError:
            raise _invalid("malformed token") from None
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise _invalid("unexpected token header")
        key = await self._key(str(header["kid"]))
        try:
            claims: dict[str, Any] = jwt.decode(
                raw,
                key=key,
                algorithms=["RS256"],
                issuer=self.issuer,
                leeway=LEEWAY_S,
                options={"require": ["exp", "iat", "iss", "sub"], "verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise _invalid(type(exc).__name__) from None
        if claims.get("azp") != self.audience_client:
            raise _invalid("unexpected authorised party")
        if claims.get("typ", "Bearer") != "Bearer":
            raise _invalid("not an access token")
        roles = frozenset(r for r in claims.get("roles", []) if r in ROLES)
        regions = frozenset(
            g.removeprefix("/regions/").casefold()
            for g in claims.get("groups", [])
            if isinstance(g, str) and g.startswith("/regions/")
        )
        return Principal(
            subject=str(claims["sub"]),
            username=str(claims.get("preferred_username", claims["sub"])),
            roles=roles,
            regions=regions,
        )


def _invalid(reason: str) -> ProblemError:
    security.warning("access token rejected", extra={"reason": reason})
    return ProblemError(
        401, "INVALID_TOKEN", headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
    )


def http_jwks_fetcher(client: httpx.AsyncClient, url: str) -> JwksFetcher:
    async def fetch() -> dict[str, Any]:
        response = await client.get(url)
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body

    return fetch
