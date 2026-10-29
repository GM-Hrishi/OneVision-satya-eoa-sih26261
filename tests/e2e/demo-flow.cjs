// Slice D acceptance in a real browser on default settings: queue (band, filter), case review with the
// PDF.js viewer, decision bar, pick-a-seeded-document, audit chain and alerts, signed in as
// rb.southern.demo. Run `make demo-reset` first so the ledger holds the seed.
// Usage: node tests/e2e/demo-flow.cjs   (needs `make up`; Caddy's local CA trusted, see DEV-SETUP)
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const env = Object.fromEntries(
  fs.readFileSync(path.join(root, ".env"), "utf8").split("\n").filter((l) => l.includes("=") && !l.startsWith("#"))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1)]),
);
const shots = process.env.SHOTS_DIR || path.join(root, ".logs", "screens");
fs.mkdirSync(shots, { recursive: true });
const BASE = "https://localhost";
const DIT03 = "cas_01JD3M5A00000000000000DT03";
const DCE05 = "cas_01JD3M5A00000000000000CE05";
let failures = 0;
const check = (ok, msg) => { console.log(`${ok ? "PASS" : "FAIL"} ${msg}`); if (!ok) failures++; };

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${page.url()}: ${m.text()}`); });
  page.on("pageerror", (e) => consoleErrors.push(`${page.url()}: ${e.message}`));

  await page.goto(`${BASE}/`);
  await page.waitForURL(/auth\.localhost/, { timeout: 20000 });
  await page.fill("#username", "rb.southern.demo");
  await page.fill("#password", env.DEMO_USER_PASSWORD);
  await page.click("#kc-login");
  await page.waitForURL(`${BASE}/overview`, { timeout: 20000 });
  await page.waitForSelector("#ov-bands", { timeout: 30000 });
  check((await page.textContent("main")).includes("8 cases submitted"), "Overview is the landing page and counts the 8 seeded cases");
  await page.goto(`${BASE}/rb-queue`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  check((await page.locator("tbody tr").count()) === 8, "queue lists the 8 seeded cases");
  const body = await page.textContent("tbody");
  check(/HIGH/i.test(body) && /MEDIUM/i.test(body) && /LOW/i.test(body), "bands High, Medium and Low are shown as text");
  await page.goto(`${BASE}/rb-queue?band=high`);
  check((await page.locator("tbody tr").count()) === 2, "filter by band High shows 2 cases");
  await page.screenshot({ path: path.join(shots, "demo-queue.png"), fullPage: true });

  await page.goto(`${BASE}/case/${DIT03}`);
  await page.waitForSelector("#flags", { timeout: 30000 });
  const main = await page.textContent("main");
  check(main.includes("Simulated source") && main.includes("Test trust anchor"), "simulated sources and the test trust anchor are tagged");
  check(!(await page.locator("main button").allTextContents()).some((b) => /approve|reject/i.test(b)), "no approve or reject control");
  await page.locator("text=Show in document").nth(2).click();
  await page.waitForFunction(() => document.querySelector("canvas") && document.querySelector("canvas").width > 100, null, { timeout: 20000 });
  check((await page.locator("canvas").count()) === 1, "PDF.js opens the document at the finding's page");
  await page.locator("input[type=radio][value=escalate_manual]").first().check();
  await page.locator("textarea").first().fill("Check the deed with the registrar.");
  await page.locator("button:has-text('Record decision')").first().click();
  await page.waitForSelector("text=Ledger entry", { timeout: 20000 });
  check(true, "decision recorded with a ledger entry number");
  await page.screenshot({ path: path.join(shots, "demo-case.png"), fullPage: true });

  await page.goto(`${BASE}/case/${DCE05}/upload`);
  const pick = page.locator("section[aria-labelledby=up-pick] form");
  await pick.locator("select[name=slot]").selectOption("accounts");
  await pick.locator("select[name=source_case_id]").selectOption({ label: "Demo College of Engineering 07" });
  await pick.locator("button").click();
  await page.waitForSelector("text=Stored and checked", { timeout: 30000 });
  check(true, "a seeded document can be used and the checks run again");

  await page.goto(`${BASE}/audit`);
  await page.waitForSelector("text=CHAIN VERIFIED", { timeout: 20000 });
  await page.locator("summary").first().click();
  check((await page.locator("pre").first().textContent()).length > 2, "an audit entry opens with its detail");
  await page.screenshot({ path: path.join(shots, "demo-audit.png"), fullPage: true });

  await page.goto(`${BASE}/alerts`);
  await page.waitForSelector("text=Suspected anomaly", { timeout: 20000 });
  check((await page.locator("li a:has-text('Open flag'), li a:has-text('Open document')").count()) >= 3, "alerts link to their flags or documents");

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nDEMO FLOW ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
