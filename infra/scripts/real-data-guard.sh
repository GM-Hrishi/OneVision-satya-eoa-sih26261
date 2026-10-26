#!/usr/bin/env bash
# Real-data guard (guard rails 3-5). Fails when:
#   1. any file under data/real-samples/ is tracked by git, or
#   2. a tracked file contains a personal-data pattern: Indian mobile \b[6-9]\d{9}\b,
#      PAN \b[A-Z]{5}\d{4}[A-Z]\b, Aadhaar-like \b\d{4}\s?\d{4}\s?\d{4}\b,
#   unless the hit is listed in .real-data-allowlist (documented synthetic fixtures).
# Allow-list format, one per line:  <path-glob><TAB><exact matched text><TAB><reason>
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

status=0
tracked_real="$(git ls-files -- 'data/real-samples/**' 'data/real-samples/*')"
if [[ -n "$tracked_real" ]]; then
  echo "FAIL: files under data/real-samples/ are tracked by git:"; echo "$tracked_real"; status=1
fi

declare -a ALLOW_GLOB=() ALLOW_TEXT=()
if [[ -f .real-data-allowlist ]]; then
  while IFS=$'\t' read -r glob text reason || [[ -n "${glob:-}" ]]; do
    [[ -z "${glob:-}" || "$glob" == \#* ]] && continue
    [[ -z "${reason:-}" ]] && { echo "FAIL: allow-list entry without a reason: $glob $text"; status=1; }
    ALLOW_GLOB+=("$glob"); ALLOW_TEXT+=("$text")
  done < .real-data-allowlist
fi

PATTERN='\b[6-9][0-9]{9}\b|\b[A-Z]{5}[0-9]{4}[A-Z]\b|\b[0-9]{4}[[:space:]]?[0-9]{4}[[:space:]]?[0-9]{4}\b'
# Lockfiles hold registry hashes and version numbers, not people's data.
mapfile -t files < <(git ls-files -z | tr '\0' '\n' | grep -vE '(^|/)(pnpm-lock\.yaml|uv\.lock)$|\.(png|jpg|jpeg|gif|webp|ico|woff2?|ttf|pdf)$')
hits=0
while IFS= read -r line; do
  file="${line%%:*}"; rest="${line#*:}"; lineno="${rest%%:*}"; match="${rest#*:}"
  allowed=0
  for i in "${!ALLOW_GLOB[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$file" == ${ALLOW_GLOB[$i]} && "$match" == "${ALLOW_TEXT[$i]}" ]]; then allowed=1; break; fi
  done
  if [[ $allowed -eq 0 ]]; then
    echo "FAIL: personal-data pattern in $file:$lineno: '$match'"; hits=$((hits + 1))
  fi
done < <(grep -HnoE "$PATTERN" -- "${files[@]}" 2>/dev/null || true)

[[ $hits -gt 0 ]] && status=1
if [[ $status -eq 0 ]]; then
  echo "real-data guard: OK (${#files[@]} tracked files scanned, ${#ALLOW_GLOB[@]} allow-list entries)"
else
  echo "real-data guard: FAILED. Remove the data, or if it is a documented synthetic fixture add it to .real-data-allowlist with a reason."
fi
exit $status
