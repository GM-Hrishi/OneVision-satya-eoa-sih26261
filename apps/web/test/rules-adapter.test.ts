import { describe, expect, it } from "vitest";
import type { QueueRow } from "../src/lib/demo-types";
import { fromRuleDetail, seenRules } from "../src/lib/api/k-adapters/rules";

// The rule detail below is the example in docs/API-NOTES.md (feat/logic-rival-parity).
const EXAMPLE = {
  advisory: true, aph_clause: "2.3.4b", aph_edition: "2024-27", label: "manual_review_required",
  limitation: { key: "limitation.shared_number", text: "This does not show wrongdoing. A number typed twice by mistake, or a filing resubmitted by the institution, would look the same." },
  limitation_key: "shared_number", preliminary_indicator: true, rule_id: "STAMP-REUSE", rule_version: "0.1.0", severity: "critical",
};

describe("rules adapter", () => {
  it("reads the documented rule detail", () => {
    expect(fromRuleDetail(EXAMPLE)).toMatchObject({ ruleId: "STAMP-REUSE", clause: "2.3.4b", edition: "2024-27", severity: "critical", label: "manual_review_required", version: "0.1.0" });
    expect(fromRuleDetail(EXAMPLE)?.limitation).toContain("does not show wrongdoing");
  });

  it("an unknown label or severity becomes null, never a guess; a body without a rule id is refused", () => {
    expect(fromRuleDetail({ ...EXAMPLE, label: "approved", severity: "huge" })).toMatchObject({ label: null, severity: null });
    expect(fromRuleDetail({})).toBeNull();
    expect(fromRuleDetail(null)).toBeNull();
  });

  it("lists each rule once, in first-seen order, from the queue rows", () => {
    const row = (...ids: string[]) => ({ top_reasons: ids.map((rule_id) => ({ flag_id: rule_id, rule_id, aph_clause: "x", short_text: `s ${rule_id}` })) }) as unknown as QueueRow;
    expect(seenRules([row("A", "B"), row("B", "C")]).map((r) => r.ruleId)).toEqual(["A", "B", "C"]);
    expect(seenRules([])).toEqual([]);
  });
});
