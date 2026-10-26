# Decisions — Slice 0
One line per non-obvious choice, with the reason. Newest at the bottom of each section.

## Process
- Branch: work is on `claude/pensive-rubin-eudosj`, not `slice-0-foundation`, because the cloud session that ran this slice may push only to its assigned branch; the PR goes from that branch. Rename on merge if the team wants the prompt's name.
- Docker daemon is not running by default in the cloud VM; started with `dockerd` in the background (documented in DEV-SETUP cloud note).

## Versions and toolchain
- TypeScript pinned to 6.0.x, not 7.0.x: `typescript-eslint` 8.72 supports `<6.1.0` only.
- ESLint pinned to 9.39.x, not 10.x: `eslint-plugin-react` and `eslint-plugin-jsx-a11y` (via `eslint-config-next`) do not yet declare ESLint 10 support.
- Auth library: `next-auth` 4.24.x (stable) with the Keycloak provider; Auth.js v5 is still beta (5.0.0-beta.x), so it is not used for a government-facing build.
- Node 24 LTS (`node:24.22.1-alpine`) for the Next.js images; Python 3.13 (`python:3.13.17-slim-trixie`) for api/worker (prompt asks 3.12+; 3.13 has wheels for pikepdf/pyHanko).
- PostgreSQL 18 via `pgvector/pgvector:0.8.7-pg18` (prompt: 16 or newer).
- Valkey 9.1 (`valkey/valkey:9.1.2-alpine`); Keycloak 26.8 from `quay.io/keycloak/keycloak` (the official registry); Caddy 2.11.

## Monorepo
- JS: pnpm workspaces (`apps/*`, `packages/shared-types`); Python: uv workspace (`services/api`, `services/worker`, `packages/shared-types/python`), one root `uv.lock`. uv chosen over Poetry because it is available, faster in Docker builds and supports workspaces natively.
- `packages/templates|rules|issuers` are README-only placeholders, not workspace members, until their slices give them code.
- `packages/shared-types` holds both the TS package (root `package.json`, code in `ts/`) and the Python package (`python/`), so schemas, TS and Pydantic stay side by side.
- Synthetic ID range: application/permanent IDs starting `1-9…` are reserved for demo data, so a real-looking ID in a fixture stands out in review.

## Shared types (S0.3)
- One file per contract under `packages/shared-types/schemas/`; the generator bundles them into one document with flat `$defs` so TS and Pydantic each get exactly one definition per type (no duplicates across files).
- TS generation strips `x-*` annotations and `if/then` blocks (TS cannot express them and they cause numbered duplicate aliases); those rules stay enforced by JSON Schema validation (ajv in TS, `jsonschema` in Python), which is what the gateway uses.
- `Timestamp` / `Date` use `format` only (no `pattern`): Pydantic maps them to `AwareDatetime` / `date` and rejects patterns on those types; `rfc3339-validator` makes `jsonschema` enforce the offset.
- `ApplicationSnapshot` is the **wire** shape the portal sends: T fields hold the raw value (e.g. `trustees[].name`) with `x-token-field` naming the stored token; the stored, tokenised shape arrives with M2 (P-19). In production AICTE would tokenise first (key custody, Portal §2.6.1).
- `ApplicationSnapshot` and its groups use `additionalProperties: false` (data minimisation beats the "ignore unknown fields" rule here); the envelope itself allows unknown top-level fields (Portal §2.12).
- Envelope `data` is a generic object in slice 0; per-type payload schemas arrive with the slices that consume them.
- Outbound-only rule (`advisory: true`, `regulatory_effect: "none"`) is a schema `if/then` keyed on `OutboundEventType`, so no outbound event can validate without it (guard rail 1).
- Pydantic generated with `datamodel-code-generator` (`--formatters black isort` pinned explicitly); TS with `json-schema-to-typescript`. Generated code is committed; `make check-types-diff` (and CI) fail on drift.
- Synthetic faculty IDs use 11 digits (`1-90000000101`) so they never match the 10-digit mobile pattern in the real-data guard.

