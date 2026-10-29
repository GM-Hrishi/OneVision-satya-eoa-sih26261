import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const root = join(__dirname, "..");
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const layout = readFileSync(join(root, "src/app/layout.tsx"), "utf8");
const tokens = readFileSync(join(root, "src/styles/tokens.css"), "utf8");

describe("self-hosted fonts (B-31)", () => {
  it("the four Fontsource packages are dependencies", () => {
    for (const name of ["noto-sans", "noto-sans-devanagari", "noto-sans-mono", "public-sans"]) {
      expect(pkg.dependencies[`@fontsource/${name}`], name).toBeTruthy();
    }
  });

  it("the root layout imports exactly the weights in use, once", () => {
    const imports = [...layout.matchAll(/^import "@fontsource\/([\w-]+)\/(\d+)\.css";$/gm)].map((m) => `${m[1]}/${m[2]}`);
    expect(imports.sort()).toEqual(
      [
        "noto-sans/400",
        "noto-sans/500",
        "noto-sans/700",
        "noto-sans-devanagari/400",
        "noto-sans-devanagari/700",
        "noto-sans-mono/400",
        "noto-sans-mono/700",
        "public-sans/800",
      ].sort(),
    );
  });

  it("the font tokens name the right families and no CDN is referenced", () => {
    expect(tokens).toMatch(/--font-sans: "Noto Sans"/);
    expect(tokens).toMatch(/--font-mono: "Noto Sans Mono"/);
    expect(tokens).toMatch(/--font-caps: "Public Sans"/);
    expect(layout).not.toMatch(/fonts\.googleapis|fonts\.gstatic|https?:\/\//);
  });
});
