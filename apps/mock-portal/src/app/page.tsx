import type { Metadata } from "next";
import { SendEventPanel } from "./SendEventPanel";

export const metadata: Metadata = {
  title: "Send test event · Approval Portal (Mock, for demo)",
  description: "Send a signed, synthetic application.precheck_requested event to the SATYA gateway.",
};

export default function Home() {
  return (
    <>
      <h1>Send test event</h1>
      <p>
        Builds a synthetic <code>application.precheck_requested</code> event for application{" "}
        <code>1-90000004217</code> (Demo Institute of Technology 03, AY 2026-27, Southern), signs it with
        HMAC-SHA256 on the server and posts it to the SATYA gateway. This proves the signed-webhook path
        end to end (Portal spec §2.2–§2.4).
      </p>
      <SendEventPanel />
    </>
  );
}
