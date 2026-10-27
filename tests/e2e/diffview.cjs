// Slice 1 (+ slice 2 M6 sections) acceptance in a real browser on default settings: RB-05 Affidavit DiffView for the
// synthetic demo cases, reached from the queue after Keycloak sign-in as rb.southern.demo.
// Usage: node tests/e2e/diffview.cjs   (needs `make up`; Caddy's local CA trusted, see DEV-SETUP)
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
  // The queue streams a skeleton (loading.tsx) while it calls the API; wait for the list itself.
  await page.waitForSelector("#case-list", { timeout: 30000 });
  const queue = await page.textContent("main");
  check(queue.includes("1-90000004217") && queue.includes("1-90000005105"), "queue lists both demo cases");
  check(queue.includes("7 of 7") && queue.includes("0 of 0"), "queue shows findings awaiting a decision (7 = 5 M5 + 2 M6, and none)");
  await page.getByRole("link", { name: "Open case for application 1-90000004217" }).click();
  await page.waitForURL(`${BASE}/case/${DIT03}`, { timeout: 30000 });
  await page.getByRole("link", { name: "Affidavit diff" }).first().click();
  await page.waitForURL(`${BASE}/case/${DIT03}/affidavit`, { timeout: 30000 });
  check(true, "queue link opens RB-05 for DIT 03");
  await page.waitForSelector("#diff-flags", { timeout: 30000 });

  const title = await page.title();
  const desc = await page.getAttribute('meta[name="description"]', "content");
  check((await page.locator("h1").count()) === 1 && title.includes("Affidavit diff") && !!desc, `one H1, title and meta description ("${title}")`);
  check((await page.locator('nav[aria-label="Breadcrumb"] a[href="/rb-queue"]').count()) === 1, "breadcrumb links back to the queue");
  const main = await page.textContent("main");
  check(main.includes("CATEGORY LINE MISSING"), "structure check: CATEGORY LINE MISSING");
  check(main.includes("Findings (7)"), "flag rail lists 7 findings (5 M5 + 2 M6)");
  check((await page.locator("del", { hasText: "contiguous and undisputed," }).count()) === 1, "clause diff strikes 'contiguous and undisputed,' in declaration 9");
  check(main.includes("3.50") && main.includes("4.50") && main.includes("11.50") && main.includes("12.50"), "land table: 3.50 vs 4.50, computed 11.50 vs 12.50");
  check(main.includes("I-201") && main.includes("DUPLICATE ROOM ID"), "duplicate room ID I-201 shown");
  check((main.match(/Preliminary indicator\. Needs human verification\./g) || []).length === 7, "every flag carries the preliminary-indicator line");
  check(main.includes("Mismatch detected") && main.includes("Manual review required"), "labels shown as text");
  check(!main.includes("DEMO-DEED-0301") && main.includes("masked, ends in"), "deed numbers masked, with screen-reader text");
  check(!main.includes("checked by M6 (P-4)") && !main.includes("arrive with M6"), "no M6 placeholder left");
  check(main.includes("Image only, not a real signature") && main.includes("Uploader signature present"), "header badges: issuer IMAGE ONLY, uploader PRESENT (F5, F6)");
  check(main.includes("Chain to the test trust anchor ok") && main.includes("Test trust anchor"), "uploader chain checked against the test trust anchor, tagged");
  check(main.includes("AICTE NEW DELHI") && main.includes("Rs 100"), "stamp: Second Party and Rs 100 duty");
  check(main.includes("PRINTED MARK DATED AFTER NOTARISATION") && main.includes("IN ORDER"), "signing order: in order, printed mark after notarisation flagged");
  check(main.includes("VALID ON THE NOTARISATION DATE"), "notary seal valid on the notarisation date");
  check(main.includes("Printed signature mark without a real signature"), "SIG-IMAGE flag in the rail");
  const buttons = await page.locator("main button").allTextContents();
  check(!buttons.some((b) => /approve|reject|clear/i.test(b)), "no approve, reject or clear control on the page");
  await page.screenshot({ path: path.join(shots, "rb05-dit03.png"), fullPage: true });

  await page.getByRole("link", { name: "Show all declarations" }).click();
  await page.waitForURL(`${BASE}/case/${DIT03}/affidavit?all=1`);
  await page.waitForSelector("#diff-flags");
  check((await page.locator("main ol li").filter({ hasText: /SAME AS DRAFT|CHANGED/ }).count()) >= 24, "show all lists every declaration");
  await page.getByRole("link", { name: "Show changed only" }).click();
  await page.waitForURL(`${BASE}/case/${DIT03}/affidavit`);

  await page.goto(`${BASE}/case/${DCE05}/affidavit`);
  await page.waitForSelector("#diff-flags");
  const clean = await page.textContent("main");
  check(clean.includes("No findings.") && clean.includes("PRESENT") && clean.includes("Every declaration matches"), "clean control DCE 05 shows no findings");
  check(clean.includes("Issuer signature verified") && clean.includes("real signature (/ByteRange)"), "clean control: issuer signature verified, DSC date from a real signature");
  await page.screenshot({ path: path.join(shots, "rb05-dce05.png"), fullPage: true });

  const nf = await page.goto(`${BASE}/case/cas_01JD3M5A00000000000000ZZ99/affidavit`);
  check(nf.status() === 404, "unknown case is a 404 page");
  const bad = await page.goto(`${BASE}/case/not-a-case/affidavit`);
  check(bad.status() === 404, "malformed case ID is a 404 page");

  // 360 px and 200 % text: no horizontal page scroll (wide tables scroll inside their own box).
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto(`${BASE}/case/${DIT03}/affidavit`);
  await page.waitForSelector("#diff-flags");
  const overflowMobile = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflowMobile <= 0, `360px width: no horizontal scroll (overflow ${overflowMobile}px)`);
  await page.screenshot({ path: path.join(shots, "rb05-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  const big = await browser.newContext({ viewport: { width: 1280, height: 900 }, bypassCSP: true, storageState: await ctx.storageState() });
  const bigPage = await big.newPage();
  await bigPage.goto(`${BASE}/case/${DIT03}/affidavit`);
  await bigPage.waitForSelector("#diff-flags");
  await bigPage.addStyleTag({ content: "html{font-size:200% !important}" });
  const overflow200 = await bigPage.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflow200 <= 0, `200% text: no horizontal scroll (overflow ${overflow200}px)`);
  await big.close();

  // Hindi.
  await page.goto(`${BASE}/case/${DIT03}/affidavit`);
  await page.getByRole("button", { name: /Account menu/ }).click();
  await page.getByRole("menuitemradio", { name: "हिन्दी" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "hi");
  await page.waitForFunction(() => document.querySelector("h1")?.textContent?.includes("शपथ-पत्र तुलना"), null, { timeout: 15000 }).catch(() => {});
  check((await page.textContent("h1")).includes("शपथ-पत्र तुलना"), "RB-05 in Hindi");
  await page.screenshot({ path: path.join(shots, "rb05-hi.png"), fullPage: true });
  await page.getByRole("button", { name: /खाता मेनू/ }).click();
  await page.getByRole("menuitemradio", { name: "English" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "en");

  // A non-RB account gets 403 "Not assigned to you".
  const ctx2 = await browser.newContext();
  const page2 = await ctx2.newPage();
  await login(page2, "institution.demo03");
  await page2.waitForURL(`${BASE}/home`, { timeout: 20000 }).catch(() => {});
  const res403 = await page2.goto(`${BASE}/case/${DIT03}/affidavit`);
  check(res403.status() === 403 && (await page2.textContent("h1")).includes("Not assigned to you"), "403 for a non-RB user");

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nDIFFVIEW ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
