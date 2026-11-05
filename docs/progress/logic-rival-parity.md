# Logic rival-parity pass: progress

Branch `feat/logic-rival-parity` (from `main` at 26963f1). Backend only, additive, no `apps/web` changes.

## Checklist
- [x] T0 discovery notes: DONE (commit 2c7d8cc), 15 lines below. No blocker.
- [x] T1 rule wording lint + `limitation_key` on every rule: DONE (1cac593). `limitation_key` on all 28 rules (14 shared keys), `packages/rules/catalogue/{en,hi}.yaml`, banned-word lint test, `limitation` on review flags, `GET /v1/rules/{rule_id}`. The commit also carries the why templates and `explain.py` helpers used by T2/T3 (shared files).
- [x] T2 plain "why" sentence per flag and per case: DONE (ae11be1). `why_detail {key, params, text}` per flag, `why_summary` (max 3) on `/review` and queue rows; golden tests.
- [x] T3 affidavit diff summary counts: DONE (968bdde). `summary` on affidavit-diff (schema + generated types updated); extra optional keys `added_in_sworn` and `differing[]`.
- [x] T4 chain verify, replay and run-diff endpoints: DONE (4cab67b). `GET /v1/audit/verify`, `GET /v1/cases/{id}/replay-check`, `GET /v1/cases/{id}/run-diff`; tamper test on a throwaway in-memory ledger, reproduction notes in `docs/TAMPER-TEST.md`. Postgres variant not written: the runtime role cannot alter ledger rows (existing test).
- [x] T5 certificate coverage: DONE (e553dc9). `satya_forensics.coverage`, `packages/rules/coverage.yaml` (session window off, `[VERIFY APH clause]`), 4 `CERT-*` rules, coverage check on time-bound documents (label mapped to `expired` / `manual_review_required` / `verified`), `Check.coverage` in the schema. Gap: the demo has no certificate documents (only affidavit and accounts slots are built), so the wiring is exercised by unit and API-helper tests, not the demo path. Replay applies the same step so digests stay equal once certificate documents exist; its submission date is read from the case file.
- [x] T6 extra PDF structural indicators: DONE (fba40fd). All four indicators implemented with pdfplumber/pdfminer geometry and pikepdf-built fixtures (clean controls included): annotation over a value, font family or size difference, opaque white/page-colour box drawn after text that is still present, overlapping glyphs. `check_kind: "heuristic"` on the flag (new optional `Flag.check_kind`), `manual_review_required`, severity `warning` (medium) or `info` (low). Not triggered by the 16 demo PDFs or by the first 40 cases of the M6 corpus.
- [x] T7 text-aimed-at-AI-readers indicator: DONE (16b00cf). `AI-READER-TEXT` (page, box, escaped snippet of at most 120 characters, medium, manual review). The lines are dropped in `satya_ocr.aimask` before every reading path: affidavit extraction (words and table cells, text and OCR), M6 text layer, page classifier (a scan with a planted line stays image-only). Tests prove the M5 extraction, M5 diff and M6 verdicts are unchanged by a planted line. No text reaches any model or classifier: there is none in the product.
- [x] T8 docs, changelog, full test run, PR text: DONE (see the last commit). `docs/API-NOTES.md`, `docs/TAMPER-TEST.md`, `packages/rules/README.md` authoring guide with the wording standard, `CHANGELOG.md`, DEMO-NOTES not-built line (replay screen, certificate documents), docs index.

## T0 discovery notes
1. Rules: `packages/rules/m5-affidavit.yaml` (9 rules) and `m6-signatures.yaml` (19 rules); each rule has `rule_id`, `version`, `text_key`, `aph_clause`, `also_cites`, `severity`, `label`, `alert{type,subtype}`, `institution_visible`, `preliminary_indicator`, `description`.
2. Rule loaders: `satya_affidavit/rules.py` and `satya_forensics/rules.py` (frozen dataclass `Rule`, `Ruleset`, `load_ruleset_file`); `services/api/.../rulepacks.py` pairs both as a pack id `m5-affidavit@x+m6-signatures@y` (replay archive).
3. Flag model: dicts built by `FlagFactory.make` in `satya_affidavit/flags.py` and `satya_forensics/flags.py` (same shape, Portal spec 2.6.4); `rule_text_key` is a key that has NO catalogue text anywhere yet.
4. Existing "why": `services/api/.../triage.py` `WHY` dict + `why_sentence(flag)`; `workflow.py` adds `flag["why"]` (a STRING) and `doc_title` on `/v1/cases/{id}/review`. Changing `why` to an object would break old clients, so the new object goes in `why_detail` (decision D-1 below).
5. i18n: the workbench catalogue is `apps/web/messages/{en,hi}.json` + `hi.review.json` (frozen for this task). Backend sentences (OCR `reasons.py`) are mirrored there. Decision D-2: new backend catalogue in `packages/rules/catalogue/{en,hi}.yaml`, Hindi entries carry `review: true`; mirroring into apps/web is left for the UI redesign.
6. Affidavit diff: `satya_affidavit/diff.py`, `engine.py` (`run`), served by `FixtureCaseRepository.affidavit_diff` in `services/api/.../cases.py` at `GET /v1/cases/{id}/affidavit-diff`; schema `AffidavitDiff` in shared-types.
7. Audit chain: `services/api/.../ledger.py` (`verify_chain`, `LedgerRow`, `ChainReport`), `ledger_verify.py` CLI, `Workflow.audit` already recomputes the chain on `GET /v1/audit` (AU, RB).
8. Replay: `services/api/.../replay.py` (`Replayer.replay`, `diff_flags`), route `GET /v1/cases/{id}/replay` (RB, AU), writes one `case.replay` ledger entry.
9. Forensics modules: `packages/forensics/src/satya_forensics` (`signatures.py`, `stamp.py`, `udin.py`, `textlayer.py`, `engine.py`); OCR fallback in `packages/ocr`.
10. Date rules: certificate `valid_to` appears on checks (`engine.py` check["valid_to"], notary seal expiry in `stamp.py`); the Overview "expiring" list in `workflow.py` uses it. There is NO fire-safety/structural certificate analyser in the repo: only the affidavit and audited-accounts slots are built. Document types named in the Document example/APH digest: `fire_safety_certificate`, structural stability, occupancy/completion.
11. Routes: `services/api/.../main.py` (`official(request, roles)`, `scoped_case`, `in_scope`, per-user limiters, `ProblemError` with codes in `problems.py`).
12. Types: `make gen-types` regenerates `packages/shared-types/{ts,python}/.../generated`; CI fails on diff.
13. Tests: `make test` runs pytest per package separately (a single `pytest` at repo root fails on duplicate `tests.conftest`, existing behaviour). Synthetic PDFs: `satya_affidavit/synth`, `satya_forensics/synth`, `satya_ocr/synth.py`.
14. Guards: `make guard`, `make secret-scan`, `make lint`, `make typecheck`, `make synth-check`.
15. Demo: `docs/DEMO-NOTES.md`, `make demo-reset`, `make smoke` (stack needed).

