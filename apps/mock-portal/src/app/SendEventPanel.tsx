"use client";
import { useActionState } from "react";
import { sendEvent, type SendResult } from "./actions";

const LABELS: Record<SendResult["mode"], string> = {
  new: "New event",
  repeat: "Same event sent again",
  tampered: "Same event, tampered signature",
  expired: "Same event, timestamp 10 minutes old",
};

export function SendEventPanel() {
  const [result, action, pending] = useActionState<SendResult | null, FormData>(sendEvent, null);
  const ok = result?.status === 200 || result?.status === 202;
  return (
    <>
      <form action={action} className="actions">
        <button type="submit" name="mode" value="new" disabled={pending}>
          Send test event
        </button>
        <button type="submit" name="mode" value="repeat" disabled={pending || !result}>
          Send the same event again
        </button>
        <button type="submit" name="mode" value="tampered" disabled={pending || !result}>
          Send with a tampered signature
        </button>
        <button type="submit" name="mode" value="expired" disabled={pending || !result}>
          Send with an old timestamp
        </button>
      </form>
      <section aria-live="polite" aria-busy={pending} className="result">
        {pending && <p>Sending…</p>}
        {!pending && result && (
          <>
            <h2>Receipt</h2>
            <p>
              <strong>{LABELS[result.mode]}:</strong>{" "}
              {result.error ?? (
                <>
                  HTTP {result.status} <span className={ok ? "status ok" : "status bad"}>{ok ? "ACCEPTED" : "REJECTED"}</span>
                </>
              )}
            </p>
            <pre data-testid="receipt">{JSON.stringify(result.response, null, 2)}</pre>
            <details>
              <summary>Event body that was signed</summary>
              <pre>{JSON.stringify(JSON.parse(result.body), null, 2)}</pre>
            </details>
          </>
        )}
        {!pending && !result && <p>No event sent yet.</p>}
      </section>
    </>
  );
}
