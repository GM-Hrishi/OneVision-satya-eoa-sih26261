# Merge notes: style K and the backend branch (draft PR #15)

**Status (6 Nov 2026): joined on branch `integration/k-join`** (main + PR #15 + PR #16, merged with no conflicts; `main` untouched, both PRs still draft). Shared types regenerate with no diff; lint, typecheck and the JS tests pass. The fallbacks below stay in place on purpose: the adapters read the new fields when present and fall back when absent, so no code change was needed. Cleaning up the shims (step 2 below) waits until the build is reviewed on the laptop. Not yet run: e2e, smoke, axe (need Docker).

Backend branch: `feat/logic-rival-parity` (draft PR #15, not merged). Shapes are taken from `docs/API-NOTES.md` on that branch, read-only. Until it merges, every endpoint below answers 404 on `main`, and every field is absent; the UI then uses the fallback in the last column and never prints a key or invents data.

After both branches are merged: (1) regenerate shared types, (2) delete `apps/web/src/lib/api/k-adapters/pending-fields.ts` and read the fields directly, remove `pending-endpoints.ts` notes, (3) run the e2e and smoke tests, (4) delete `apps/web/src/lib/api/__fixtures__` if no test needs it.

| Contract | Placeholder in code | Consumer | When absent |
|---|---|---|---|
| `GET /v1/audit/verify` `{status, checked_at, entries, first_bad_entry}` | `AUDIT_VERIFY` in `lib/api/pending-endpoints.ts`, `k-adapters/chain.ts` `fromVerify` | footer `ChainChip` | falls back to the `chain` block of `GET /v1/audit` (exists on main, recomputed per call); chip hidden if neither answers |
| `GET /v1/cases/{id}/replay-check` | `replayCheck()`, `k-adapters/replay.ts` | `/audit/replay` (`ReplayDiff`) | page says "Replay check is not available on this build." |
| `GET /v1/cases/{id}/run-diff` | `runDiff()` | not consumed yet (reserved for the case replay view) | n/a |
| `GET /v1/rules/{rule_id}` (`limitation_key`, `limitation`) | `ruleDetail()` | `/rules/[ruleId]` (T12) | rule detail shows the list fields only |
| flag `limitation {key,text}` | `pending-fields.ts` `limitationText` | `LimitationNote` on the case page | note hidden (never a key) |
| flag `why_detail {key,params,text}` | `whyText` | pinned findings, ladder verdicts | existing `why` string |
| flag `check_kind: "heuristic"` | `isHeuristic` | finding order (indicators last), no clashing numerals, ink pin | treated as an ordinary finding |
| review/queue row `why_summary[<=3]` | `whySummary` | case lead sentence (T4), queue and overview sentences (T7, T8) | first finding's `why` |
| affidavit-diff `summary {...}` | T9 | affidavit headline and numerals | counted client-side from the rows |
| expiry check `coverage {...}` | T10 | document evidence page | not shown |
| replay `as_of`, `digest_original`, `digest_replayed` | `replay.ts` | `ReplayDiff` | not shown |
| Cross-case fingerprint index (stamp serial, signature image fingerprint): proposed `GET /v1/cases/{id}/reuse` returning `{institutions:[{id,name}], artifacts:[{id, kind: stamp_serial or signature_image, label, institution_ids:[id]}]}` | `reuseIndex()` in `pending-endpoints.ts`, `k-adapters/reuse.ts` | reuse graph `/case/[id]/reuse` (T13), behind `features.reuseGraph` | route answers 404, no nav item; dev fixture only with `NEXT_PUBLIC_UI_FIXTURES=1` |
| Manual-task list and resolve endpoints (spec §7.6) | none on either branch | `/manual/[taskId]` and the resolve panel (not built, T11) | `/manual` lists the overview's open checks and opens the case |
| Rule list endpoint (count, ruleset id/hash) | none on either branch | `/rules` headline 'N rules run' (not built, T12) | `/rules` lists rules seen on queue rows |

Other seams
- Waiting days: no field on `GET /v1/cases` rows. Derived client-side from `submitted_at` against the overview `as_of` (T8).
- Stage trail on the case page: the review payload has no stage names, so none is drawn (not invented).
- Journey audit entry numbers: ledger events (`document.read`, `check.run`, ...) are per run, not per step, so entry numbers are not shown.
- "Manual checks" and "Rules" navigation items appear only when their routes exist.
