// Generates TS types, Pydantic v2 models and shared constants from schemas/*.schema.json.
// The JSON Schemas are the single source of truth; never edit files under */generated/ by hand.
// Usage: pnpm --filter @satya/shared-types gen   (or `make gen-types` from the repo root)
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { compile } from "json-schema-to-typescript";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemaDir = join(root, "schemas");
const tsOut = join(root, "ts", "src", "generated");
const pyOut = join(root, "python", "satya_shared_types", "generated");
const BANNER = "GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit.";

const files = readdirSync(schemaDir).filter((f) => f.endsWith(".schema.json")).sort();
const schemas = Object.fromEntries(files.map((f) => [f, JSON.parse(readFileSync(join(schemaDir, f), "utf8"))]));
const titleOf = (file) => schemas[file].title;

// ---- 1. Bundle every schema into one document with flat $defs --------------------------------
const defs = {};
const addDef = (name, body, from) => {
  if (defs[name]) throw new Error(`Duplicate definition name ${name} (from ${from})`);
  defs[name] = body;
};
const rewriteRefs = (node) => {
  if (Array.isArray(node)) return node.map(rewriteRefs);
  if (node && typeof node === "object") {
    const out = {};
    for (const [k, v] of Object.entries(node)) {
      if (k === "$ref" && typeof v === "string") {
        const [file, frag = ""] = v.split("#");
        if (frag.startsWith("/$defs/")) out[k] = `#${frag}`;
        else if (file && schemas[file] && (frag === "" || frag === "/")) out[k] = `#/$defs/${titleOf(file)}`;
        else throw new Error(`Unsupported $ref ${v}`);
      } else out[k] = rewriteRefs(v);
    }
    return out;
  }
  return node;
};
for (const file of files) {
  const body = { ...schemas[file] };
  const inner = body.$defs ?? {};
  for (const key of ["$schema", "$id", "$defs"]) delete body[key];
  for (const [name, def] of Object.entries(inner)) addDef(name, rewriteRefs(def), file);
  if (file !== "common.schema.json") addDef(body.title, rewriteRefs(body), file);
}
const sortedDefs = Object.fromEntries(Object.keys(defs).sort().map((k) => [k, defs[k]]));
const bundle = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "https://schemas.satya-eoa.invalid/v1/bundle.schema.json",
  title: "SatyaContracts",
  description: `${BANNER} All SATYA-EoA contracts (Portal spec §2) in one document.`,
  type: "object",
  $defs: sortedDefs,
};
const bundleText = JSON.stringify(bundle, null, 2) + "\n";
for (const dir of [tsOut, pyOut]) {
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "bundle.schema.json"), bundleText);
}

