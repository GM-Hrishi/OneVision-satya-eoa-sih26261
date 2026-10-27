# Stack versions (slice 0)
Exact versions pinned on 26 Oct 2026, checked against the registries (Docker Hub, npm, PyPI) at build time, not from memory. Every image is pinned by tag (never `latest`). Lockfiles (`pnpm-lock.yaml`, `uv.lock`) pin the full dependency trees.

## Container images
| Service | Image | Notes |
|---|---|---|
| postgres | `pgvector/pgvector:0.8.7-pg18` | PostgreSQL 18 + pgvector 0.8.7 |
| valkey | `valkey/valkey:9.1.2-alpine` | Celery broker (db 0) + results (db 1) |
| keycloak, keycloak-config | `keycloak/keycloak:26.8.1` | Docker Hub mirror published by the Keycloak project (quay.io unreachable from the build VM) |
| caddy | `caddy:2.11.7-alpine` | |
| api, migrate, worker (base) | `python:3.13.17-slim-trixie` | Python 3.13.17 |
| web, mock-portal (base) | `node:24.22.1-alpine` | Node 24 LTS |
| CI secret scan | `zricethezav/gitleaks:v8.30.1` | |

## Toolchain
| Tool | Version |
|---|---|
| uv | 0.11.32 (also installed in the Python builder images) |
| pnpm | 10.28.0 (`packageManager` in `package.json`) |
| Node (CI, images) | 24 (24.22.1 in images) |
| Docker Engine / Compose (build VM) | 29.9.2 / 5.6.1 |
| Playwright (browser acceptance) | 1.64.1 |

## JavaScript (npm)
| Package | Version | Used in |
|---|---|---|
| next | 16.4.3 | web, mock-portal |
| react, react-dom | 19.3.1 | web, mock-portal |
| typescript | 6.0.3 | all (7.0 not used: typescript-eslint supports `<6.1`) |
| next-auth | 4.24.15 | web (stable; v5 still beta) |
| next-intl | 4.14.9 | web |
| react-aria-components | 1.22.1 | web |
| @fontsource/public-sans · noto-sans-mono · noto-sans-devanagari | 5.3.0 | web (self-hosted fonts) |
| eslint | 9.39.5 | all (10.x not used: React/jsx-a11y plugins lack support) |
| eslint-config-next | 16.4.3 | web, mock-portal |
| typescript-eslint · @eslint/js | 8.72.0 · 9.39.5 | shared-types |
| vitest · vite | 5.0.5 · 8.3.5 | all |
| json-schema-to-typescript | 16.0.0 | shared-types generator |
| ajv · ajv-formats | 8.20.0 · 3.0.1 | shared-types tests |
| @types/node · @types/react · @types/react-dom | 24.19.2 · 19.3.0 · 19.3.0 | |

## Python (PyPI)
| Package | Version | Used in |
|---|---|---|
| fastapi (starlette) | 0.162.0 (1.10.0) | api |
| uvicorn[standard] | 0.54.0 | api |
| pydantic · pydantic-settings | 2.14.1 · 2.16.1 | api, shared-types |
| sqlalchemy[asyncio] | 2.1.6 | api |
| psycopg[binary] | 3.3.6 | api |
| alembic | 1.20.1 | api (migrate job) |
| redis | 6.4.0 | api, worker (kombu requires `<6.5`) |
| httpx | 0.28.1 | api (health check), tests |
| python-ulid | 4.0.1 | api |
| jsonschema · rfc3339-validator | 4.26.0 · 0.1.4 | shared-types validation |
| celery[redis] (kombu) | 5.6.3 (5.6.2) | worker |
| pdfplumber (pdfminer.six, pypdfium2) | 0.11.10 (20260107, 5.14.0) | affidavit (M5 text-layer extraction), forensics (M6 stamp/notary/mark/UDIN text), api |
| pyyaml | 6.0.3 | affidavit (template profiles, rules) |
| pyjwt[crypto] (cryptography) | 2.15.1 (50.0.2) | api (Workbench API bearer tokens, RS256 + JWKS); cryptography also forensics (test PKI, chain, CRL) |
| reportlab | 5.0.1 | synthetic PDF generator only (dev group; never in a runtime image). 5.1.0 skipped: released 4 days before the slice |
| types-pyyaml | 6.0.12.20260906 | mypy |
| pikepdf | 10.17.0 | worker (for M6) |
| pyhanko (pyhanko-certvalidator, asn1crypto) | 0.38.0 (0.33.0, 1.5.1) | forensics (M6 signature validation + modification analysis; synthetic signing in `synth/`), api. MIT |
| datamodel-code-generator (black, isort) | 0.86.0 (26.10.1, 8.0.1) | shared-types generator |
| ruff · mypy | 0.17.2 · 2.4.0 | lint, types |
| pytest · pytest-asyncio | 9.1.1 · 1.4.1 | tests |
| hatchling | 1.32.4 | build backend |

## GitHub Actions
`actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v7`, `pnpm/action-setup@v6` (latest major tags at build time).

## Updating
Bump a version in one place (image tag in `infra/docker-compose.yml` / Dockerfile `ARG`, or the manifest + lockfile), run `make test` and `make up && make smoke && make e2e`, then update this table in the same commit.

| Library (workbench) | Version | Notes |
|---|---|---|
| pdfjs-dist | 5.7.284 (Apache-2.0) | Slice D evidence viewer; worker served from the workbench origin |
