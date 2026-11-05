# Changelog

Synthetic data only. Advisory only. The portal and every source are simulated.

## Unreleased: logic pass (branch feat/logic-rival-parity)
Backend only and additive: no existing field, route, enum value, rule ID or label changed.

- Rules: optional `limitation_key` on every rule; plain-language catalogue (`packages/rules/catalogue`, English complete, Hindi marked `review: true`); a test that fails on banned wording.
- API: `limitation` and `why_detail` on flags, `why_summary` on case and queue rows, `summary` on the affidavit diff, `GET /v1/rules/{rule_id}`.
- Audit: `GET /v1/audit/verify`, `GET /v1/cases/{id}/replay-check`, `GET /v1/cases/{id}/run-diff`; tamper test on a throwaway ledger.
- Certificates: coverage of the submission date for time-bound certificates, session window off by default.
- Indicators (heuristic, manual review at most): annotation over a value, font difference, opaque box over text, overlapping glyphs, text addressed to automated readers (ignored by every reading path).
- Contracts regenerated: `AffidavitDiff.summary`, `Check.coverage`, `Flag.check_kind`.

Details: docs/API-NOTES.md and docs/progress/logic-rival-parity.md.