// ---- 2. Constants read from schema annotations -----------------------------------------------
const label = schemas["verification-label.schema.json"];
const envDefs = schemas["event-envelope.schema.json"].$defs;
const alert = schemas["alert.schema.json"];
const snapshot = schemas["application-snapshot.schema.json"];
const handling = {};
const tokenFields = {};
const walk = (node, path) => {
  if (node.$ref?.startsWith("#/$defs/")) node = { ...snapshot.$defs[node.$ref.slice(8)], ...node, $ref: undefined };
  if (node.type === "array" && node.items) return walk(node.items, `${path}[]`);
  for (const [name, prop] of Object.entries(node.properties ?? {})) {
    const p = path ? `${path}.${name}` : name;
    if (!prop["x-handling"]) throw new Error(`ApplicationSnapshot field ${p} has no x-handling annotation`);
    handling[p] = prop["x-handling"];
    if (prop["x-token-field"]) tokenFields[p] = prop["x-token-field"];
    walk(prop, p);
  }
};
walk(snapshot, "");
const consts = {
  EVENT_SPEC: schemas["event-envelope.schema.json"].properties.spec.const,
  VERIFICATION_LABELS: label.enum,
  LABEL_PRECEDENCE: label["x-precedence"],
  INBOUND_EVENT_TYPES: envDefs.InboundEventType.enum,
  OUTBOUND_EVENT_TYPES: envDefs.OutboundEventType.enum,
  EVENT_TYPES: envDefs.EventType.enum,
  DISPOSITION_ACTIONS: schemas["disposition.schema.json"].properties.action.enum,
  RISK_BANDS: schemas["risk-band.schema.json"].enum,
  YOY_VERDICTS: schemas["yoy-verdict.schema.json"].enum,
  ROLES: schemas["common.schema.json"].$defs.Role.enum,
  ALERT_TYPES: alert.$defs.AlertType.enum,
  ALERT_SUBTYPES: alert["x-subtypes"],
  SNAPSHOT_FIELD_HANDLING: handling,
  SNAPSHOT_TOKEN_FIELDS: tokenFields,
  SNAPSHOT_REJECTED_FIELDS: snapshot["x-rejected-fields"],
  SCHEMA_TITLES: files.filter((f) => f !== "common.schema.json").map(titleOf),
};
const ts = [`// ${BANNER}`, ""];
for (const [k, v] of Object.entries(consts)) ts.push(`export const ${k} = ${JSON.stringify(v, null, 2)} as const;`, "");
writeFileSync(join(tsOut, "constants.ts"), ts.join("\n"));
const py = [`"""${BANNER}"""`, "", "from typing import Final", ""];
const pyLit = (v) => JSON.stringify(v, null, 4).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False");
for (const [k, v] of Object.entries(consts)) {
  const val = Array.isArray(v) ? `(${v.map((x) => JSON.stringify(x)).join(", ")}${v.length === 1 ? "," : ""})` : pyLit(v);
  py.push(`${k}: Final = ${val}`, "");
}
writeFileSync(join(pyOut, "constants.py"), py.join("\n"));

// ---- 3. TypeScript types ---------------------------------------------------------------------
// TS cannot express x- annotations or if/then rules, and keeping them makes the compiler emit
// numbered duplicate aliases. They stay enforced by JSON Schema validation (ajv / jsonschema).
const forTs = (node) => {
  if (Array.isArray(node)) return node.map(forTs);
  if (node && typeof node === "object") {
    const out = {};
    for (const [k, v] of Object.entries(node)) {
      if (k.startsWith("x-")) continue;
      if (k === "allOf" && v.every((e) => "if" in e)) continue;
      out[k] = forTs(v);
    }
    return out;
  }
  return node;
};
const tsTypes = await compile(forTs(bundle), "SatyaContracts", {
  bannerComment: `/* ${BANNER} */`,
  unreachableDefinitions: true,
  additionalProperties: false,
  strictIndexSignatures: true,
  format: true,
  style: { singleQuote: false, printWidth: 100 },
});
writeFileSync(join(tsOut, "contracts.ts"), tsTypes);

// ---- 4. Pydantic v2 models (datamodel-code-generator via uv) ----------------------------------
execFileSync(
  "uv",
  [
    "run", "--frozen", "datamodel-codegen",
    "--input", join(pyOut, "bundle.schema.json"),
    "--input-file-type", "jsonschema",
    "--output", join(pyOut, "models.py"),
    "--output-model-type", "pydantic_v2.BaseModel",
    "--target-python-version", "3.12",
    "--use-title-as-name",
    "--use-standard-collections",
    "--use-union-operator",
    "--use-double-quotes",
    "--use-annotated",
    "--field-constraints",
    "--use-schema-description",
    "--use-field-description",
    "--disable-timestamp",
    "--formatters", "black", "isort",
    "--field-extra-keys-without-x-prefix", "x-handling", "x-token-field",
    "--custom-file-header", `# ${BANNER}`,
  ],
  { stdio: "inherit", cwd: resolve(root, "../..") },
);
writeFileSync(join(pyOut, "__init__.py"), `"""${BANNER}"""\n`);
console.log(`shared-types: ${Object.keys(sortedDefs).length} definitions -> TS + Pydantic + constants`);