## API gateway (S0.4)
- Signature check order: parse → HMAC (constant-time, computed even for unknown kids so timing does not reveal valid kids) → timestamp window. A correctly signed old event gets `SIGNATURE_EXPIRED`; a tampered one always gets `SIGNATURE_INVALID`.
- Inbound auth in slice 0 is the HMAC signature per `kid`. The OAuth client-credentials check for `portal-integration` (Portal §2.0) is deferred to the Portal §5/§6 slice (spec pending); the Keycloak client already exists.
- Only inbound event types are accepted on `/v1/portal-events`; an outbound type gets `UNSUPPORTED_EVENT_TYPE`.
- If `data.snapshot` is present, X fields are refused with `403 PERSONAL_DATA_REJECTED` and the snapshot is schema-validated (Portal §2.2 data minimisation). Tokenisation (T) is not needed yet because slice 0 stores no payloads, only metadata + SHA-256 of the raw body.
- Dedupe and ledger append run in one transaction under `pg_advisory_xact_lock`, so concurrent events cannot fork the chain or double-insert. Rows older than 30 days are dropped on re-receipt (the daily purge comes with the worker sweep).
- Ledger `at` is canonicalised as UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ` before hashing; Postgres `timestamptz` keeps microseconds so verification is exact. The table is append-only by trigger and by grants (runtime role has no UPDATE/DELETE).
- Rate limiting is a small fixed-window limiter on Valkey (per IP on every endpoint, per `kid` after signature verification) with an in-process fallback, instead of slowapi, whose decorator model needs a `request` parameter on every route.
- Body limit middleware buffers at most `SATYA_MAX_BODY_BYTES` (+1) and returns 413 for declared or streamed bodies; Caddy enforces the same limit at the edge.
- Least privilege: `satya_migrator` owns schema objects and is used only by a one-shot `migrate` job; `satya_app` (api/worker) gets per-table SELECT/INSERT (+DELETE on dedupe) from the migration.
- `redis` (redis-py) is used as the Valkey client in api and worker because Celery/kombu's transport requires it; Valkey is protocol-compatible.
- Swagger/ReDoc are disabled (CSP and internal tool); `/v1/openapi.json` is served only when `SATYA_ENV=dev`.
- `415 UNSUPPORTED_MEDIA_TYPE` for non-JSON bodies and `405 METHOD_NOT_ALLOWED` are used in addition to the §2.13 table.

## Worker (S0.5)
- `redis` (redis-py) pinned to 6.4.0 in api and worker: `kombu[redis]` 5.6 (Celery 5.6.3) requires `redis<6.5`, and the uv workspace keeps one version.
- Celery broker on Valkey db 0, results on db 1; JSON-only serialisation (`accept_content=["json"]`) so no pickle deserialisation from the broker.
- Worker and beat run in one container (`worker --beat`): one replica in the demo, so no duplicate schedules. Split beat out before scaling workers.
- pikepdf and pyHanko are installed now (light, wheel-only); PaddleOCR waits for the M3 slice as the prompt says.
- Each Python service's tests run in a separate pytest invocation (two `tests` packages would collide in one session).

## Infra (S0.6)
- Compose file lives in `infra/docker-compose.yml` (project name `satya`); the Makefile always passes `--env-file .env`. Build contexts are the repo root so the uv and pnpm workspaces resolve.
- Two networks: `backend` (internal, no egress: postgres, valkey, keycloak, worker, migrate) and `edge` (caddy, api, web, mock-portal). Only Caddy publishes ports (80 → 308 redirect, 443).
- Two one-shot jobs besides the 8 services: `migrate` (Alembic as `satya_migrator`) and `keycloak-config` (sets secrets/passwords from `.env`). Both have memory limits and exit 0; `make up` waits for them.
- Keycloak runs `start` (production mode, not `start-dev`) behind Caddy with `KC_HOSTNAME=https://auth.localhost` and `KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true`, so browsers use the public URL and containers use `http://keycloak:8080` while tokens keep the public issuer.
- Keycloak image from Docker Hub `keycloak/keycloak` (published by the Keycloak project) because `quay.io` was unreachable from the build VM; same tag on both registries.
- Caddy blocks `/admin` on `auth.localhost` (no admin console at the edge) and tightens Keycloak's `frame-ancestors 'self'` to `'none'`. Apps set their own nonce-based CSP; Caddy adds a strict fallback CSP only when the upstream sends none.
- `tls internal` with Caddy's local CA; `make trust-ca` exports the root certificate (git-ignored) for one-time trust in the OS/browser.
- Internal hops (mock-portal → api, web → api/keycloak) are plain HTTP on the private Docker network; the browser-facing path is HTTPS only. Production would use mTLS (Portal spec V-9).
- Build-time TLS proxy support: an optional BuildKit secret `extra_ca` (empty file by default). `make secrets` copies a bundle given in `SATYA_EXTRA_CA_FILE` into `infra/certs/` (git-ignored) because compose only reads secret files inside the project. Never baked into an image.
- uv is installed in the builder stage from PyPI (`pip install uv==0.11.32`) rather than copied from `ghcr.io/astral-sh/uv`, because ghcr.io blob downloads were blocked in the build VM.
- Valkey password is passed on the `valkey-server` command line (visible only inside that container); an ACL file can replace it before shared hosting.
- Memory limits: postgres 768m, valkey 256m, keycloak 1280m, api 512m, worker 768m, web 768m, mock-portal 512m, caddy 128m, migrate 256m, keycloak-config 512m = 5.62 GiB (`make mem-check`, also in CI).