## Decisions
- D-1: `flag.why` stays a string (existing field). Object form is `flag.why_detail: {key, params, text}`.
- D-2: backend catalogue in `packages/rules/catalogue/`, because `apps/web` is frozen.

- D-3: `/v1/audit/verify` is read-only and writes no ledger entry (the repo does not log `/v1/audit` recomputations either).
- D-4: `replay-check` reuses `Replayer._compute` with the original pack, writes nothing (unlike `/replay`). Digest = sha256 of canonical JSON of flag records (by flag_id) + document labels; no timestamps. Gap: source answers are the stored ones, as in the existing replay, so no lookup is repeated.
- D-5: run diff compares two `check.run` ledger entries (default: previous and latest, or `from_seq`/`to_seq`), matched by (document, rule, check) like replay's diff.
- D-6: new routes return plain JSON like their neighbours (no response_model), so OpenAPI documents the paths but not the bodies; the one schema-backed addition is `AffidavitDiff.summary`.
- D-7: the rule YAML gained `limitation_key` without a version bump (metadata only, flags unchanged), so archived-pack replay is unaffected.
- D-9: metrics gate extended with `INDICATORS_WITH_OWN_TESTS` (question 1 below).
- D-8: the workbench validation handler answers bad query values with 400 (existing behaviour).
- Baseline before changes: shared-types 38 passed; services/api 126 passed, 3 skipped; services/worker 4 passed; packages/affidavit 63 passed.

## Blockers / questions
- Stack smoke tests (`make smoke`, `make demo-reset`, `make e2e`) were NOT RUN: this cloud session has no Docker daemon. The in-process demo flow tests (`services/api/tests/test_demo_flow.py` and neighbours) pass. Run them on the team laptop before merging; if the known flaky smoke test X-44 flakes, re-run once and do not weaken it.
- Secret scan (`make secret-scan`, gitleaks in Docker) NOT RUN for the same reason. The real-data guard passes; no secret, token or personal value was added.
- `apps/web` untouched, so the new fields are not shown anywhere and the catalogue keys are not mirrored into `apps/web/messages` (decision D-2).

## Questions for the team
1. Metrics gate: `satya_forensics.eval` now has `INDICATORS_WITH_OWN_TESTS` (the four PDF indicators, `AI-READER-TEXT`, the four `CERT-*` rules). They are not planted in the signature/stamp/UDIN corpus, so they are excluded from the precision/recall table, guarded by a test (label, limitation, preliminary) and by a test that none of them fires on the first 40 dev-seed cases. Confirm this is acceptable or ask for planted cases instead.
2. `why`: the existing string stays; the object is `why_detail` (the brief asked for `why: {key, params, text}`, which would change the type of an existing field).
3. APH clauses for the PDF indicators, certificate coverage and the session window are all `[VERIFY]`; no clause in the APH digest covers them. The session window stays off.
4. Time-bound document type names other than `fire_safety_certificate` follow the APH digest wording and need checking against the portal's list.
5. Alert subtypes for the new rules use the nearest existing Portal 2.9 values (`document_expired`, `field_missing`, `signature_integrity`) `[VERIFY with M11]`.

## Test summary (counts from this branch; before in brackets)
- `packages/shared-types/python`: 38 passed [38]
- `services/api`: 165 passed, 3 skipped [126 passed, 3 skipped]
- `services/worker`: 4 passed, 1 deselected [same]
- `packages/affidavit`: 65 passed [63]
- `packages/forensics`: 153 passed and 1 failed in the full run, the failure (an invalid placeholder document id inside a new test) fixed afterwards and re-run alone: 17 passed in `test_coverage.py`; so 154 expected [114 passed]. The structure and AI scans add about 1.5 minutes to this package's run.
- `packages/blindgen`: 4 passed [4]
- `packages/ocr`: 56 passed, 1 skipped [34 passed, 1 skipped]
- `ruff check`, `ruff format --check`, `mypy` (Makefile paths): clean. Generated contracts: no diff after regeneration. Real-data guard: OK. `make synth-check`: up to date. `tsc` for `@satya/shared-types`: clean.
- Not run: stack smoke tests, e2e, secret scan (no Docker daemon), `pnpm` workspace tests other than the shared-types type check.

## PR text
See the pull request description (title: "Logic pass: why sentences, limitations, coverage, new indicators (draft, do not merge before Update day)").

