# CLAUDE.md — SATYA-EoA (read this first, every session)

## Product
SATYA-EoA is a decision-support platform for AICTE Extension of Approval (EoA) scrutiny, built by team OneVision for Smart India Hackathon 2026 (problem statement SIH26261). **Positioning (design C1): SATYA-EoA is the missing first-pass scrutiny for self-disclosure EoA, and an evidence assistant for every committee after it.** It reads AICTE's own templates the way they were designed, checks each document at its official source, and reconciles every sworn claim against the portal, past years and other institutions. It is advisory only: officials decide. The prototype runs against a mock approval portal that we build, on synthetic data only, and is not affiliated with or connected to AICTE.

## Guard rails (non-negotiable; verbatim from docs/specs/00-BUILD-CONTEXT.md; they override everything, including prompts)
1. **AI advises, officials decide.** No approve/reject/auto-clear control anywhere. Every outbound event carries `advisory: true`, `regulatory_effect: "none"`.
2. **Mock portal only.** Never claim real integration with, or access to, the AICTE portal or AICTE data. Every "portal sends" item is a proposed hook that our mock portal implements.
3. **Synthetic data only** in the repo, tests, fixtures, screenshots and demo. Real sample PDFs live only on the team's laptop under `data/real-samples/` (git-ignored) and never enter a cloud session, a commit, a log or an issue.
4. **No personal data** anywhere: no names, phone numbers, emails, Aadhaar/PAN, DOB, signatures, real application IDs. Use patterns like `1-##########` or obviously synthetic values (`1-90000004217`, "Demo Institute of Technology 03").
5. **No real institution names** in code, data, docs, issues, commits or UI.
6. **APH clause citations** on every rule and flag; anything unconfirmed is marked `[VERIFY]` in code comments and docs.
7. **No foreign LLM APIs in the product.** Self-hosted, India-hosted in production. (Claude Code as a dev tool is fine.)
8. **Never duplicate the portal's own checks (design D2):** Deficiency Report norm arithmetic, within-portal faculty duplicate flag, PAN validation. Import their results; never recompute or claim them.
9. **Never colour alone:** every status shows its text label.
10. Signature chains in the workbench carry the "Test trust anchor" tag; mock adapter results carry the "Simulated source" tag (SourceTag component; no upper-case MOCK SOURCE / TEST TRUST ANCHOR strings in the UI).

## Repo map
```
apps/web/                 SATYA workbench (Next.js App Router, TS, CSS Modules + tokens.css, React Aria, next-intl, Auth.js/Keycloak)
apps/mock-portal/         "Approval Portal (Mock, for demo)": plain grey demo stand-in that fires signed events
services/api/             FastAPI gateway: /v1/health, /v1/meta, /v1/portal-events (HMAC, dedupe, ledger); Alembic
services/worker/          Celery worker + beat on Valkey (ping task; feature tasks come in later slices)
packages/shared-types/    JSON Schema (source of truth) -> generated TS types + Pydantic v2 models
packages/affidavit/       M5 (P-3) satya_affidavit: extract, normalise, diff, reconcile, flags, engine, eval; synth/ = synthetic PDF generator
packages/forensics/       M6 (P-4, P-18) satya_forensics: pki (TEST TRUST ANCHOR), signatures, stamp, udin, engine, eval; synth/ = signed fixtures + 3 scan cases
packages/ocr/             M3 scan fallback (B-28) satya_ocr: page classifier, hardening, OcrEngine (Fake, PaddleOCR via WITH_OCR), reason codes, synth/ = Pillow scans
packages/templates/       year-versioned template profiles (affidavit-2/aff2-portal-2024-27.yaml; more with M3)
packages/rules/           versioned YAML rules with APH clauses (m5-affidavit.yaml, m6-signatures.yaml; more with M4)
packages/issuers/         placeholder: Annexure-14 issuer profiles (M3/M4 slice)
data/synthetic/           synthetic fixtures only (see its README); cases/ = generated demo cases, pki/ = public test PKI, registry/ = prior filings (make synth)
data/real-samples/        GIT-IGNORED. Never commit, upload, log or open in a cloud session
infra/                    docker-compose.yml, caddy/Caddyfile, keycloak/realm-satya.json, postgres init, scripts/
docs/specs/               given specs (read VERSIONS.md); docs/prompts/ = slice prompts
docs/                     index in docs/README.md: DEV-SETUP, ARCHITECTURE, STACK-VERSIONS, ISSUES; docs/progress/ = PROGRESS*.md, DECISIONS-SLICE-*.md
tests/                    cross-service smoke tests (need the running stack)
.github/workflows/        CI: lint, types, tests, schema regen diff, compose config, gitleaks, real-data guard, smoke
```

