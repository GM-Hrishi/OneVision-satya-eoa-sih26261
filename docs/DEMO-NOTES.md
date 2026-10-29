# Demo notes (Slice D, UI polish v0.8, scan fallback B-28)
Synthetic data only. Mock approval portal. Advisory only. Reset first: `make demo-reset`.

## Say this at the start, and again at the end
"Everything here is synthetic. The portal is our own mock, not the AICTE portal. Every source answer carries a Simulated source tag and every signature chain a Test trust anchor tag; hover or tab to either tag to read what it means. Neither proves anything outside this demo. SATYA advises. Officials decide. There is no approve or reject button."

## Click path (about 6 minutes)
| Step | Where | Do | What it proves |
|---|---|---|---|
| 1 | https://localhost, sign in as `rb.southern.demo` | Land on the Overview | Seven plain panels: cases by risk band, case status, documents by label, open manual tasks, certificates expiring, recent decisions, sources. Every count is a link |
| 2 | Overview, then Open validation queue | Click High in "Cases by risk band", then Reset filters. Sort by Submitted, press it again, then Reset sort | The queue opens already filtered. Sorting applies inside each risk band (High, Medium, Low stay in order); the header says nothing in words but a screen reader hears "Sorted by Submitted, ascending" |
| 3 | Open `1-90000004217` (Demo Institute of Technology 03) | Read the band and the three top reasons | The band comes from stored findings and labels. The line "The band orders review only" is on screen |
| 4 | Same case, Documents and labels | Point at the affidavit: Manual review required, issuer badge "Image only, not a real signature", uploader badge "Uploader signature present" | A valid uploader signature does not make the document verified; a printed "digitally signed" mark is never a signature |
| 5 | Same table | Point at the audited statement: Source unavailable and the manual task | No UDIN printed, so no source can answer; a manual task is created |
| 6 | Findings | Choose Show in document on the land area finding | PDF.js opens page 3 and outlines the row. The card shows rule id, APH clause, extracted 3.5 acre vs expected 4.5 acre, and a fixed-template reason |
| 7 | Decision bar on that finding | Pick "ESCALATE → send for manual verification", type a reason, Record decision | Five dispositions only, reason of 10+ characters, ledger entry number returned. Nothing changes regulatory status |
| 8 | Audit trail | Read CHAIN VERIFIED, open the newest entry | Every upload, check, source response and decision is a hash-chained entry; the chain is recomputed on each visit |
| 9 | Alerts | Read the cards (High, Medium, Low severity, unread first), follow Open flag | Alerts come from stored data: High band, expired certificate, source unavailable. Opening one moves it to Earlier. The rail shows the latest unread alert |
| 10 | Case `1-90000005105` (clean control) | Open it | Low band, both documents Verified (both source answers carry the Simulated source tag) |
| 11 | Add documents tab on any case | Use a seeded document from another case | The file is hashed, the checks run again and the new entries appear in the audit trail |
| 12 | Case `1-90000013113` (Demo Institute of Technology 13, a clean scan) | Read the label cell of the affidavit | Manual review required with the line "This file is a scan. Pages 1, 2, 3, 4 were read by OCR (confidence NN%)" and one line per scanned page. Without the OCR engine the line says it was not available. Either way the band stays Low: a scan is not evidence of wrongdoing |
| 13 | Case `1-90000015115` (Demo College of Engineering 15, a noisy low quality scan) | Same cell | OCR confidence under 80 percent: "the text read by OCR is not reliable ... An official must read it." No finding is made from that text |
| 14 | Case `1-90000017117` (Demo Institute of Technology 17, mixed file) | Same cell | Only page 2 is an image; the other pages keep their text layer. The page lines name page 2 as scanned |
| 15 | Overview, Open manual tasks, then Add documents on any case | Upload a PDF that is damaged, encrypted or empty | It is stored, labelled Manual review required with a plain reason, a manual task appears on the Overview and nothing returns an error |

Other cases to mention if time allows: `1-90000011111` (e-stamp number already used on a prior filing, manual review), `1-90000007107` (UDIN structure problem), `1-90000009109` (issuer certificate had expired at signing, label Expired).

Header: the account menu (top right) holds Language, Accessibility settings and Sign out. The search field finds an application by ID or institution.

## The six labels, as built
Verified, Mismatch detected (broken digest, edit after signing, revoked certificate), Expired, Verification pending, Source unavailable, Manual review required (untrusted chain, signer name mismatch, image-only mark, reused stamp, UDIN problem). The uploader's own signature never makes a document verified.

## What is mock and what is synthetic
- Mock: the approval portal; the SHCIL e-stamp lookup (`shcil-estamp-mock`); the ICAI UDIN lookup (`icai-udin-mock`, a structure check, not an ICAI lookup). Each carries the Simulated source tag.
- Offline: the signature chain check against a generated test root, tagged Test trust anchor.
- Synthetic: every institution, application ID, document, certificate, stamp number and UDIN. Institutions are "Demo Institute of Technology NN" and "Demo College of Engineering NN".
- Results claim: "all planted cases detected on synthetic test sets". The generator and the rules were written together, so this does not describe real documents. Do not quote any percentage.

## Scans and OCR (B-28), what to say
"A scan has no digital signature, so it can never be Verified. We read it by OCR where we can, mark every finding that rests on OCR as a preliminary indicator with the page confidence, and send anything unreadable to manual review with a fixed sentence saying why. A scan does not raise the risk band." Reason codes: SCAN_IMAGE_ONLY, OCR_LOW_CONFIDENCE, OCR_UNAVAILABLE, DOC_UNREADABLE. Confidence is OCR's own per-page figure, not an accuracy claim. The default threshold is 80 percent and every limit (50 pages, 30 s a page) is configurable.
The three scan cases are made by rasterising our own synthetic affidavits with Pillow (skew, noise, lower resolution). If the image was built without the OCR engine, all three read "OCR engine is not available"; build with `WITH_OCR=1` (the compose default) to see the engine read them.

## Not built (say so if asked)
Template-aware extraction beyond Affidavit 2 (M3 proper), intake vault with redaction and tokenisation (P-19), identity graph, year-over-year, EVC selection, the full mock portal screens, manual-task screen (RB-09), case replay, Hindi for these screens, hosting, HTTPS tunnel, mobile app. The stage-1 private pre-check is not part of this flow and never feeds the band.

## If something looks wrong
- Queue empty or audit empty: run `make demo-reset`.
- Audit shows CHAIN BROKEN: someone edited the database by hand. Run `make demo-reset`.
- A PDF page does not draw: reload; the viewer needs the workbench origin and no extension blocking workers.
