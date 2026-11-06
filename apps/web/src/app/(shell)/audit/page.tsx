// Audit view: every upload, check run, source response, manual task and disposition in the
// hash-chained ledger, newest first. The chain is recomputed by the gateway on each request.
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import styles from "@/components/demo/Demo.module.css";
import diff from "@/components/diff/DiffView.module.css";
import { ChainBlocks } from "@/components/k/ChainBlocks";
import { Numeral } from "@/components/k/Numeral";
import ak from "@/components/k/Audit.module.css";
import { Icon } from "@/components/ui/Icon";
import { SourceTag } from "@/components/ui/SourceTag";
import { audit } from "@/lib/demo";
import { requireSession } from "@/lib/session";
import { forbidden } from "next/navigation";
import { Note } from "@/components/ui/Note";

type Props = { searchParams: Promise<{ case?: string }> };

type DemoT = Awaited<ReturnType<typeof getTranslations<"demo">>>;

/** A plain label for a ledger event kind; a kind without a label reads "Other event". */
function eventLabel(t: DemoT, kind: string): string {
  const key = `audit.event.${kind.replace(/\./g, "_")}`;
  return t.has(key as never) ? t(key as never) : t("audit.event.unknown");
}

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("demo");
  return { title: t("audit.title"), description: t("audit.description") };
}

export default async function AuditPage({ searchParams }: Props) {
  const { case: caseId } = await searchParams;
  const session = await requireSession("/audit");
  if (!session.user.roles.some((r) => r === "RB" || r === "AU")) forbidden();
  const data = await audit("/audit", caseId);
  const t = await getTranslations("demo");
  const tk = await getTranslations("k.audit");
  const locale = await getLocale();
  const fmt = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "medium" });
  return (
    <>
      <header className={ak.head}>
        <Numeral value={data.chain.rows} caption={tk("countCaption")} />
        <div>
          <h1 className="k-h1">{tk("headline", { count: data.chain.rows })}</h1>
          <p className={ak.state} data-state={data.chain.ok ? "intact" : "broken"}>
            <Icon name={data.chain.ok ? "circle-check" : "circle-x"} size={20} />
            {data.chain.ok ? tk("intact") : tk("broken", { entry: data.chain.broken_at ?? 0 })}
          </p>
          <div className={ak.actions}>
            <Link className="k-btn k-btn-2" href={caseId ? `/audit?case=${caseId}` : "/audit"}>
              {tk("verifyAgain")}
            </Link>
          </div>
          <div className={ak.links}>
            <Link href="/audit/replay">{tk("replayLink")}</Link>
            <Link href="/audit/integrity">{tk("integrityLink")}</Link>
          </div>
        </div>
      </header>
      <Note>{t("audit.intro")}</Note>
      <div className={styles.chain} data-ok={data.chain.ok} role="status">
        {data.chain.ok
          ? t("audit.chainOk", { rows: data.chain.rows })
          : t("audit.chainBroken", { seq: data.chain.broken_at ?? 0, reason: data.chain.reason ?? "" })}
        <p className={diff.note}>{t("audit.method")} {fmt.format(new Date(data.chain.recomputed_at))}</p>
      </div>
      <h2 className={ak.sectionTitle}>{tk("blocksHeading")}</h2>
      <ChainBlocks entries={data.entries} eventLabel={(kind) => eventLabel(t, kind)} />
      <h2 className={ak.sectionTitle}>{tk("tableHeading")}</h2>
      {caseId ? (
        <p>
          {t("audit.filtered")} <Link href="/audit">{t("audit.showAll")}</Link>
        </p>
      ) : null}
      {data.entries.length === 0 ? (
        <p>{t("audit.empty")}</p>
      ) : (
        <div className={diff.tableWrap}>
          <table className={diff.table}>
            <thead>
              <tr>
                <th scope="col">{t("audit.colNo")}</th>
                <th scope="col">{t("audit.colTime")}</th>
                <th scope="col">{t("audit.colEvent")}</th>
                <th scope="col">{t("audit.colCase")}</th>
                <th scope="col">{t("audit.colHash")}</th>
                <th scope="col">{t("audit.colDetails")}</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((e) => (
                <tr key={e.seq}>
                  <td className={diff.num}>{e.seq}</td>
                  <td>{fmt.format(new Date(e.at))}</td>
                  <td>
                    {eventLabel(t, e.event_type)}
                    {e.event_type === "source.response" ? (
                      <>
                        {" "}
                        <SourceTag kind="simulated" />
                      </>
                    ) : null}
                  </td>
                  <td>{e.case_id ? <Link href={`/case/${e.case_id}`}>{e.case_id.slice(-4)}</Link> : t("audit.none")}</td>
                  <td className={styles.mono}>{e.hash.slice(0, 16)}</td>
                  <td>
                    <details>
                      <summary>{t("audit.open", { no: e.seq })}</summary>
                      <p className={diff.note}>{t("audit.actor", { actor: e.actor ?? t("audit.none") })}</p>
                      <p className={styles.mono}>{t("audit.payload", { hash: e.payload_sha256 })}</p>
                      <p className={styles.mono}>{t("audit.fullHash", { hash: e.hash })}</p>
                      <pre className={styles.pre}>{e.detail ? JSON.stringify(e.detail, null, 2) : t("audit.noDetail")}</pre>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
