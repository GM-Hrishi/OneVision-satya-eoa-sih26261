# PROGRESS — Slice 0 (foundation)
Prompt: docs/prompts/SLICE-0-PROMPT.md v1.0 · Branch: slice-0-foundation
Resume rule: continue from the first step whose status is not `done`/`done-with-note`.

| Step | Status | Updated (UTC) | Verify | Note |
|---|---|---|---|---|
| S0.1 Read specs; write CLAUDE.md, .gitignore, .editorconfig, .env.example | done | 2026-10-26 00:33 | CLAUDE.md exists; data/real-samples/ ignored | CLAUDE.md, .gitignore, .editorconfig, .env.example written; real-samples ignored (git check-ignore ok) |
| S0.2 Monorepo skeleton (pnpm + uv workspaces, placeholders, READMEs) | done | 2026-10-26 00:35 | `pnpm -r build` no-op passes; `uv sync` passes | pnpm -r build (4 workspace projects) and uv sync --all-packages pass; placeholder READMEs + data/synthetic README + demo-institute-03.json |
| S0.3 shared-types: JSON Schemas + generated TS/Pydantic + tests | done | 2026-10-26 00:44 | schema tests pass; regen diff empty | 11 schemas (+Check); vitest 27 passed, pytest 34 passed; make check-types-diff empty |
| S0.4 services/api: health, meta, portal-events (HMAC, dedupe, ledger), migrations, tests | done | 2026-10-26 00:51 | pytest green | pytest: 35 unit passed; 3 Postgres tests passed against pgvector:0.8.7-pg18 (migrated with Alembic as satya_migrator); ruff + mypy clean |
| S0.5 services/worker: Celery + Valkey + ping | done | 2026-10-26 00:53 | ping task returns pong | ping returned pong through a real Valkey 9.1.2 container + local worker (integration test passed); 4 unit tests passed; beat placeholder scheduled |
| S0.6 infra: compose (8 services, health checks, memory limits), Caddy TLS + headers, make targets, secrets script | done | 2026-10-26 01:26 | `make up` all healthy | All 8 services + migrate + keycloak-config healthy (web/mock-portal verified in S0.8/S0.9); health 200 all ok; smoke + worker-test passed; limits 5.62 GiB |
| S0.7 Keycloak realm import + demo users (passwords from .env) | done | 2026-10-26 01:05 | login as rb.southern.demo works | realm imported; keycloak-config exited 0; headless OIDC code+PKCE login as rb.southern.demo ok (iss https://auth.localhost/realms/satya, roles [RB]); wrong password gets generic error; brute force + policy confirmed via admin API |
| S0.8 apps/web: tokens.css, AppShell, i18n, auth, pages, a11y | done | 2026-10-26 01:23 | acceptance 3 passes | Acceptance 3 passes in Chromium (tests/e2e/workbench.cjs, 30+ checks): HTTPS via trusted local CA, redirect to Keycloak, rb.southern.demo lands on RB shell with empty queue; 403/404, Hindi, 360px, 200% text, sign-out, no console errors; tsc/eslint/vitest (9) green; no source maps served |
| S0.9 apps/mock-portal: banner + signed test event | done | 2026-10-26 01:26 | acceptance 4 and 5 pass | Acceptance 4 + 5 pass in Chromium via the portal UI (tests/e2e/mock-portal.cjs): 202 receipt, 200 duplicate:true, 401 SIGNATURE_INVALID, 401 SIGNATURE_EXPIRED; make ledger-verify ok; tsc/eslint/vitest green |
| S0.10 CI: lint, types, tests, regen check, secret scan, real-data guard, smoke | done | 2026-10-26 01:38 | CI green | CI run 3 (865a400) green, all 7 jobs: js, python (+Postgres tests), contracts diff, compose+mem, gitleaks, real-data guard, smoke (make up on a fresh runner, make smoke, browser acceptance). Run 1 failed on ruff only; fixed. Guard proven by planting fake PII |
| S0.11 Issues P-1..P-19 (gh) or docs/ISSUES.md + script | done-with-note | 2026-10-26 01:31 | 19 issues or file+script exist | gh present but its token is invalid in this session, so the fallback path was taken: docs/ISSUES.md (19 issues) + infra/scripts/create-issues.sh (idempotent; DRY_RUN=1 printed 19 gh issue create calls), both rendered from docs/backlog/promises.json |
| S0.12 README, DEV-SETUP, ARCHITECTURE, STACK-VERSIONS, DECISIONS; acceptance run; PR | done | 2026-10-26 01:38 | all 9 acceptance criteria pass | README, DEV-SETUP, ARCHITECTURE, STACK-VERSIONS, DECISIONS written; all 9 acceptance criteria pass (see table below); PR opened |

## Acceptance results (slice 0)
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `make secrets && make up` → all healthy ≤10 min first run, ≤2 min later | PASS | Fresh CI runner (pulls + builds): 3 min 33 s. Local from empty volumes: 67 s. Warm restart incl. one image rebuild: 84 s. |
| 2 | `curl -k https://localhost/api/v1/health` 200, all deps ok | PASS | `{"status":"ok","checks":{"postgres":"ok","valkey":"ok","keycloak":"ok"}}` |
| 3 | HTTPS on default browser settings after trusting the local CA; Keycloak sign-in as `rb.southern.demo`; RB shell + empty queue; portal banner | PASS | `make e2e` (Chromium, CA in NSS, no TLS bypass): 29 workbench checks incl. 403, 404, Hindi, 360 px, 200 % text, sign-out, no console errors |
| 4 | Send test event → 202; again → 200 duplicate; `make ledger-verify` valid | PASS | `tests/e2e/mock-portal.cjs` through the portal UI; ledger `{"ok": true}` |
| 5 | Tampered → 401 SIGNATURE_INVALID; old timestamp → 401 SIGNATURE_EXPIRED | PASS | portal UI buttons, `tests/smoke.sh`, API unit tests |
| 6 | CI green incl. secret scan and real-data guard | PASS | Actions run 3 on 865a400: 7/7 jobs green |
| 7 | CLAUDE.md, README, DEV-SETUP, STACK-VERSIONS, DECISIONS, ISSUES exist and match | PASS | every documented `make` target exists; versions read from lockfiles |
| 8 | No real names, IDs or real-sample data | PASS | real-data guard, gitleaks, name/email/logo sweep: no hits |
| 9 | Memory limits on every service, sum ≤ 8 GB | PASS | `make mem-check`: 5.62 GiB |

## Blockers / questions
Answered by the team lead on 26 Oct 2026:
- **LICENSE:** hold off until the repo goes public, then use Apache-2.0 if the SIH rules allow it. No LICENSE file until then.
- **GitHub issues:** skipped for now. Slice 1 (M5) references P-n IDs from `docs/ISSUES.md`. The team lead runs `infra/scripts/create-issues.sh` from their laptop later (after `gh auth login`).
- **Priority of M2 (P-19) and M10 (P-14):** keep the defaults (M2 `prio-3` with M3, M10 `prio-9` with M11).
- **Hindi review (OPEN):** the team lead will name one teammate who reads Hindi to review `apps/web/messages/hi.review.json`. Deadline: before the first demo rehearsal.

## Deviations from the prompt
- Keycloak redirect URIs are the exact callback paths, not `https://<host>/*` (stricter). Auth.js runs under `/auth` because `/api/*` belongs to the gateway.
- Keycloak's `frame-ancestors` is tightened to `'none'` and `/admin` is not routed through Caddy (no admin console at the edge).
- Two one-shot jobs (`migrate`, `keycloak-config`) run besides the 8 services, for least-privilege migrations and secrets from `.env`.
- Inbound OAuth client-credentials check (Portal §2.0) deferred to the Portal §5/§6 slice; slice 0 authenticates events by HMAC per `kid`.
- Branch is `claude/pensive-rubin-eudosj` (the session's assigned push branch) instead of `slice-0-foundation`. The PR is opened from it. See docs/progress/DECISIONS-SLICE-0.md.
