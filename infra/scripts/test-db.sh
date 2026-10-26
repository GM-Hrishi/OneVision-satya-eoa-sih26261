#!/usr/bin/env bash
# Run the Postgres-backed API tests against a throwaway pgvector container with the real init
# script and Alembic migrations. Synthetic data only.
set -euo pipefail
cd "$(dirname "$0")/../.."
NAME=satya-testdb-$$
PORT="${SATYA_TEST_DB_PORT:-55432}"
cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run -d --name "$NAME" -p "127.0.0.1:${PORT}:5432" \
  -e POSTGRES_PASSWORD=test-super -e SATYA_DB_MIGRATOR_PASSWORD=test-migrator \
  -e SATYA_DB_APP_PASSWORD=test-app -e KEYCLOAK_DB_PASSWORD=test-kc \
  -v "$PWD/infra/postgres/init:/docker-entrypoint-initdb.d:ro" \
  pgvector/pgvector:0.8.7-pg18 >/dev/null
for _ in $(seq 1 60); do
  docker exec "$NAME" psql -U satya_app -d satya -h 127.0.0.1 -c 'select 1' >/dev/null 2>&1 && break
  sleep 1
done
(cd services/api && SATYA_MIGRATOR_DATABASE_URL="postgresql+psycopg://satya_migrator:test-migrator@127.0.0.1:${PORT}/satya" \
  uv run alembic upgrade head)
SATYA_TEST_DATABASE_URL="postgresql+psycopg://satya_app:test-app@127.0.0.1:${PORT}/satya" \
  uv run pytest services/api/tests/test_postgres_store.py -v
