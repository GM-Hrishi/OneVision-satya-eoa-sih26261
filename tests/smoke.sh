#!/usr/bin/env bash
# Cross-service smoke test through Caddy (needs `make up`). Synthetic data only.
# Checks: health 200 with all deps ok; meta; signed event 202 then duplicate 200;
# tampered signature 401 SIGNATURE_INVALID; old timestamp 401 SIGNATURE_EXPIRED; ledger chain ok.
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="${SATYA_BASE_URL:-https://localhost}"
CURL=(curl -sS --fail-with-body)
if [[ -f infra/caddy/local-root.crt ]]; then CURL+=(--cacert infra/caddy/local-root.crt); else CURL+=(-k); fi
set -a; source .env; set +a

echo "== health"; "${CURL[@]}" "$BASE/api/v1/health" | tee /dev/stderr | python3 -c \
  'import json,sys; b=json.load(sys.stdin); assert b["status"]=="ok" and set(b["checks"].values())=={"ok"}, b'
echo; echo "== meta"; "${CURL[@]}" "$BASE/api/v1/meta" | python3 -c \
  'import json,sys; b=json.load(sys.stdin); assert b["schema_version"]=="satya.event/1"; print("ok")'
[[ "${SMOKE_SKIP_PORTAL:-0}" == 1 ]] || { echo "== mock portal"; "${CURL[@]}" -o /dev/null -w '%{http_code}\n' "https://portal.localhost/" -k; }

python3 - "$BASE" <<'PY'
import hashlib, hmac, json, os, ssl, sys, time, urllib.request, urllib.error, secrets
base = sys.argv[1]
kid, secret = os.environ["PORTAL_HMAC_KID"], os.environ["PORTAL_HMAC_SECRET"].encode()
ctx = ssl.create_default_context(cafile="infra/caddy/local-root.crt") if os.path.exists("infra/caddy/local-root.crt") else ssl._create_unverified_context()
alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ulid = lambda: "".join(secrets.choice(alphabet) for _ in range(26))
env = {"spec": "satya.event/1", "event_id": f"evt_{ulid()}", "type": "application.precheck_requested",
       "occurred_at": "2026-12-14T11:05:42+05:30", "producer": "mock-portal",
       "subject": {"application_id": "1-90000004217", "permanent_id": "1-9000317", "ay": "2026-27"},
       "sequence": 1, "correlation_id": f"cor_{ulid()}", "data": {}}
body = json.dumps(env).encode()
def post(sig):
    req = urllib.request.Request(f"{base}/api/v1/portal-events", data=body, method="POST",
        headers={"Content-Type": "application/json", "X-SATYA-Signature": sig})
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)
def sign(t):
    return f"t={t},kid={kid},v1=" + hmac.new(secret, f"{t}.".encode() + body, hashlib.sha256).hexdigest()
now = int(time.time())
s, b = post(sign(now)); print("== signed event", s, b); assert s == 202 and b["duplicate"] is False
s, b = post(sign(now)); print("== duplicate", s, b); assert s == 200 and b["duplicate"] is True
bad = sign(now)[:-4] + "0000"
s, b = post(bad); print("== tampered", s, b["code"]); assert s == 401 and b["code"] == "SIGNATURE_INVALID"
s, b = post(sign(now - 900)); print("== expired", s, b["code"]); assert s == 401 and b["code"] == "SIGNATURE_EXPIRED"
PY
echo "== ledger"; docker compose --env-file .env -f infra/docker-compose.yml exec -T api python -m satya_api.ledger_verify
echo "SMOKE OK"
