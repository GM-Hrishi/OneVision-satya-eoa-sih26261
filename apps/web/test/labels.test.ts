import { describe, expect, it } from "vitest";
import { LABEL_PRECEDENCE } from "@satya/shared-types";
import { LABEL_ORDER } from "../src/lib/labels";

describe("labels", () => {
  it("the workbench label order is the contract's precedence (Portal §2.6.3)", () => {
    expect([...LABEL_ORDER]).toEqual([...LABEL_PRECEDENCE]);
  });
});
