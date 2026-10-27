# SATYA-EoA workbench + mock portal: UI/UX design spec
**v0.7.1 (25 Oct 2026, 22:00).** Running spec for (a) the SATYA web workbench (`apps/web`, officials arrive from the portal via Keycloak SSO) and (b) the demo stand-in portal (`apps/mock-portal`). Grounded in `claude/SATYA-EoA-v2-process-grounded-design.md` **v2.2 (Research chat's 45-PDF version)** (A2, B1 rows 1 + Application Report, C2, C3, C4/C4a, C6, Part D incl. D2), `claude/SATYA-portal-integration-spec.md` (§1, §2.8, §2.9) and `claude/MASTER-status.md` v5 (#19–#22, X-1, X-5, X-11). Team: OneVision (six members). All mock data is synthetic.

| § | Section | Status |
|---|---|---|
| 0 | Design principles | v0.5 |
| 1 | Roles | v0.7: #19, #20 recorded |
| 2 | Screen inventory + phase tags (X-5) | v0.7: every screen tagged P1 / P2 / later |
| 3 | Navigation and route map | v0.3 (S3 left rail) |
| 4 | Flag anatomy, DecisionBar, signature badges | v0.7.1: X-11 final |
| 5 | Risk display | v0.5 (#20) |
| 6 | Data needs per screen | v0.7.1: alert enum matches Portal §2.9 |
| 7 | Key screen specs + wireframes (deliverable 2) | v0.7: 7 wireframes done |
| 8 | Design system (deliverable 3) | v0.6: locked |
| 9 | Hero mockups (deliverable 4) | v0.7.1: deck PNG exports |
| 10 | Build handoff | Deferred to after 28 Oct |
| 11 | Decisions and open items | Live |
| 12 | Changelog | Live |

---

## 0. Design principles (apply to every screen)
1. **AI advises, the official decides.** Every flag shows: evidence region, rule, APH clause, confidence, status label (§4). Every flag needs a recorded human disposition with a reason (5 dispositions, #20). No approve, reject or auto-clear control exists anywhere in SATYA. Regulatory decisions are taken in the portal by an AICTE official; SATYA records them from the echoed event (integration spec §0).
2. **Provenance is always visible.** Each item is tagged SATYA (our finding) or PORTAL (imported, e.g. Deficiency Report result, the portal's own faculty-duplicate and PAN-validation columns). Per design doc D2, portal-computed items are never presented as SATYA findings.
3. **Case-centric.** Every role converges on one case; documents, diff, verification, M13 and audit are views of it, at most two clicks away.
4. **Process-native.** The case header always shows the Table 2.3 route and current stage (C2 ①-⑦). No committee view is offered for a route that has no committee.
5. **Never colour alone.** Every status carries its full text label (e.g. HIGH, MISMATCH DETECTED) plus colour. No icons on risk chips or status labels; the text alone carries the meaning.
6. **Government web standards.** GIGW 3.0, WCAG 2.1 AA, Hindi/English with no hard-coded strings, full keyboard operation, skip links, visible focus, text resize to 200%, no silent timeouts, motion optional (`prefers-reduced-motion` respected, WCAG 2.3.3).
7. **Personal data minimised.** Faculty shown by pseudonymous token (M8); reveal needs a reason and is logged (AU-04). Mockups show redacted seals/signatures. Application Report personal fields (HOI, trustees, faculty PAN list) never reach the UI unpseudonymised (Portal §3, X-10).
8. **Not an admin template.** Dense, document-first, ledger-like. Anti-patterns from the web-design guidelines in CLAUDE.md are banned (§10.6).
9. **Two visibly different systems.** The mock portal uses a plainer, distinct style (P1 grey) and is titled "Approval Portal (Mock, for demo)". No AICTE logo, State Emblem, AICTE branding or AICTE URL anywhere in either app.
10. **Mismatches must be visible at a glance.** Wherever two values disagree (FlagCard, DiffView tables, YoYView), the wrong value is the heaviest, darkest element in its block (§8.9).

---

## 1. Roles (design doc A2)
| Code | Role | Where they work | Scope |
|---|---|---|---|
| INS | Institution (Chairman/Secretary, Principal) | **Mock portal only**: runs the SATYA check from the portal and sees results there (no workbench login) | Own application; tiered visibility per §1.1 |
| RB | Regulation Bureau official | Workbench | Assigned region(s) / national |
| SC | Scrutiny / Re-scrutiny expert | Workbench, deep link from portal assignment | Assigned sitting only, within its window |
| EV | EVC expert / Regional Office | Workbench | Assigned inspections only |
| HC | SHC / SAC / EC member | Workbench | Listed hearings, read-only evidence |
| RA | Rule administrator | Workbench | Rules, templates, issuer profiles, adapters; no case actions |
| AU | Auditor | Workbench | Read-only ledger, access log, case replay |

**PGRC / SCSC: out of v1 (MASTER #20).**

### 1.1 Institution visibility: private + tiered
- **MASTER #19:** stage ① pre-check results are **private to the institution**: not sent to AICTE, not used in risk scoring (Portal D-1).
- **Tiered visibility (team lead, UI chat, 25 Oct):**

| Item | Institution sees it? |
|---|---|
| Missing fields, incomplete uploads, expired documents, own-data inconsistencies (incl. affidavit vs own portal data after the lock), M13 year-over-year changes in its own data | Yes, with APH clause + how to fix + rectification route |
| Verification labels on its own documents | Yes |
| Anomaly / forgery indicators, raw forensics | Only after an official reviews the flag and chooses Escalate → Ask institution to clarify; then that item, with the evidence the official chose to share, and a response box |
| Risk band | Never (internal triage, not a regulatory finding) |
| Identity-graph hits | Never in raw form; at most "faculty record needs clarification", without other institutions' data |
| Pre-check results to AICTE | Never (#19); only the fact that a pre-check ran is logged |

**Design-doc note:** this chat edited design doc A2 + M11 for tiered visibility at ~18:35, but the Research chat's v2.2 (the 45-PDF version) replaced the file afterwards, so the edit is not in the current doc. The Research chat is the sole design-doc writer (#18); the change is routed via MASTER (§11, U-2).

---

## 2. Screen inventory with phase tags (X-5)
**Phase 1 (P1)** = Tamil Nadu-first self-disclosure EoA end to end (design C6): mock portal, RB validation, documents, affidavit diff, verification with TN mock adapters (#22), M13, alerts, audit. **Phase 2 (P2)** = Scrutiny/EVC categories, risk-ranked EVC selection, SHC/SAC dossiers, rule editing. **Later** = nice-to-have beyond Phase 2.

### 2.0 Workbench shared shell
| ID | Screen | Phase | Purpose |
|---|---|---|---|
| SH-01 | SSO hand-off | P1 | Receives the Keycloak session + optional case deep link from the portal; routes to role home or the case |
| SH-02 | Role switcher | later | Only for users holding two roles; never mixes scopes |
| SH-03 | Global search | P1 | App ID, Permanent ID, F.No., AY; scoped |
| SH-04 | **Alerts centre** | P1 | PS alert types (missing information, expired documents, pending source verification, suspected anomalies, unresolved items); each opens the exact flag. Wireframe W2 |
| SH-05 | Alert preferences | later | Channel and digest per type |
| SH-06 | Help + APH clause reference | P1 | Every clause chip opens the clause text |
| SH-07 | Accessibility + language | P1 | Hindi/English, text size, high contrast; GIGW accessibility statement |
| SH-08 | GIGW footer pages | P1 | About, policies, help, contact, sitemap, last updated |
| SH-09 | State pages | P1 | 403 "not assigned to you", 404, session expired (back to portal), source-outage banner |

### 2.1 Mock portal (`apps/mock-portal`)
| ID | Screen | Phase | Purpose |
|---|---|---|---|
| MP-01 | Login | P1 | Institution or demo-official login (synthetic accounts) |
| MP-02 | Application form | P1 | Category set, intake, land table, four room tables, faculty IDs (pseudonymous); "Run SATYA check" (fires `application.precheck_requested`); "Final submit" with lock warning (2.3.3c) |
| MP-03 | Document upload | P1 | Annexure-2.1 list; per document: uploaded / missing, DSC detected, SATYA status |
| MP-04 | Deficiency report | P1 | Portal-computed report (D2), shown as the portal's own output |
| MP-05 | **SATYA results** | P1 | Four sections: **A** pre-submission check (private, #19); **B** checks on submitted documents after the lock, **incl. the affidavit check (old INS-04, moved here by X-1)**; **C** clarification requests from AICTE with response box; **D** compliance tracker after the EoA letter (window by template year). Wireframe W3 |
| MP-06 | Official side (demo) | P1 | Application list with "Open in SATYA" deep link; where officials post decisions so SATYA can echo them |

**X-1 resolved:** the institution affidavit pre-check (INS-04) can't run at stage ① because the sworn affidavit exists only after the data lock (2.3.3c, 2.3.4a; Affidavit-2 NOTE; design v2.2 A1 step 7). It is now MP-05 section B, after the lock, with the rectification route shown per item: the one paid reopening (2.3.3d-e) or when AICTE asks. If V-2 ever confirms uploads can precede the lock, section B can also run before final submission [VERIFY].

### 2.2 Regulation Bureau (RB): C2 ②, ④, ⑦
| ID | Screen | Phase | Purpose |
|---|---|---|---|
| RB-01 | Cycle overview | P1 | PS dashboard as a ledger table |
| RB-02 | **Validation queue (risk-ranked)** | P1 | HERO 1 · grouped by risk band (T2), top 3 reasons, label counts, filters |
| RB-03 | **Case view + EvidenceViewer** | P1 | HERO 2 · header + tabs; Documents tab opens EvidenceViewer |
| RB-04 | Document evidence (full page) | P1 | EvidenceViewer at full width |
| RB-05 | **Affidavit DiffView** | P1 | HERO 3 · normalised 24-declaration diff per application, category line check, tables vs Application Report data, stamp/signing order (§7.1) |
| RB-06 | **Verification panel** | P1 | Exactly one of 6 labels per document + two signature badges + image-only state (§4.3, §7.2). Wireframe W1 |
| RB-07 | **YoYView (M13)** | P1 | HERO 4 |
| RB-08 | Faculty & identity | P1 | M8 findings by token; portal columns tagged PORTAL |
| RB-09 | Manual verification tasks | P1 | "Manual review required" / "source unavailable" items |
| RB-10 | EVC selection | P2 | Risk-ranked + seeded random share (2.3.5a) |
| RB-11 | Monitoring board | P2 | Expiries, compliance windows, CA/DSC sweep (expiry alerts already reach SH-04 in P1) |
| RB-12 | Observations | P1 | All dispositions; candidate items for the EoA letter's self-disclosure deficiency table |

### 2.3 Scrutiny / Re-scrutiny (SC): C2 ③ · all P2
SC-01 My sittings (P2) · SC-02 Evidence pack (P2) · SC-03 Deficiency notes (P2) · **SC-04 Re-scrutiny: open deficiencies only** (P2, wireframe W5) · SC-05 Proceedings record (P2).

### 2.4 EVC (EV): C2 ⑤ · all P2
EV-01 My inspections (P2) · **EV-02 Inspection checklist** (P2, wireframe W6) · **EV-03 Video compliance** (P2, wireframe W6) · EV-04 Presence vs salary statement (P2) · EV-05 EVC report draft (P2).

### 2.5 SHC / SAC / EC (HC): C2 ⑥ · all P2
HC-01 Hearing list (P2) · **HC-02 Evidence dossier** (P2, wireframe W7) · HC-03 Compliance vs deficiency (P2) · HC-04 Evidence index for the Speaking Order (P2).

### 2.6 Rule admin (RA)
RA-01 Rule library, read-only (P1) · RA-02 Rule editor + dry run + maker-checker (P2) · RA-03 Template library, read-only, year-versioned (P1) · RA-04 Issuer profiles, TN first (P1) · RA-05 Source adapters incl. mock-mode marker (P1) · RA-06 APH edition diff (later) · RA-07 Risk + EVC-selection settings (P2).

### 2.7 Auditor (AU)
**AU-01 Audit trail** (P1, wireframe W4) · AU-02 Chain integrity (P1) · AU-03 Case replay (P1) · AU-04 Personal-data access log (P1) · AU-05 Signed export (P2).

### 2.8 Phase totals
| Group | P1 | P2 | later |
|---|---|---|---|
| Shared shell (9) | 7 | 0 | 2 |
| Mock portal (6) | 6 | 0 | 0 |
| RB (12) | 10 | 2 | 0 |
| SC (5) | 0 | 5 | 0 |
| EV (5) | 0 | 5 | 0 |
| HC (4) | 0 | 4 | 0 |
| RA (7) | 4 | 2 | 1 |
| AU (5) | 4 | 1 | 0 |
| **Total (53)** | **31** | **19** | **3** |

---

## 3. Navigation and route map (`apps/web/app/(roles)/…`)

### 3.1 Shell: S3 left rail
- Left rail per role (chrome colour) with top-level destinations; current page = saffron left bar + bold label. Bottom: Alerts (count + notification), Help, English | हिन्दी, Accessibility.
- Top strip: breadcrumb, global search, role + region chip, AY chip; prototype strip above it.
- Case pages: rail collapses to 56px (OVR / QUEUE / MAN / EVC / MON / ALR + tooltips + accessible names); PIN keeps it open. Below 1024px the rail becomes a top menu button.
- Case pages: header + tabs (Summary · Documents · Affidavit diff · Verification · Year-over-year · Faculty and identity · Observations · Audit); EvidenceViewer = page pane + flag rail with DecisionBar (Q1).

Rail per role: RB Overview · Validation queue · Manual verification · EVC selection (P2) · Monitoring (P2) · Alerts | SC My sittings · Alerts | EV My inspections · Alerts | HC Hearings | RA Rules · Templates · Issuer profiles · Source adapters · APH editions · Risk settings | AU Audit trail · Integrity · Case replay · Access log · Exports. Phase-2 items stay hidden in a P1 build (no dead navigation).

### 3.2 Routes
| Route | Screens | Phase | Main components |
|---|---|---|---|
| `/` | SH-01 | P1 | — |
| `/rb-queue` | RB-02, RB-01 (`?view=overview`) | P1 | QueueTable, StatusBadge, RiskBand, FilterBar |
| `/rb-queue/manual` | RB-09 | P1 | FlagCard, DecisionBar |
| `/rb-queue/evc-selection` | RB-10 | P2 | QueueTable, DecisionBar |
| `/rb-queue/monitoring` | RB-11 | P2 | AlertList |
| `/case/[id]` | RB-03 | P1 | CaseHeader, FlagCard, StatusBadge |
| `/case/[id]/documents/[docId]` | RB-04 | P1 | EvidenceViewer, FlagCard, DecisionBar, SignatureBadge |
| `/case/[id]/affidavit` | RB-05 | P1 | DiffView, FlagCard, DecisionBar, SignatureBadge |
| `/case/[id]/verification` | RB-06 | P1 | VerificationTable, StatusBadge, SignatureBadge |
| `/case/[id]/yoy` | RB-07 | P1 | YoYView, FlagCard, DecisionBar |
| `/case/[id]/faculty` | RB-08 | P1 | FlagCard |
| `/case/[id]/observations` | RB-12 | P1 | DecisionLog |
| `/case/[id]/audit` | AU-01 filtered | P1 | AuditTimeline |
| `/scrutiny…` | SC-01…05 | P2 | case shell (committee mode) |
| `/evc…` | EV-01…05 | P2 | Checklist, VideoCompliance |
| `/shc…` | HC-01…04 | P2 | Dossier, AuditTimeline |
| `/audit`, `/audit/integrity`, `/audit/replay`, `/audit/access` | AU-01…04 | P1 | AuditTimeline |
| `/admin/rules`, `/admin/templates`, `/admin/issuers`, `/admin/adapters` | RA-01, 03, 04, 05 | P1 (read-only) | RuleList |
| `/admin/risk`, rule editing | RA-02, RA-07 | P2 | RuleEditor |
| `/alerts`, `/search`, `/help`, `/accessibility` | SH-03…08 | P1 | AlertList |
All routes render inside `AppShell`.

---

## 4. Flag anatomy, DecisionBar, signature badges

### 4.1 FlagCard: C1 + mismatch emphasis V1 (locked)
Header strip (label tint, StatusBadge N1, flag ID, provenance P-a); body two columns (finding, rule + version, APH clause chips, confidence | evidence sheet with extracted vs expected value and sources); V1 emphasis on the wrong value (18px bold mono `#8B0F0F` on `#FDE3E3`, 1.5px `#B42318` border, "DIFFERENCE: …" line); footer (evidence link, compare link, disposition state). Anomaly/forgery-type flags carry "Preliminary indicator. Needs human verification." (PS FR2).

### 4.2 DecisionBar: Q1, five dispositions (MASTER #20)
| # | Disposition | Card | Reason |
|---|---|---|---|
| 1 | `accept` | ACCEPT · record as an official observation | Mandatory |
| 2 | `override` | OVERRIDE · not an issue | Mandatory |
| 3 | `escalate_clarify` | ESCALATE → ask institution to clarify (appears in MP-05 section C) | Mandatory |
| 4 | `escalate_refer` | ESCALATE → refer to Scrutiny / EVC | Mandatory |
| 5 | `escalate_manual` | ESCALATE → send for manual verification (RB-09) | Mandatory |
Reason template (optional) + reason (required, ≥10 characters, goes to the ledger); full-width E1 "RECORD DECISION"; C-b stamp on success. No action changes regulatory status; undo = a new ledger entry.

### 4.3 SignatureBadge (X-11; design v2.2 C3)
Two independent badges per document, separate from the 6 PS labels:
| Badge | States (text on badge) | Meaning |
|---|---|---|
| **Issuer signature** | ISSUER SIGNATURE VERIFIED · IMAGE ONLY, NOT A REAL SIGNATURE · CHAIN BROKEN / EDITED AFTER SIGNING · NOT DIGITAL (WET SEAL) · N/A (SOURCE LOOKUP) | Real CMS signature (/ByteRange) chaining to CCA, or an online lookup by the issuer |
| **Uploader signature** | UPLOADER SIGNATURE PRESENT (with "CCA chain ok · signer role Chairman/Secretary") · ABSENT, REQUIRED · IMAGE ONLY | The institution's DSC on the uploaded file |
Visual: outlined caps chip (Public Sans 800, 10.5px, 1.5px border, white fill): verified/present `#1B7F45` or `#0B2E59` outline, image-only `#6B3FA0` outline (same violet as MANUAL REVIEW REQUIRED), absent `#B42318` dashed outline. Text carries the meaning.
**Mapping to the 6 labels (X-11, final per Portal spec §2.8):** chains to CCA → VERIFIED · chain broken / edited after signing → MISMATCH DETECTED · image only → MANUAL REVIEW REQUIRED · required signature absent → a flag, not a label.
A printed "Signature valid / Digitally signed by…" mark without /ByteRange is always IMAGE ONLY and never counts as verified (design v2.2 C3, #16).

---

## 5. Risk display (locked, MASTER #20)
High / Medium / Low band only, no 0-100 score; text-only chip, CAPS, Public Sans 800, R1 colours (HIGH `#B42318`/white, MEDIUM `#F5B83D`/`#2B1D00`, LOW `#1B7F45`/white), shown with its contributing flags and the line "The band orders review only." Never shown to the institution. [VERIFY contrast and Hindi wording.]

---

## 6. Data needs per screen (for integration spec §2 to match)
Enums:
- `verification_label`: `verified | mismatch_detected | expired | verification_pending | source_unavailable | manual_review_required` (+ UI-only `not_applicable` when no issuing authority exists)
- `provenance`: `satya | portal`
- `disposition.action`: `accept | override | escalate_clarify | escalate_refer | escalate_manual`
- `risk_band`: `high | medium | low`
- `yoy_verdict`: `explained | discrepancy`
- `issuer_sig.state`: `verified | image_only | chain_broken | edited_after_signing | not_digital | not_applicable`
- `uploader_sig.state`: `present | absent_required | image_only`
- `alert.type`: `missing_info | expired | pending_source | suspected_anomaly | unresolved` (+ role alerts) (X-4; matches Portal spec §2.9)
- `route`: `self_disclosure | scrutiny | scrutiny_evc | scrutiny_only` (Table 2.3)

### 6.1 RB-02 queue: `GET /cases`
Row: `case_id, application_id, region, ay, category_set[], route, stage, submitted_at, risk_band, top_reasons[≤3]{flag_id, rule_id, aph_clause, short_text}, label_counts{6}, open_flags, undisposed_flags, yoy_discrepancies, assigned_to, last_activity_at`; `totals{submitted, by_band, flags_awaiting, sources_unavailable}`; `group_counts`. Filters: route, region, stage, category, risk_band, label, rule/flag type, has_yoy_discrepancy, assigned, AY. Sort: grouped by band, then undisposed desc, submitted asc. Cursor pagination, 50.

### 6.2 RB-03 / RB-04 case + EvidenceViewer
`GET /cases/{id}`, `GET /cases/{id}/documents/{doc}/pages/{n}`. `documents[]{doc_id, annexure_item, title, format_type, classified_as (by body text/issuer, design C3), template_id?, sha256, page_count, issuer_sig{state, detail}, uploader_sig{state, chain, signer_role, page}, verification{label, source, adapter_mode: live|mock, checked_at, response_ref}, flag_count}`. `flags[]` as v0.6 (regions, rule, clause, extracted/expected + sources, delta, confidence, label, provenance, preliminary_indicator, disposition). Reason templates: `GET /reason-templates?action=`.

### 6.3 RB-05 DiffView: `GET /cases/{id}/affidavit-diff`
`expected{template_id, template_year, aid, category_list[], declarations[24]{no, block: core|existing_institute, text}}` (portal draft for **this AID and AY**, design v2.2 B1 row 1); `sworn{page_count, template_match, ocr_mean_confidence, issuer_sig, uploader_sig, category_list_found[]|null, declarations[]{no, text, page, region, ocr_confidence}}`; `normalisation{whitespace, strike_through_resolved, names_substituted}`; `ops[]{op: equal|added|removed|changed, decl_no, spans[]}`; `structure{category_line: {expected[], found[], state: present|missing|extra}, core:{expected:19, found}, existing_institute:{expected:5, found}, extra_blocks[]}`; `tables[]{table: land|room_admin|room_amenities|room_instructional|room_common, rows[]{key, sworn_cells[], application_report_cells[], cell_match[], delta?}, total_rows, computed_total_acres, room_id_duplicates[]}`; `stamp{instrument, certificate_no, second_party, duty, state}`; `chronology{application_date, stamp_date, notary_date, dsc_date?, upload_date, order_ok, notary_expiry?}`; linked `flags[]`. Dates parsed per template year (portal affidavit = MM/DD/YYYY, design D4).

### 6.4 RB-06 verification: `GET /cases/{id}/verification`
`documents[]{doc_id, title, format_type, state_code?, issuer_profile (Annex-14), source{channel, adapter_mode: live|mock}, label|not_applicable, issuer_sig{state, detail}, uploader_sig{state, chain, signer_role}, checked_at, response_ref, actions[]: recheck|route_manual|retry}`; `label_counts{6}`; `last_full_run_at`.

### 6.5 RB-07 YoYView
As v0.6 (`summary`, `items[]` with both-year doc refs, verdict, explanation, crops).

### 6.6 MP-05 institution results
`precheck{run_at, items[]}` (section A, private, #19); `post_lock{items[]{item_id, doc_or_field, what, aph_clause, how_to_fix_key, rectification_route: reopening_2_3_3d|when_aicte_asks|compliance_stage, label?}}` (section B, incl. affidavit category line / tables); `clarification_requests[]{request_id, flag_ref (opaque), shared_evidence[]{crop_url}, official_note, due_date, response|null}` (section C); `compliance{eoa_fno, template_year, window, due_date, items[]}` (section D). Never: risk band, raw forensics, identity hits.

### 6.7 Alerts, audit, re-scrutiny, EVC, dossier
Field lists are on each wireframe's annotation panel (W2, W4–W7) and carry over to §10.5.

---

## 7. Key screen specs and wireframes (deliverable 2)
Canvas "SATYA-EoA hero screens", page **Wireframes (Deliverable 2)**: lo-fi grey, real labels, numbered annotations, data needs per screen. Hero mockups (high-fi) cover RB-02, RB-03/04, RB-05, RB-07.
| Wireframe | Screen | Phase |
|---|---|---|
| W1 | RB-06 Verification panel (6 labels, two signature badges, image-only state, mock-adapter marker, mapping legend) | P1 |
| W2 | SH-04 Alerts centre (PS alert types as tabs, new-alert arrival, exact-flag links) | P1 |
| W3 | MP-05 Institution results in the mock portal (sections A–D; affidavit check after the lock, X-1) | P1 |
| W4 | AU-01 Audit trail (chain status, filters, event types, personal-data reveal entries, case replay) | P1 |
| W5 | SC-04 Re-scrutiny: open deficiencies only (1.8g; content-based classification; original sighted) | P2 |
| W6 | EV-02 + EV-03 EVC checklist (Annex-3/4 + flag-driven spots) and video compliance (1.9 f–g, timestamps) | P2 |
| W7 | HC-02 SHC/SAC evidence dossier (hash, numbered evidence index for the Speaking Order, export gate) | P2 |

### 7.1 RB-05 DiffView (design v2.2 C3, B1 row 1)
1. **Header cards:** expected = portal-generated Affidavit 2 for **this AID and AY** (template year, category list, 24 declarations + land table + 4 room tables); sworn copy = pages, SignatureBadges (§4.3), template match, OCR confidence, SHA-256.
2. **Structure check:** category line in the opening block (expected list vs found; **"CATEGORY LINE MISSING"** state with page + flag); core 19 expected/found; existing institute 5 expected/found; any extra block (e.g. a 2023-24-style Increase-in-Intake block) shown as "extra block present".
3. **Clause-by-clause diff:** normalised (whitespace, strike-through options resolved, institution names substituted) before comparing; changed-only by default; removed = red tint + strike, added = green tint + underline (M2 sweep); "MISSING IN SWORN COPY" state for a dropped declaration.
4. **Table reconciliation vs Application Report data:** land deeds (area, plot, document no.), computed total acres (portal leaves the total blank), 4 room tables (carpet area, completion), **room IDs unique across the 4 tables**; mismatch emphasis V1 in cells.
5. **Stamp and signing order:** application ≤ stamp ≤ notarisation ≤ DSC (if any) ≤ upload; stamp Second Party = AICTE and duty ≥ ₹100; notary expiry ≥ notarisation date.
6. **Flag rail:** one compact FlagCard per finding (incl. category line missing), each opening the EvidenceViewer at its region.

### 7.2 RB-06 Verification (W1)
One row per document: document · issuer (Annex-14 profile) · source checked (+ MOCK ADAPTER marker for TN e-District / fire, #22) · result (exactly one of 6, or "not applicable" for self-issued documents like the coordinates) · issuer signature badge · uploader signature badge · checked at · action (re-check / route to manual / retry). Counts strip per label. Mapping legend kept on screen as a help note (X-11 final, Portal §2.8).

---

## 8. Design system (deliverable 3): locked
As v0.6 (palette B tokens, F2 + Public Sans 800 caps + Noto Sans Mono, N1 labels with violet manual review, P-a provenance, YoY verdict chips, motion M1/M2/M5/L-a/S-c/C-b/A-a, S3 shell, T2 density, E1 keycap buttons, P1 mock portal, mismatch emphasis rule). Added v0.7: SignatureBadge (§4.3); wireframe convention (greyscale `#E9E9E9` / `#FAFAFA` / `#9E9E9E`, numbered black annotation dots, annotation panel per board).

Token summary: chrome `#0B2E59`, chrome-2 `#123A6D`, chrome-muted `#C9D4E5`, saffron rule `#E07B00`, page `#F4F6F9`, surface `#FFFFFF`, text `#111827`, muted `#4B5563`, accent `#1F5FBF`, rule `#E3E7EE`, field `#B9C3D3`, mismatch ink/tint `#8B0F0F`/`#FDE3E3`, added tint/ink `#DDF1E3`/`#0E3F21`, viewer `#E9ECF1`. Labels: VERIFIED `#1B7F45`, MISMATCH `#B42318`, EXPIRED `#A8471A`, PENDING `#1F5FBF`, SOURCE UNAVAILABLE `#4B5563`, MANUAL REVIEW `#6B3FA0`. Risk: HIGH `#B42318`, MEDIUM `#F5B83D`/`#2B1D00`, LOW `#1B7F45`.

## 9. Hero mockups (deliverable 4)
Canvas page **Hero mockups**: 1 RB queue · 2 case + EvidenceViewer · 3 affidavit DiffView · 4 YoY (M13). v0.7 updates: case toolbar and DiffView sworn-copy card show the two SignatureBadges ("uploader signature present" + "p. 9 mark: image only"); DiffView shows the 24-declaration structure check with **CATEGORY LINE MISSING**, the normalisation note, the v2.2 order application → stamp → notary → DSC → upload, Second Party/duty, and flag F-0422. Synthetic data only; Hindi strings and clause wording are placeholders [VERIFY].

**Deck exports (25 Oct, 22:00, for the PPT):** `SATYA-concept-RB02-risk-queue.png` (2160×1791) and `SATYA-concept-RB05-affidavit-diff.png` (2160×2187), rendered at 1.5× from the canvas with self-hosted fonts. Both carry the strip "Concept UI, not a working build · mock approval portal · synthetic data only"; no AICTE branding. Project docs accept text only, so the PNGs were handed to team lead to upload to the Project as files.

## 10. Build handoff
Deferred to after 28 Oct (MASTER). Styling B: CSS Modules + CSS custom properties (`tokens.css`) + React Aria Components + next-intl. Pending: 10.1 route → page → components (§3.2) · 10.2 component inventory with props + states (StatusBadge, RiskBand, SignatureBadge, FlagCard, DecisionBar, EvidenceViewer, DiffView, YoYView, VerificationTable, QueueTable, AlertList, AuditTimeline, AppShell) · 10.3 tokens (§8) · 10.4 accessibility · 10.5 data needs (§6) · 10.6 web-design-guidelines checklist.

---

## 11. Decisions and open items
| ID | Item | Status |
|---|---|---|
| MASTER #19 | Pre-check private to the institution, not in risk scoring | Recorded (§1.1, MP-05 A) |
| MASTER #20 | Risk = High/Medium/Low band; 5 dispositions; PGRC/SCSC out of v1 | Recorded (§1, §4.2, §5) |
| X-1 | INS-04 at stage ① | **Fixed:** moved to MP-05 section B (after the lock) |
| X-5 | Phase tags | **Fixed:** §2, 31 P1 / 19 P2 / 3 later |
| X-11 | Signature → label mapping | **Closed:** Portal spec §2.8 final; UI matches (§4.3, W1) |
| X-4 | Alert enum | **Matches** Portal spec §2.9 |
| X-2, X-3 | Outbound advisory events, compliance uploads | UI shows them (W3); Portal chat owns |
| U-2 (for MASTER) | Tiered institution visibility is not in design v2.2 A2/M11 after the Research chat's rewrite | Research chat to add to A2 + M11 in v2.3 |
| S-1 / H-7 | Styling | Decided B (team lead, UI chat) |
| V-2..V-7 | Visual choices | Decided (v0.5–v0.6) |
| Deferred | Remaining P1 screens (RB-01, RB-08, RB-09, RB-12, MP-01..04, RA read-only) + §10 | After 28 Oct |
| [VERIFY] | Hindi strings, chip contrast, "UX4G uses Noto", V-2 upload-before-lock | Open |

## 12. Changelog
- v0.7.1 (25 Oct 2026, 22:00): deck PNG exports of RB-02 and RB-05 with the "Concept UI, not a working build" tag; RB-05 hero sworn-copy card uses SignatureBadges; X-11 closed (Portal §2.8); alert enum matches Portal §2.9; remaining P1 screens + §10 deferred to after 28 Oct.
- v0.7 (25 Oct 2026, evening): MASTER #19, #20 recorded; X-1 fixed (affidavit check → MP-05 B after the lock); X-5 phase tags for all 53 screens; RB-05 spec aligned to design v2.2; SignatureBadge + X-11 mapping; deliverable 2: 7 wireframes; hero mockups updated; U-2 raised.
- v0.6 (25 Oct 2026): V1 + P-a locked; hero mockups built.
- v0.5 (25 Oct 2026): R1 + K5, N1, C1, E1, Q1, T2, motions; tiered visibility decided.
- v0.4 (25 Oct 2026): round-2 candidates; S-1 decided B.
- v0.3 (25 Oct 2026): palette B, F2, M1/M2/M5, S3, P1.
- v0.2 (25 Oct 2026): aligned to integration spec §1; mock portal; DecisionBar; route map.
- v0.1 (25 Oct 2026): first inventory.