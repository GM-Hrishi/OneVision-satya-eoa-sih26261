# Slice W progress: truthful wording and consistent labels (B-43)

NEXT: W9 open PR, wait for CI, report

- [x] W0 setup
- [x] W1 inventory (below)
- [x] W2 D2 codes and roadmap lines
- [x] W3 D3 reason sentences and OCR source line
- [x] W4 D1 comparison state
- [x] W5 D4 one source of truth
- [x] W6 D5 audit labels
- [x] W7 tests
- [x] W8 (gitleaks not installed here; smoke and Playwright run in CI) full checks
- [ ] W9 PR

## W1 before-list

### D2 offending strings (apps/web/messages en.json + hi.json, same keys)
| key | en text |
|---|---|
| diff.textLayer | Text layer (OCR arrives with M3) |
| diff.signaturesPending | Issuer and uploader signature checks arrive with M6 (P-4). |
| diff.stampPending | Stamp details, notarisation and the order ... are checked by M6 (P-4). They are not evaluated on this page yet. |
| diff.dispositionPending | No disposition recorded yet. Officials record decisions with the decision bar (M11, P-10). |
| diff.stampStateNote | Format checks on the stamp page. The e-stamp lookup itself arrives with M7 (P-5). |
| verification.issuerProfilePending | Not profiled yet (Annexure-14 issuer profiles arrive with M3/M4, P-6) |
| verification.actionsNote | Re-check, route to manual verification and retry arrive with M11 (P-10). Suggested here: {actions}. |
| accessibility.limitsBody | "...a full audit with assistive technology is planned before any pilot." (word "planned") |
Other user-facing sources: services/api/src/satya_api/main.py /v1/meta text ("No source adapters in slice 0 ... arrive ... with M7 (P-5)"); schema descriptions in affidavit-diff, case-verification, event-envelope schemas (generated TS/Pydantic carry them); `pending` array in AffidavitDiff carries module "M6"/"P-4" codes (engine output, not shown as text; UI only reads `section`). hi.review.json holds reviewer notes, not shown to officers.

### D1 where it lives
apps/web/src/components/diff/DiffView.tsx: noFlags (flag rail), noChanges / changesCount (clauses), normalisation note. API has no "compared" state: engine `_empty` or OCR text yields empty ops. m5_diff in services/api/src/satya_api/cases.py is where the read (OCR) is known.

### D3
Case tab: (review)/page.tsx `case.task` uses `reason.<CODE>` map (demo.reason) or raw code; Verification tab: VerificationPanel.reasonText (verification.reason.*) shows raw code when no key. DiffView text source row uses diff.textLayer / diff.ocr. The sentence exists: read.why / demo.ocr.why.<variant>.

### D4 root cause
Case tab data = Workflow.analyse (M6 result + source hub apply_hub + OCR gating). Verification tab data = CaseRepository.verification -> case_verification(M6 result only): no hub, no OCR gating. So the UDIN document is Verified (SRC_MATCH) on one and Source unavailable (NO CHANNEL) on the other.

### D5
Ledger kinds written: see W6.
