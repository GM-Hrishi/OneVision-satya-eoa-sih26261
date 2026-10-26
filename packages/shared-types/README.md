# @satya/shared-types · satya-shared-types
The SATYA-EoA data contracts (Portal spec §2). **`schemas/*.schema.json` are the single source of truth.**

| Path | What |
|---|---|
| `schemas/` | JSON Schema 2020-12, one file per contract; field names exactly as in the Portal spec |
| `scripts/generate.mjs` | bundles the schemas, emits TS types, Pydantic v2 models and constants |
| `ts/src/generated/` | `contracts.ts` (json-schema-to-typescript), `constants.ts`, `bundle.schema.json` |
| `python/satya_shared_types/generated/` | `models.py` (datamodel-code-generator), `constants.py`, `bundle.schema.json` |
| `examples/valid`, `examples/invalid` | one synthetic example per contract each way |

Regenerate after any schema change and commit the result: `make gen-types`. CI regenerates and fails on any diff.

## Annotations
- `x-handling` on every `ApplicationSnapshot` field: **K** keep · **T** tokenise (`x-token-field` names the stored token) · **R** result only. **X** fields do not exist in the model; they are listed in `x-rejected-fields` and the gateway answers `PERSONAL_DATA_REJECTED`. Exposed as `SNAPSHOT_FIELD_HANDLING`, `SNAPSHOT_TOKEN_FIELDS`, `SNAPSHOT_REJECTED_FIELDS`; Pydantic fields carry `json_schema_extra={"handling": …}`.
- `x-precedence` on `VerificationLabel` → `LABEL_PRECEDENCE` (most severe first).
- `x-subtypes` on `Alert` → `ALERT_SUBTYPES`; the type/subtype pairing is enforced with `if/then`.
- Rules TS cannot express (`if/then`, e.g. outbound events must carry `advisory: true`, `regulatory_effect: "none"`) are enforced by JSON Schema validation: `validator("EventEnvelope")` in Python, ajv in TS.
