// One valid synthetic example per schema validates; one invalid example fails (ajv, JSON Schema 2020-12).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import bundle from "../src/generated/bundle.schema.json" with { type: "json" };
import {
  ALERT_SUBTYPES,
  ALERT_TYPES,
  EVENT_TYPES,
  INBOUND_EVENT_TYPES,
  LABEL_PRECEDENCE,
  OUTBOUND_EVENT_TYPES,
  SCHEMA_TITLES,
  SNAPSHOT_FIELD_HANDLING,
  SNAPSHOT_REJECTED_FIELDS,
  VERIFICATION_LABELS,
} from "../src/index.js";

const ajv = new Ajv2020.default({ strict: true, strictRequired: false, allowUnionTypes: true, allErrors: true });
addFormats.default(ajv);
for (const keyword of ["x-handling", "x-token-field", "x-precedence", "x-rejected-fields", "x-subtypes"]) {
  ajv.addKeyword(keyword);
}
ajv.addSchema(bundle, "bundle");
const validate = (name: string, data: unknown) => {
  const fn = ajv.getSchema(`bundle#/$defs/${name}`);
  if (!fn) throw new Error(`no schema ${name}`);
  return fn(data);
};
const examples = join(import.meta.dirname, "..", "..", "examples");
const load = (kind: "valid" | "invalid", name: string): unknown =>
  JSON.parse(readFileSync(join(examples, kind, `${name}.json`), "utf8"));
const names = [...SCHEMA_TITLES, "Check"];

describe.each(names)("%s", (name) => {
  it("accepts the valid synthetic example", () => {
    expect(validate(name, load("valid", name))).toBe(true);
  });
  it("rejects the invalid example", () => {
    expect(validate(name, load("invalid", name))).toBe(false);
  });
});

describe("constants", () => {
  it("label precedence is a permutation of the six labels, most severe first", () => {
    expect([...LABEL_PRECEDENCE].sort()).toEqual([...VERIFICATION_LABELS].sort());
    expect(LABEL_PRECEDENCE[0]).toBe("mismatch_detected");
  });
  it("event types are inbound plus outbound", () => {
    expect(new Set(EVENT_TYPES)).toEqual(new Set([...INBOUND_EVENT_TYPES, ...OUTBOUND_EVENT_TYPES]));
  });
  it("every alert type has a subtype list", () => {
    expect(Object.keys(ALERT_SUBTYPES).sort()).toEqual([...ALERT_TYPES].sort());
  });
  it("snapshot has no X fields", () => {
    expect(new Set(Object.values(SNAPSHOT_FIELD_HANDLING))).toEqual(new Set(["K", "T", "R"]));
    for (const rejected of SNAPSHOT_REJECTED_FIELDS) expect(SNAPSHOT_FIELD_HANDLING).not.toHaveProperty([rejected]);
  });
});

describe("guard rails in the envelope", () => {
  it("an outbound event without advisory is rejected", () => {
    const env = { ...(load("valid", "EventEnvelope") as object), type: "case.validation_completed", producer: "satya" };
    expect(validate("EventEnvelope", env)).toBe(false);
    expect(validate("EventEnvelope", { ...env, advisory: true, regulatory_effect: "none" })).toBe(true);
  });
});
