# Logic rival-parity pass: progress

Branch `feat/logic-rival-parity` (from `main` at 26963f1). Backend only, additive, no `apps/web` changes.

## Checklist
- [x] T0 discovery notes: DONE (commit 2c7d8cc), 15 lines below. No blocker.
- [x] T1 rule wording lint + `limitation_key` on every rule: DONE (1cac593). `limitation_key` on all 28 rules (14 shared keys), `packages/rules/catalogue/{en,hi}.yaml`, banned-word lint test, `limitation` on review flags, `GET /v1/rules/{rule_id}`. The commit also carries the why templates and `explain.py` helpers used by T2/T3 (shared files).
- [x] T2 plain "why" sentence per flag and per case: DONE (ae11be1). `why_detail {key, params, text}` per flag, `why_summary` (max 3) on `/review` and queue rows; golden tests.
- [x] T3 affidavit diff summary counts: DONE (968bdde). `summary` on affidavit-diff (schema + generated types updated); extra optional keys `added_in_sworn` and `differing[]`.
- [ ] T4 chain verify, replay and run-diff endpoints: in progress
- [ ] T5 certificate coverage
- [ ] T6 extra PDF structural indicators
- [ ] T7 text-aimed-at-AI-readers indicator
- [ ] T8 docs, changelog, full test run, PR text

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
- D-8: the workbench validation handler answers bad query values with 400 (existing behaviour).
- Baseline before changes: shared-types 38 passed; services/api 126 passed, 3 skipped; services/worker 4 passed; packages/affidavit 63 passed.

## Blockers / questions
(none yet)
