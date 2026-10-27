// Generates src/styles/tokens.css from src/styles/tokens.json (design system, UI spec §8).
// `--check` fails if tokens.css is out of date or a §8 colour is missing (used by `pnpm build` and CI).
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const app = join(here, "..");
const tokens = JSON.parse(readFileSync(join(app, "src/styles/tokens.json"), "utf8"));
const lines = ["/* GENERATED from tokens.json by scripts/gen-tokens.mjs. Do not edit. Source: UI spec §8. */", ":root {"];
for (const [group, values] of Object.entries(tokens)) {
  if (group.startsWith("_")) continue;
  for (const [name, value] of Object.entries(values)) lines.push(group === "raw" ? `  --${name}: ${value};` : `  --${group}-${name}: ${value};`);
}
lines.push("}", "");
const css = lines.join("\n");
const target = join(app, "src/styles/tokens.css");

const spec = readFileSync(join(app, "../../docs/specs/05-ui-design-spec.md"), "utf8");
const summary = spec.split("\n").find((l) => l.startsWith("Token summary:")) ?? "";
const specHex = new Set((summary.match(/#[0-9A-Fa-f]{6}/g) ?? []).map((h) => h.toUpperCase()));
const ours = new Set(Object.values({ ...tokens.color, ...tokens.raw }).map((h) => h.toUpperCase()));
const missing = [...specHex].filter((h) => !ours.has(h));
if (specHex.size === 0 || missing.length) {
  console.error(`tokens.json is missing UI spec §8 colours: ${missing.join(", ") || "(no summary line found)"}`);
  process.exit(1);
}
if (process.argv.includes("--check")) {
  const current = readFileSync(target, "utf8");
  if (current !== css) {
    console.error("src/styles/tokens.css is out of date: run `pnpm --filter @satya/web gen:tokens`");
    process.exit(1);
  }
  console.log(`tokens.css up to date (${specHex.size} §8 colours present)`);
} else {
  writeFileSync(target, css);
  console.log(`wrote tokens.css (${specHex.size} §8 colours present)`);
}
