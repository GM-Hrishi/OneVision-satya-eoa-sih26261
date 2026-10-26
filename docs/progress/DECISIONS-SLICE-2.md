# Decisions: slice 2 (M6 signatures, stamp chronology, PDF forensics P-4; UDIN structure P-18)
One line per non-obvious choice. Specs: design v2.2.1 (B1 rows 1 + 7, C3, D1, D4, D5), Portal spec v0.2.1 (§2.6.3, §2.7, §2.8, §2.9), UI spec v0.7.1 (§4.3, §6.3, §6.4, §7.1, §7.2).

## Test PKI and synthetic documents
- **Keys are Ed25519 derived from public seeds** (`SATYA TEST PKI | <name>`): certificates, CRL and signatures are byte-for-byte reproducible and no private key is ever stored. Anyone can derive them, so they prove nothing outside the tests. Root "SATYA TEST TRUST ANCHOR", shown as TEST TRUST ANCHOR (guard rail 10).
- Real Indian DSCs are mostly RSA-2048; Ed25519 is used only because it is deterministic. pyHanko validates both. [VERIFY on laptop samples: RSA chains to CCA].
- **pyHanko 0.38.0 (MIT)** signs and validates. Fixtures pin the signing time, the /ModDate it writes into Info and XMP, and the second half of the trailer /ID, so `make synth-check` stays byte-exact.
- `make synth` is now owned by `satya_forensics.synth`: the served sworn copy is the signed one, and M5 and M6 must read the same bytes (same SHA-256, same doc_id). `python -m satya_affidavit.synth` keeps only `--bulk` for the M5 corpus.
- The slice-1 generator gained two hooks (case metadata, print model). The e-stamp page now prints SHCIL-style fields (certificate no., issue date-time, Article, First/Second Party, duty) and a physical-paper variant; the stamp page is still marked SYNTHETIC … (MOCK).
- The printed "Digitally signed by … / Signature valid" mark is **text in the page content** (like a flattened stamp appearance). Raster marks need OCR (M3, P-2) and are a known gap.
- Dates: application D, stamp D+1, notarisation D+2, deponent DSC D+3 10:15 IST, uploader DSC and upload D+3 16:30/16:40, submission D+4. The demo case moves the image mark to notarisation + 2 days (F5) and the upload with it.
- Benign incremental update = DSS (validation data) or an Info-dictionary change. An added text annotation after signing was reported as a page-object rewrite (OTHER) by pyHanko's diff policy, so it is not used as a "benign" control.
- A synthetic register of earlier filings (`data/synthetic/registry/prior-filings.json`): each profile's 2025-26 e-stamp number, FY 2024-25 UDIN and a same-FY "sister filing" UDIN by the same partner. Reuse rules compare against it plus the other current cases.
- 22 planted variants + 10 noisy-but-clean controls (31 %) × 8 profiles = 256 cases; dev seeds 03/05/07/11, held-out 09/13/15/17 (same split as M5).

## Signature checks
- **V-8 confirmed:** `pyhanko.sign.validation.validate_pdf_signature(EmbeddedPdfSignature, ValidationContext)` → `PdfSignatureStatus.intact`, `.valid`, `.coverage` (SignatureCoverageLevel), `.modification_level` (ModificationLevel NONE/LTA_UPDATES/FORM_FILLING/ANNOTATIONS/OTHER), `.docmdp_ok`, `.trust_problem_indic`, `.bottom_line`.
- Modified after signing = coverage below ENTIRE_FILE **and** (level OTHER or DocMDP violated). DSS/Info updates (LTA_UPDATES) and later signatures (FORM_FILLING) are benign.
- Validation moment = the signer's claimed CMS signingTime (no TSA in the demo). [VERIFY: production should require a timestamp token or LTV data.]
- Chain building, validity window and revocation are done by SATYA on top of pyHanko (chain via `verify_directly_issued_by`, CRL via a mock endpoint registry with 3 retries), so each failure maps to exactly one Portal §2.8 reason code instead of interpreting pyHanko's AdES sub-indications.
- Order when several apply (most severe first): digest > modified > revoked > expired/not-yet-valid > untrusted > signer mismatch > CRL unreachable.
- **Which signature is whose.** Affidavit: real signatures in revision order; with ≥ 2, the first is the deponent's (issuer) and the last the uploader's. With one, it is the uploader's if a separate printed mark claims to be the deponent's signature, otherwise the issuer's (uploader missing). External documents: the last signature whose signer token equals `signatory_token` is the uploader's; another signer is the issuing authority's. [VERIFY on laptop samples of compiled uploads.]
- A printed mark under a real signature's visible widget is that signature's appearance, not an image (control `clean_visible_sig`).
- Signer check = keyed token of the certificate CN (whitespace and case normalised, same tokeniser as M5) vs `signatory_token`; applied to the affidavit's issuer and to every uploader. Certificate Title gives `signer_role`.
- An affidavit with no digital signature at all gets an issuer check `manual_review_required` / `SIG_NOT_DIGITAL` (not in Portal §2.8; added). For external documents a wet issuer seal is not a finding (badge NOT DIGITAL (WET SEAL), no check).
- `UPLOADER_DSC_MISSING`: no check and no document label (Portal §2.8). The flag schema requires a label, so the flag carries `manual_review_required`.
- Document label = most severe check outcome; `verified` needs a passing issuer signature or source lookup. A document whose only passing checks are the uploader signature and format checks is `manual_review_required`.
- Mark text and signer names are never copied into flags (the SIG-IMAGE flag says "printed mark without /ByteRange").

