# SATYA-EoA v2.2.1: design grounded in the approval process
Repo copy of the team's core design document (source version v2.2.1, 25 Oct 2026). Real institution names from the sample corpus are removed from this copy; nothing else is changed. Every claim cites the AICTE Approval Process Handbook (APH) 2024-25 to 2026-27. Items marked **[VERIFY]** still need confirmation before we build on them.

**v2.2.1:** D4 parser note: F.No. may carry spaces around "/".

**v2.2:** corpus run 2 (19 more public PDFs; 45 in total). Changes:
- The affidavit structure is settled at 24 declarations (B1 row 1, D3).
- Tamil Nadu fire, structural and Form D formats are recorded (B1 rows 3–5).
- New document type: the portal **Application Report** (B1), the closest public view of "portal data".
- UDIN format rules (B1 row 7).
- Signature images vs real signatures (C3, M6).
- Classify documents by body text, not by heading or filename (C3).
- C7 re-scored; Part D now covers both runs.

**v2.1:** first 26-PDF corpus (Part D); D2 coverage of the portal Deficiency Report; new module M13 Year-over-Year Reconciliation.

---

## Part A. How EoA actually works (APH Chapter II)

### A1. The annual cycle
1. **Public Notice** sets the schedule. It is "final and binding", and offline applications are rejected (2.2).
2. **The institution logs in** to the AICTE portal, enters or edits its data, and receives a unique application ID (2.3.1a).
3. **TER (processing fee)** is paid only through the portal gateway (2.3.2d; Ch. VIII-9). The portal prints a pay receipt.
4. **The portal generates a Deficiency Report** from the entered data (2.3.3b). The institution must reach "Nil Deficiency" (1.7 note; 2.4). **This is arithmetic on self-declared data only; it verifies no document (see D2).** The portal also prints an **Application Report** of everything entered (D1).
5. **Final submission locks the data** (2.3.3c). It can be **reopened once**, with a Format 3 resolution, TER and a penalty (2.3.3d-e). The report's own declaration (c) confirms there is "no provision for correction of data … once submitted".
6. **Documents are uploaded per Annexure-2, each digitally signed with DSC.** No hard copies (2.3.4a).
7. **The affidavit** is downloaded from the portal, printed on ₹100 non-judicial or e-stamp paper, sworn, digitally signed and uploaded (2.3.4b; Affidavit-2 NOTE).
   - Real samples show the order **portal application date → stamp purchase → notarisation → DSC → upload** (D1).
   - Several "DSC" marks on uploaded pages are only **printed images**, not verifiable signatures (C3).
8. **Routing by category (Table 2.3):**

| Category | Documents | Self-disclosure | Scrutiny / Re-scrutiny | EVC | SHC / SAC |
|---|---|---|---|---|---|
| **EoA based on Self-Disclosure** | Annexure-2 | **Yes** | **—** | **—** | **—** |
| NRI seats (introduction/continuation) | Annexure-2 | Yes | — | — | — |
| Increase in intake / additional course, new programme/level, merger, conversion, restoration after break, change of site, integrated/dual, FPM, collaboration, Deemed-University conversion, ODL/OL | Annexure-2 | — | Yes | Yes | As applicable |
| Name changes, closure, bank details, Trust name, women's ↔ co-ed, OCI/FN seats | Annexure-2 | — | Yes | — | — |

9. **Self-disclosure EoA is granted on what the institution declares.** The Council "shall monitor" afterwards and take penal action (2.5). Institutions are also "at random" subject to an EVC (2.3.5a). **This is the largest annual flow, and no committee looks at it before approval.**
   - Real EoA letters confirm this: the letter itself can carry a table titled "Deficiencies Noted based on Self Disclosure".
   - The compliance window changed over the years: "Two years" in 2020-21, "Six Months" in 2024-25 (D1).
10. **Scrutiny/Re-scrutiny Committee** (other categories; 1.8):
    - experts are auto-selected on the portal;
    - two institution representatives present originals;
    - the committee "shall verify the authenticity of the documents";
    - deficiencies are posted on the portal;
    - Re-scrutiny checks **only** those deficiencies;
    - the proceedings are recorded (1.8 note; 2.28).
