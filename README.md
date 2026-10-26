# SATYA-EoA
**Decision support for AICTE Extension of Approval (EoA) scrutiny.** SATYA-EoA reads the documents an institution submits, checks each one at its official source where one exists, and compares what was sworn with the portal's own data and earlier years. It gives officials evidence-linked, advisory findings. Officials make every decision.

Smart India Hackathon 2026 · problem statement **SIH26261** · **Team OneVision**

## What this prototype is, and is not
- **Advisory decision support.** There is no approve, reject or auto-clear control anywhere; every outbound event carries `advisory: true`, `regulatory_effect: "none"`.
- **Officials decide.** Every finding needs a recorded human disposition with a reason.
- **Runs against a mock portal** that the team built ("Approval Portal (Mock, for demo)"). It shows the hooks a real portal would need; it is not a real integration.
- **Synthetic data only.** No real institutions, people, IDs or documents.
- **Not affiliated with, endorsed by or connected to AICTE.**

## Architecture
```mermaid
```mermaid
flowchart LR
  subgraph EXT[Outside SATYA]
    MP[Mock approval portal<br/>demo stand-in, synthetic data]
    AP[AICTE portal<br/>future, same hooks]:::proposed
  end
  subgraph SATYA[SATYA-EoA, self-hosted in India]
    WB[Workbench<br/>Next.js + PDF.js]
    GW[Gateway FastAPI + Keycloak SSO<br/>router, pseudonymise, signed webhooks]
    subgraph WK[Workers: Celery + Valkey]
      M2[M2 Vault + redact] --> M3[M3 Template parse]
      M3 --> M5[M5 Affidavit diff]
      M3 --> M6[M6 DSC + stamp]
      M3 --> M4[M4 APH rules]
      M3 --> M7[M7 Source checks]
      M3 --> M8[M8 Identity graph]
      M3 --> M13[M13 Year-over-year]
      M3 --> M9[M9 Location]
      M5 & M6 & M4 & M7 & M8 & M13 & M9 --> M10[M10 Risk band]
    end
    DB[(PostgreSQL<br/>pgvector, NetworkX)]
    LG[(M12 audit ledger<br/>hash-chained)]
  end
  subgraph SRC[Issuing sources]
    CCA[CCA / DSC chain]
    SH[SHCIL e-Stamp]:::proposed
    FD[TN Form D]:::proposed
    FI[TN fire licence]:::proposed
    UD[ICAI UDIN]:::proposed
  end
  MP -- SSO link --> WB
  MP -- signed events --> GW
  GW --> WK
  WB <--> GW
  M10 --> DB
  WK --> LG
  M7 --> CCA & SH & FD & FI & UD
  classDef proposed stroke-dasharray: 5 4
```
```
Legend: dashed = mock adapter or proposed hook in the demo. CCA/DSC is a real offline check (against a test anchor on synthetic documents).

Slice 0 runtime details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start
Needs Docker (with Compose), `make` and `python3`. On Windows use WSL2: see [docs/DEV-SETUP.md](docs/DEV-SETUP.md).
```bash
make secrets     # random secrets into .env (git-ignored)
make up          # build, start all services, wait until healthy
make trust-ca    # export the local HTTPS root CA once, then trust it (DEV-SETUP)
```
Then open **https://localhost** and sign in as `rb.southern.demo`: the queue lists two synthetic cases; open *Affidavit diff* for `1-90000004217` to see RB-05 (`docs/DEMO-SCRIPT.md` has the full demo) (password: `grep DEMO_USER_PASSWORD .env`). The mock portal is at **https://portal.localhost**: press *Send test event* and watch the signed event get a receipt.

## Status
| Slice | Scope | Status |
|---|---|---|
| 0 Foundation | Monorepo, compose stack with HTTPS, shared contracts, signed event gateway + hash-chained ledger, Keycloak SSO, workbench shell, mock portal test event, CI with secret scan and real-data guard | Built |
| 1 M5 | Affidavit 2 diff and reconciliation (P-3), RB-05 DiffView; all planted cases detected on synthetic test sets | Built on synthetic data |
| 2 M6 | Real signature vs image, test trust anchor, stamp chronology, UDIN (P-4, P-18), RB-05/RB-06 badges; all planted cases detected on synthetic test sets | Built on synthetic data |
| Intake + vault | Document intake and vault (P-19) | Planned |
| Workbench | Queue, decision bar, alerts, audit (P-10, P-11, P-12) | Planned |
| Mock portal | Complete screens and events (P-17) | Planned |
| M3 | Template-aware extraction and OCR on synthetic templates (P-2, P-6) | Planned |
| M13, M7, M4, M8 | Year-over-year (P-8), source adapters (P-5), APH date rules (P-7), identity graph (P-9) | Planned |
| M1 / M9 | Category router, coordinates (P-1, P-13) | Planned |

Build order follows decision #40 (hardest first). The backlog is in [docs/ISSUES.md](docs/ISSUES.md).

## Repository
| Path | Contents |
|---|---|
| `apps/web` | SATYA workbench (Next.js) |
| `apps/mock-portal` | Approval Portal (Mock, for demo) |
| `packages/affidavit` | M5 affidavit diff engine + synthetic Affidavit 2 generator (`satya_affidavit`) |
| `services/api` | FastAPI gateway |
| `services/worker` | Celery worker on Valkey |
| `packages/shared-types` | JSON Schema contracts → TypeScript + Pydantic |
| `infra` | Docker Compose, Caddy, Keycloak realm, scripts |
| `docs` | Specs, setup, architecture, versions, decisions, backlog |

Working on the code: start with [CLAUDE.md](CLAUDE.md) (rules and commands), then [docs/DEV-SETUP.md](docs/DEV-SETUP.md).

## Licence
None yet. The team plans Apache-2.0 when the repository goes public, if the SIH rules allow it.
