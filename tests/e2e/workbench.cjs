// Acceptance 3 (slice 0) in a real browser on default settings: HTTPS without warnings (Caddy's
// local CA trusted once, see docs/DEV-SETUP.md), redirect to Keycloak, sign in as rb.southern.demo,
// RB shell, Overview landing page, validation queue (slice 1: the demo cases). Also: titles, one H1, no console errors, 403, 404, Hindi, mobile
// width, 200% text, sign-out. Usage: node tests/e2e/workbench.cjs   (needs `make up`)
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

async function login(page, username) {
  await page.goto(`${BASE}/`);
  await page.waitForURL(/auth\.localhost/, { timeout: 20000 });
  await page.fill("#username", username);
  await page.fill("#password", env.DEMO_USER_PASSWORD);
  await page.click("#kc-login");
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${page.url()}: ${m.text()}`); });
  page.on("pageerror", (e) => consoleErrors.push(`${page.url()}: ${e.message}`));

  await login(page, "rb.southern.demo");
  await page.waitForURL(`${BASE}/overview`, { timeout: 20000 });
  check(page.url() === `${BASE}/overview`, "signed in as rb.southern.demo lands on /overview");
  // The Overview streams a skeleton (loading.tsx) while it calls the API; wait for its first panel.
  await page.waitForSelector("#ov-bands", { timeout: 30000 }).catch(() => {});
  const overviewBody = await page.textContent("body");
  check(overviewBody.includes("Cases by risk band") && overviewBody.includes("Open validation queue"), "Overview shows its panels and the queue button");
  const overviewCurrent = await page.getAttribute('nav[aria-label="Main navigation"] [aria-current="page"]', "href");
  check(overviewCurrent === "/overview", "rail marks Overview as current page");
  await page.screenshot({ path: path.join(shots, "overview.png"), fullPage: true });
  await page.getByRole("link", { name: "Open validation queue" }).click();
  await page.waitForURL(`${BASE}/rb-queue`, { timeout: 20000 });
  await page.waitForSelector("#case-list", { timeout: 30000 }).catch(() => {});
  const body = await page.textContent("body");
  // Slice 1: the gateway serves the synthetic demo cases, so the queue lists them (the empty state
  // shows only when the gateway holds no case for the region).
  check(body.includes("Cases for review") && body.includes("1-90000004217"), "queue lists the synthetic demo cases");
  check(!/prototype/i.test(body), "no prototype wording in the workbench");
  check(body.includes("Regulation Bureau · Southern region") && body.includes("AY 2026-27"), "header shows plain role, region and AY text");
  check(await page.getByRole("button", { name: /Account menu/ }).isVisible(), "user menu is in the header");
  const current = await page.getAttribute('nav[aria-label="Main navigation"] [aria-current="page"]', "href");
  check(current === "/rb-queue", "rail marks Validation queue as current page");
  await page.screenshot({ path: path.join(shots, "rb-queue.png"), fullPage: true });

  const titles = new Map();
  for (const p of ["/overview", "/rb-queue", "/alerts", "/audit", "/help", "/accessibility", "/about", "/policies", "/sitemap"]) {
    const res = await page.goto(`${BASE}${p}`);
    const title = await page.title();
    const h1 = await page.locator("h1").count();
    const desc = await page.getAttribute('meta[name="description"]', "content");
    check(res.status() === 200 && h1 === 1 && !!desc, `${p}: 200, one H1, meta description ("${title}")`);
    titles.set(title, (titles.get(title) || 0) + 1);
    const footerOk = await page.locator('footer a[href="/accessibility"]').count();
    check(footerOk === 1, `${p}: GIGW footer links present`);
  }
  check([...titles.values()].every((n) => n === 1), "page titles are unique");

  const nf = await page.goto(`${BASE}/no-such-page`);
  check(nf.status() === 404 && (await page.textContent("h1")).includes("Page not found"), "custom 404 page");

  // Skip link is the first focusable element.
  await page.goto(`${BASE}/help`);
  await page.keyboard.press("Tab");
  check((await page.evaluate(() => document.activeElement?.textContent)) === "Skip to main content", "skip link first in tab order");

  // 200% text without horizontal scroll. All sizes are rem, so a 200% root font size is what the
  // browser's text-size setting does. This context bypasses our CSP only to inject that one rule.
  const big = await browser.newContext({ viewport: { width: 1280, height: 900 }, bypassCSP: true, storageState: await ctx.storageState() });
  const bigPage = await big.newPage();
  await bigPage.goto(`${BASE}/rb-queue`);
  await bigPage.addStyleTag({ content: "html{font-size:200% !important}" });
  const rootPx = await bigPage.evaluate(() => getComputedStyle(document.documentElement).fontSize);
  const overflow200 = await bigPage.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(rootPx === "32px" && overflow200 <= 0, `200% text (root ${rootPx}): no horizontal scroll (overflow ${overflow200}px)`);
  await bigPage.screenshot({ path: path.join(shots, "rb-queue-200pct.png"), fullPage: true });
  await big.close();

  // Mobile width.
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto(`${BASE}/rb-queue`);
  const overflowMobile = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflowMobile <= 0, `360px width: no horizontal scroll (overflow ${overflowMobile}px)`);
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  check(await page.getByRole("dialog").getByRole("link", { name: "Validation queue" }).isVisible(), "mobile menu opens with rail items");
  await page.keyboard.press("Escape");
  await page.screenshot({ path: path.join(shots, "rb-queue-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1366, height: 900 });

  // Hindi.
  await page.goto(`${BASE}/rb-queue`);
  await page.getByRole("button", { name: /Account menu/ }).click();
  await page.getByRole("menuitemradio", { name: "हिन्दी" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "hi");
  await page.waitForFunction(() => document.querySelector("h1")?.textContent?.includes("सत्यापन कतार"), null, { timeout: 15000 }).catch(() => {});
  check((await page.textContent("h1")).includes("सत्यापन कतार"), "switches to Hindi (lang=hi)");
  await page.screenshot({ path: path.join(shots, "rb-queue-hi.png"), fullPage: true });
  await page.getByRole("button", { name: /खाता मेनू/ }).click();
  await page.getByRole("menuitemradio", { name: "English" }).click();
  await page.waitForFunction(() => document.documentElement.lang === "en");

  // Sign out goes through Keycloak and ends signed out.
  await page.getByRole("button", { name: /Account menu/ }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await page.waitForURL(/localhost\/(signin|$)|auth\.localhost/, { timeout: 20000 });
  await page.goto(`${BASE}/rb-queue`);
  await page.waitForURL(/auth\.localhost/, { timeout: 20000 });
  check(page.url().includes("auth.localhost"), "after sign-out the queue requires sign-in again");

  // Institution user gets 403 "Not assigned to you".
  const ctx2 = await browser.newContext();
  const page2 = await ctx2.newPage();
  page2.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${page2.url()}: ${m.text()}`); });
  await login(page2, "institution.demo03");
  await page2.waitForURL(`${BASE}/home`, { timeout: 20000 }).catch(() => {});
  const res403 = await page2.goto(`${BASE}/rb-queue`);
  check(res403.status() === 403 && (await page2.textContent("h1")).includes("Not assigned to you"), "403 Not assigned to you for a non-RB user");
  await page2.screenshot({ path: path.join(shots, "forbidden.png"), fullPage: true });

  const relevant = consoleErrors.filter((e) => !e.includes("status of 403") && !e.includes("status of 404"));
  check(relevant.length === 0, `no console errors${relevant.length ? ": " + relevant.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nWORKBENCH ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