## Stamp, notary, chronology
- Rules split for per-rule metrics: STAMP-PARTY and STAMP-DUTY (test-set plan v1.0 had one STAMP-PARTY row), STAMP-INSTRUMENT, STAMP-REUSE, NOTARY-EXPIRY, STAMP-CHRONO with two keys (`chronology:order`, `chronology:mark_after_notary`).
- Chronology compares IST calendar dates. DSC date = the deponent's real signing time, else the printed mark's date (`dsc_kind` says which). A printed mark dated after notarisation is its own finding even when the order holds (design D1 review case).
- Second Party = the Council when it contains "AICTE" or the Council's full name. [VERIFY: from executed copies, not APH text.]
- Stamp section `state` = the worst stamp finding, else `verification_pending`: the SHCIL lookup that can actually verify an e-stamp is M7 (P-5). It never feeds the document label.
- Certificate numbers are masked (`•••` + last 4) in API output and flags (Portal §3 masking default); the reuse check compares the full number server-side.
- Stamp page dates are read SHCIL-style (`21-Nov-2026 11:05 AM`); notary dates in the template's order (MM/DD/YYYY) with the M5 impossible-month fallback. Control `clean_ambiguous_dates` (all days ≤ 12) proves the order is respected.

## UDIN (P-18)
- Structure YY + 6-digit membership no. + 6 letters + 4 digits (design B1 row 7 [VERIFY]); YY must lie between the FY end year and one year after (`max_year_gap: 1`).
- Membership no. compared after zero-padding to 6 digits; UDIN read with spaces removed (control `clean_udin_spaced`).
- No ICAI channel: every audited statement gets a `source_lookup` check `source_unavailable` (`icai-udin`, mode `none`; `SRC_NO_CHANNEL`, or `SRC_NO_IDENTIFIER` with no UDIN printed). This keeps demo F10 as SOURCE UNAVAILABLE + manual task.
- Portal §2.9 has no UDIN alert subtype: UDIN-STRUCT and UDIN-MEMBER map to `missing_info.field_missing`, UDIN-REUSE to `suspected_anomaly.yoy_discrepancy`. [VERIFY with M11.]

## Contracts and API
- New `CaseVerification` schema (UI §6.4). `issuer_sig` / `uploader_sig` reuse `SignatureCheck` (so `detail` → `reason_code`, `chain` → `trust_anchor_label`); per-document `checks[]` and `flags[]` are additive, so RB-06 can show findings no other P1 screen shows yet (UDIN).
- Additive fields: `Check.check_ref`, `signed_at`, `trust_anchor_label`; `AffidavitStamp.article`, `issue_date`, `page`; `AffidavitChronology.dsc_kind`, `mark_after_notary`, `notary_expiry_ok`.
- The affidavit diff endpoint now merges M6 (badges, stamp, chronology, the affidavit's M6 flags); `pending` keeps only `ocr`. `GET /v1/cases` counts M5 + M6 flags.
- M6 runs once per case per set of document hashes, off the event loop, behind the same one-at-a-time gate as M5. Trust store and CRL come from `data/synthetic/pki`, the register from `data/synthetic/registry` (both copied read-only into the API image).
- `checked_at` / `last_full_run_at` = when the gateway computed the result (not part of the deterministic run output).

## Web
- RB-06 at `/case/[id]/verification`; RB-05 and RB-06 share a two-tab case strip (only built views, no dead tabs).
- SignatureBadge keeps the UI §4.3 badge texts per state and adds a detail line from the reason code (e.g. "The signing certificate was expired …"), so states such as "signer not matched" are not hidden behind CHAIN BROKEN.
- Actions (re-check, route to manual, retry) are listed as text "arrive with M11 (P-10)"; no disabled buttons.
- The workbench imports only types from `@satya/shared-types` (Next.js cannot resolve the package's `.js`→`.ts` runtime re-export), so the label order is a local copy pinned to `LABEL_PRECEDENCE` by a unit test.
- Status chips inside fact lists wrap at narrow widths (the stamp section overflowed by 33 px at 360 px before).
