# Merge notes: style K and the backend branch (draft PR #15)

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
| Cross-case fingerprint index (stamp serial, signature image fingerprint) | none on either branch | reuse graph `/case/[id]/reuse` (T13), behind `features.reuseGraph` | route and nav hidden |

Other seams
- Waiting days: no field on `GET /v1/cases` rows. Derived client-side from `submitted_at` against the overview `as_of` (T8).
- Stage trail on the case page: the review payload has no stage names, so none is drawn (not invented).
- Journey audit entry numbers: ledger events (`document.read`, `check.run`, ...) are per run, not per step, so entry numbers are not shown.
- "Manual checks" and "Rules" navigation items appear only when their routes exist.
