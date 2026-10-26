"""Headless OIDC authorization-code + PKCE login through Caddy (S0.7 verify; part of make smoke).

Logs in as a synthetic demo user, exchanges the code with the satya-web client secret, and checks
the access token's realm roles. Also checks that a wrong password gets a generic error.
Usage: uv run python tests/oidc_login_check.py [username] [expected-role]
"""

import base64
import hashlib
import html
import json
import os
import re
import secrets
import socket
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

# Browsers and curl send *.localhost to loopback; glibc does not, so do it here (RFC 6761).
_getaddrinfo = socket.getaddrinfo


def _loopback_localhost(host, *args, **kwargs):  # type: ignore[no-untyped-def]
    if isinstance(host, str) and host.endswith(".localhost"):
        host = "127.0.0.1"
    return _getaddrinfo(host, *args, **kwargs)


socket.getaddrinfo = _loopback_localhost

ROOT = Path(__file__).resolve().parents[1]
env = dict(
    line.split("=", 1)
    for line in (ROOT / ".env").read_text().splitlines()
    if "=" in line and not line.startswith("#")
)
CA = ROOT / "infra/caddy/local-root.crt"
VERIFY: str | bool = str(CA) if CA.exists() else False
ISSUER = "https://auth.localhost/realms/satya"
REDIRECT = "https://localhost/auth/callback/keycloak"


def attempt(username: str, password: str) -> httpx.Response:
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    client = httpx.Client(verify=VERIFY, follow_redirects=False, timeout=15, trust_env=False)
    params = {
        "client_id": "satya-web",
        "response_type": "code",
        "scope": "openid",
        "redirect_uri": REDIRECT,
        "state": secrets.token_urlsafe(16),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    page = client.get(f"{ISSUER}/protocol/openid-connect/auth", params=params)
    page.raise_for_status()
    action = html.unescape(re.search(r'action="([^"]+)"', page.text).group(1))
    response = client.post(action, data={"username": username, "password": password})
    response.verifier = verifier  # type: ignore[attr-defined]
    response.client = client  # type: ignore[attr-defined]
    return response


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "rb.southern.demo"
    role = sys.argv[2] if len(sys.argv) > 2 else "RB"
    wrong = attempt(username, "Wrong-Password-0000")
    assert wrong.status_code == 200 and "Invalid username or password" in wrong.text, (
        "no generic error"
    )
    print("wrong password -> generic error: ok")
    ok = attempt(username, env["DEMO_USER_PASSWORD"])
    assert ok.status_code == 302, f"login failed: {ok.status_code}"
    location = ok.headers["location"]
    assert location.startswith(REDIRECT), location
    code = parse_qs(urlparse(location).query)["code"][0]
    token = ok.client.post(  # type: ignore[attr-defined]
        f"{ISSUER}/protocol/openid-connect/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT,
            "client_id": "satya-web",
            "client_secret": env["SATYA_WEB_CLIENT_SECRET"],
            "code_verifier": ok.verifier,  # type: ignore[attr-defined]
        },
    )
    token.raise_for_status()
    payload = token.json()["access_token"].split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert claims["iss"] == ISSUER, claims["iss"]
    assert role in claims["roles"], claims.get("roles")
    print(
        f"login {username}: ok · iss={claims['iss']} · roles={sorted(claims['roles'])} · groups={claims.get('groups')}"
    )
    return 0


if __name__ == "__main__":
    os.environ.setdefault("NO_COLOR", "1")
    sys.exit(main())
