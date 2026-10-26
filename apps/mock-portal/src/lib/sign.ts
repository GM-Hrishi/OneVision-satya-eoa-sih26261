// X-SATYA-Signature (Portal spec §2.2): t=<unix>,kid=<key-id>,v1=<hex HMAC-SHA256 of "t.body">.
// Runs on the server only; the secret never reaches the browser.
import { createHmac } from "node:crypto";

export function signatureHeader(body: string, secret: string, kid: string, unixSeconds: number): string {
  const mac = createHmac("sha256", secret).update(`${unixSeconds}.`).update(body).digest("hex");
  return `t=${unixSeconds},kid=${kid},v1=${mac}`;
}
