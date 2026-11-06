# Progress: SATYA-EoA workbench UI rebuild, style K

Prompt: `docs/prompts/PROMPT_ui_style_k.md` (v1.1). Rule: continue from the first task not marked DONE; never redo DONE tasks.

**Branch note (deviation from the prompt).** The prompt names `feat/ui-style-k`. The remote declined a push to that name ("push declined due to email privacy restrictions") and this cloud session may push only to its designated branch, so all work is on `claude/satya-eoa-ui-style-k-t3pz9w`, created from `main` (`a652b6d`). Resume with that branch name instead of `feat/ui-style-k`. Nothing else was pushed anywhere.

## Checklist
| Task | Status | Commit | Note |
|---|---|---|---|
| Setup: prompt copy + progress file | DONE | see git log | prompt, progress file and mockups committed |
| T0 discovery | DONE | see git log | notes below |
| T1 tokens, fonts, motion, contrast script | DONE | see git log | k/dur/ease token groups, Archivo variable width axis (62-125%) bundled so no fallback needed, motion.css + lib/motion.ts, contrast script: 51 pairs all pass | |
| T2 shell: top bar, nav per role, footer, breadcrumbs, menu | TODO | | |
| T3 primitives + DecisionBar restyle | TODO | | |
| T4 Case page + Ladder | TODO | | |
| T5 Evidence map + Journey | TODO | | |
| T6 Audit + replay diff | TODO | | |
| T7 Overview | TODO | | |
| T8 Queue + timeline | TODO | | |
| T9 Affidavit + tie lines | TODO | | |
| T10 Document evidence page | TODO | | |
| T11 Manual verification | TODO | | |
| T12 Alerts and Rules | TODO | | |
| T13 Reuse graph (flagged) | TODO | | |
| T14 Sweep | TODO | | |

## T0 notes (real names found on `main` at a652b6d; backend shapes from `origin/feat/logic-rival-parity:docs/API-NOTES.md`, read-only)
1. Baseline before any change: `pnpm lint` 0 errors (1 existing unused-var warning in overview/page.tsx), `pnpm typecheck` clean, `pnpm test` 34 passed in 9 files. Deps install with `pnpm install --frozen-lockfile` (build scripts are not approved; not needed).
2. Routes on main (`apps/web/src/app/(shell)`): overview, rb-queue, case/[id] (review), case/[id]/upload, case/[id]/affidavit, case/[id]/verification, alerts, audit, help, about, accessibility, policies, sitemap, signin, home. NOT on main: /manual, /rules, /case/[id]/documents/[docId], /audit/integrity, /audit/replay, /case/[id]/reuse. Those become new routes that show honest not-available states.
3. Shell is a left rail (`components/shell/AppShell.tsx`, `lib/rail.ts` RAIL per role RB and AU). Rail items: overview, queue, alerts, audit (RB). Manual checks and Rules are not reachable yet, so they are added to nav only when the route exists (no dead links).
4. Tokens are GENERATED: edit `src/styles/tokens.json`, run `pnpm gen:tokens`; `scripts/gen-tokens.mjs --check` (in `pnpm build` and `test/tokens.test.ts`) also requires every UI spec §8 colour to stay present. Style K tokens are therefore added as a new `k` group (emits `--k-*`) and the old tokens stay until T14.
5. Fonts: `app/layout.tsx` imports Fontsource weights; `test/fonts.test.ts` pins the exact import list and must be updated in T1 when Archivo and JetBrains Mono are added.
6. Queue row (`lib/demo-types.ts` QueueRow): `case_id, application_id, risk_band, top_reasons[], label_counts, status, manual_tasks, submitted_at, last_activity_at, open_flags, undisposed_flags, institution_name, stage, route, region, ay`. There is NO waiting-days field: days waiting is derived client-side from `submitted_at` against the overview `as_of` (pure, tested). Pending: `why_summary` (up to 3 strings).
7. Overview payload (`Overview`): `as_of, ay, region, cases{submitted,by_band}, status{}, documents{total,by_label}, manual_tasks{open,oldest_age_days,top[]}, expiring{d30,d60,d90,top[]}, recent_decisions[], sources[]`.
8. Review payload: `documents[] {doc_id, slot, title, sha256, label, source{channel,adapter_mode}, issuer_sig, uploader_sig, checks[], manual_task, read}`, `flags[] {Flag & why, doc_title, disposition}`, `tasks[]`, `label_counts`, `risk{band,reasons,note}`, `status`, `undisposed_flags`. Flags carry `regions` (x,y,w,h, 0..1), `page`, `rule_id`, `aph_clause`, `extracted_value`, `expected_value`, `delta`, `check_ref`, `evidence_sha256`.
9. Ledger event kinds found in `services/api/src` (T0 grep): `case.json`, `case.replay`, `check.run`, `disposition.recorded`, `document.note`, `document.pdf`, `document.read`, `document.uploaded`, `manual_task.created`. Journey steps (template, fields read, rules, issuer asked, signature) cannot be cleanly separated per step from these kinds, so VISUAL 2 shows step status from the review document (`read`, `checks[]`, `issuer_sig`) and entry numbers only where an event maps one-to-one (to be confirmed in T5).
10. Audit payload (`Audit`): `chain{ok,rows,broken_at,reason,recomputed_at,method}` already exists on main in `/v1/audit`; the footer chain chip and the Audit page can read it today. `GET /v1/audit/verify` is the pending, cleaner form.
11. Backend branch API-NOTES (read-only): flags gain `limitation {key,text}|null` (the notes DO confirm it at flag level, contrary to the prompt's doubt), `why_detail {key,params,text}`, `check_kind: "heuristic"`; review and queue rows gain `why_summary`; affidavit-diff gains `summary {total,match,differ,missing_in_sworn,not_comparable,added_in_sworn,differing[]}`; new routes `GET /v1/rules/{rule_id}`, `GET /v1/audit/verify`, `GET /v1/cases/{id}/replay-check`, `GET /v1/cases/{id}/run-diff`; certificate `coverage` on expiry checks. Catalogue text is already localised server-side (Hindi marked review): show what the API returns, never translate on the client.
12. There is no `GET /v1/rules` list or `GET /v1/manual-tasks` list route in the notes: T11/T12 list views read what exists on main and otherwise show not-available (recorded in MERGE-NOTES).
13. Reuse graph (VISUAL 6): no cross-case shared-artifact signal in the review payload on main (UDIN-REUSE and STAMP-REUSE exist as flags only, no fingerprint index endpoint). Build behind `features.reuseGraph` (off).
14. Mockups (static `.dc.html`, 15 files) copied to `docs/ui-style-k/mockups/` as visual reference only.
15. e2e specs are Playwright `.cjs` files in `tests/e2e/` and need the running stack (`make up`); they cannot run in this cloud session. Unit tests (`pnpm test`), lint and typecheck can.

## Blockers / questions
- Branch name (see top). 
- e2e and smoke need Docker (`make up`); not available here. Recorded per task; they must be run by the team before merge.

## Needs a decision
- Confirm the branch rename (`feat/ui-style-k` is rejected by the remote's email-privacy rule on this account; the designated branch is used instead).
