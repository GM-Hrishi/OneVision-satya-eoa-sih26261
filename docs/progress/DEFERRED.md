# Deferred (out of scope on purpose)
- Persisting OCR word boxes in the evidence viewer for scanned pages beyond the finding's own region (a text-selectable overlay).
- Table reading from OCR pages (land and room tables need cell detection; today M5 leaves tables out of OCR pages and says so in `pending`).
- Deskew and denoise before OCR (Pillow or OpenCV) if the laptop run shows the noisy scan can be rescued.
- Hindi translation of the new reason sentences (English text is in place, listed in `hi.review.json`).
- A per-file OCR progress indicator and a retry action once RB-09 exists.
- UI spec v0.9 sections 14 and 10.3 are not in `docs/specs/`; re-run the token reconciliation when the file is copied in.
- Moving OCR into the Celery worker with a queue: the gateway runs one OCR document at a time in a thread, like M5/M6.
- **Accessibility defect (WCAG 2.4.3 Focus Order), found by CI diagnostics on 03bdc30:** after the queue filter "Apply" submit, keyboard focus falls back to the page body because the filter button is replaced (CI line: `DIAG keyboard select: listOpenedByEnter=false expanded=false text="All" {"active":"BODY[]","listboxes":0}`). A keyboard user must tab through the page again after every filter change. Fix idea: keep the same element across the submit (do the filter with a client-side router push instead of a full GET form submit) or restore focus to the filter after the page renders (an `autoFocus` or a focus restore keyed on the query string). Not fixed in PR #8: the cause is not yet traced and the fix is not known to be under 10 lines.
