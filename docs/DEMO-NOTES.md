# Demo notes (Slice D)
Synthetic data only. Mock approval portal. Advisory only. Reset first: `make demo-reset`.

## Say this at the start, and again at the end
"Everything here is synthetic. The portal is our own mock, not the AICTE portal. Every source answer is labelled MOCK SOURCE and the signature chain is checked against a TEST TRUST ANCHOR that proves nothing outside this demo. SATYA advises. Officials decide. There is no approve or reject button."

## Click path (about 6 minutes)
| Step | Where | Do | What it proves |
|---|---|---|---|
| 1 | https://localhost, sign in as `rb.southern.demo` | Land on the validation queue | Five synthetic cases, each with a text band (High, Medium, Low), documents counted by label, findings, status, top reasons |
| 2 | Queue | Sort by Institution, filter Risk band = High, then Clear filters | Deterministic ordering and filtering without scripts |
| 3 | Open `1-90000004217` (Demo Institute of Technology 03) | Read the band and the three top reasons | The band comes from stored findings and labels. The line "The band orders review only" is on screen |
| 4 | Same case, Documents and labels | Point at the affidavit: MANUAL REVIEW REQUIRED, issuer badge IMAGE ONLY, uploader badge UPLOADER SIGNATURE PRESENT | A valid uploader signature does not make the document verified; a printed "digitally signed" mark is never a signature |
| 5 | Same table | Point at the audited statement: SOURCE UNAVAILABLE and the manual task | No UDIN printed, so no source can answer; a manual task is created |
| 6 | Findings | Choose Show in document on the land area finding | PDF.js opens page 3 and outlines the row. The card shows rule id, APH clause, extracted 3.5 acre vs expected 4.5 acre, and a fixed-template reason |
| 7 | Decision bar on that finding | Pick "ESCALATE → send for manual verification", type a reason, Record decision | Five dispositions only, reason of 10+ characters, ledger entry number returned. Nothing changes regulatory status |
| 8 | Audit trail | Read CHAIN VERIFIED, open the newest entry | Every upload, check, source response and decision is a hash-chained entry; the chain is recomputed on each visit |
| 9 | Alerts | Read the list, follow a link | Alerts come from stored data: High band, expired certificate, source unavailable |
| 10 | Case `1-90000005105` (clean control) | Open it | LOW band, both documents VERIFIED (both source answers are MOCK SOURCE) |
| 11 | Add documents tab on any case | Use a seeded document from another case | The file is hashed, the checks run again and the new entries appear in the audit trail |

Other cases to mention if time allows: `1-90000011111` (e-stamp number already used on a prior filing, manual review), `1-90000007107` (UDIN structure problem), `1-90000009109` (issuer certificate had expired at signing, label EXPIRED).

## The six labels, as built
VERIFIED, MISMATCH DETECTED (broken digest, edit after signing, revoked certificate), EXPIRED, VERIFICATION PENDING, SOURCE UNAVAILABLE, MANUAL REVIEW REQUIRED (untrusted chain, signer name mismatch, image-only mark, reused stamp, UDIN problem). The uploader's own signature never makes a document verified.

## What is mock and what is synthetic
- Mock: the approval portal; the SHCIL e-stamp lookup (`shcil-estamp-mock`); the ICAI UDIN lookup (`icai-udin-mock`, a structure check, not an ICAI lookup). Each shows MOCK SOURCE.
- Offline: the signature chain check against the TEST TRUST ANCHOR (a generated demo root).
- Synthetic: every institution, application ID, document, certificate, stamp number and UDIN. Institutions are "Demo Institute of Technology NN" and "Demo College of Engineering NN".
- Results claim: "all planted cases detected on synthetic test sets". The generator and the rules were written together, so this does not describe real documents. Do not quote any percentage.

## Not built (say so if asked)
Scans and OCR (M3), intake vault with redaction and tokenisation (P-19), identity graph, year-over-year, EVC selection, the full mock portal screens, manual-task screen (RB-09), case replay, Hindi for these screens, hosting, HTTPS tunnel, mobile app. The stage-1 private pre-check is not part of this flow and never feeds the band.

## If something looks wrong
- Queue empty or audit empty: run `make demo-reset`.
- Audit shows CHAIN BROKEN: someone edited the database by hand. Run `make demo-reset`.
- A PDF page does not draw: reload; the viewer needs the workbench origin and no extension blocking workers.
