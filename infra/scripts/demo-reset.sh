#!/usr/bin/env bash
# Reset the demo to the same synthetic state every time (Slice D). Needs `make up` first.
# 1. regenerate the synthetic cases (deterministic) and rebuild the api image so it carries them
# 2. empty the ledger and the uploaded files (DEMO ONLY: superuser bypasses the append-only guard)
# 3. restart the api and record the intake and first check run of every case
set -euo pipefail
cd "$(dirname "$0")/../.."
COMPOSE="docker compose --env-file .env -f infra/docker-compose.yml"

echo "[1/4] synthetic cases"
uv sync --all-packages --quiet
uv run python -m satya_forensics.synth >/dev/null
uv run python -m satya_forensics.synth --check
$COMPOSE up -d --build api

echo "[2/4] empty ledger and uploads (demo database only)"
$COMPOSE exec -T postgres psql -U postgres -d satya -v ON_ERROR_STOP=1 -q <<'SQL'
ALTER TABLE ledger DISABLE TRIGGER USER;
TRUNCATE inbound_events, ledger RESTART IDENTITY;
ALTER TABLE ledger ENABLE TRIGGER USER;
SQL
$COMPOSE exec -T api sh -c 'rm -rf /var/lib/satya/uploads/* 2>/dev/null || true'

echo "[3/4] restart api"
$COMPOSE restart api >/dev/null
bash infra/scripts/wait-healthy.sh 300

echo "[4/4] seed"
$COMPOSE exec -T api python -m satya_api.demo_seed
$COMPOSE exec -T api python -m satya_api.ledger_verify
echo "Demo reset. Open https://localhost and sign in as rb.southern.demo (password in .env)."
