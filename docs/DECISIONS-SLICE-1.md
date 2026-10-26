# Decisions: slice 1 (demo script, test-set plan, M5 affidavit diff P-3)
One line per non-obvious choice. Specs: design v2.2.1, Portal spec v0.2.1, UI spec v0.7.1.

## Contracts
- **`AffidavitDiff` is a new shared schema** (`packages/shared-types/schemas/affidavit-diff.schema.json`), field names from UI §6.3; it reuses `Flag`, `Region` and `SignatureCheck`, so RB-05, the API and the tests share one source of truth.
- **Declaration numbering restarts in the existing-institute block** (core 1–19, then 1–5), following design B1 row 1 ("Existing Institute decl. 3"). The contract keeps a canonical `no` 1–24 plus `printed_no` and `block`, and sworn declarations add a `block` (`extra` for a block the draft does not print). [VERIFY] the numbering on a real 2024-27 draft.
- `category_line.state` adds `different` to the spec's `present | missing | extra` (a category line that lists other categories is neither missing nor extra).
- `stamp`, `chronology`, `issuer_sig` and `uploader_sig` are in the contract but `null` until M6 (P-4); a `pending[]` list tells the UI which module fills them, so no panel is silently empty.
- Table rows carry `state` (`matched | differs | missing_in_sworn | extra_in_sworn`) and `flag_ids`; ops carry `flag_id`. The land total flag has no row and is shown beside the computed total.

## Template and rules
- **Template wording is our own synthetic paraphrase** of the APH digest (structure from B1 row 1/D3, stale "Appendix 16/17", "Regulation Regulations, 2021" kept). The real portal wording stays on the team laptop; [VERIFY] before any claim of wording fidelity.
- The regulation name in declaration 16 is written as "the Council's … Regulations" so no synthetic document spells out the regulator's full name as a heading-like string.
- Option groups (`[[group: a|b]]`) model strike-through choices: Principal/Director, owned/leased, Trust/Society/Company. Any surviving valid choice equals the draft; the choice is reported in `options[]`.
- Rule IDs follow the Portal §2.14 example (`AFF-CAT-LINE`, `LAND-AREA-RECON`). `LAND-AREA-RECON` keeps the example's `Annex-3 3.1g` citation and `ROOM-RECON` / `ROOM-ID-DUP` cite clauses marked [VERIFY] in the YAML.
- All M5 flags are `preliminary_indicator: true` (safer default). `institution_visible` follows UI §1.1: table and header inconsistencies yes, declaration changes no (anomaly indicators reach the institution only after an official escalates).
- `ROOM-ID-DUP` is labelled `manual_review_required`, not `mismatch_detected`: a duplicate ID can be an aggregate row (D3), not necessarily an error.

## Engine
- **Text layer only** (pdfplumber 0.11.10, MIT). No text layer → no flags and `pending: ocr (M3, P-2)`; we never guess.
- Strike-through = a horizontal line crossing a glyph between 30 % and 80 % of its height, excluding table rules. Struck characters are dropped before comparing.
- Hyphen re-join is vocabulary-aware: "Self-" + "Financing" keeps the hyphen when the draft has "Self-Financing"; otherwise the hyphen is a line-break artefact.
- Declarations are aligned **by content** (order-preserving Needleman–Wunsch on word similarity, threshold 0.45), so a dropped declaration with renumbering is one removal, not a cascade of changes.
- Equality is on a canonical form: NFKC, ASCII dashes/quotes, whitespace removed, case folded, institution/trust names, AID, PID and AY substituted, option groups tokenised.
- Dates follow the template year (portal affidavit MM/DD/YYYY, design D4); an impossible month is retried in the other order and counted as `date_order_fallbacks`, not flagged.
- **Deeds are matched by the keyed HMAC token of the document number** (a T field, Portal §2.6.1); holder and document number are masked in every output. Identifier tokens drop all whitespace because a number wrapped in a narrow cell comes back with a space (the M5 eval found this; the gateway's M2 tokeniser must use the same normalisation).
- A snapshot that already carries `deed_token` (post-gateway form) reconciles without the raw number.
- Flag and doc IDs are deterministic (SHA-256 of document hash + check_ref + rule version), so a replay gives identical JSON (Portal §2.11).
- The land total is computed from the sworn rows and compared with `land.total_area` in acres (hectare and m² converted); a changed deed area yields the row flag and the total flag.

## Synthetic data and metrics
- The generator draws with the reportlab canvas (BSD; dev dependency only, never in a runtime image) using its own layout code, so hyphenation, strike-through and table geometry are exactly controlled and output is byte-deterministic (`invariant=True`).
- 8 TN profiles: dev seeds 03, 05, 07, 11 and held-out 09, 13, 15, 17; 4 clean render styles + 9 planted variants = 104 affidavits. The demo case (DIT 03) combines four plants.
- The demo PDFs are committed (`data/synthetic/cases/`) so the API image and the demo need no generator; `synth --check` (CI and tests) fails if they drift. Every page says SYNTHETIC; the stamp page is a labelled mock, not an instrument.
- Generated footers read "Approval Portal (Mock, for demo)" rather than the regulator's name (guard rail 2, UI §0.9).
- Metrics are 1.000 across the board on both seed sets. This shows the pipeline is wired correctly end to end. It does not show real-world accuracy, because the generator and the engine were written together; real-format validation needs the laptop-only samples (blocker below).

## API and web
- **Slice 1 serves the committed synthetic cases read-only** (`FixtureCaseRepository`, `SATYA_DEMO_CASES_DIR`) instead of the ingest path (`application.submitted` → M2 vault → worker), which belongs to P-19/P-17. The repository checks the snapshot schema and the PDF's SHA-256 before running M5, runs one M5 job at a time off the event loop and caches by document hash.
- Workbench API auth: RS256 access tokens checked against the realm JWKS (internal URL, cached 10 min, refetch on unknown `kid` at most every 30 s), public issuer, expiry, `azp = satya-web` and `typ = Bearer` (an ID token is refused). `aud` is not checked because Keycloak's default access-token audience is `account`; `azp` pins the client instead.
- RB role required; case scope = the token's `/regions/*` groups (`national` sees all). Out-of-region → 403 `SCOPE_DENIED` ("Not assigned to you", UI SH-09); unknown or malformed case ID → 404. Per-user quota (`SATYA_USER_RATE_LIMIT`, default 300/min) besides the per-IP limit.
- `GET /v1/cases` is an interim, region-scoped list (case, application, region, AY, route, stage, open findings) so RB-05 is reachable from the queue; the risk-banded RB-02 queue stays with M11.
- **No refresh token in the web session.** Keycloak rotates refresh tokens (`revokeRefreshToken: true`) and React Server Components cannot write cookies, so a refreshed token could not be persisted. The 5-minute access token is stored in the encrypted session cookie; when it expires the page redirects to `/signin?renew=1`, which re-runs the SSO flow silently while the Keycloak session is alive. Token refresh in the proxy is a known gap.
- Sign-out now reads the session with `getToken`, which re-assembles a session cookie next-auth split into chunks (the access token can push it past 4 kB).
- The case header shows no tab strip yet: the other case tabs (Summary, Documents, Verification, Year-over-year, …) belong to later slices and would be dead links. The case breadcrumb is plain text for the same reason.
- FlagCards show "No disposition recorded yet"; the DecisionBar is M11 (P-10). Long values are shortened to 160 characters in the card; the full text is in the clause diff.
- Masked cells render bullets hidden from screen readers plus a visually hidden "masked, ends in …".
