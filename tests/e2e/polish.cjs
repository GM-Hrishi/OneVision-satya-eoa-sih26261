// v0.8 UI polish acceptance in a real browser on default settings: sortable queue headers (cycle,
// aria-sort, live announcement, Reset sort), Overview links landing on a filtered queue, status
// label tooltips, user menu keyboard behaviour (Escape returns focus), severity alert cards.
// Run `make demo-reset` first. Usage: node tests/e2e/polish.cjs   (needs `make up`)
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

  // Overview links land on a pre-filtered queue.
  await page.waitForSelector("#ov-bands", { timeout: 30000 });
  await page.getByRole("link", { name: /^High/ }).first().click();
  await page.waitForURL(`${BASE}/rb-queue?band=high`, { timeout: 20000 });
  await page.waitForSelector("#case-list", { timeout: 30000 });
  check((await page.locator("tbody tr").count()) === 2, "Overview band link opens the queue filtered to High (2 cases)");
  await page.goto(`${BASE}/rb-queue?label=manual_review_required&status=not_started`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  check((await page.locator("tbody tr").count()) >= 1, "label and status filters from the URL apply");
  await page.goto(`${BASE}/rb-queue?band=nonsense&sort=drop;table&dir=sideways`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  check((await page.locator("tbody tr").count()) === 8, "unknown filter and sort values are ignored");

  // Sortable headers: plain text plus indicator, cycle ascending, descending, ascending.
  await page.goto(`${BASE}/rb-queue`);
  await page.waitForSelector("#case-list", { timeout: 30000 });
  const sortable = await page.locator("th[aria-sort], th[data-allows-sorting]").allTextContents();
  check(["Application", "Awaiting", "Submitted", "Last activity"].every((n) => sortable.some((t) => t.trim() === n)), "Application, Awaiting, Submitted and Last activity are sortable");
  check(!(await page.locator("thead").textContent()).match(/ascending|descending/i), "no visible direction word in the headers");
  const submitted = page.getByRole("columnheader", { name: "Submitted" });
  const live = page.locator('[role="status"][aria-live="polite"]').last();
  await submitted.click();
  await page.waitForURL(/sort=submitted_at&dir=asc/, { timeout: 15000 });
  check((await submitted.getAttribute("aria-sort")) === "ascending", "first press sorts ascending (aria-sort)");
  check((await live.textContent()).includes("Sorted by Submitted, ascending"), "polite announcement: Sorted by Submitted, ascending");
  await submitted.click();
  await page.waitForURL(/sort=submitted_at&dir=desc/, { timeout: 15000 });
  check((await submitted.getAttribute("aria-sort")) === "descending", "second press sorts descending");
  await submitted.click();
  await page.waitForURL(/sort=submitted_at&dir=asc/, { timeout: 15000 });
  check((await submitted.getAttribute("aria-sort")) === "ascending", "third press is ascending again");
  const bands = await page.locator("tbody tr td:first-child").allTextContents();
  const rank = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const order = bands.map((b) => rank[b.trim().toUpperCase()]);
  check(order.every((v, i) => i === 0 || v >= order[i - 1]), "sort applies inside risk band groups (bands stay High, Medium, Low)");
  // Keyboard: focus a header and press Enter.
  await page.getByRole("columnheader", { name: "Application" }).focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(/sort=application_id&dir=asc/, { timeout: 15000 });
  check(true, "a sortable header works from the keyboard");
  await page.screenshot({ path: path.join(shots, "polish-queue-sorted.png"), fullPage: true });
  await page.getByRole("link", { name: "Reset sort" }).click();
  await page.waitForURL(`${BASE}/rb-queue`, { timeout: 15000 });
  check(!(await page.locator('th[aria-sort="ascending"], th[aria-sort="descending"]').count()), "Reset sort clears the active sort");

  // Status label tooltip: the full name opens on hover and on keyboard focus.
  const pill = page.locator("tbody [tabindex='0']").first();
  await pill.hover();
  await page.waitForSelector('[role="tooltip"]', { timeout: 5000 }).catch(() => {});
  const full = /Manual review required|Source unavailable|Verified|Expired|Mismatch detected|Verification pending/;
  const tipHover = await page.locator('[role="tooltip"]').first().textContent().catch(() => "");
  check(full.test(tipHover), `status label tooltip shows the full name on hover ("${tipHover}")`);
  await page.mouse.move(0, 0);
  // The table is one tab stop; arrow keys move between cells (down to the row, right to the labels).
  await page.getByRole("columnheader", { name: "Application" }).focus();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowRight");
  await page.waitForSelector('[role="tooltip"]', { timeout: 5000 }).catch(() => {});
  const tipFocus = await page.locator('[role="tooltip"]').first().textContent().catch(() => "");
  check(full.test(tipFocus), `status label tooltip shows the full name on keyboard focus ("${tipFocus}")`);

  // User menu: Escape closes and returns focus to the trigger.
  const trigger = page.getByRole("button", { name: /Account menu/ });
  await trigger.focus();
  await page.keyboard.press("Enter");
  check(await page.getByRole("menuitem", { name: "Sign out" }).isVisible(), "user menu opens with Sign out");
  check(await page.getByRole("menuitem", { name: "Accessibility settings" }).isVisible(), "user menu offers Accessibility settings");
  await page.keyboard.press("Escape");
  // React Aria restores focus after the popover has unmounted, so wait for it instead of reading once.
  const restored = await page
    .waitForFunction(() => (document.activeElement?.getAttribute("aria-label") || "").startsWith("Account menu"), null, { timeout: 5000 })
    .then(() => true, () => false);
  check(restored && !(await page.getByRole("menuitem", { name: "Sign out" }).isVisible()), "Escape closes the menu and focus returns to the trigger");
  check((await page.getByRole("link", { name: "Sign out" }).count()) === 0, "no standalone sign-out link");

  // Alert cards: whole-card tint with a full border and no side stripe.
  await page.goto(`${BASE}/alerts`);
  await page.waitForSelector("article", { timeout: 20000 });
  const card = await page.locator("article").first().evaluate((el) => {
    const s = getComputedStyle(el);
    return { l: s.borderLeftWidth, t: s.borderTopWidth, c: s.borderLeftColor === s.borderTopColor, r: s.borderRadius };
  });
  check(card.l === "1px" && card.t === "1px" && card.c && card.r === "6px", "alert card has a full 1px border and 6px radius (no side stripe)");
  const first = await page.locator("main article").first().textContent();
  check(/(High|Medium|Low) severity/.test(first) && /unread/.test(first), `alert first line names the severity and says unread ("${first.slice(0, 90)}")`);
  await page.getByRole("link", { name: /Open flag|Open document/ }).first().click();
  await page.waitForURL(/\/case\/cas_/, { timeout: 20000 });
  await page.goto(`${BASE}/alerts`);
  check((await page.locator("h2").allTextContents()).some((t) => t.startsWith("Earlier")), "opening an alert moves it out of the unread group");

  // Footer is one short line of links plus the advisory text; no disclaimer paragraph.
  const footer = await page.locator("footer").textContent();
  check(footer.includes("Website policies") && footer.includes("Findings are advisory. Decisions rest with AICTE officials."), "one-line footer text");

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nPOLISH ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
