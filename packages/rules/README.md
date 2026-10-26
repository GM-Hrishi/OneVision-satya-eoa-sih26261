# packages/rules (placeholder)
Versioned YAML rules for the M4 rule engine (P-7) and later modules.

- Every rule carries `rule_id`, `rule_version`, `aph_clause`, `aph_edition` (guard rail 6). Unconfirmed clauses are marked `[VERIFY]`.
- **Never** re-implement what the portal Deficiency Report already computes (design D2, guard rail 8); import its result instead.
- Built in the **M4 slice** (P-7). Not implemented in slice 0.
