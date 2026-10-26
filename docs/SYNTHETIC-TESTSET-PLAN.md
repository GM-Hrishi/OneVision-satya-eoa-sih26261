# Synthetic test-set plan (Phase 1 rules)
Version 1.0 (slice 1, 26 Oct 2026). Synthetic data only. Specs: design v2.2.1 (B1, C3, C4, C4a, D1–D5), Portal spec v0.2.1 (§2.6 schemas, §2.7–2.9), UI spec v0.7.1 (§6). Problem statement "Prototype Demonstration and Evaluation" asks for extraction accuracy, validation accuracy, anomaly-detection performance, source-verification rate, discrepancy-identification reliability and alert timeliness; this plan says how each Phase-1 rule is measured.

**Status of the rules below:** M5 (P-3) is built in slice 1 and its rule IDs are final. Every other rule ID is the planned ID; its slice may refine the ID or split a rule, and must update this file in the same PR.

## 1. Principles
1. **Every rule gets at least one planted anomaly and at least one clean control.** A clean control is a document or snapshot that *looks* like the anomaly but is legitimate (re-typeset copy, valid strike-through choice, benign incremental PDF update, explained change). Controls measure false flags.
2. **Ground truth is written by the generator, not by the engine.** The generator records what it planted (and what it printed) in a `truth.json` next to every case. The engine never reads it.
3. **Field names come from the contracts.** Ground-truth flags use the `Flag` fields of Portal §2.6.4, document outcomes use the six labels of §2.6.3 and `VerificationResult.checks[]` of §2.7, alerts use `Alert.type` / `subtype` of §2.9.
4. **Portal checks are never tested as SATYA rules (D2).** Deficiency Report norm arithmetic, the within-portal faculty duplicate flag and PAN validation are imported results (`provenance: portal`). The test set only checks that SATYA displays them unchanged and never emits its own flag for them.
5. **Dev seeds and held-out seeds.** Rules are tuned on dev seeds only; the reported metric is the held-out run. Both are printed.
6. **Synthetic only.** Values follow `data/synthetic/README.md` (Demo Institute/College names, `1-9…` IDs, demo-range licence numbers, Bay-of-Bengal coordinates, tokens for people). Generated PDFs carry "SYNTHETIC" in their text layer; a test fails if one does not.

## 2. Ground-truth format
One `truth.json` per generated case (`data/synthetic/...` for committed demo cases; the test temp directory for the bulk set):
```json
{
  "case": "dit03-2026-27-land_area_changed",
  "variant": "land_area_changed",
  "control": false,
  "slot": "annex2.1(i) affidavit",
  "expected_flags": [
    { "rule_id": "LAND-AREA-RECON", "check_ref": "m5:LAND-AREA-RECON:land:2:area_acre",
      "page": 6, "label": "mismatch_detected", "severity": "warning",
      "alert": { "type": "suspected_anomaly", "subtype": "affidavit_diff" },
      "extracted_value": 3.5, "expected_value": 4.5, "value_unit": "acre",
      "institution_visible": true, "preliminary_indicator": true }
  ],
  "expected_document_label": null,
  "expected_checks": [],
  "printed": { "header.ay": "2026-27", "decl.9": "…", "land.2.area_acre": 3.5 }
}
```
- `expected_flags[]` holds the subset of `Flag` fields that are deterministic for the case. A clean control has `"expected_flags": []` for the rules it controls.
- `check_ref` is the match key: `m<module>:<rule_id>:<subject key>`. A produced flag matches a truth flag when `rule_id` and `check_ref` are equal (and `page`, when the truth gives one).
- `expected_document_label` / `expected_checks[]{kind, outcome, reason_code}` are used by M6/M7 rules (§2.7–2.8).
- `printed{}` is what the generator actually printed in the document (after planting). Extraction accuracy compares extracted fields with `printed`, not with the snapshot.

