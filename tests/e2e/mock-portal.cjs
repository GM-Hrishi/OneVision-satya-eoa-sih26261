// Acceptance 4 + 5 (slice 0) through the mock portal UI in a real browser:
// banner and title, no AICTE branding; Send test event -> 202 receipt; same event again -> 200
// duplicate:true; tampered signature -> 401 SIGNATURE_INVALID; old timestamp -> 401 SIGNATURE_EXPIRED.
// Then run `make ledger-verify`. Usage: node tests/e2e/mock-portal.cjs   (needs `make up`)
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const shots = process.env.SHOTS_DIR || path.join(__dirname, "../../.logs/screens");
fs.mkdirSync(shots, { recursive: true });
let failures = 0;
const check = (ok, msg) => { console.log(`${ok ? "PASS" : "FAIL"} ${msg}`); if (!ok) failures++; };

(async () => {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto("https://portal.localhost/");
  check((await page.title()).includes("Approval Portal (Mock, for demo)"), "title names the mock portal");
  const text = await page.textContent("body");
  check(text.includes("Demo stand-in. Not an AICTE system. Synthetic data only."), "demo stand-in banner shown");
  check((await page.locator("img").count()) === 0, "no images, so no logo or emblem");
  check(!/aicte\.(gov|org)|aicte-india/i.test(await page.content()), "no AICTE URL in the page");

  async function send(name) {
    await page.getByRole("button", { name }).click();
    await page.waitForFunction(() => document.querySelector('[data-testid="receipt"]') && !document.querySelector('[aria-busy="true"]'));
    const status = Number((await page.textContent(".result")).match(/HTTP (\d{3})/)?.[1]);
    const body = JSON.parse(await page.textContent('[data-testid="receipt"]'));
    return { status, body };
  }
  const first = await send("Send test event");
  check(first.status === 202 && first.body.duplicate === false && /^rcp_/.test(first.body.receipt_id), `new event -> 202 receipt ${first.body.receipt_id}`);
  await page.screenshot({ path: path.join(shots, "mock-portal-202.png"), fullPage: true });
  const again = await send("Send the same event again");
  check(again.status === 200 && again.body.duplicate === true && again.body.receipt_id === first.body.receipt_id, "same event again -> 200 duplicate:true, same receipt");
  const tampered = await send("Send with a tampered signature");
  check(tampered.status === 401 && tampered.body.code === "SIGNATURE_INVALID", "tampered signature -> 401 SIGNATURE_INVALID");
  const expired = await send("Send with an old timestamp");
  check(expired.status === 401 && expired.body.code === "SIGNATURE_EXPIRED", "old timestamp -> 401 SIGNATURE_EXPIRED");
  await page.screenshot({ path: path.join(shots, "mock-portal-expired.png"), fullPage: true });
  check(errors.length === 0, `no console errors${errors.length ? ": " + errors.join(" | ") : ""}`);
  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : "\nMOCK PORTAL ACCEPTANCE OK");
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
