import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { precheckEnvelope } from "../src/lib/envelope";
import { signatureHeader } from "../src/lib/sign";
import { ulid } from "../src/lib/ulid";

describe("mock portal signing", () => {
  it("matches the gateway's format: t=<unix>,kid=<kid>,v1=<hex HMAC of 't.body'>", () => {
    const header = signatureHeader('{"a":1}', "synthetic-secret", "k1", 1_800_000_000);
    const mac = createHmac("sha256", "synthetic-secret").update('1800000000.{"a":1}').digest("hex");
    expect(header).toBe(`t=1800000000,kid=k1,v1=${mac}`);
  });

  it("builds a synthetic precheck envelope with valid prefixed ULIDs", () => {
    const env = precheckEnvelope(new Date("2026-12-14T05:35:42Z"));
    expect(env.type).toBe("application.precheck_requested");
    expect(env.event_id).toMatch(/^evt_[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(env.correlation_id).toMatch(/^cor_[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(env.subject.application_id).toBe("1-90000004217");
    expect(ulid()).toHaveLength(26);
  });
});
