// Slice A acceptance in a real browser on default settings (B-28 scan fallback, B-31 UI fixes).
// Uploads a scan (the committed synthetic scan of case dit13) into a clean case, checks the label,
// the reason sentence and the Overview manual-task count, the queue filter select (mouse and
// keyboard), the header name, the footer date and the noindex meta. Run `make demo-reset` first.
// With the real OCR engine in the image the sentence says "read by OCR"; without it, "not available".
// Usage: node tests/e2e/ocr-scan.cjs   (needs `make up`)
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
const DCE05 = "cas_01JD3M5A00000000000000CE05";
const DT13 = "cas_01JD3M5A00000000000000DT13";
const DCE15 = "cas_01JD3M5A00000000000000CE15";
const SCAN = path.join(root, "data/synthetic/cases/dit13-2026-27/affidavit-sworn.pdf");
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
  await page.waitForSelector("#ov-tasks", { timeout: 30000 });

  // B-31: header name, footer date, noindex
  const header = await page.textContent("header");
  check(header.includes("RB Officer 01") && !/demo/i.test(header), "header shows RB Officer 01 and no 'demo'");
  check(/Updated \d{1,2} [A-Z][a-z]{2,4} \d{4}/.test(await page.textContent("footer")), "footer date reads like 27 Oct 2026");
  check(/noindex/.test((await page.getAttribute('meta[name="robots"]', "content")) || ""), "noindex meta on Overview");
  // Through the browser: Node's own HTTP client does not trust the local Caddy CA.
  await page.goto(`${BASE}/robots.txt`);
  check(/Disallow: \//.test(await page.textContent("body")), "robots.txt disallows everything");
  await page.goto(`${BASE}/overview`);
  await page.waitForSelector("#ov-tasks", { timeout: 30000 });

  const openTasks = async () => {
    await page.goto(`${BASE}/overview`);
    await page.waitForSelector("#ov-tasks", { timeout: 30000 });
    const text = await page.locator("section[aria-labelledby=ov-tasks]").textContent();
    return Number((text.match(/(\d+) open task/) || [0, 0])[1]);
  };
  const before = await openTasks();

  // B-31: queue filter select, mouse and keyboard
  await page.goto(`${BASE}/rb-queue`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  check((await page.locator("tbody tr").count()) === 8, "queue lists the 8 seeded cases (5 + 3 scans)");
  const band = page.getByTestId("filter-band-button");
  check((await band.boundingBox()).height === 34, "filter select is 34px high");
  await band.click();
  await page.getByRole("option", { name: /^High/ }).click();
  await page.getByRole("button", { name: "Apply" }).click();
  await page.waitForURL(/band=high/);
  check((await page.locator("tbody tr").count()) === 2, "mouse: High filter shows 2 cases");
  const status = page.getByTestId("filter-status-button");
  // CI diagnostics showed focus falling back to BODY: the page re-renders once after the filter
  // submit and replaces the button. So focus again on every try, then press Enter, until the list
  // is open (the assertions below are unchanged).
  for (let i = 0; i < 8 && !(await page.getByRole("listbox").isVisible()); i++) {
    await status.focus();
    await page.keyboard.press("Enter");
    await page.waitForTimeout(400);
  }
  const opened = await page.getByRole("listbox").isVisible();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  const chosen = !(await status.textContent()).startsWith("All");
  if (!chosen) {
    const diag = await page.evaluate(() => {
      const a = document.activeElement;
      return { active: a ? `${a.tagName}[${a.getAttribute("data-testid") || a.getAttribute("role") || ""}]` : null, listboxes: document.querySelectorAll('[role="listbox"]').length };
    });
    console.log(`DIAG keyboard select: listOpenedByEnter=${opened} expanded=${await status.getAttribute("aria-expanded")} text="${(await status.textContent()).trim()}" ${JSON.stringify(diag)}`);
  }
  check(chosen, "keyboard: the select opens, moves and chooses");

  // B-28: the seeded scan cases carry a reason
  await page.goto(`${BASE}/case/${DT13}`);
  await page.waitForSelector("#flags", { timeout: 30000 });
  const scanText = await page.textContent("main");
  check(/This file is a scan/.test(scanText), "seeded scan case shows the reason sentence");
  check(/Scanned page|scanned page/.test(scanText), "seeded scan case shows a line per scanned page");
  await page.screenshot({ path: path.join(shots, "ocr-scan-case.png"), fullPage: true });
  await page.goto(`${BASE}/case/${DCE15}`);
  await page.waitForSelector("#flags", { timeout: 30000 });
  check(/This file is a scan/.test(await page.textContent("main")), "noisy scan case shows the reason sentence");

  // B-43: the affidavit diff of a scan says it was not compared, never that it matches
  for (const id of [DT13, DCE15]) {
    await page.goto(`${BASE}/case/${id}/affidavit`);
    await page.waitForSelector("#diff-notcompared", { timeout: 30000 });
    const diffText = await page.textContent("main");
    check(!/matches the portal draft/i.test(diffText) && !/No declaration differs/.test(diffText), `scan case ${id.slice(-4)}: the diff never says matches`);
    check(/Scan, /.test(diffText) && !/M3|P-2/.test(diffText), `scan case ${id.slice(-4)}: the text source names the scan and no build code shows`);
  }

  // B-28: upload a scan into a clean case
  await page.goto(`${BASE}/case/${DCE05}/upload`);
  const form = page.locator("section[aria-labelledby=up-file] form");
  await form.locator("select[name=slot]").selectOption("affidavit");
  await form.locator("input[type=file]").setInputFiles(SCAN);
  await form.locator("button[type=submit]").click();
  await page.waitForSelector("text=Stored and checked", { timeout: 120000 });
  await page.goto(`${BASE}/case/${DCE05}`);
  await page.waitForSelector("#flags", { timeout: 30000 });
  const text = await page.textContent("main");
  check(/Manual review required/i.test(text), "the uploaded scan is labelled Manual review required");
  check(/This file is a scan/.test(text), "the fixed reason sentence is shown");
  const labelRow = await page.locator("tbody tr", { hasText: "Affidavit 2" }).first().textContent();
  check(!/Verified/.test(labelRow.split("Audited")[0]), "OCR never gives the scanned affidavit the Verified label");
  check(!(await page.locator("main button").allTextContents()).some((b) => /approve|reject/i.test(b)), "no approve or reject control");
  await page.screenshot({ path: path.join(shots, "ocr-scan-upload.png"), fullPage: true });
  const after = await openTasks();
  check(after === before + 1, `Overview manual tasks went from ${before} to ${after}`);

  // damaged file: refused by content check or stored as unreadable, never an error page
  await page.goto(`${BASE}/case/${DCE05}/upload`);
  await form.locator("input[type=file]").setInputFiles({ name: "broken.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.7\njunk junk\n%%EOF") });
  await form.locator("button[type=submit]").click();
  await page.waitForSelector("text=Stored and checked", { timeout: 60000 });
  await page.goto(`${BASE}/case/${DCE05}`);
  await page.waitForSelector("#flags", { timeout: 30000 });
  check(/This file is damaged/.test(await page.textContent("main")), "a damaged PDF lands on manual review with its reason");

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `${failures} check(s) failed` : "all checks passed; run `make demo-reset` to restore the demo state");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
