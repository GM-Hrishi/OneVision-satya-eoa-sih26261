# packages/rules

Versioned YAML rules for the M5 affidavit diff, the M6 signature, stamp, UDIN and indicator checks, and the plain-language catalogue that goes with them.

- Every rule carries `rule_id`, `rule_version`, `aph_clause`, `aph_edition` (guard rail 6). Unconfirmed clauses are marked `[VERIFY]`.
- **Never** re-implement what the portal Deficiency Report already computes (design D2, guard rail 8); import its result instead.
- Files: `m5-affidavit.yaml`, `m6-signatures.yaml`, `coverage.yaml` (certificate coverage settings), `catalogue/en.yaml` and `catalogue/hi.yaml`, `archive/<pack id>/` for older rule packs used by replay.

## Authoring a rule
1. Give the rule an ID, a version, an APH clause with its edition, a severity, a label from the six labels, and an alert type and subtype (Portal spec 2.9).
2. Set `limitation_key` on every rule that reports an anomaly, a heuristic indicator, or a mismatch with an innocent cause. The key must exist in `catalogue/en.yaml` under `limitation` and in `hi.yaml`.
3. Add a `why.<RULE-ID>` sentence to the catalogue. It is one plain sentence with placeholders (`{extracted}`, `{expected}`, `{unit_label}`, `{doc_title}`, `{page}`, `{clause}`, plus the rule-specific ones), with no rule IDs in it. Without a template the API builds a generic sentence from the rule description and clause.
4. Add Hindi text with `review: true`.
5. Heuristic indicators set `check_kind: "heuristic"` on the flag, use `manual_review_required`, and a low or medium severity (`info` or `warning`). They are listed in `INDICATORS_WITH_OWN_TESTS` in `satya_forensics.eval` and need their own tests instead of a place in the metrics table.

## Wording standard
- State what differs and what could innocently explain it. A finding is a preliminary indicator that needs human verification.
- Never use the words forged, forgery, fake, fraud, fraudulent, tampered, cheat or guilty. A test (`services/api/tests/test_explain.py`) fails on them in every rule description and catalogue text in English.
- A limitation text has the pattern: what the finding does not show, then the most likely innocent cause, in one or two sentences. Example: "This does not show wrongdoing. A typing slip in the portal form would look the same."
- No percentages and no accuracy claims.