11. **EVC** (1.9):
    - auto-selected experts;
    - online or physical;
    - checks readiness per Annexures 3 and 4, faculty appointments, equipment, books and computers;
    - an online EVC needs a video of at least 30 minutes;
    - a physical EVC is recorded on video (at the institution's cost) with date and time;
    - the video must show the committee's entry and exit times, the approved building plan, and **GPS coordinates at the main, academic and administrative buildings and the library** (1.9 f–g NOTE);
    - the EVC checks faculty through salary statements as well as physical presence (6.14a).
12. **SHC:** the institution submits compliance → **EC** decides and a **Speaking Order** is uploaded (2.23.3) → **SAC** hears one appeal within 7 days, and the Council's decision is final (2.24).
13. **Grant:** the EC places a consolidated list before the Council, and the institution downloads its EoA letter with "Approved Intake" (2.25). Student enrolment is uploaded by 30 November (2.25n).
14. **Penalties:** false, incomplete or incorrect information in an EoA application is a violation (7.4a). A false affidavit means action against the deponent (7.1 NOTE). A fraudulent document leads to a criminal case against the Director/Principal and Chairman/Secretary (2.3.5b).
15. **Complaints:** PGRC → SCSC → warning, show-cause or EVC → SHC → EC (7.10).

### A2. Users and the stage each works in
| Role (APH) | Stage | What SATYA gives them |
|---|---|---|
| Institution (Chairman/Secretary, Principal) | Data entry → before final submission → rectification | Pre-submission self-check that goes beyond the portal Deficiency Report |
| Regulation Bureau officials | After submission; monitoring under 2.5(c) | Validation queue, risk ranking, evidence, year-over-year changes |
| Scrutiny/Re-scrutiny experts | Committee sitting | Evidence pack per document; Re-scrutiny view of open deficiencies only |
| EVC experts / Regional Office | Inspection | Video-compliance check, recommended spots to inspect, checklist from Annexures 3/4 |
| SHC / SAC / EC | Hearing / appeal / decision | Signed evidence dossier and audit history |
| PGRC / SCSC | Complaints | Cross-record history of the institution (out of v1) |

**Institution visibility (tiered; to be restored in design v2.3, see UI spec §1.1):** the institution sees fixable findings, its own document labels and its own year-over-year changes, inside the portal only. Anomaly indicators reach it only as clarification requests raised by an official. It never sees the risk band or identity-graph hits. The pre-check is never used in risk scoring.

---

## Part B. Document catalogue: what arrives, in what format

**Format types:**
- **T** = a fixed AICTE template (from the APH or generated by the portal), so its layout and fields are known.
- **E** = an external document issued by a third party; the format varies by issuer or state.
- **P** = portal data or a portal-generated record.

**Source labels in the tables:** "real sample" means the format was seen in the 45-PDF corpus (Part D); "APH" means it comes from the handbook text only.

### B1. EoA based on Self-Disclosure (Annexure-2.1); the core of the prototype

| # | Document | Type | Issuer / signer | Known fields (real samples) | Signing / stamp | Validity rules (APH + samples) | Official verification channel | SATYA checks |
|---|---|---|---|---|---|---|---|---|
| 1 | **Affidavit (portal-generated "common affidavit"; APH Affidavit 2)** | **T** | Chairman/Secretary (for government institutions, the department/institution fills the Trust slot) as deponent; sworn before a Judicial First Class Magistrate, Notary Public or Oath Commissioner | **Settled for AY 2024-25, 2025-26 and 2026-27** (4 portal drafts + 1 executed copy). The text is word-for-word the same each year:<br>• headings "AFFIDAVIT / ACADEMIC YEAR – YYYY-YYYY";<br>• opening block with PID, AID, institute name/address/type/region, application date and a numbered **category list** (e.g. "1. EoA Only", "1. Merger of Institutions…");<br>• **19 core + 5 "Existing Institute" = 24 numbered declarations** (+5 committee bullets);<br>• "EoA Only" and "Merger" print **no** extra block; a 2023-24 "Increase in Intake" copy had an extra 3-item block [VERIFY whether change blocks still print in 2024-27];<br>• land table `Name of the deed Holder \| Document No. \| Date of Registration \| Plot No. \| Address (Village) District \| Area in Acre` + an empty "Total area in Acre" row;<br>• 4 room tables (Administrative, Amenities, Instructional, Instructional–Common Facilities), each `Room No. \| Room type \| Carpet area (m²) \| Completion of Flooring \| … Walls and painting \| … Electrification and lighting`;<br>• verification + notary line;<br>• footer "Application Number: 1-########### / All India Council for Technical Education / Page N of M".<br>Stale text in every year: "Appendix 16/17", "Appendix 6", "Regulation Regulations, 2021".<br>Portal dates print as **MM/DD/YYYY**. The 2020-21 predecessor was a 12-item "UNDERTAKING" with no tables. | ₹100 stamp. Instruments seen: **SHCIL e-Stamp** (KA: "Certificate No. IN-KA + 14 digits + letter", "Article 4 Affidavit", Second Party "AICTE NEW DELHI", verify at shcilestamp.com) and a state **e-Court Fee** + adhesive stamps (BR). Notary seal with reg. no. and **expiry date**. DSC: real (/ByteRange) in 1 copy; an **image only** in another. | Application date ≤ stamp issue ≤ notarisation ≤ DSC (if any) ≤ upload; notary expiry ≥ notarisation date; AY strings = application AY | Stamp: shcilestamp.com / e-Stamp app (public, per the certificate's own text) [VERIFY automated-access terms]; DSC: CCA chain; notary: no public registry → manual review | **Normalised clause diff** against the portal draft for the same AID (byte comparison fails: executed copies are re-typeset, with strike-through option selection); **category line present** (one executed copy dropped it); table reconciliation vs Application Report / portal data and last year (M13); **room IDs unique across the 4 tables**; computed total acres; decl. 4 vs a "same campus" merger category; stamp "Second Party" = AICTE and duty ≥ ₹100; stamp/DSC chronology; DSC real vs image |
| 2 | Pay receipt | **P** | AICTE portal | Application no., amount, transaction ID, date | — | Paid by the Public Notice deadline; amount = Table 2.1 × divisions | AICTE gateway (internal) | Amount vs Table 2.1; date vs deadline. **No real sample yet.** |
| 3 | Occupancy / Completion Certificate / **Building License / Form D** (the affidavit's decl. 3 names all four) | **E** | State competent authority per **Annexure-14** | **DL:** MCD Hindi form "प्रपत्र-1 … अधिभोग प्रमाण-पत्र", Executive Engineer (Building), floor-wise schedule.<br>**TN:** **Form D Public Building Licence** (TN Public Buildings (Licensing) Act 1965, s.6(1); Rules 1966 r.6), issued by the district "Licence Issuing Authority" via TN e-District: licence no. `##/YYYY`, purpose, persons accommodated, fee challan, validity window, DSC + 2D barcode.<br>**Revenue certificates (TN, RJ):** a Tahsildar "Occupancy Certificate" from revenue records (survey/khasra numbers, hectares) with **no validity, built-up area or block list**.<br>CMDA/DTCP completion certificates: still none seen. | Issuer seal/signature or e-District DSC; institution's DSC on upload | **Partial/provisional OC accepted for only 2 consecutive academic years** (Annex-3 3.1c); Form D: 3-year validity | **TN Form D: tnedistrict.tn.gov.in "VerifyCerti" by licence number, or by the 2D barcode** (printed on the licence) [VERIFY automated access]; other states [VERIFY] | **Issuer type** (planning authority / local body / e-District licensing / revenue / engineer). Revenue → manual review. Entity = this institution (one sample names a sister polytechnic); blocks covered = academic blocks (one covers a hostel only); Form D purpose = higher education (one sample says "School"); validity vs AY; partial-OC year counter (M13) |
| 4 | Structural Stability Certificate | **E** | Registered/panel structural engineer | **TN:** panel engineer's **Forms A, B and C** under the TN Public Buildings (Licensing) Act 1965 / Rules 1966, plus a declaration. CMDA/DTCP registration numbers on the letterhead (patterns `SE/GR-1/##/##/###`, `CGLRGN/SE/GR-1/YYYY/##/###`). Form B "Remarks" carry **conditional clauses** (annual repair or the certificate is cancelled, etc.). Engineer's period 5 years; it feeds the Form D licence (3 years). | Engineer wet signature + stamp; owner undertakings (unsigned in the sample) | Required if the building is **more than 30 years** past its Completion Certificate (2.1(iv)); effective validity = **Form D licence end date**, not the engineer's period | Engineer registration lists [VERIFY]; Form D via e-District | Registration-number patterns present; Forms A/B/C complete; owner signatures present; conditional clauses flagged; licence vs engineer period; old/new district names mapped (Kanchipuram → Chengalpattu) |
| 5 | Fire Safety Certificate | **E** | State Fire & Rescue Services | **TN:** "TAMIL NADU FIRE AND RESCUE SERVICES LICENCE (Under section 13 of the Tamil Nadu Fire Service Act 1985 and … Rule 1990 - Appendix-III)", "RENEWAL OF FIRE LICENSE", **`Licence No: ####/RFL/NMSB/YYYY`**, district office, inspecting station officer, 9–10 standard conditions (NBC 2016 Part IV; IS 2190:2010; IS 1646:1997; G.O. 713/2005). **Two body variants:** (a) floors + height + built-up area + explicit "valid … from … to …"; (b) survey numbers + "valid for three years from date of issue". QR holds **plain text** (approver + date), not a URL. **Note:** the 1985 Act is to be repealed by the Tamil Nadu Fire and Rescue Service Act 2025; commencement not yet notified [VERIFY]; rule tables must be versioned by Act.<br>**DL:** DFS "FIRE SAFETY CERTIFICATE", 3 years (r.36), block list, occupancy class Group-B B-2, conditional clauses.<br>**TG:** renewal NOC with QR, block-wise, occupancy class "B-1 Schools".<br>**RJ:** a municipal certificate with no validity. | Fire-department DSC (often an **image** once pasted into a PDF) or seal; institution's DSC on upload | Valid on the processing date (Annex-3 3.1d); TN/DL: 3 years | State fire portals [VERIFY per state]; QR where present | Expiry (computed when only "three years from date of issue" is printed); issuer type; **"NMSB" vs stated height (< 15 m)**; **licence built-up area / floors vs application building data**; occupancy class fits higher education; blocks covered; conditional clauses; separate licences for college and hostel recognised |
| 6 | **Satellite map** | **E/free-form** | Institution ("using suitable Web site") | Lat/long at the main building's entrance. The **portal Application Report stores coordinates as integer D/M/S fields + N/S, E/W selectors**. Disclosures print DMS with decimal seconds or decimal degrees. **No satellite image sample yet.** | Institution's DSC | Location = approved location (Affidavit decl. 2) | Open imagery (Bhuvan / Sentinel-2) for cross-checking | Convert all forms to decimal; point inside the declared district/PIN; vs earlier years (M13); **land ≤ 3 plots, ≤ 2 km apart** (Annex-3 3.1g) |
| 7 | Audited statement of accounts | **E** | Chartered Accountant | AICTE-linked samples (4): CA-signed I&E with membership no. + FRN, **no UDIN**; trust-signed extracts (no CA); an income-tax computation; file names only.<br>**UDIN format** (from one non-AICTE college's audit): **18 chars = YY + 6-digit CA membership no. + 6 letters + 4 digits**, one per FY, repeated on that FY's statements; FRN printed both as 6+1 and 7+1 (leading zero). | CA signature, membership no., FRN, UDIN; date + place of report | Previous FY (Annex-2.1(vii)); EoA letter Instruction 1(iii) asks for **3 FYs** on the website | **ICAI UDIN** verification [VERIFY third-party access] | Statement type; FY = previous year; Trust name; **UDIN chars 3–8 = membership no. printed beside it**; UDIN YY ≥ FY end (a large gap → review); one UDIN per FY, not reused (M13); FRN normalised; report date/place present; management signatures present |
| — | Faculty, staff and student data | **P** | Entered by the Head of Institution (affidavit "Existing Institute" decl. 3) | Portal faculty export (29 columns, incl. "Is Duplicate", "PAN Validation", "Faculty Record Status"). The Application Report prints "FACULTY MEMBERS LIST … (Faculty members with a Valid PAN and Valid Record status)" as a **rotated table** (reversed text). Faculty ID `1-` + 9–11 digits. | — | FSR 1:20 (UG E&T), cadre 1:2:6 (Annex-5); ID added/deleted **within the same month** (6.14c) | AICTE Faculty ID registry (internal) | **The portal already flags within-portal duplicates and validates PAN; never claim these.** Our checks: course-wise faculty count (course table) vs list rows; cross-year churn and late removal (6.14c, M13); portal list vs the college website's list (Annex-18) |
| — | **Portal Application Report** | **P** | AICTE portal printout (Oracle BI/Analytics Publisher); two layouts: **full** (27–51 pp) and **short** (3–11 pp: basic details, HOI personal details, faculty list, declaration) | Basic details (application/permanent IDs, type, status, dates, **Overall Deficiency flag only**); trust + trustee table with tenure; course table (intake approved for the last 2 AYs, applied intake, required vs actual faculty, NRI and International-student status, NBA); **land details** (area, pieces, max distance, registration, land-use certificate issuer/date, D/M/S coordinates, per-deed blocks); **building details** (sanctioned vs constructed areas, **Building Plan Approving Authority + date**); room blocks; facilities; committees; bank, income and expenditure; declaration a–f.<br>2025-26: MM/DD dates, aicte-india.org masthead, watermark tokens in the text layer. 2026-27: DD/MM dates, aicte.gov.in masthead, signature footer. | — | For the named AY | AICTE (internal). In real integration, SATYA receives this as **structured data** through the API (Portal spec §2.6.1); the printout shows the field set | **The reference for affidavit reconciliation** (land, rooms, buildings) and internal consistency: land area across fields with unit conversion; building approved = sanctioned; deed areas sum = total; duplicated deed numbers; trustee tenure expired; certificate valid-till > issue date; income totals; stale bank IFSC; course-wise faculty count vs list |
| — | **Previous EoA letter** (baseline for this year) | **P** | AICTE portal, "Member Secretary, AICTE"; "Computer generated … No signature is required" | 9 samples, AY 2020-21 → 2026-27. **Stable:** `F.No. <Region>/1-<AppID>/YYYY/EOA` (optional "/Corrigendum-N"; region may contain a hyphen); running footer with "Printed By" + "Letter Printed On"; aicte-india.org note.<br>**Changes by year:** masthead "Ministry of HRD" → "Ministry of Education" (2022); "Date:" → "Date of Approval:" (2024); course columns "Program \| Level" → "Level \| Program" (2022); last column "PIO/FN/Gulf/OCI" → "FN/Gulf/OCI" → "International Students Approval Status" (2026); deficiency block optional ("Two years" 2020 → "Six Months" 2024); Important Instructions 4 → 9 → 10; copy-to 6 → 5. **LoA** uses `<Region>/<AY>/<AppID>` and 19 general conditions. | No DSC, no QR | Valid for the named AY | AICTE records (internal); "verify at aicte-india.org" | Approved intake + last year's open deficiencies for M13; compliance deadline = issue date + window by template year (Portal spec §2.10); map columns **by header text**, not position; "Page N of M" = the letter's own length |

### B2. Other categories (Scrutiny/EVC route): fixed templates we can parse reliably

| Document | Type | Where it's used | Notes |
|---|---|---|---|
| **Format 2:** NOC from the affiliating University/Board | T | New programme, conversions, merger, closure, name changes (2.3, 2.4, 2.7–2.11) | Clause options i–xv; ticked clause = the application category. **No genuine sample yet.** One upload headed "AICTE Format-2" was actually a society resolution, so classify by **issuer** (university Registrar vs trust officers) |
| **Format 3:** Resolution of the Trust/Society/Company | T | Almost every non-EoA category; reopening (2.3.3d) | **1 sample (AP 2025-26):** "Executive meeting held on DDth Month, YYYY … Vide item no. ##"; roman-numeral clauses (change of site, Trust name, institution name, intake 180→360); governing-body member list with signatures; society seal; one real PDF signature (consumer-class DSC). Two copies of the same resolution differed in names, roles and venue → **compare copies** when more than one is uploaded; letterhead name = name in force on the meeting date |
| **Format 1:** NOC from the State Government/UT | T | Change of site, conversions, closure, Trust name change | No sample. **State rule tables exist:** the AP DTE 2024-25 circular maps 8 change categories to their required documents (Format 1/2/3, Affidavits 2/3/4/10, ₹100 stamp, fee receipt, liability affidavit, land/building documents). Other states may differ [VERIFY] |
| **Affidavits 3, 4, 8, 9, 10** | T | Category-specific | Same stamp/notary rules. The 2025-26 merger affidavit printed **no** category block, so category evidence must come from Format 3, NOCs and other documents. [VERIFY whether a separate Affidavit 8 is still uploaded for intake increases] |
| **Certificate 1** (advocate: land and Trust registration), **2** (architect: site/building plans + room table), **3** (bank manager: funds/FDR) | T | New institutions (Annexure-1); Trust changes | Room table in Certificate 2 = same structure as the affidavit room tables |
| EVC video (≥30 min) | E (URL on the Trust website / YouTube) | EVC categories (1.9 f–g; Annexure-1 1.2 ix) | Checks: link present; duration; GPS visible at the 4 named buildings; date/time overlay |
| Salary statements (ECS) | E | EVC (6.14a); closure (2.7 ii) | Faculty count vs salary-sheet count; PF/TDS lines |

### B3. Public data the APH requires (usable for a realistic prototype)
- **Annexure-18 Mandatory Disclosures:** every institution publishes, on its own website, its approved programmes and seats, a course-wise faculty list, and each faculty member's Unique ID, date of birth, qualifications and experience. Three layout generations are in use (D3). Use them for layout realism and synthetic seeding only; **never load real people's data into the repo or demo.**
- **AICTE public dashboard:** approved institutions and intake.

---

## Part C. Solution

### C1. Positioning (one line)
**SATYA-EoA is the missing first-pass scrutiny for self-disclosure EoA, and an evidence assistant for every committee after it.** It reads AICTE's own templates the way they were designed, checks each document at its official source, and reconciles every sworn claim against the portal, past years and other institutions.

### C2. Where it plugs into the process
| Stage | SATYA module | Why it matters |
|---|---|---|
| ① Before final submission (institution) | **Pre-submission check:** runs the same rules early, so deficiencies are fixed before the data locks (2.3.3c), not via the one paid reopening. Private to the institution; never used in risk scoring | Fewer deficiency cycles; uses the APH's own clause references |
| ② After submission: self-disclosure EoA (no committee) | **Full validation:** template diff, reconciliation, source checks, date rules, identity graph, year-over-year changes, risk band | The only structured check this flow gets before the EoA letter is issued |
| ③ Scrutiny / Re-scrutiny | **Evidence pack:** per-document status (6 PS labels), flags with page regions, Format 1/2/3 checks; Re-scrutiny view shows only open deficiencies (1.8g) | Matches how committees already work |
| ④ Choosing institutions for the "random" EVC (2.3.5a) | **Risk-ranked selection**, with a random share kept so the process stays fair | AICTE keeps the decision; the selection becomes evidence-based |
| ⑤ EVC | **Video-compliance check + inspection checklist** from Annexures 3/4 and the flags | Turns 1.9 f–g into automatic checks |
| ⑥ SHC / SAC / EC | **Signed evidence dossier** + hash-chained audit trail | Hearing-ready; supports the Speaking Order |
| ⑦ Monitoring (2.5c) and next cycle | **Continuous re-validation:** expiries (fire, Form D, partial OC, NBA periods), CA distrust sweep, **follow-up of self-disclosure deficiencies after their compliance window** (M13) | Monitoring the APH already requires, made automatic |

### C3. Core mechanism: template-aware parsing (the technical edge)
- **Classify by body text and issuer, never by heading, filename or uploader label.** In run 2, 7 of 19 labels were wrong, and one "Format-2" heading sat over a Trust resolution.
- **For T documents** (the portal affidavit, Formats 1–3, Affidavits 3/4/8/9/10, Certificates 1–3) and **portal P documents** (Deficiency Report, Application Report, EoA/LoA letters, faculty export):
  - **The template version is chosen from the document itself:** the "APPROVAL PROCESS YYYY-YY" line, the heading word (AFFIDAVIT vs UNDERTAKING), and the masthead. Templates change by year: the Deficiency Report checklist went 32 → 51 → 40 items; EoA columns were renamed and reordered; date order flipped between MM/DD and DD/MM.
  1. **Anchor extraction:** fields are read at known positions in a known table instead of guessing with generic OCR. This raises extraction accuracy, which is a PS metric.
  2. **Normalised template diff:** compare the sworn copy, clause by clause, against the expected text for **that year and that AID**, after normalisation (whitespace removed, strike-through selections resolved, institution names substituted). This catches deleted clauses (e.g. a missing category line), altered numbers or a swapped table row.
  3. **Reconciliation:** compare table values (land, rooms, buildings, faculty) against the portal data (Application Report fields), last year's records (M13) and other institutions' records.
- **For E documents:**
  - an issuer profile per state from **Annexure-14**, extended with real formats (TN Form D, TN fire licence, panel-engineer Forms A/B/C, DFS DL, TG fire NOC);
  - a document classifier; field extraction with confidence;
  - expiry (printed or computed from the state rule), **issuer type, addressee entity, block coverage, occupancy class, height/area vs application, conditional clauses**;
  - source verification where an official channel exists (SHCIL, TN e-District Form D, QR text, DSC); otherwise "source unavailable / manual review required".
- **Signatures: two separate checks** (label mapping: Portal spec §2.8).
  - "Issuer signature verified": a real CMS signature (/ByteRange) chaining to the CCA, or an online lookup.
  - "Uploader signature present": the institution's DSC on the compiled file.
  - A printed "Signature valid / Digitally signed by…" mark **without /ByteRange is an image** and never counts as verified.
  - Seen in 4 run-2 files; only 3 of 45 corpus PDFs carry any real PDF signature.
- **For P data:** rule engine on APH norms **only where the portal Deficiency Report does not already compute them** (D2), plus the identity graph and M13.
- **Ingest pipeline must handle:**
  - scanned wet-signed printouts (seal over footer labels); phone photos (deskew);
  - hyphen-wrapped and space-less text layers; doubled glyphs from flattened DSC marks; watermark tokens inside values;
  - **rotated tables with reversed text**;
  - Hindi + English; merged PDFs (page-level sub-document splitting);
  - MM/DD vs DD/MM chosen per template year (reject impossible months).

### C4. Module list
| ID | Module | APH grounding | PS area |
|---|---|---|---|
| M1 | Portal gateway + category router (17 categories → Table 2.3 route → Annexure-2 checklist; **state rule tables** such as the AP DTE list) | 2.0, Table 2.3, Annex-2 | FR1, DEL1, DEL2 |
| M2 | Secure vault (hash, encrypt, DSC capture, **redact personal data on ingest**) | 2.3.4a | DEL8 |
| M3 | Template-aware extraction (T/E/P profiles with **year-versioned templates**; Annexure-14 issuer profiles; content-based classifier; sub-document splitter; rotated-table and text-layer normalisers) | Affidavits, Formats, Certificates, Annex-14 | FR1, DEL3 |
| M4 | Rule engine (versioned YAML per APH edition; clause-cited; **imports the portal Deficiency Report result instead of recomputing it**) | Ch. VI, Annex-3/5, 2.1(e), Annex-2 | FR1, FR4, DEL2 |
| M5 | Affidavit & template diff + reconciliation (normalised clause diff per AID; category line; tables vs Application Report data) | Affidavit-2 NOTE; land and room tables | FR1, FR2 |
| M6 | Signature, stamp & PDF forensics (real DSC vs signature image; CCA chain; signer = Chairman/Secretary; edited after signing; stamp chronology/reuse across e-Stamp, e-Court Fee and adhesive stamps; notary-seal expiry) | 2.3.4a–b; Annex-2.1(i) | FR2, FR3 |
| M7 | Source verification hub (6 PS status labels; adapters: CCA, SHCIL e-Stamp, **TN e-District Form D**, QR text, UDIN, state fire portals; otherwise "source unavailable", which creates a manual task, Portal spec §2.6.3) | PS FR3 | FR3, DEL5 |
| M8 | Cross-record identity graph (Faculty ID/PAN pseudonymised; cross-year and cross-institution; ID update lag 6.14c; **portal list vs website list**). Within-portal duplicate and PAN validation are already done by the portal. | 6.14c, 6.14i, Annex-18 | FR1, FR2, OBJ2, OBJ3 |
| M9 | Location & infrastructure evidence (D/M/S and decimal coordinates; ≤3 plots ≤2 km; fire-licence and Form D area/height vs building data; EVC video compliance; reused media) | Annex-2.1(vi), Annex-3 3.1g, 1.9 f–g | FR4, DEL6 |
| M10 | Risk triage & EVC selection (High/Medium/Low band; risk-ranked + random share) | 2.3.5a, 2.5c | FR4, FR5, OBJ5 |
| M11 | Role dashboards (institution pre-check, RB queue, Scrutiny/Re-scrutiny pack, EVC checklist, SHC/SAC dossier, **year-over-year view**) | 1.8, 1.9, 2.23, 2.24 | FR5, DEL7 |
| M12 | Audit ledger (hash-chained; mirrors the 2.28 requirement to record proceedings) | 1.8 note, 2.28 | FR5, DEL8 |
| **M13** | **Year-over-Year Reconciliation** (C4a) | 2.25, 2.25n, 2.5c, Annex-3 3.1c/3.1g, 2.1(iv), 6.14c, Annex-18; PS FR1 "previous EoA and approval status … application history" | FR1, FR2, OBJ1, OBJ2, DEL4 |

### C4a. M13 Year-over-Year Reconciliation
Every change across years is compared with the APH. It is marked **"explained"** if an approved application that year accounts for it (e.g. an approved increase in intake). Otherwise it is filed as a discrepancy, with links to **both years'** documents and the clause. It stays advisory.

| Compared across years | Flag when | Basis |
|---|---|---|
| Approved intake (last EoA letter) vs this application vs enrolment | Intake changes with no matching approved category; admissions above approved intake **after allowing for supernumerary seats** (TFW 5%, EWS 10%, PMSSS, NRI/International) | 2.25, 2.25n, 7.3 |
| Affidavit land table / Application Report land details | Area, plots or deeds change with no change-of-site or merger application | Affidavit land table; Annex-3 3.1g |
| Affidavit room tables / Application Report buildings | Rooms or carpet area shrink while intake stays the same or grows | Annex-3 built-up area norms |
| Faculty IDs | Heavy churn; late removal; the same ID at another institution the year before | 6.14c, 6.14i |
| OC / CC / Form D | Partial OC in a 3rd consecutive year; CC date different from earlier years (breaks the 30-year structural rule); Form D lapsed | Annex-3 3.1c; 2.1(iv) |
| Fire licence, stamp, UDIN | Fire licence re-uploaded after expiry; a stamp number or UDIN reused in another year | Annex-3 3.1d; 2.3.4b |
| Coordinates | Move beyond a set threshold | Annex-2.1(vi) |
| "Deficiencies Noted based on Self Disclosure" in last year's EoA letter | The same deficiency appears again after its compliance window (window from the letter text, else by template year; Portal spec §2.10) | EoA letter; 2.5(c) |
| Merger / change-request grid in EoA letters | A structural change (e.g. "Merger … Approved") is not reflected in this year's land, rooms or programmes | Table 2.3 |
| Published Mandatory Disclosure vs portal data | Intake, faculty or fire-certificate status on the website differs from what was filed; letters "since inception" missing | Annex-18 |

**Demo data:** the corpus includes several real same-institution year pairs and the template evolution of the affidavit (2020-21 → 2026-27), the EoA letter (2020-21 → 2026-27) and the Deficiency Report (2016-17 → 2024-25). Their **layouts** are reused with **synthetic values only**. Real files stay on the team's laptop and never enter this repo.

### C5. Differentiators
**Already done by the AICTE portal itself (never claim these):** norm arithmetic in the Deficiency Report (D2); within-portal faculty duplicate flag and PAN validation.

Ours, all grounded in the APH:
1. **Process-native routing:** every check is tied to its Table 2.3 stage and committee, including **self-disclosure EoA as an unscrutinised flow**.
2. **Template-aware, year-versioned affidavit diff** against the portal draft for the same application, plus **reconciliation against the portal's own Application Report data**.
3. **Annexure-14 issuer validation** per state and area type, plus issuer-type, addressee-entity, block-coverage, occupancy-class and **height/area** checks on OC, Form D and fire licences.
4. **APH date logic:** partial OC limited to 2 consecutive years; structural stability required after 30 years; lease remaining vs longest course duration; fire/Form D validity; compliance windows.
5. **Coordinates + the 3-plot / 2-km rule.**
6. **EVC video compliance** (≥30 min; GPS at 4 named buildings).
7. **Real DSC vs signature image**, stamp chronology/reuse, signer = Chairman/Secretary, edited after signing, notary-seal expiry, **UDIN structure**.
8. **Risk-ranked selection for the "random" EVC.**
9. **Faculty ID update lag (6.14c) + a pseudonymised cross-year/cross-institution identity graph + portal-vs-website faculty check.**
10. **Year-over-Year Reconciliation (M13)** where each change is cleared only if an approved application explains it.

### C6. Prototype scope
- **Phase 1:** self-disclosure EoA end to end (B1 documents 1–7 + faculty data + Application Report data + previous EoA letter) on a synthetic corpus built from the real templates, with:
  - the 24-declaration affidavit diff, reconciliation against Application Report fields, and date rules working on real-format documents;
  - TN fire licence + Form D adapters (TN-first demo; mock mode);
  - M13 on two synthetic years per institution.
- **Phase 2:** Scrutiny/EVC categories (Formats 1–3, state rule tables, Certificate 2), EVC video compliance, risk-ranked EVC selection, and SHC/SAC dossiers.

### C7. Open items
| # | Item | Status |
|---|---|---|
| 1 | Portal-generated affidavit layout | **Resolved for 2024-27:** 19 + 5 = 24 declarations, 4 room tables, land table. Remaining [VERIFY]: whether "Increase in Intake" still adds a block after 2023-24; a 2024+ executed copy with a real DSC. |
| 2 | TN OC (CMDA/DTCP) and fire formats | Mostly resolved (TN fire licences, Form D, Tahsildar certificate). Missing: a CMDA/DTCP completion certificate. |
| 3 | SHCIL e-stamp format | Resolved (format). Automated-access terms [VERIFY]. |
| 4 | ICAI UDIN | Structure known. Third-party verification access [VERIFY]. |
| 5 | What the portal Deficiency Report covers | Resolved (D2). |
| 6 | APH: Annexure-2.1(iii) cites "Clause 7.17", but Chapter VII ends at 7.13 | Unchanged. |
| 7 | Non-nil Deficiency Report layout | Resolved: same skeleton as nil. |
| 8 | Structural stability, satellite map, Format 2/3, EVC video | Structural resolved for TN; Format 3: 1 sample; missing: Format 2, satellite map image, building plans, land deeds. |

---

## Part D. Real-format findings (45-PDF public corpus, two runs)
Coverage: 14 states/UTs, AY 2016-17 to 2026-27. All extractions were redacted (names, contacts, ID values replaced by patterns). All observations are neutral inputs for rule design, not allegations about any institution.

### D1. Formats confirmed
- **Portal Deficiency Report** (Oracle BI Publisher):
  - masthead "APPROVAL PROCESS YYYY-YY / Application Deficiency Report";
  - header with Regional Office, Application ID, Permanent ID, "Overall Deficiency";
  - every table ends in a **Yes/No "Deficiency" column**, with no remarks or compliance column;
  - running footer with signature/seal/date boxes, "Printed By", "Page N of M";
  - declaration a)–f), where f) is assembled from the categories applied for.
  - It exists as a text download and as a scanned wet-signed printout.
  - Rule: Overall = Yes iff any row = Yes. Ignore the Land "TOTAL" row (it adds unlike units).
- **Portal Application Report, portal affidavit, EoA and LoA letters, faculty export, external certificates:** see B1.
- **Date order seen in executed affidavits:** application → stamp → notarisation → DSC → upload. One executed copy prints a DSC mark dated two days **after** the notarisation on the same notarised page, and that mark is an image (review case).

### D2. What the portal Deficiency Report already covers (SATYA must not duplicate it)
It computes, from **self-declared data only**: principal eligibility; "Other Details" (5 items); anti-ragging (7 items); faculty total vs required; administrative and amenities areas; computational and library facilities; instructional common facilities and per-programme room areas; an "Other Facilities" yes/no checklist (32 items in 2018-19, 51 in 2019-20, 40 in 2024-25), which includes "Fire and Safety Certificate" as **Yes/No only**.

**It does not:** verify any document's authenticity, issuer, validity or scope; compare the affidavit with portal data; look at previous years or other institutions; check faculty identities. **These gaps are SATYA's scope.** M4 imports the report's result rather than recomputing it.

### D3. APH text vs real documents
| Item | APH text | Real documents |
|---|---|---|
| Affidavit declarations | 33 listed | **24** in the 2024-25, 2025-26 and 2026-27 portal drafts (19 core + 5 Existing Institute); 27 in a 2023-24 copy with an Increase-in-Intake block; 12 in the 2020-21 "Undertaking" |
| Affidavit land table | document name, deed holder, registration date, plot no., address, district, acres | `Name of the deed Holder \| Document No. \| Date of Registration \| Plot No. \| Address (Village) District \| Area in Acre`; total left blank by the portal |
| Affidavit room table | room no., type, carpet m², completion status | 4 area tables; completion split into 3 columns; values "Ready"; room IDs can be lists or aggregate rows |
| Clause references inside the affidavit | Annexure numbering (APH 2024-27) | "Appendix 16/17", "Appendix 6", "Regulation Regulations, 2021" in every year |
| Stamp instrument | ₹100 e-stamp or non-judicial stamp | SHCIL e-Stamp (KA); e-Court Fee + adhesive stamps (BR) |
| Occupancy document | OC/CC per Annexure-14 | Also **Building License / Form D** (TN e-District licence) and revenue (Tahsildar) certificates |
| Mandatory Disclosure | Annexure-18 order | Three generations in use: Annexure-18; "Appendix 8"; older Roman I–XV |
| Audited accounts | previous year; 3 FYs on the website | 1 FY or stale FYs; UDIN absent in all AICTE-linked samples |
| Deficiency Report checklist | — | changes yearly (32 → 51 → 40 items) |
| EoA letter | — | columns renamed/reordered by year; deficiency block optional; instructions count 4/9/10 |

### D4. Parser rules learned
- **IDs:**
  - Permanent ID `1-` + **7–11 digits**;
  - Application ID `1-` + 10 digits (≤ 2020) or 11 digits, with an optional "*" suffix in 2012–13;
  - Faculty ID `1-` + 9–11 digits, optional space after "1-"; the hyphen can be a non-ASCII glyph;
  - portal user IDs: `ae` + 6–7 digits (AICTE side), `aict` + 5 digits (institution login).
- **F.No.:** EoA `<Region>/1-<AppID>/YYYY/EOA` (+ "/Corrigendum-N"); LoA `<Region>/<AY>/1-<AppID>`; regions include "South-West", "North-West", "South-Central", historic "J&K". Institution-typed copies may put **spaces around "/"**, so match with `\s*/\s*`.
- **TN references:** fire `####/RFL/NMSB/YYYY`; Form D `##/YYYY`; panel-engineer registrations `SE/GR-1/##/##/###`, `CGLRGN/SE/GR-1/YYYY/##/###`; Tahsildar `L.Dis.No. ####/##`.
- **Stamps and audit:** SHCIL e-Stamp `IN-<ST>` + 14 digits + letter; UDIN 18 characters (see B1 row 7).
- **Text layers:** re-join hyphen-wrapped words; compare with whitespace removed; collapse doubled glyphs; strip watermark tokens; de-rotate rotated tables; strip "##" from intake numbers; accept No/NA.
- **Dates:** portal affidavit and 2025-26 Application Report are **MM/DD/YYYY**; 2026-27 Application Report and most letters are DD/MM/YYYY or DD-Mon-YYYY; pick the order per template year and reject impossible months; a deed date can appear in both orders in one row.
- **Template version:** key on "APPROVAL PROCESS YYYY-YY" plus the heading word. The masthead ministry and website domain are secondary hints only.
- **Blank values:** treat a blank "Overall Deficiency" as **unknown**, never "No".

### D5. Neutral rules suggested by the corpus
1. Every certificate/statement carries `valid_from`, `valid_to` and FY fields; compute expiry from state rules when only a duration is printed.
2. Certificate **issuer type, addressee, building/block, occupancy class, height and area** must match the institution and its application building data.
3. **Conditional clauses** in certificates are flagged.
4. Admissions above approved intake, after supernumerary allowances.
5. Internal-consistency checks: land area across fields with unit conversion; deed areas sum; building approved = sanctioned; trustee tenure; certificate valid-till > issue date; course-wise faculty counts vs list rows; admitted vs registered; computed averages and totals.
6. "Page N of M" in a portal letter equals the letter's own length.
7. Governing-body composition includes the mandated nominees.
8. Annexure-18 completeness (incl. LoA/EoA letters since inception).
9. Privacy check: public files exposing DOB, PAN or mobiles beyond Annexure-18 needs.
10. Room IDs unique across affidavit tables; the category line is present; decl. 4 is consistent with merger categories.
11. Multiple uploaded copies of one resolution must agree.

**Corpus counts (neutral, no names; 45 PDFs):**
- **3 of 45** PDFs carry a real PDF digital signature; **4 more** show a "digitally signed" mark that is only an image.
- **0 of 4** AICTE-linked financial samples carry an ICAI UDIN.
- QR/2D codes appear on 5 documents; the one decoded holds plain text, not a URL.
- **7 of 19** run-2 documents were labelled wrongly by heading/filename or by the search agent.

### D6. Still missing or under-sampled
A genuine university Format 2; a satellite map image; building plan sheets and land deeds; a CMDA/DTCP completion certificate; pay receipts; an AICTE-trust audit with a UDIN; a 2024+ executed affidavit with a real DSC. One sample only: non-nil Deficiency Report, structural stability (TN), Format 3, LoA. Fire/OC samples only from TN, TG, DL, RJ.