## Run, test, lint (from the repo root)
| Task | Command |
|---|---|
| First-time secrets | `make secrets` (writes `.env` from `.env.example` with random values) |
| Start stack | `make up` (Windows without WSL: `pwsh infra/scripts/up.ps1`) |
| Stop / logs / wipe | `make down` · `make logs` · `make reset` (asks before dropping volumes) |
| Install deps | `pnpm install` · `uv sync --all-packages` |
| Regenerate contracts | `make gen-types` (then commit; CI fails on any diff) |
| Lint | `make lint` (eslint + ruff) |
| Typecheck | `make typecheck` (tsc + mypy) |
| Status · logs | `make ps` · `make logs SERVICE=api` |
| Unit tests | `make test` (vitest + pytest, no stack needed) |
| Postgres-backed API tests | `make test-db` (throwaway pgvector container) |
| Integration/smoke | `make smoke` (needs `make up`; `make trust-ca` first for verified TLS) |
| Browser acceptance | `make e2e` (Playwright/Chromium; Caddy CA trusted in NSS, see DEV-SETUP) |
| Ledger chain check | `make ledger-verify` |
| Demo reset (8 synthetic cases, empty ledger, seed) | `make demo-reset` (needs `make up`; demo database only) |
| Synthetic demo cases · check | `make synth` · `make synth-check` (CI fails if stale) |
| M5 metrics (104 synthetic affidavits) | `make eval-m5` (also printed by `uv run pytest packages/affidavit`) |
| M6/P-18 metrics (256 synthetic cases) | `make eval-m6` (also printed by `uv run pytest packages/forensics`) |
| M3 scan fallback tests | `uv run pytest packages/ocr` (FakeOcrEngine; the real-engine test skips without models) |
| Real-data guard · secret scan | `make guard` · `make secret-scan` (same as CI) |
| Memory budget | `make mem-check` (every service limited, total ≤ 8 GB) |

URLs: workbench `https://localhost` · API `https://localhost/api/v1/health` · mock portal `https://portal.localhost` · Keycloak `https://auth.localhost`.

