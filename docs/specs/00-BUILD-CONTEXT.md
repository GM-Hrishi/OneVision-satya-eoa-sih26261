# SATYA-EoA: build context (decisions, guard rails, promise list)
Repo copy of the team's planning status (MASTER-status v15, 25 Oct 2026), reduced to what a builder needs. Team: OneVision (one 6-member team). Problem statement: SIH26261 (AICTE Regulation Bureau, Software, Smart Automation).

## Guard rails (non-negotiable)
1. **AI advises, officials decide.** No approve/reject/auto-clear control anywhere. Every outbound event carries `advisory: true`, `regulatory_effect: "none"`.
2. **Mock portal only.** Never claim real integration with, or access to, the AICTE portal or AICTE data. Every "portal sends" item is a proposed hook that our mock portal implements.
3. **Synthetic data only** in the repo, tests, fixtures, screenshots and demo. Real sample PDFs live only on the team's laptop under `data/real-samples/` (git-ignored) and never enter a cloud session, a commit, a log or an issue.
4. **No personal data** anywhere: no names, phone numbers, emails, Aadhaar/PAN, DOB, signatures, real application IDs. Use patterns like `1-##########` or obviously synthetic values (`1-90000004217`, "Demo Institute of Technology 03").
5. **No real institution names** in code, data, docs, issues, commits or UI.
6. **APH clause citations** on every rule and flag; anything unconfirmed is marked `[VERIFY]` in code comments and docs.
7. **No foreign LLM APIs in the product.** Self-hosted, India-hosted in production. (Claude Code as a dev tool is fine.)
8. **Never duplicate the portal's own checks (design D2):** Deficiency Report norm arithmetic, within-portal faculty duplicate flag, PAN validation. Import their results; never recompute or claim them.
9. **Never colour alone:** every status shows its text label.
10. Demo signatures are tagged "TEST TRUST ANCHOR"; mock adapter results are tagged "MOCK SOURCE".

## Key decisions (numbering from the planning log)
| # | Decision |
|---|---|
| 4 | API-first REST + webhook + SSO-linked workbench; prototype against a MOCK portal |
| 5 | Stack: Next.js + PDF.js; FastAPI (Python); PaddleOCR; pikepdf / qpdf / pyHanko; PostgreSQL + NetworkX (Apache AGE later); pgvector + perceptual hashing; Celery + Valkey; Keycloak; Docker; Caddy |
| 9 | Monorepo layout: `apps/web`, `apps/mock-portal`, `services/api`, `services/worker`, `packages/templates`, `packages/rules`, `packages/issuers`, `packages/shared-types`, `data/synthetic`, `data/real-samples` (git-ignored), `infra`, `docs`, `tests` |
| 10 | No mobile app; web over HTTPS on default browsers |
| 13 | Affidavit-2 = 24 declarations (19 core + 5 existing institute), 4 room tables + land table; normalised diff per AY + application ID |
| 14 | Portal Application Report = the reference data for reconciliation (Portal spec §2.6.1) |
| 15 | Classify documents by body text / issuer, never by heading, filename or uploader label |
| 16 | Two signature checks (issuer vs uploader); an image-only "digitally signed" mark is never verified |
| 17 | Phase 1 demo is Tamil Nadu-first (TN fire licence + TN Form D, as mock adapters) |
| 19 | Stage ① pre-check is private to the institution; never used in risk scoring |
| 20 | Risk shown as High/Medium/Low band with contributing flags, never a 0–100 score; 5 dispositions (accept, override, escalate_clarify, escalate_refer, escalate_manual); PGRC/SCSC out of v1 |
| 22 | TN adapters are mocks that mirror fields printed on real licences; live lookup is a flagged Phase 2 adapter |
| 25 | Styling: CSS Modules + CSS custom properties (`tokens.css`) + React Aria Components + next-intl (English + Hindi) |
| 27 | Portal API contract v0.2 adopted (Portal spec §2) |
| 28 | `source_unavailable` creates a manual task; a valid uploader DSC never makes a document "verified" |
| 29 | UI screens tagged 31 P1 / 19 P2 / 3 later (UI spec §2.8); build P1 only |
| 31 | Untrusted chain or signer mismatch → "manual review required"; "mismatch detected" only for broken digest, edit after signing, revoked certificate |
| 34 | Tokenisation key: gateway's own key in the demo; AICTE-held key in production |
| 37 | Developer laptop: Windows 11 + Docker Desktop (WSL2); 16 GB RAM, so compose memory limits matter |
| 38 | Hosting: (A) dev via docker-compose; (B) HTTPS tunnel labelled "demo hosting"; (C) India-region VM + Caddy + domain later |
| 40 | Build order after slice 0, hardest first among slices whose specs are ready: M5 affidavit diff → M6 signatures/stamp chronology → M3 template-aware extraction engine (synthetic templates) → M13 year-over-year → M7 source adapters (mocks) → M4 APH date rules → M8 identity graph → M12 audit ledger → M11 workbench screens → mock portal → M1 router / M9 coordinates |

## Promise list (each deck claim → one GitHub issue)
| # | Claim | Module | Phase |
|---|---|---|---|
| P-1 | Category router: Table 2.3 → Annexure-2 checklist | M1 | 1 |
| P-2 | Template-aware extraction, year-versioned templates, content-based classifier | M3 | 1 |
| P-3 | Affidavit 2 normalised 24-declaration diff + Application Report reconciliation | M5 | 1 |
| P-4 | Real DSC vs image; CCA chain (test anchor); signer check; edited-after-signing; stamp chronology; notary-seal expiry | M6 | 1 |
| P-5 | Source verification with the 6 PS labels (CCA offline; SHCIL, TN Form D, TN fire QR as mocks) | M7 | 1 |
| P-6 | Annexure-14 issuer + height/area checks on OC, Form D, fire licences | M3/M4/M9 | 1 |
| P-7 | APH date rules incl. compliance window | M4 | 1 |
| P-8 | Year-over-Year Reconciliation | M13 | 1 |
| P-9 | Pseudonymised identity graph; Faculty ID update lag (6.14c) | M8 | 1 |
| P-10 | Evidence-linked flags + 5 dispositions | M11 | 1 |
| P-11 | Hash-chained audit trail + case replay | M12 | 1 |
| P-12 | Dashboard + alerts (type + subtype enum) | M11 | 1 |
| P-13 | Coordinates + ≤3 plots ≤2 km (imagery Phase 2) | M9 | 1 |
| P-14 | Risk band (Phase 1); risk-ranked EVC selection (Phase 2) | M10 | 2 (band 1) |
| P-15 | EVC video compliance | M9 | 2 |
| P-16 | Formats 1–3; Certificate 2 ↔ affidavit rooms | M3/M5 | 2 |
| P-17 | Mock portal + proposed webhooks + SSO hand-off; private pre-check | Portal §7 | 1 |
| P-18 | UDIN structure check | M6/M7 | 1 |
| P-19 | M2 secure vault + redaction/tokenisation on ingest | M2 | 1 |

## Known open conflicts a builder should respect
- Design v2.3 (pending) restores the tiered institution-visibility rule; until then follow UI spec §1.1.
- TN Fire Service Act 1985 is to be repealed by a 2025 Act (commencement not notified) [VERIFY]: version fire rules by Act.
- Identifiers extracted from documents in the vault (e.g. deed numbers) are masked by default in the UI with a logged reveal (Portal §3, pending).
- Specs still being written: Portal §3–§7, UI §10 build handoff. Build only what the current specs define; leave clearly marked TODOs elsewhere.
