#!/usr/bin/env bash
# Generate .env from .env.example, replacing every CHANGE_ME with a fresh random value.
# Never overwrites an existing .env unless FORCE=1. Values are hex, so they are URL-safe.
# Set SATYA_EXTRA_CA_FILE in the environment first if builds run behind a TLS-intercepting proxy.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [[ -f .env && "${FORCE:-0}" != "1" ]]; then
  echo ".env already exists; keeping it. Use FORCE=1 make secrets to regenerate (then make reset)."
  exit 0
fi

rand_hex() { od -An -tx1 -N"$1" /dev/urandom | tr -d ' \n'; }

tmp="$(mktemp)"
while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^([A-Z0-9_]+)=CHANGE_ME$ ]]; then
    key="${BASH_REMATCH[1]}"
    case "$key" in
      # Satisfies the realm password policy: upper, lower, digit, special, length >= 14.
      DEMO_USER_PASSWORD) value="Demo-$(rand_hex 10)-Z9" ;;
      *) value="$(rand_hex 32)" ;;
    esac
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
  else
    printf '%s\n' "$line" >> "$tmp"
  fi
done < .env.example

if [[ -n "${SATYA_EXTRA_CA_FILE:-}" ]]; then
  # Copied inside the project because compose build secrets may only read project files.
  cp "$SATYA_EXTRA_CA_FILE" infra/certs/extra-ca.pem
  printf '\n# Build-time CA bundle for a TLS-intercepting proxy (set by make secrets)\nSATYA_EXTRA_CA_FILE=./certs/extra-ca.pem\n' >> "$tmp"
fi

mv "$tmp" .env
chmod 600 .env
echo "Wrote .env with fresh random secrets (git-ignored). Demo user password: grep DEMO_USER_PASSWORD .env"
