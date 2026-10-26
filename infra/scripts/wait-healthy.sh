#!/usr/bin/env bash
# Wait until every long-running service is healthy and every one-shot job exited 0.
# Usage: wait-healthy.sh <timeout-seconds> [service ...]   (default: all services)
set -euo pipefail
cd "$(dirname "$0")/.."
TIMEOUT="${1:-600}"; shift || true
COMPOSE=(docker compose --env-file ../.env -f docker-compose.yml)
ONESHOT="migrate keycloak-config"
services=("$@")
[[ ${#services[@]} -eq 0 ]] && mapfile -t services < <("${COMPOSE[@]}" config --services)

start=$(date +%s)
while true; do
  pending=()
  for svc in "${services[@]}"; do
    [[ "$svc" == "worker-test" ]] && continue
    cid="$("${COMPOSE[@]}" ps -a -q "$svc" 2>/dev/null | head -1)"
    if [[ -z "$cid" ]]; then pending+=("$svc:missing"); continue; fi
    if [[ " $ONESHOT " == *" $svc "* ]]; then
      state="$(docker inspect -f '{{.State.Status}}:{{.State.ExitCode}}' "$cid")"
      case "$state" in
        exited:0) ;;
        exited:*) echo "FAIL $svc ($state)"; "${COMPOSE[@]}" logs --tail 40 "$svc"; exit 1 ;;
        *) pending+=("$svc:$state") ;;
      esac
    else
      health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid")"
      [[ "$health" == "healthy" ]] || pending+=("$svc:$health")
    fi
  done
  elapsed=$(( $(date +%s) - start ))
  if [[ ${#pending[@]} -eq 0 ]]; then echo "All services healthy after ${elapsed}s."; exit 0; fi
  if (( elapsed > TIMEOUT )); then echo "Timed out after ${elapsed}s: ${pending[*]}"; exit 1; fi
  echo "[$elapsed s] waiting: ${pending[*]}"
  sleep 5
done
