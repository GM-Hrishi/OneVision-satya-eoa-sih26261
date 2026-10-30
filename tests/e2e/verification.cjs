// Slice 2 acceptance in a real browser on default settings: RB-06 Verification panel (UI §7.2) for the
// synthetic demo cases, reached from the queue and the case tabs after Keycloak sign-in.
// Usage: node tests/e2e/verification.cjs   (needs `make up`; Caddy's local CA trusted, see DEV-SETUP)
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

async function login(page, username, start = `${BASE}/`) {
  await page.goto(start);
  await page.waitForURL(/auth\.localhost/, { timeout: 20000 });
  await page.fill("#username", username);
  await page.fill("#password", env.DEMO_USER_PASSWORD);
  await page.click("#kc-login");
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${page.url()}: ${m.text()}`); });
  page.on("pageerror", (e) => consoleErrors.push(`${page.url()}: ${e.message}`));

  await login(page, "rb.southern.demo");
  await page.waitForURL(`${BASE}/overview`, { timeout: 20000 });
  await page.goto(`${BASE}/rb-queue`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  await page.getByRole("link", { name: "Open case for application 1-90000004217" }).click();
  await page.waitForURL(`${BASE}/case/${DIT03}`, { timeout: 30000 });
  await page.getByRole("link", { name: "Verification" }).first().click();
  await page.waitForURL(`${BASE}/case/${DIT03}/verification`, { timeout: 30000 });
  await page.waitForSelector("#ver-docs", { timeout: 30000 });
  check(true, "queue link opens RB-06 for DIT 03");

  const title = await page.title();
  const desc = await page.getAttribute('meta[name="description"]', "content");
  check((await page.locator("h1").count()) === 1 && title.includes("Verification") && !!desc, `one H1, title and meta description ("${title}")`);
  check((await page.locator('nav[aria-label="Breadcrumb"] a[href="/rb-queue"]').count()) === 1, "breadcrumb links back to the queue");
  check((await page.locator('nav[aria-label="Case views"] a[aria-current="page"]').textContent()) === "Verification", "case tabs mark Verification as current");
  const main = await page.textContent("main");
  check(main.includes("Affidavit 2 (sworn copy)") && main.includes("Audited statement of accounts FY 2025-26"), "one row per document");
  check(main.includes("Manual review required") && main.includes("Source unavailable"), "labels as text: affidavit manual review, accounts source unavailable");
  check(main.includes("Image only, not a real signature"), "issuer badge IMAGE ONLY on the affidavit (F5)");
  check((main.match(/Uploader signature present/g) || []).length === 2, "uploader badge PRESENT on both documents (F6)");
  check(main.includes("Wet seal, not digital"), "audited statement issuer badge NOT DIGITAL (WET SEAL)");
  check(main.includes("Chain to the test trust anchor ok") && main.includes("Test trust anchor"), "chain checked against the test trust anchor and tagged");
  check(main.includes("ICAI UDIN: no automated channel") && main.includes("NO CHANNEL"), "accounts source: no ICAI channel (F10)");
  check(main.includes("A valid uploader signature never makes a document verified."), "mapping legend states the uploader rule");
  check(main.includes("How signatures map to the six labels"), "mapping legend on screen");
  check(main.includes("Suggested next steps") && !main.includes("M11"), "actions are suggestions, no build codes, no dead buttons");
  const buttons = await page.locator("main button").allTextContents();
  check(!buttons.some((b) => /approve|reject|clear/i.test(b)), "no approve, reject or clear control on the page");
  await page.locator("details summary").first().click();
  const details = await page.textContent("main");
  check(details.includes("Printed mark dated after notarisation") && details.includes("Second Party is the Council"), "checks per document listed with reasons");
  await page.screenshot({ path: path.join(shots, "rb06-dit03.png"), fullPage: true });

  await page.getByRole("link", { name: "Affidavit diff" }).first().click();
  await page.waitForURL(`${BASE}/case/${DIT03}/affidavit`, { timeout: 30000 });
  check(true, "case tab back to RB-05");

  await page.goto(`${BASE}/case/${DCE05}/verification`);
  await page.waitForSelector("#ver-docs");
  const clean = await page.textContent("main");
  check(clean.includes("Verified") && clean.includes("Issuer signature verified"), "clean control DCE 05: affidavit VERIFIED, issuer signature verified");
  await page.screenshot({ path: path.join(shots, "rb06-dce05.png"), fullPage: true });

  const nf = await page.goto(`${BASE}/case/cas_01JD3M5A00000000000000ZZ99/verification`);
  check(nf.status() === 404, "unknown case is a 404 page");

  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto(`${BASE}/case/${DIT03}/verification`);
  await page.waitForSelector("#ver-docs");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflow <= 0, `360px width: no horizontal scroll (overflow ${overflow}px)`);
  await page.screenshot({ path: path.join(shots, "rb06-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  const big = await browser.newContext({ viewport: { width: 1280, height: 900 }, bypassCSP: true, storageState: await ctx.storageState() });
  const bigPage = await big.newPage();
  await bigPage.goto(`${BASE}/case/${DIT03}/verification`);
  await bigPage.waitForSelector("#ver-docs");
  await bigPage.addStyleTag({ content: "html{font-size:200% !important}" });
  const overflow200 = await bigPage.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflow200 <= 0, `200% text: no horizontal scroll (overflow ${overflow200}px)`);
  await big.close();

  await page.goto(`${BASE}/case/${DIT03}/verification`);
  await page.getByRole("button", { name: /Account menu/ }).click();
  await page.getByRole("menuitemradio", { name: "हिन्दी" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "hi");
  await page.waitForFunction(() => document.querySelector("h1")?.textContent?.includes("सत्यापन"), null, { timeout: 15000 }).catch(() => {});
  check((await page.textContent("h1")).includes("सत्यापन"), "RB-06 in Hindi");
  await page.screenshot({ path: path.join(shots, "rb06-hi.png"), fullPage: true });
  await page.getByRole("button", { name: /खाता मेनू/ }).click();
  await page.getByRole("menuitemradio", { name: "English" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "en");

  const ctx2 = await browser.newContext();
  const page2 = await ctx2.newPage();
  await login(page2, "institution.demo03");
  await page2.waitForURL(`${BASE}/home`, { timeout: 20000 }).catch(() => {});
  const res403 = await page2.goto(`${BASE}/case/${DIT03}/verification`);
  check(res403.status() === 403, "403 for a non-RB user");

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nVERIFICATION ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
