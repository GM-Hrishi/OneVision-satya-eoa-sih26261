// Replay check (VISUAL 5): runs the original rule pack again on the stored documents and compares digests.
// The endpoint is on the backend branch only (NOT ON MAIN UNTIL PR #15 MERGES); until then this page says so.
import type { Metadata } from "next";
import Link from "next/link";
import { forbidden } from "next/navigation";
import { getTranslations } from "next-intl/server";
import ak from "@/components/k/Audit.module.css";
import { ReplayDiff } from "@/components/k/ReplayDiff";
import { apiGetOptional } from "@/lib/api";
import { fromReplayCheck, type ReplayVM } from "@/lib/api/k-adapters/replay";
import { replayCheck } from "@/lib/api/pending-endpoints";
import okFixture from "@/lib/api/__fixtures__/replay-check.ok.json";
import { queue } from "@/lib/demo";
import { uiFixtures } from "@/lib/fixtures";
import { requireSession } from "@/lib/session";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;
type Props = { searchParams: Promise<{ case?: string; fixture?: string }> };

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("k.replay");
  return { title: t("pickHeading"), description: t("intro") };
}

export default async function ReplayPage({ searchParams }: Props) {
  const { case: caseId, fixture } = await searchParams;
  const session = await requireSession("/audit/replay");
  if (!session.user.roles.some((r) => r === "RB" || r === "AU")) forbidden();
  const t = await getTranslations("k.replay");

  if (!caseId || !CASE_ID.test(caseId)) {
    const rows = session.user.roles.includes("RB") ? (await queue("/audit/replay")).items : [];
    return (
      <>
        <h1 className="k-h1">{t("pickHeading")}</h1>
        <p className={ak.note}>{t("intro")}</p>
        {rows.length === 0 ? (
          <p>{t("pickEmpty")}</p>
        ) : (
          <ul>
            {rows.map((r) => (
              <li key={r.case_id}>
                <Link href={`/audit/replay?case=${r.case_id}`}>{t("pickCase", { id: r.application_id })}</Link>
              </li>
            ))}
          </ul>
        )}
      </>
    );
  }

  // Dev fixtures only: show the documented example, or the same example with one digest changed (a failed replay).
  let vm: ReplayVM | null = null;
  let status: "ok" | "unavailable" | "forbidden" | "error" = "unavailable";
  let fixtureNote = false;
  if (uiFixtures() && (fixture === "ok" || fixture === "failed")) {
    const body = fixture === "failed" ? { ...okFixture, digest_replayed: "0".repeat(64), reproduced_identically: false } : okFixture;
    vm = fromReplayCheck(body);
    status = vm ? "ok" : "error";
    fixtureNote = fixture === "failed";
  } else {
    const answer = await apiGetOptional<unknown>(replayCheck(caseId), `/audit/replay?case=${caseId}`);
    status = answer.status;
    if (answer.status === "ok") {
      vm = fromReplayCheck(answer.data);
      if (!vm) status = "unavailable";
    }
  }
  return (
    <>
      {vm ? null : <h1 className="k-h1">{t("pickHeading")}</h1>}
      {vm ? (
        <ReplayDiff vm={vm} caseId={caseId} fixtureNote={fixtureNote} />
      ) : (
        <p role="status">{status === "forbidden" ? t("forbidden") : status === "error" ? t("error") : t("unavailable")}</p>
      )}
      <div className={ak.actions}>
        <Link className="k-btn k-btn-2" href={`/audit/replay?case=${caseId}`}>
          {t("retry")}
        </Link>
      </div>
    </>
  );
}