## Keycloak (S0.7)
- Realm JSON holds no secrets or credentials. `keycloak-config` (one-shot, kcadm) sets the three client secrets and one shared demo password from `.env` after Keycloak is healthy; it is idempotent.
- `satya-web` and `satya-mock-portal` are confidential clients (server-side sessions) that also require PKCE S256. Redirect URIs are the exact callback (`https://localhost/auth/callback/keycloak`, `https://portal.localhost/auth/callback/keycloak`) rather than `/*`: stricter than the prompt's pattern, same host. Post-logout redirect is `https://<host>/*`.
- Auth.js runs under `/auth` (not the default `/api/auth`) because Caddy routes `https://localhost/api/*` to the FastAPI gateway.
- Region is modelled as a group (`/regions/southern`, `/regions/national`) mapped to a `groups` claim; Keycloak 26's declarative user profile drops unmanaged attributes on import, and groups need no profile change. Roles go to a flat `roles` claim.
- Password policy: length 14, upper, lower, digit, special, not username, not email. `passwordHistory` is left out so the post-start script can set the same demo password on every run.
- Brute-force detection on (5 failures, temporary lockout up to 15 min), self-registration and password reset off, login with email off, login/admin events stored 30 days.
- Demo users: `rb.southern.demo`, `rb.national.demo`, `sc.demo`, `ev.demo`, `hc.demo`, `ra.demo`, `auditor.demo`, `institution.demo03`; first name "Demo", emails `@example.invalid`.
- The bootstrap admin (random username/password from `.env`) stays as Keycloak's temporary admin for local use; there is no committed default credential and `/admin` is not routed through Caddy.
- `tests/oidc_login_check.py` maps `*.localhost` to loopback inside the script (glibc does not, browsers and curl do) and bypasses the HTTP proxy for local names.

