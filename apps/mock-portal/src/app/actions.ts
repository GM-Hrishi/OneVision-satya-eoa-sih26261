"use server";
// Sends a signed event to the SATYA gateway and returns what came back, for display.
import { signatureHeader } from "@/lib/sign";
import { precheckEnvelope } from "@/lib/envelope";

export type Mode = "new" | "repeat" | "tampered" | "expired";

export interface SendResult {
  mode: Mode;
  status: number | null;
  response: unknown;
  body: string; // the exact envelope bytes that were signed, kept for "send the same event again"
  error?: string;
}

const MODES: Mode[] = ["new", "repeat", "tampered", "expired"];

export async function sendEvent(previous: SendResult | null, formData: FormData): Promise<SendResult> {
  const requested = String(formData.get("mode"));
  const mode: Mode = (MODES as string[]).includes(requested) ? (requested as Mode) : "new";
  const kid = process.env.PORTAL_HMAC_KID ?? "";
  const secret = process.env.PORTAL_HMAC_SECRET ?? "";
  const api = process.env.SATYA_API_INTERNAL_URL ?? "http://api:8000";
  // Re-use the previous event only for the repeat/tamper/expired demos; otherwise build a new one.
  const body = mode !== "new" && previous?.body ? previous.body : JSON.stringify(precheckEnvelope());
  const now = Math.floor(Date.now() / 1000);
  let header = signatureHeader(body, secret, kid, mode === "expired" ? now - 600 : now);
  if (mode === "tampered") header = header.slice(0, -4) + (header.endsWith("0000") ? "ffff" : "0000");
  try {
    const res = await fetch(`${api}/v1/portal-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-SATYA-Signature": header },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    const text = await res.text();
    let response: unknown = text;
    try {
      response = JSON.parse(text);
    } catch {
      // keep text
    }
    return { mode, status: res.status, response, body };
  } catch {
    return { mode, status: null, response: null, body, error: "The SATYA gateway could not be reached." };
  }
}
