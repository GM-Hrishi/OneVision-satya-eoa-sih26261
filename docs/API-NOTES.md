# API notes: fields and routes added by the rival-parity logic pass

All additions are optional or new. Existing fields, routes, enum values, rule IDs and labels are unchanged. Every answer is advisory (`advisory: true`, `regulatory_effect: "none"`); officials decide. Synthetic data only; the portal and every source are simulated.

Authentication, roles and region scope follow the neighbouring routes. Errors are RFC 9457 problem responses with generic text.

## Fields added to existing responses
| Where | Field | Shape | Notes |
|---|---|---|---|
| `GET /v1/cases/{id}/review` flags | `limitation` | `{key, text}` or `null` | What the finding does not show, and the likeliest innocent cause. Key `limitation.<name>` from `packages/rules/catalogue/en.yaml` |
| same | `why_detail` | `{key, params, text}` | One plain sentence from a template (`why.<rule id>`); a missing template falls back to the rule title and APH clause. The existing `why` string is unchanged |
| `GET /v1/cases/{id}/review` and queue rows (`GET /v1/cases`) | `why_summary` | up to 3 strings | Most severe findings first, no duplicates |
| `GET /v1/cases/{id}/affidavit-diff` | `summary` | `{total, match, differ, missing_in_sworn, not_comparable, added_in_sworn, differing[]}` | Counts over the declarations the portal form prints, taken from `ops`. A copy that was not compared (a scan, an unreadable file) is `not_comparable` throughout. `differing[]` has `decl_no`, `sworn_no`, `op`, `flag_id`, `why` per non-matching declaration. Schema: `AffidavitDiff.summary` |
| Flags (any) | `check_kind` | `"heuristic"` | Only on commodity indicators (T6, T7). Absent on rule-based findings. Schema: `Flag.check_kind` |
| Document `checks[]` of kind `expiry` | `coverage` | `{status, valid_from, valid_to, days_off, session?}` | `status`: `covers`, `expired_before_submission`, `not_yet_valid`, `validity_unknown`. Schema: `Check.coverage` |
| `GET /v1/cases/{id}/replay` | `as_of`, `digest_original`, `digest_replayed` | strings or `null` | Same digests the replay check compares |

## Routes added
| Route | Roles | Answer |
|---|---|---|
| `GET /v1/rules/{rule_id}` | RB, AU | Current rule: version, APH clause and edition, severity, label, `limitation_key`, `limitation` |
| `GET /v1/audit/verify` | RB, AU | `{status: "intact"\|"broken", checked_at, entries, first_bad_entry}`; walks the whole hash chain on every call, nothing cached, writes no ledger entry |
| `GET /v1/cases/{id}/replay-check` | RB (own region), AU | `{reproduced_identically, ruleset_id, ruleset_hash, as_of, digest_original, digest_replayed, reasons[]}`. Runs the original rule pack on the stored documents and the stored source answers, compares digests; writes nothing (unlike `/replay`, which records one `case.replay` entry) |
| `GET /v1/cases/{id}/run-diff?from_seq=&to_seq=` | RB (own region), AU | `{comparable, from_run, to_run, new_findings, resolved, unchanged, items[]}`. Compares two `check.run` ledger entries of the case (default: the previous and the latest). Findings are matched by document, rule and check |

`reproduced_identically` is true only when both digests exist and are equal. The digest covers the flag records (by flag id) and the document labels; it holds no timestamp. `as_of` is the time of the original run.

## Indicators (flags with `check_kind: "heuristic"`)
They ask a person to look. They route to `manual_review_required` at most, never `mismatch_detected`, and carry a low or medium severity (`info` or `warning`), a page, a region and a limitation text.
| Rule | Looks for |
|---|---|
| `PDF-ANNOT-OVERLAP` | a FreeText, Square, Highlight or Stamp annotation over a date or key value |
| `PDF-FONT-DIFF` | a key value in another font family or size than its line |
| `PDF-COVER-TEXT` | an opaque white (page-colour) box drawn after text that is still in the text layer |
| `PDF-GLYPH-OVERLAP` | characters of a key value drawn on top of each other |
| `AI-READER-TEXT` | text addressed to automated readers (including white, tiny or off-page text); SATYA drops that text before any reading, so it changes no extracted value and no verdict |

These are commodity checks, not unique to SATYA. No precision or recall is claimed for them; each has its own tests (`packages/forensics/tests/test_structure.py`, `test_airead.py`, `test_coverage.py`). They are excluded from the signature, stamp and UDIN metrics table, and a test shows that none of them fires on that corpus.

## Certificate coverage
`packages/rules/coverage.yaml` lists the time-bound document types and holds the optional session window (off, `[VERIFY APH clause]`). `expired_before_submission` maps to the existing `expired` label; `not_yet_valid` and `validity_unknown` map to `manual_review_required`. No label was added. The demo cases contain no certificate documents, so the demo path does not show this yet.

## Catalogue
`packages/rules/catalogue/{en,hi}.yaml` hold `limitation.*` and `why.*`. Hindi entries carry `review: true`. The workbench message files (`apps/web/messages`) were not changed in this pass, so mirroring these keys there is left for the interface work.
