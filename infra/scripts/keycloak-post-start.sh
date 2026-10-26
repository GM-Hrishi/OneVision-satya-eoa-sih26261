#!/usr/bin/env bash
# One-shot (compose service keycloak-config): after Keycloak is healthy, set the OIDC client
# secrets and the synthetic demo users' password from .env. Nothing secret is in realm-satya.json.
# Idempotent: re-running sets the same values again.
set -euo pipefail
: "${KC_URL:?}" "${KC_BOOTSTRAP_ADMIN_USERNAME:?}" "${KC_BOOTSTRAP_ADMIN_PASSWORD:?}" "${DEMO_USER_PASSWORD:?}"
: "${SATYA_WEB_CLIENT_SECRET:?}" "${SATYA_MOCK_PORTAL_CLIENT_SECRET:?}" "${PORTAL_INTEGRATION_CLIENT_SECRET:?}"

KCADM=(/opt/keycloak/bin/kcadm.sh)
CFG=(--config /tmp/kcadm.config)
REALM=satya

for attempt in $(seq 1 30); do
  if "${KCADM[@]}" config credentials "${CFG[@]}" --server "$KC_URL" --realm master \
       --user "$KC_BOOTSTRAP_ADMIN_USERNAME" --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null 2>&1; then
    break
  fi
  [[ $attempt -eq 30 ]] && { echo "keycloak-config: could not log in to Keycloak admin API"; exit 1; }
  sleep 3
done

set_secret() {
  local client_id="$1" secret="$2" id
  id="$("${KCADM[@]}" get clients "${CFG[@]}" -r "$REALM" -q "clientId=$client_id" --fields id --format csv --noquotes)"
  [[ -n "$id" ]] || { echo "keycloak-config: client $client_id not found"; exit 1; }
  "${KCADM[@]}" update "clients/$id" "${CFG[@]}" -r "$REALM" -s "secret=$secret"
  echo "keycloak-config: secret set for client $client_id"
}
set_secret satya-web "$SATYA_WEB_CLIENT_SECRET"
set_secret satya-mock-portal "$SATYA_MOCK_PORTAL_CLIENT_SECRET"
set_secret portal-integration "$PORTAL_INTEGRATION_CLIENT_SECRET"

for user in rb.southern.demo rb.national.demo sc.demo ev.demo hc.demo ra.demo auditor.demo institution.demo03; do
  "${KCADM[@]}" set-password "${CFG[@]}" -r "$REALM" --username "$user" --new-password "$DEMO_USER_PASSWORD"
  echo "keycloak-config: password set for $user"
done
rm -f /tmp/kcadm.config
echo "keycloak-config: done"
