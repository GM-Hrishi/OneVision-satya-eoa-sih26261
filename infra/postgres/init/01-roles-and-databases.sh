#!/bin/sh
# Runs once on an empty data volume (docker-entrypoint-initdb.d). Creates least-privilege roles:
#   satya_migrator  owns the satya schema objects (DDL, used only by the one-shot migrate job)
#   satya_app       runtime role for api/worker (DML only, granted per table by migrations)
#   keycloak        owns the keycloak database
# Passwords come from the environment (.env); nothing secret is committed.
set -eu
: "${SATYA_DB_MIGRATOR_PASSWORD:?}" "${SATYA_DB_APP_PASSWORD:?}" "${KEYCLOAK_DB_PASSWORD:?}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  -v migrator_pw="$SATYA_DB_MIGRATOR_PASSWORD" \
  -v app_pw="$SATYA_DB_APP_PASSWORD" \
  -v kc_pw="$KEYCLOAK_DB_PASSWORD" <<'SQL'
CREATE ROLE satya_migrator LOGIN PASSWORD :'migrator_pw';
CREATE ROLE satya_app LOGIN PASSWORD :'app_pw';
CREATE ROLE keycloak LOGIN PASSWORD :'kc_pw';
CREATE DATABASE satya OWNER satya_migrator;
CREATE DATABASE keycloak OWNER keycloak;
REVOKE ALL ON DATABASE satya FROM PUBLIC;
REVOKE ALL ON DATABASE keycloak FROM PUBLIC;
GRANT CONNECT ON DATABASE satya TO satya_app;
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname satya <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO satya_migrator;
GRANT USAGE ON SCHEMA public TO satya_app;
SQL
