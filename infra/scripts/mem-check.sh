#!/usr/bin/env bash
# Fail if any service lacks a memory limit or the limits sum to more than 8 GiB (S0 acceptance 9).
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-../.env}"
[[ -f "$ENV_FILE" ]] || ENV_FILE=../.env.example
docker compose --env-file "$ENV_FILE" -f docker-compose.yml config --format json > /tmp/satya-compose.json
python3 - /tmp/satya-compose.json <<'PY'
import json, sys
services = json.load(open(sys.argv[1]))["services"]
missing = [n for n, s in services.items() if not s.get("mem_limit")]
total = sum(int(s.get("mem_limit", 0)) for s in services.values())
for name, svc in sorted(services.items()):
    print(f"{name:16} {int(svc.get('mem_limit', 0)) / 2**20:6.0f} MiB")
print(f"TOTAL {total / 2**30:.2f} GiB (budget 8 GiB)")
if missing:
    print("missing mem_limit:", ", ".join(missing))
sys.exit(1 if missing or total > 8 * 2**30 else 0)
PY
