import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import { LABEL_PRECEDENCE } from "@satya/shared-types";
import { StatusLabel } from "../src/components/ui/StatusLabel";
import en from "../messages/en.json";
import hi from "../messages/hi.json";

const render = (props: Parameters<typeof StatusLabel>[0], locale: "en" | "hi" = "en") =>
  renderToStaticMarkup(
    createElement(
      NextIntlClientProvider,
      { locale, messages: locale === "en" ? en : hi } as never,
      createElement(StatusLabel, props),
    ),
  );

describe("StatusLabel", () => {
  it("has a full and a short name for each of the six labels", () => {
    for (const label of LABEL_PRECEDENCE) {
      expect(en.status.label[label]).toBeTruthy();
      expect(en.status.short[label]).toBeTruthy();
      expect(hi.status.label[label]).toBeTruthy();
    }
  });

  it("renders sentence-case text with an aria-hidden icon", () => {
    const html = render({ label: "mismatch_detected" });
    expect(html).toContain("Mismatch detected");
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain("MISMATCH");
  });

  it("table rows use the short text, a count and a descriptive aria-label", () => {
    const html = render({ label: "mismatch_detected", size: "sm", short: true, count: 2 });
    expect(html).toContain(">Mismatch<");
    expect(html).toContain('aria-label="Mismatch detected: 2 documents"');
    expect(html).toContain('tabindex="0"');
  });

  it("a zero count renders untinted but keeps its text", () => {
    const html = render({ label: "expired", count: 0 });
    expect(html).toContain('data-zero="true"');
    expect(html).toContain("Expired");
    expect(html).toContain('aria-label="Expired: 0 documents"');
  });

  it("renders in Hindi", () => {
    expect(render({ label: "verified" }, "hi")).toContain("सत्यापित");
  });
});
