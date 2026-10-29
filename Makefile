# SATYA-EoA developer commands. Synthetic data only.
SHELL := /bin/bash
.DEFAULT_GOAL := help
COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-16s %s\n",$$1,$$2}'

install: ## Install JS and Python dependencies
	pnpm install --frozen-lockfile
	uv sync --all-packages --frozen

gen-types: ## Regenerate TS types + Pydantic models from packages/shared-types/schemas
	pnpm --filter @satya/shared-types gen

check-types-diff: gen-types ## Regenerate and fail if generated code differs from the commit
	git diff --exit-code -- packages/shared-types

guard: ## Real-data guard (same script as CI)
	@bash infra/scripts/real-data-guard.sh

secret-scan: ## gitleaks over the git history (same as CI)
	docker run --rm -v "$$PWD:/repo" zricethezav/gitleaks:v8.30.1 git /repo --redact --no-banner --config /repo/.gitleaks.toml

lint: ## ESLint + ruff
	pnpm -r lint
	uv run ruff check .
	uv run ruff format --check .

typecheck: ## tsc + mypy
	pnpm -r typecheck
	uv run mypy services/api/src services/worker/src packages/shared-types/python/satya_shared_types packages/affidavit/src packages/forensics/src packages/ocr/src packages/blindgen/src

test: ## Unit tests (no running stack needed)
	pnpm -r test
	uv run pytest packages/shared-types/python
	uv run pytest services/api
	uv run pytest services/worker
	uv run pytest packages/affidavit
	uv run pytest packages/forensics
	uv run pytest packages/blindgen
	uv run pytest packages/ocr

synth: ## Regenerate the synthetic demo cases, registers and public test PKI (data/synthetic)
	uv run python -m satya_forensics.synth

eval-m5: ## M5 metrics (precision, recall, false-flag rate, extraction) over the 104 synthetic affidavits
	uv run python -m satya_affidavit.eval

pki: ## Write the public half of the synthetic test PKI (TEST TRUST ANCHOR root, sub-CA, empty CRL) to .logs/pki
	uv run python -m satya_forensics.pki --out .logs/pki

eval-m6: ## M6/P-18 metrics (precision, recall, false-flag rate, label accuracy) on dev + held-out seeds
	uv run python -m satya_forensics.eval

synth-check: ## Fail if the committed synthetic files (cases, registers, test PKI) differ from a fresh generation
	uv run python -m satya_forensics.synth --check

secrets: ## Generate .env from .env.example with random values (keeps an existing .env)
	@bash infra/scripts/gen-secrets.sh

up: ## Build and start the whole stack, then wait until every service is healthy
	@test -f .env || { echo "No .env: run 'make secrets' first"; exit 1; }
	$(COMPOSE) up -d --build --remove-orphans
	@bash infra/scripts/wait-healthy.sh 600

down: ## Stop the stack (keeps volumes)
	$(COMPOSE) down

ps: ## Show service status
	$(COMPOSE) ps -a

logs: ## Follow logs (SERVICE=api to filter)
	$(COMPOSE) logs -f --tail 100 $(SERVICE)

reset: ## Stop the stack and DROP ALL VOLUMES (asks first)
	@read -r -p "This deletes the database, Keycloak data and Caddy certificates. Type 'reset' to continue: " ans; \
	  if [ "$$ans" = "reset" ]; then $(COMPOSE) --profile test down -v --remove-orphans; else echo "Aborted."; fi

mem-check: ## Check every service has a memory limit and the sum is <= 8 GiB
	@bash infra/scripts/mem-check.sh

config: ## Validate the compose file
	$(COMPOSE) config --quiet && echo "compose config OK"

demo-reset: ## Reset the demo to the same 8 synthetic cases, empty ledger plus seed (needs make up)
	bash infra/scripts/demo-reset.sh

ledger-verify: ## Recompute the ledger hash chain inside the api container
	$(COMPOSE) exec -T api python -m satya_api.ledger_verify

replay: ## Replay a case at its original or a named rule version: make replay CASE=<id> [RULE_VERSION=<pack id>]
	@test -n "$(CASE)" || { echo "usage: make replay CASE=cas_... [RULE_VERSION=<pack id>]"; exit 2; }
	$(COMPOSE) exec -T api python -m satya_api.replay_cli "$(CASE)" $(if $(RULE_VERSION),--rule-version "$(RULE_VERSION)")

trust-ca: ## Export Caddy's local root CA to infra/caddy/local-root.crt (import it into your OS/browser)
	$(COMPOSE) cp caddy:/data/caddy/pki/authorities/local/root.crt infra/caddy/local-root.crt
	@echo "Exported infra/caddy/local-root.crt. See docs/DEV-SETUP.md to trust it."

smoke: ## Cross-service smoke tests against the running stack
	bash tests/smoke.sh
	uv run python tests/oidc_login_check.py rb.southern.demo RB
	$(COMPOSE) --profile test run --rm --build worker-test

e2e: ## Browser acceptance (Playwright/Chromium): workbench sign-in + shell, mock portal signed events, RB-05 DiffView, RB-06 Verification
	NODE_PATH=$$(npm root -g) node tests/e2e/workbench.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/mock-portal.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/diffview.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/verification.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/demo-flow.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/polish.cjs
	NODE_PATH=$$(npm root -g) node tests/e2e/ocr-scan.cjs
	$(COMPOSE) exec -T api python -m satya_api.ledger_verify

test-db: ## Postgres-backed API tests in a throwaway pgvector container
	bash infra/scripts/test-db.sh

.PHONY: eval-blind eval-blind-small replay demo-reset pki eval-m6 synth synth-check eval-m5 guard secret-scan help install secrets up down ps logs reset mem-check config ledger-verify trust-ca smoke e2e test-db gen-types check-types-diff lint typecheck test

eval-blind: ## Blind test set: generate (data/blind, git-ignored) and evaluate; writes docs/eval/BLIND-REPORT.md and blind-results.json
	uv run python -m satya_blindgen run

eval-blind-small: ## Small-N smoke run of the blind generator and evaluator (CI), report written to .logs
	uv run python -m satya_blindgen run --n 12 --out .logs/blind-small --docs .logs/blind-small-docs