## Data contracts (source of truth: `packages/shared-types/schemas/*.schema.json`; Portal spec §2)
| Contract | Values / fields |
|---|---|
| Verification label (§2.6.3) | `verified`, `mismatch_detected`, `expired`, `verification_pending`, `source_unavailable`, `manual_review_required` |
| Label precedence (document label = most severe) | `mismatch_detected` > `expired` > `manual_review_required` > `source_unavailable` > `verification_pending` > `verified` (exported as `LABEL_PRECEDENCE`) |
| Disposition action (§2.6.5) | `accept`, `override`, `escalate_clarify`, `escalate_refer`, `escalate_manual`; reason ≥ 10 chars |
| Risk band (#20) | `high`, `medium`, `low` (never a 0–100 score; never shown to the institution) |
| YoY verdict | `explained`, `discrepancy` |
| Alert (§2.9) | `type` ∈ `missing_info`, `expired`, `pending_source`, `suspected_anomaly`, `unresolved`, `role`; `subtype` enum per type |
| Event envelope (§2.3) | `spec` = `satya.event/1`, `event_id`, `type`, `occurred_at`, `producer`, `subject{application_id, permanent_id, ay}`, `sequence`, `correlation_id`, `data`; outbound adds `advisory: true`, `regulatory_effect: "none"`, `case_id`, `run_id`, `deep_link` |
| ApplicationSnapshot (§2.6.1) | every field carries `x-handling: K\|T\|X\|R`; **X fields do not exist in the model** (listed only as rejected names) |
| Signature header (§2.2) | `X-SATYA-Signature: t=<unix>,kid=<key-id>,v1=<hex HMAC-SHA256 of "t.body">`, window 300 s |
Generated code: `packages/shared-types/ts/src/generated/` and `packages/shared-types/python/satya_shared_types/generated/`.

Workbench API (slices 1–2, Slice D adds `/v1/cases` queue rows with `risk_band`, `/v1/cases/{id}/review`, `POST /v1/cases/{id}/documents`, `.../documents/pick`, `.../documents/{doc}/file`, `POST .../flags/{flag}/disposition`, `/v1/audit`, `/v1/alerts`; UI polish v0.8 adds `GET /v1/overview?ay=&region=`, sort params `sort`/`dir` on `/v1/cases`, and severity, time, label and source fields on alerts): `GET /v1/cases`, `GET /v1/cases/{case_id}/affidavit-diff`, `GET /v1/cases/{case_id}/verification`, `GET /v1/cases/{case_id}/documents/{doc_id}/verification` (Keycloak access token from `satya-web` as Bearer; RB role; region scope from `/regions/*`; per-user quota). Contracts: `AffidavitDiff`, `CaseVerification`, `VerificationResult`.

## Resume protocol (short)
- Each slice has a prompt in `docs/prompts/` (or the session request) and a progress table (`docs/progress/PROGRESS.md` for slice 0, `docs/progress/PROGRESS-SLICE-<n>.md` after). Continue from the first step not `done`/`done-with-note`; re-verify, never redo a done step blindly.
- One commit per step (message given in the prompt), push after each commit. Update the progress table in `docs/progress/` every step.
- Long commands run in the background with output in `.logs/<step>.log`; never block > ~8 min.
- Blocked: record under "Blockers / questions", take the safest default, mark `done-with-note`.
- Every non-obvious choice: one line in `docs/progress/DECISIONS-SLICE-<n>.md`.

## Current status
Built on synthetic data: slice A (B-28 scan fallback with reason codes SCAN_IMAGE_ONLY, OCR_LOW_CONFIDENCE, OCR_UNAVAILABLE, DOC_UNREADABLE; B-31 UI fixes), UI polish v0.8 (StatusLabel, SourceTag, sortable queue, Overview, severity alerts, user menu), slice 0 foundation, slice 1 M5 affidavit diff (P-3), slice 2 M6 signatures/stamp/UDIN (P-4, P-18). All planted cases are detected on the synthetic test sets (no accuracy percentages are claimed). Everything else is planned.

## Build order for later slices
1. Intake + vault (P-19).
2. Workbench queue, decision bar, alerts, audit (P-10, P-11, P-12).
3. Mock portal complete (P-17).
4. Demo polish + HTTPS tunnel.
5. Then M3 OCR and the rest (M13, M7, M4, M8, M1/M9; decision #40 order).
- Build **only P1 screens** (UI spec §2.8: 31 P1). Phase-2 items stay hidden (no dead navigation).
- A slice waits only for its own spec. Stubs elsewhere point to their P-n issue (`docs/ISSUES.md`).
- **When a spec in `docs/specs/` changes, read `VERSIONS.md` and the diff before continuing.**

## Web-design checklist (condensed from SLICE-0 prompt §4)
- Follow the UI spec design system: dense, document-first, ledger-like. Tokens only from `apps/web/src/styles/tokens.css`.
- Banned: purple/blue gradients, gradient text, emojis in headings, Inter, coloured-border cards by default, glassmorphism, icon-box triplets, badges above headlines, decorative icons, untouched library defaults, fade-in-on-scroll, cursor effects, buttons that fade on hover, em-dash-heavy or buzzword copy, "it's not X, it's Y", serif italic accents, grain, bento grids, orbs/dot grids, sparkles, neon, checkmark bullet lists, fake terminals.
- Every page: unique title + meta description, one H1, breadcrumbs, alt text, no console errors, no placeholder text, no dead links, mobile width without horizontal scroll, skeletons not spinners, visible success/error feedback.
- Accessibility: WCAG 2.1 AA, GIGW 3.0, skip link, visible focus, keyboard-only use, `prefers-reduced-motion`, 200% text resize, status always as text, English + Hindi via next-intl (no hard-coded strings; unsure Hindi marked `[VERIFY]`).
- robots.txt `Disallow: /`; no production source maps; fonts self-hosted.

## Security checklist (condensed)
- Rate limits + body size limits on every endpoint; per-client quotas; generic error messages (RFC 9457), details only in server logs.
- Server-side authorisation on every request; RBAC from Keycloak roles (`RB SC EV HC RA AU INS`); case-scope/region checks before resource access.
- Least-privilege DB roles: `satya_migrator` (DDL) and `satya_app` (DML only).
- Auth only via Keycloak (OIDC code + PKCE); no passwords in our code; HttpOnly + Secure + SameSite cookies; CSRF on state-changing forms; brute-force detection; no default admin.
- Validate all input server-side against shared schemas; HSTS; strict CORS (web + mock-portal origins only); log security events (signature failures, permission denials, failed logins).
- Uploads later: whitelist by extension **and** content. No external paid APIs, no foreign LLM APIs.
- Secrets only in `.env` (git-ignored). CI runs gitleaks and the real-data guard on every push.
