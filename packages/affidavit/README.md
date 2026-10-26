# packages/affidavit · satya-affidavit (M5, P-3)
Affidavit 2 normalised clause diff + ApplicationSnapshot reconciliation (design v2.2.1 B1 row 1, C3, D3, D4; Portal spec §2.6–2.7; UI spec §6.3, §7.1). Advisory only; synthetic data only.

| Module | What |
|---|---|
| `template.py` | Loads the year-versioned template profile (`packages/templates/affidavit-2/`) and renders the expected portal draft for one AID and AY |
| `rules.py` | Loads `packages/rules/m5-affidavit.yaml` (rule ID, version, APH clause, edition, severity, label, alert type/subtype) |
| `normalise.py` | Whitespace, dashes, hyphen re-join, strike-through option groups, names substituted, MM/DD dates |
| `ids.py` | Deterministic `doc_`/`flg_` IDs, HMAC tokens for T fields, masks |

Text layer only in slice 1; OCR comes with M3 (P-2).
