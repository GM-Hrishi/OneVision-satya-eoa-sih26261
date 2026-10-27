# Slice D progress (demo-complete flow)
Branch: `demo-slice` (from origin/main 5f4f46f). Resume rule: continue from the first step not DONE; re-verify, never redo.
Git identity: kept as configured in this environment (owner instruction, overrides the prompt's rule).

| Step | Status | Commit | Notes |
|---|---|---|---|
| D0 Orient, branch, progress + decisions files | DONE | see git log | Existing code mapped in DECISIONS-SLICE-D.md |
| D1 Demo seed + reset (5 cases) | DONE | 53b417c | 5 cases via existing generators; ledger columns; seed; make demo-reset (not run here, no Docker) |
| D2 Upload / pick flow, M5+M6 stored per case | DONE | dd0433a | upload + pick endpoints and screen; M5/M6 rerun; stored in ledger; PDF-only checks |
| D3 Mock source hub, 6 labels, manual task | DONE | dd0433a | 3 mock adapters, 6 labels, manual task entries |
| D4 Queue with risk band; case view | DONE | see git log | queue band/sort/filter; case view. RECORDABLE-A |
| D5 Flags, evidence, template why, PDF at region | DONE | see git log | flags with rule id, APH clause, extracted vs expected, page region, template why; PDF.js viewer opens at region |
| D6 Decision bar (5 dispositions) to ledger | DONE | see git log | 5 dispositions, reason required, written to ledger. RECORDABLE-B |
| D7 Audit view + chain verification; alerts panel | DONE | see git log | audit view with recomputed chain + entry details; alerts panel |
| D8 Wrap-up: notes, checklist, README, CI, PR | DONE | see git log | DEMO-NOTES, DEMO-CHECKLIST, README section; full local CI run below; PR opened, not merged |

## Blockers / questions
- No Docker daemon in the cloud session: `make demo-reset`, `make up` and `make e2e` were not run here. See DECISIONS D-16 for what was verified instead.

RECORDABLE-A reached after D4 (queue + case view with labels).
RECORDABLE-B reached after D6 (decision bar writing to the ledger).

## Full local CI run (D8, cloud session, no Docker daemon)
lint (eslint + ruff check + ruff format --check) pass; typecheck (tsc + mypy src) pass; `make guard` pass; `make synth-check` pass (5 cases); `make check-types-diff` pass; `make config` pass (after `make secrets`); `make mem-check` 5.62 GiB of 8; `make test`: shared-types 31, mock-portal 2, web 11, py shared 38, api 71 passed + 3 skipped (Postgres-only), worker 4, affidavit 63, forensics 111. Postgres-backed store tests (3) and migration 0002 + seed + chain verified on a local Postgres 16. Not run: `make up`, `make demo-reset`, `make smoke`, `make e2e`, gitleaks (CI runs it).

## Browser check without the stack
Built web app + real API with a test token verifier + Chromium: queue (5 rows, bands, filter), case page, PDF.js viewer opens page 3 with the region outlined, decision recorded (ledger entry shown), too-short reason refused, audit CHAIN VERIFIED with entry details, alerts, pick a seeded document, bad upload refused, 375 px width without horizontal scroll, no console errors. `tests/e2e/demo-flow.cjs` is the same walk for the real stack (not run here).

## Known issues
- `make demo-reset` and the Keycloak login path were not exercised here.
- Hindi for the new screens is English text ([VERIFY]).
- `tests/e2e/demo-flow.cjs` changes demo state; run `make demo-reset` after it.

## CI-FIX 404
Failing: `tests/e2e/diffview.cjs` "unknown case is a 404 page", "malformed case ID is a 404 page" (CI job Stack smoke test).
- [x] (1) reproduce: no Docker daemon in this session, so not run against the stack; reasoned from the route tree (`git log` shows `case/[id]/loading.tsx` arrived in D4, after the check passed in slice 1)
- [x] (2) decide cause: app bug. `[id]/loading.tsx` wraps the affidavit/verification layouts in Suspense, so `notFound()` fires after streaming has started (status 200). Test is correct. See DECISIONS D-17
- [x] (3) fix: move case page, loading.tsx and upload/ into `case/[id]/(review)/`
- [x] (4) verify: lint, typecheck and web unit tests locally; `make e2e` not runnable here, CI to confirm
- [x] (5) push to demo-slice