## 3. Metrics (per rule)
| Metric | Definition |
|---|---|
| Precision | TP / (TP + FP) over all cases; 1.0 when the rule produced no flags and none were expected |
| Recall | TP / (TP + FN) over all cases with an expected flag for the rule |
| False-flag rate (FFR) | clean-control cases with ≥ 1 flag of the rule / all clean-control cases |
| Extraction accuracy | fields extracted equal to `printed` / all `printed` fields the rule depends on (numbers within the unit tolerance; text compared after the rule's own normalisation) |
| Label accuracy (M6, M7) | documents whose produced label equals `expected_document_label` / all documents |
| Verdict accuracy (M13) | flags whose `yoy.verdict` equals the truth verdict / all M13 truth items |
| Source-verification rate (M7) | lookups that ended `verified` or `mismatch_detected` / lookups attempted on cases whose truth says the source answers |
| Alert timeliness (M11) | seconds from `case.validation_completed` to `alert.raised` for each truth alert (p50, p95) |

**Phase-1 targets on the synthetic set:** precision ≥ 0.95, recall ≥ 0.95, FFR ≤ 0.02, extraction accuracy ≥ 0.98 on text layers (≥ 0.90 once OCR lands with M3). A rule below target is reported, never hidden; the threshold is not lowered to pass.

## 4. Corpus composition
| Axis | Values |
|---|---|
| Institutions | 8 synthetic TN institutions (Demo Institute of Technology 03, 11, 13, 17; Demo College of Engineering 05, 07, 09, 15) with different deed counts (1–3), room counts (3–6 per table), category sets and intakes. Dev seeds: 03, 05, 07, 11. Held-out: 09, 13, 15, 17 |
| Years | 2025-26 and 2026-27 per institution (M13); 2024-25 for the partial-OC 3-year counter |
| Render styles (clean controls) | plain re-typeset; aggressive hyphenation; alternative valid strike-through choices; whitespace and letter-case noise with a DD/MM date that MM/DD cannot parse |
| Planted variants | one per rule anomaly below, each rendered in a randomly chosen style |
| Volume (M5 now) | 8 institutions × (4 controls + 9 planted) = 104 sworn affidavits |

## 5. Rule catalogue

### 5.1 M5 affidavit diff and reconciliation (P-3) — built in slice 1
Doc slot `annex2.1(i) affidavit`; expected draft = template `aff2-portal-2024-27` rendered for the same AID and AY. Alert type/subtype per Portal §2.9. Every M5 flag: `provenance: satya`, `stage: "2"`, `preliminary_indicator: true`, `aph_edition: "2024-27"`.

| Rule ID | APH clause | Planted anomaly (variant) | Clean control | Ground truth (`check_ref` key → label, severity, alert, institution_visible) | Metrics |
|---|---|---|---|---|---|
| `AFF-CAT-LINE` | Affidavit-2 NOTE; 2.3.4b | `cat_line_missing`: the numbered category line ("1. EoA Only") is deleted from the opening block | all 4 controls (category list re-typeset, different spacing/case) | `category_line` → `mismatch_detected`, critical, `missing_info.category_line_missing`, visible true; `expected_value` = expected list, `extracted_value` = null | P, R, FFR, extraction accuracy of `category_list` |
| `AFF-DECL-MISSING` | Affidavit-2 NOTE; 7.4(a) | `decl_dropped`: one of the 24 declarations removed, later ones renumbered | controls with renumbered spacing and hyphen-wrapped declarations | `decl:<n>` → `mismatch_detected`, critical, `suspected_anomaly.affidavit_diff`, visible false | P, R, FFR, decl text extraction accuracy |
| `AFF-DECL-CHANGED` | Affidavit-2 NOTE; 7.4(a) | `clause_narrowed`: a qualifying phrase removed (e.g. decl 9 "contiguous and undisputed" → "contiguous") | `clean_alt_options` (a different but valid strike-through choice is not a change); `clean_hyphenated` | `decl:<n>` → `mismatch_detected`, critical, `suspected_anomaly.affidavit_diff`, visible false; `extracted_value` / `expected_value` = normalised clause text | P, R, FFR |
| `AFF-DECL-ADDED` | Affidavit-2 NOTE | `decl_inserted`: an extra numbered declaration inserted after decl 12 | controls (no extra text) | `decl:added:after-<n>` → `mismatch_detected`, warning, `suspected_anomaly.affidavit_diff`, visible false | P, R, FFR |
| `AFF-HEADER` | 2.3.4b; Affidavit-2 NOTE | `header_ay_stale`: "ACADEMIC YEAR – 2025-2026" on a 2026-27 application | `clean_spacing_case` (institution name in capitals, extra spaces) | `header:ay` → `mismatch_detected`, warning, `suspected_anomaly.affidavit_diff`, visible true | P, R, FFR, extraction accuracy of AID, PID, AY, institution name, application date (MM/DD) |
| `LAND-AREA-RECON` | Annex-3 3.1g [VERIFY: the area itself is sworn in the Affidavit-2 land table]; Affidavit-2 NOTE | `land_area_changed`: one deed's area reduced by 1.00 acre | controls (areas printed as 8, 8.0, 8.00) | `land:<row>:area_acre` and `land:total` → `mismatch_detected`, warning, `suspected_anomaly.affidavit_diff`, visible true; `value_unit: "acre"`, `delta` | P, R, FFR, extraction accuracy of land cells |
| `LAND-ROW-RECON` | Affidavit-2 NOTE; 2.3.4b | `land_row_changed`: plot no. of deed 1 changed | `clean_spacing_case` (deed date printed DD/MM where MM/DD is impossible: parsed by fallback, not flagged) | `land:<row>:plot_no` → `mismatch_detected`, warning, `suspected_anomaly.affidavit_diff`, visible true | P, R, FFR |
| `ROOM-RECON` | Annex-3 (built-up area norms) [VERIFY sub-clause]; Affidavit-2 NOTE | `room_values_changed`: one instructional room's carpet area reduced, one administrative room's flooring "Ready" → "Not ready" | controls (areas printed 66 / 66.0; completion in different case) | `<table>:<room_id>:<field>` → `mismatch_detected`, warning, `suspected_anomaly.affidavit_diff`, visible true | P, R, FFR, extraction accuracy of room cells |
| `ROOM-ID-DUP` | Affidavit-2 NOTE [VERIFY]; design D5.10 | `room_ids_duplicated`: the same room ID in the Instructional and Instructional–Common tables (in the portal data and printed faithfully) | controls (IDs unique, similar-looking IDs such as `I-201` / `I-210`) | `room_id:<id>` → `manual_review_required`, warning, `suspected_anomaly.affidavit_diff`, visible true | P, R, FFR |

Notes: a dropped or added declaration is reported once (no extra `AFF-DECL-CHANGED` for renumbering). A changed deed area produces the row flag and the total flag; both are in the truth.

### 5.2 M6 signatures, stamp chronology, notary (P-4) and UDIN structure (P-18) — slice 2
`check.kind` and `reason_code` per Portal §2.8. Signed fixtures use the SATYA test root ("TEST TRUST ANCHOR").

| Rule ID | APH clause | Planted anomaly | Clean control | Ground truth | Metrics |
|---|---|---|---|---|---|
| `SIG-DIGEST` | 2.3.4a | byte flipped inside the signed /ByteRange | correctly signed file | `issuer_signature` → `mismatch_detected` / `SIG_DIGEST_MISMATCH`; alert `suspected_anomaly.signature_integrity` | P, R, FFR, label accuracy |
| `SIG-MODIFIED` | 2.3.4a | page content added in an incremental update after signing | benign incremental update (annotation / DSS) | `mismatch_detected` / `SIG_MODIFIED_AFTER_SIGNING` | P, R, FFR |
| `SIG-REVOKED` | 2.3.4a | test cert revoked in the test CRL before signing time | revoked after signing time | `mismatch_detected` / `SIG_CERT_REVOKED` | P, R, FFR |
| `SIG-CERT-EXPIRED` | 2.3.4a | signed outside the cert validity | signed one day before expiry | `expired` / `SIG_CERT_EXPIRED`; alert `expired.signing_cert_expired` | P, R, FFR |
| `SIG-UNTRUSTED` | 2.3.4a | self-signed / unknown CA | chain to the test anchor | `manual_review_required` / `SIG_UNTRUSTED_CHAIN` | P, R, FFR |
| `SIG-IMAGE` | 2.3.4a; design C3 | printed "Digitally signed by … / Signature valid" mark with no /ByteRange | real signature with a visible appearance | `manual_review_required` / `SIG_IMAGE_ONLY`; alert `suspected_anomaly.signature_image_only` | P, R, FFR |
| `SIG-SIGNER` | 2.3.4a; Annex-2.1 | valid signature, signer token ≠ `signatory_token` | signer token = `signatory_token` | `manual_review_required` / `SIG_SIGNER_NOT_MATCHED` | P, R, FFR |
| `SIG-REVOCATION` | 2.3.4a | test OCSP/CRL endpoint down | endpoint up | `verification_pending` → `source_unavailable` / `SIG_REVOCATION_UNREACHABLE` | P, R, FFR |
| `SIG-UPLOADER-MISSING` | 2.3.4a | compiled file without the institution's DSC | uploader DSC present | no label; flag `missing_info.uploader_dsc_missing` / `UPLOADER_DSC_MISSING` | P, R, FFR |
| `STAMP-CHRONO` | 2.3.4b; design D1 | stamp issued after notarisation; DSC mark two days after notarisation on the same page | all five dates the same day; MM/DD vs DD/MM ambiguous date resolved per template year | `chronology` → `manual_review_required`; alert `suspected_anomaly.stamp_chronology` | P, R, FFR, date extraction accuracy |
| `STAMP-PARTY` | Annex-2.1(i); 2.3.4b | duty ₹50; Second Party not the Council | duty ₹100, Second Party as required | `format` → `mismatch_detected` | P, R, FFR, extraction accuracy (certificate no., duty, party) |
| `STAMP-INSTRUMENT` | Annex-2.1(i) | physical non-judicial paper (no e-stamp certificate) | e-stamp certificate | `manual_review_required` | P, R, FFR |
| `NOTARY-EXPIRY` | Annex-2.1(i) | notary seal expiry before the notarisation date | expiry on the notarisation date | `expired` | P, R, FFR, expiry-date extraction accuracy |
| `UDIN-STRUCT` | Annex-2.1(vii) [VERIFY: UDIN not named in APH]; design B1 row 7 | 17 characters; chars 3–8 ≠ printed membership no.; YY before the FY end | valid UDIN; FRN printed 6+1 and 7+1 (leading zero) | `format` → `manual_review_required` | P, R, FFR, extraction accuracy |

### 5.3 M7 source verification (P-5) — slice 5
Adapters run in mock mode; every truth item expects `source.mode: "mock"` and the UI tag MOCK SOURCE.

| Rule ID | APH clause | Planted anomaly | Clean control | Ground truth | Metrics |
|---|---|---|---|---|---|
| `SRC-ESTAMP` | Annex-2.1(i) | certificate no. not in the mock register; duty differs from the register | register record matches | `source_lookup` → `mismatch_detected` with `field_diff[]` / `verified` `SRC_MATCH` | label accuracy, source-verification rate, P, R |
| `SRC-FORMD` | Annex-2.1(iii); Annex-14 | licence no. unknown; validity ended before the processing date | record matches and valid | `mismatch_detected` / `expired` / `verified`; alert `expired.document_expired` | label accuracy, P, R, FFR |
| `SRC-FIRE` | Annex-2.1(v); Annex-3 3.1d | QR plain text names another approver/date; licence no. unknown | QR text matches printed fields | `qr_consistency` + `source_lookup` outcomes | label accuracy, P, R, FFR |
| `SRC-NONE` | PS FR3; Portal §2.6.3 | — (structural: audited accounts, Tahsildar certificate) | — | `source_unavailable` + RB-09 manual task; alert `pending_source.source_unavailable` | task-creation rate = 1.0 |
| `SRC-RETRY` | Portal §2.11 | mock source times out 3 times | answers on retry 2 | `verification_pending` while retrying, then `source_unavailable`; alert `pending_source.source_pending_overdue` | label accuracy |

### 5.4 M3 classification and template choice (P-2) — slice 3
| Rule ID | APH clause | Planted anomaly | Clean control | Ground truth | Metrics |
|---|---|---|---|---|---|
| `DOC-CLASS` | Annex-2.1; design C3 | "Format-2" heading over a Trust resolution; affidavit uploaded in the fire slot | correct slot with a misleading file name (file names are ignored) | `Document.classified_type`; alert `suspected_anomaly.document_misclassified` | classification accuracy, P, R, FFR |
| `TPL-VERSION` | design C3, D4 | 2023-24 affidavit with an Increase-in-Intake block; 2020-21 "UNDERTAKING" | 2024-25 / 2025-26 / 2026-27 drafts (same text, different AY line) | `template_id` | template-choice accuracy |
| (extraction) | — | scanned/rotated variants once OCR lands | text-layer variants | `printed{}` per field | extraction accuracy per document type |

### 5.5 Issuer, entity, height/area checks (P-6, M3/M4/M9) — slices 3 and 6
| Rule ID | APH clause | Planted anomaly | Clean control | Ground truth | Metrics |
|---|---|---|---|---|---|
| `ISSUER-TYPE` | Annex-14; Annex-2.1(iii) | revenue (Tahsildar) occupancy certificate | TN e-District Form D | `manual_review_required` | P, R, FFR |
| `ENTITY-MATCH` | Annex-2.1(iii), (v) | certificate names a sister institution | same institution, name in capitals | `mismatch_detected` | P, R, FFR |
| `BLOCK-COVER` | Annex-2.1(iii), (v) | fire licence covers the hostel block only | separate college and hostel licences | `mismatch_detected` | P, R, FFR |
| `FORMD-PURPOSE` | Annex-2.1(iii) | purpose "School" | purpose higher education | `mismatch_detected` | P, R, FFR |
| `FIRE-NMSB-HEIGHT` | Annex-3 3.1d | "NMSB" licence for a 16.5 m building | NMSB at 14.9 m | `mismatch_detected` | P, R, FFR, height extraction accuracy |
| `FIRE-AREA` | Annex-3 3.1d | licence built-up area / floors below `buildings[]` | equal within 1 % | `mismatch_detected` | P, R, FFR, area extraction accuracy |
| `OCC-CLASS` | Annex-3 3.1d | occupancy class outside education | Group-B educational | `manual_review_required` | P, R, FFR |
| `COND-CLAUSE` | design D5.3 | Form B "annual repair or cancelled" clause | no condition | `manual_review_required`, severity info | P, R, FFR |

### 5.6 M4 APH date and consistency rules (P-7) — slice 6
| Rule ID | APH clause | Planted anomaly | Clean control | Ground truth | Metrics |
|---|---|---|---|---|---|
| `FIRE-VALID` | Annex-3 3.1d | expired on the processing date; "valid for three years from date of issue" computed expiry passed | valid; computed expiry in the future | `expiry` → `expired` (`basis: printed` / `computed_from_state_rule`); alert `expired.document_expired` | P, R, FFR |
| `FORMD-VALID` | Annex-2.1(iii); TN 3-year licence | lapsed | valid | `expired` | P, R, FFR |
| `EXPIRING-SOON` | Portal §2.9 | expires in 45 days | expires in 90 days | alert `expired.expiring_soon` | P, R, FFR, alert timeliness |
| `PARTIAL-OC-2Y` | Annex-3 3.1c | partial OC in a 3rd consecutive AY | partial OC in the 2nd AY | alert `expired.partial_oc_limit_reached` | P, R, FFR |
| `STRUCT-30Y` | Annex-2.1(iv) | CC older than 30 years, no structural certificate | 29 years; or certificate present | `missing_info.document_missing` | P, R, FFR |
| `LEASE-REMAIN` | 2.1(e) | remaining lease = longest course duration, no 30-year extension | extension present | flag, critical | P, R, FFR |
| `COMPLIANCE-WINDOW` | Portal §2.10; 2.5(c) | deficiency still open after the window | evidence submitted in time; window text missing → `window: unknown`, manual review, no invented deadline | alert `unresolved.compliance_window_lapsed` / `_expiring` | P, R, FFR, timeliness |
| `TRUSTEE-TENURE` | design D5.5 | Chairman tenure ended before the application date | open tenure | flag, warning | P, R, FFR |
| `CERT-DATES` | design D5.5 | valid-till before issue date | ordered dates | flag, warning | P, R, FFR |
| `SNAP-CONSIST` | design D5.5 | deed areas do not sum to `land.total_area`; hectares vs acres mismatch; approved ≠ sanctioned | sums equal after unit conversion | flag, warning | P, R, FFR |

### 5.7 M13 year-over-year (P-8) — slice 4
Truth items carry `yoy{ay_a_ref, ay_b_ref, verdict}`; every rule has an **explained** control (an approved application that accounts for the change).

| Rule ID | APH clause | Planted anomaly (`discrepancy`) | Clean control (`explained` or unchanged) | Metrics |
|---|---|---|---|---|
| `YOY-INTAKE` | 2.25, 7.3 | intake up with no approved increase | increase approved in the previous EoA letter | P, R, FFR, verdict accuracy |
| `YOY-ENROLMENT` | 2.25n, 7.3 | admissions above intake after supernumerary seats | above intake only by TFW/EWS/NRI heads | P, R, FFR |
| `YOY-LAND` | Annex-3 3.1g; Table 2.3 | land area or deed set changes, no change-of-site/merger | approved merger in the EoA letter grid | P, R, FFR, verdict accuracy |
| `YOY-ROOMS` | Annex-3 | carpet area shrinks, intake same or higher | shrink with an approved intake reduction | P, R, FFR |
| `YOY-FACULTY-CHURN` | 6.14c | > 40 % token churn [VERIFY threshold] | normal churn | P, R, FFR |
| `YOY-CC-DATE` | Annex-2.1(iv) | CC date differs from earlier years | same CC date | P, R, FFR |
| `YOY-FIRE-REUPLOAD` | Annex-3 3.1d | last year's expired licence re-uploaded | renewed licence | P, R, FFR |
| `YOY-STAMP-REUSE` | 2.3.4b | e-stamp certificate no. reused across years | new certificate | P, R, FFR |
| `YOY-UDIN-REUSE` | Annex-2.1(vii) | UDIN reused for another FY | one UDIN per FY | P, R, FFR |
| `YOY-COORDS` | Annex-2.1(vi) | coordinates move > 500 m [VERIFY threshold] | same point in DMS vs decimal | P, R, FFR |
| `YOY-DEFICIENCY-REPEAT` | 2.5(c); Portal §2.10 | same self-disclosure deficiency after the window | resolved within the window | P, R, FFR |
| `YOY-STRUCTURAL-CHANGE` | Table 2.3 | "Merger … Approved" not reflected in land/rooms/programmes | reflected | P, R, FFR |

### 5.8 M8 identity graph (P-9) — slice 7
Faculty appear only as tokens (`fac_tok_…`). The portal's `is_duplicate` and `pan_validation` columns are imported (`provenance: portal`) and must never produce a SATYA flag (control: a portal duplicate with no SATYA finding).

| Rule ID | APH clause | Planted anomaly | Clean control | Metrics |
|---|---|---|---|---|
| `ID-LAG` | 6.14c | relieved in January, removed from the portal in March | removed in the same month | P, R, FFR |
| `ID-CROSS-INST` | 6.14c, 6.14i | same token at another institution in the same AY | moved institutions between AYs | P, R, FFR; alert `suspected_anomaly.identity_graph` |
| `ID-WEBSITE` | Annex-18 | website list token absent from the portal list | lists equal | P, R, FFR |
| `FAC-COUNT` | design D5.5 | course-wise faculty count ≠ list rows | equal | P, R, FFR |

### 5.9 M9 coordinates and plots (P-13) — slice 10
| Rule ID | APH clause | Planted anomaly | Clean control | Metrics |
|---|---|---|---|---|
| `COORD-PARSE` | Annex-2.1(vi) | — (extraction) | D/M/S with decimal seconds, decimal degrees, portal integer D/M/S | extraction accuracy (≤ 1 m after conversion) |
| `COORD-DISTRICT` | Annex-2.1(vi); affidavit decl. 2 | point outside the declared synthetic district polygon | inside | P, R, FFR |
| `LAND-PLOTS` | Annex-3 3.1g | 4 plots, or two plots 2.3 km apart | 3 plots within 1.9 km | P, R, FFR |

### 5.10 Cross-cutting rules
| Rule ID | Module | Planted | Control | Metrics |
|---|---|---|---|---|
| `ROUTE` | M1 (P-1), Table 2.3 | category set needing Scrutiny (e.g. increase in intake) | EoA Only, NRI seats → self-disclosure | routing accuracy |
| `DOC-MISSING` | M1 (P-1), Annex-2.1 | Annexure-2.1 slot empty | all 7 present | P, R, FFR; alert `missing_info.document_missing` |
| `X-FIELD` | M2 (P-19), Portal §2.6.1 | snapshot with `faculty[].pan` / `hoi` | tokenised snapshot | rejection rate = 1.0 (`PERSONAL_DATA_REJECTED`) |
| `DOC-HASH` | M2 (P-19), Portal §2.1 | fetched bytes differ from `sha256` | equal | rejection rate = 1.0 (`DOC_HASH_MISMATCH`) |
| `BAND` | M10 (P-14) | ≥ 1 critical flag | clean case | band agreement; a band always lists its contributing flags; never shown to INS |
| `ALERT-MAP` | M11 (P-12), Portal §2.9 | every truth flag | — | type/subtype mapping accuracy = 1.0; alert timeliness p50/p95 |

## 6. Running the M5 set now
- `uv run pytest packages/affidavit -k metrics -s` generates the 104 affidavits into a temp directory, runs M5, compares with `truth.json` and prints a per-rule table (precision, recall, FFR, extraction accuracy) for the dev and held-out seeds.
- `make synth` regenerates the committed demo cases under `data/synthetic/cases/`; the test suite fails if the committed PDFs differ from a fresh generation.
- Later modules add their own `-k metrics` test and a row block to the summary printed in the PR handoff.
