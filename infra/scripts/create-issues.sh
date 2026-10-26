#!/usr/bin/env bash
# Create the P-1..P-19 GitHub issues with the gh CLI (run on a laptop after `gh auth login`).
# Idempotent: skips any issue whose exact title already exists. DRY_RUN=1 prints instead.
# Source of truth: docs/backlog/promises.json (rendered to docs/ISSUES.md).
set -euo pipefail
cd "$(dirname "$0")/../.."
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo GM-Hrishi/satya-eoa)}"
run() { if [[ "${DRY_RUN:-0}" == "1" ]]; then printf 'DRY_RUN:'; printf ' %q' "$@"; echo; else "$@"; fi; }

if [[ "${DRY_RUN:-0}" != "1" ]]; then gh auth status >/dev/null; fi

declare -A COLOR=([phase-1]=0B2E59 [phase-2]=4B5563)
for i in $(seq 1 11); do COLOR[prio-$i]=E07B00; done
for label in "${!COLOR[@]}"; do
  run gh label create "$label" --repo "$REPO" --color "${COLOR[$label]}" --force \
    --description "SATYA-EoA backlog (decision #40)" >/dev/null
done

existing=""
[[ "${DRY_RUN:-0}" == "1" ]] || existing="$(gh issue list --repo "$REPO" --state all --limit 500 --json title -q '.[].title')"

while IFS=$'\t' read -r id title labels; do
  if grep -qxF -- "$title" <<<"$existing"; then echo "exists: $title"; continue; fi
  body="$(python3 infra/scripts/issues.py body "$id")"
  run gh issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body"
done < <(python3 infra/scripts/issues.py tsv)