## Workbench (S0.8)
- next-auth v4 under `/auth`; sign-in starts with `signIn("keycloak")` (CSRF-protected POST) from a small client component, which auto-starts once and keeps a button as fallback. Session = encrypted JWT cookie (`__Secure-` prefix, HttpOnly, Secure, SameSite=Lax), 30 min, holding only username, roles, regions and the id_token for logout; no tokens reach browser JS. A server-side session store is not needed until the workbench calls the API with user tokens.
- Sign-out is a plain form POST to `/signout` (route handler, Origin check) that clears the Auth.js cookies and 303-redirects to Keycloak's end-session endpoint. A server action could not be used: the client router did not follow an external redirect.
- Authorisation is server-side: `requireRole()` in `rb-queue/layout.tsx` (before `loading.tsx` streams, so 307/403 are real status codes) and again in the page. `forbidden()` (Next `authInterrupts`) renders the 403 "Not assigned to you" page with HTTP 403.
- Non-RB workbench roles land on `/home` ("no screens for this role in this build"); INS users get the 403 page with an institution-specific line. No rail item points at an unbuilt screen (RB-09 manual verification and SH-04 alerts join with their slices).
- CSP is set per request in `src/proxy.ts` with a nonce (`script-src 'nonce-…' 'strict-dynamic'`, `style-src 'self' 'nonce-…'`, `style-src-attr 'unsafe-inline'` for React Aria's inline style attributes). React Aria's injected `<style>` picks the nonce up from `<meta name="csp-nonce" nonce=…>`. All pages are dynamic so every response gets a fresh nonce.
- next-intl without locale routing: language in an HttpOnly `NEXT_LOCALE` cookie set by a server action (Origin-checked by Next). English and Hindi files share keys (tested); unsure Hindi strings are listed in `messages/hi.review.json` with `[VERIFY]` rather than shown on screen.
- `react/jsx-no-literals` (ESLint) enforces "no hard-coded UI strings".
- Fonts via `@fontsource/*` packages, bundled and served from `/_next/static/media` (no font CDN).
- `tokens.css` is generated from `src/styles/tokens.json`; the generator fails if any colour in the UI spec §8 token summary line is missing (checked in `pnpm build` and the unit tests). The Docker build runs `next build` directly because `docs/` is not in the build context.
- SEO items (sitemap.xml, structured data, llms.txt, OG images, Search Console) are N/A for the authenticated workbench: robots.txt disallows everything and pages carry `noindex, nofollow`. They apply only to public README material.
- Images: the only image is an SVG favicon (no raster images yet, so WebP compression is N/A for now).
- Mobile: below 1024px the rail becomes a React Aria `DialogTrigger` + `Popover` menu, and the language switcher moves to the footer.
- Browser acceptance (`tests/e2e/workbench.cjs`, Playwright/Chromium) trusts Caddy's root CA in the browser's NSS store (as a user would once) instead of ignoring TLS errors. Only the 200% text check uses a CSP-bypassing context, to inject the root font-size rule.

## Mock portal (S0.9)
- One page ("Send test event") with four demo controls: new event, the same event again (duplicate), the same event with a tampered signature, and with a 10-minute-old timestamp. This makes acceptance criteria 4 and 5 visible in the UI, not just in scripts.
- The event's `data.snapshot` is the shared synthetic example (`packages/shared-types/examples/valid/ApplicationSnapshot.json`), so the mock portal, the schemas and the gateway's snapshot validation all use one fixture. Types come from `@satya/shared-types`.
- Signing runs in a server action; the HMAC secret never reaches the browser. The previous event body travels in React action state so "send again" re-sends the exact bytes.
- Plain grey style (UI spec wireframe greys `#E9E9E9/#FAFAFA/#9E9E9E`, Arial), no images at all, banner "Demo stand-in. Not an AICTE system. Synthetic data only." Status shown as text (ACCEPTED/REJECTED) beside the HTTP code.
- No sign-in on the mock portal yet (MP-01 arrives with the mock-portal slice); the `satya-mock-portal` Keycloak client is ready for it.

## CI (S0.10)
- One workflow, seven jobs: `js`, `python` (incl. Postgres-backed tests via `infra/scripts/test-db.sh`), `contracts` (regenerate + `git diff --exit-code`), `compose` (config, memory budget, Caddyfile validate), `secret-scan`, `real-data-guard`, `smoke` (full `make up`, `make smoke`, browser acceptance with Playwright).
- gitleaks runs from its Docker image over the full git history (not `gitleaks-action`, which needs a licence key for organisation repos). `.gitleaks.toml` extends the default rules and allow-lists only two exact synthetic test strings, never a path.
- Real-data guard is a shell script shared by CI and `make guard`; allow-list entries need a path glob, the exact matched text and a reason. Lockfiles and binary assets are skipped (registry hashes, not people's data). Verified by planting a tracked file under `data/real-samples/` and a mobile/PAN/Aadhaar-like value: all four were caught.
- Actions pinned to major tags current at build time (checkout v7, setup-node v7, setup-uv v7, pnpm/action-setup v6).

## Backlog (S0.11)
- `gh` CLI present but its token is invalid in the cloud session, so the prompt's fallback was used: `docs/ISSUES.md` + `infra/scripts/create-issues.sh`. Creating issues through other GitHub tooling was not attempted because it is an outward-facing action the prompt routes to the team's laptop.
- One source (`docs/backlog/promises.json`) renders both the Markdown and the `gh` calls (`infra/scripts/issues.py`), so they cannot drift. The script creates labels with `--force` and skips titles that already exist.
- P-14 carries both `phase-1` (risk band) and `phase-2` (EVC selection) labels.

## Team answers (26 Oct 2026, after slice 0 review)
- Licence: none until the repo goes public; then Apache-2.0 if the SIH rules allow it.
- GitHub issues: skipped for now; slices reference P-n IDs from `docs/ISSUES.md`. The team lead creates them later with `gh auth login` + `infra/scripts/create-issues.sh`.
- Priorities: defaults kept (M2/P-19 `prio-3`, M10/P-14 `prio-9`).
- Next slice: M5 affidavit diff (P-3, prio-1), prompt supplied in a new session.
- Hindi: the team lead names one reviewer (open item); review of `apps/web/messages/hi.review.json` before the first demo rehearsal.
