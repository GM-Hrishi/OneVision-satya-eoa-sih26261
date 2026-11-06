// RB-01 Overview: where the Regulation Bureau lands after sign-in. Equal plain panels, no charts and
// no KPI cards. Every count links to the queue (or the audit trail) already filtered. Advisory
// only: nothing here approves, rejects or clears anything.
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { RiskBand } from "@/components/demo/RiskBand";
import styles from "@/components/overview/Overview.module.css";
import { Numeral } from "@/components/k/Numeral";
import { buildCaseView } from "@/lib/api/k-adapters/case";
import { longestWait, rowSentence, waitingDays, waitingRows, worstLabel } from "@/lib/api/k-adapters/queue";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { caseReview, overview, queue } from "@/lib/demo";
import { BANDS, STATUSES } from "@/lib/demo-types";
import { LABEL_ORDER } from "@/lib/labels";
import { requireRole } from "@/lib/session";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("overview");
  return { title: t("title"), description: t("description") };
}

const AY = "2026-27";

export default async function OverviewPage() {
  await requireRole("RB", "/overview");
  const [t, tq, tr, tk, locale, data, q] = await Promise.all([
    getTranslations("overview"),
    getTranslations("demo"),
    getTranslations("regions"),
    getTranslations("k.overview"),
    getLocale(),
    overview("/overview", AY),
    queue("/overview"),
  ]);
  const waiting = waitingRows(q.items);
  const top = waiting[0] ?? null;
  const topFinding = top ? buildCaseView(await caseReview(top.case_id, "/overview")).findings[0] : undefined;
  const longest = longestWait(waiting, data.as_of);
  const intl = locale === "hi" ? "hi-IN" : "en-IN";
  const asOf = new Intl.DateTimeFormat(intl, { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" }).format(new Date(data.as_of));
  const when = new Intl.DateTimeFormat(intl, { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" });
  const region = data.region === "southern" || data.region === "national" ? tr(data.region) : tr("none");
  const answering = data.sources.filter((s) => s.status === "answering").length;
  const simulated = data.sources.filter((s) => s.mode === "mock");
  const reason = (code: string) => (t.has(`reason.${code}` as never) ? t(`reason.${code}` as never) : code);
  return (
    <>
      <header>
        <h1>{tk("headline", { waiting: waiting.length, high: data.cases.by_band.high })}</h1>
        <p className={styles.context}>{t("context", { ay: data.ay, region, asOf })}</p>
      </header>

      <ul className={styles.numerals} aria-label={tk("numeralsLabel")}>
        <li>
          <Numeral value={waiting.length} caption={tk("waiting")} />
        </li>
        <li>
          <Numeral value={data.cases.by_band.high} caption={tk("high")} tone="red" />
        </li>
        <li>
          <Numeral value={data.manual_tasks.open} caption={tk("manual")} tone="ink" />
        </li>
        <li>
          <Numeral value={longest ?? tk("longestNone")} caption={tk("longest")} tone="ink" />
        </li>
      </ul>

      <section className={styles.start} aria-labelledby="ov-start">
        <div>
          <h2 id="ov-start" className="k-label">
            {tk("startHeading")}
          </h2>
          {top ? (
            <>
              <p className="k-label">
                <span className="k-mono">{top.application_id}</span> <RiskBand band={top.risk_band} />
              </p>
              <p className={styles.sentence}>{rowSentence(top) ?? tk("noSentence")}</p>
              {topFinding?.values ? (
                <div className={styles.pair}>
                  <Numeral tone="red" value={topFinding.values.left} caption={topFinding.values.leftSource} />
                  <Numeral tone="ink" value={topFinding.values.right} caption={topFinding.values.rightSource} />
                </div>
              ) : null}
              <p className={styles.context}>{tk("startNote")}</p>
            </>
          ) : (
            <p>{tk("startNone")}</p>
          )}
        </div>
        {top ? (
          <Link className="k-btn" href={`/case/${top.case_id}`}>
            {tk("openCase")}
          </Link>
        ) : null}
      </section>

      <p>
        <Link className="k-btn k-btn-2" href="/rb-queue">
          {t("openQueue")}
        </Link>
      </p>

      {waiting.length > 1 ? (
        <section aria-labelledby="ov-next">
          <h2 id="ov-next" className={styles.sectionLabel}>
            {tk("nextHeading")}
          </h2>
          <div className={styles.nextWrap}>
            <table className={styles.next}>
              <thead>
                <tr>
                  <th scope="col" className="k-label">{tk("colBand")}</th>
                  <th scope="col" className="k-label">{tk("colApplication")}</th>
                  <th scope="col" className="k-label">{tk("colWhy")}</th>
                  <th scope="col" className="k-label">{tk("colLabel")}</th>
                  <th scope="col" className="k-label">{tk("colWait")}</th>
                  <th scope="col" className="k-label">{tk("colOpen")}</th>
                </tr>
              </thead>
              <tbody>
                {waiting.slice(1, 7).map((r) => {
                  const label = worstLabel(r.label_counts);
                  const days = waitingDays(r.submitted_at, data.as_of);
                  return (
                    <tr key={r.case_id}>
                      <td>
                        <RiskBand band={r.risk_band} />
                      </td>
                      <td className="k-mono">{r.application_id}</td>
                      <td>{rowSentence(r) ?? tk("noSentence")}</td>
                      <td>{label ? <StatusLabel label={label} size="sm" /> : null}</td>
                      <td>{days === null ? "" : tk("days", { days })}</td>
                      <td>
                        <Link href={`/case/${r.case_id}`} aria-label={tk("open", { id: r.application_id })}>
                          {tk("openCase")}
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <p className={styles.sits}>
        <strong className="k-label">{tk("sitsHeading")}</strong>
        <br />
        {tk("sits")}
      </p>

      <h2 className={styles.sectionLabel}>{tk("detailHeading")}</h2>
      <div className={styles.grid}>
        <section className={styles.panel} aria-labelledby="ov-bands">
          <h2 id="ov-bands">{t("bandsHeading")}</h2>
          <p className={styles.total}>{t("bandsTotal", { count: data.cases.submitted })}</p>
          {data.cases.submitted === 0 ? (
            <p className={styles.empty}>{t("bandsEmpty")}</p>
          ) : (
            <ul className={styles.rows}>
              {BANDS.map((b) => (
                <li key={b}>
                  <Link className={styles.row} href={`/rb-queue?band=${b}`}>
                    <RiskBand band={b} />
                    <span className={styles.count}>{data.cases.by_band[b]}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.panel} aria-labelledby="ov-status">
          <h2 id="ov-status">{t("statusHeading")}</h2>
          <ul className={styles.rows}>
            {STATUSES.map((s) => (
              <li key={s}>
                <Link className={styles.row} href={`/rb-queue?status=${s}`}>
                  <span>{tq(`status.${s}`)}</span>
                  <span className={styles.count}>{data.status[s]}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className={styles.panel} aria-labelledby="ov-labels">
          <h2 id="ov-labels">{t("labelsHeading")}</h2>
          <p className={styles.total}>{t("labelsTotal", { count: data.documents.total })}</p>
          <ul className={styles.rows}>
            {LABEL_ORDER.map((l) => (
              <li key={l}>
                <Link className={styles.row} href={`/rb-queue?label=${l}`}>
                  <StatusLabel label={l} count={data.documents.by_label[l]} />
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className={styles.panel} aria-labelledby="ov-tasks">
          <h2 id="ov-tasks">{t("tasksHeading")}</h2>
          <p className={styles.total}>
            {t("tasksOpen", { count: data.manual_tasks.open })}
            {data.manual_tasks.open > 0 ? ` ${t("tasksOldest", { days: data.manual_tasks.oldest_age_days })}` : ""}
          </p>
          {data.manual_tasks.top.length === 0 ? (
            <p className={styles.empty}>{t("tasksEmpty")}</p>
          ) : (
            <ul className={styles.list}>
              {data.manual_tasks.top.map((task) => (
                <li key={`${task.case_id}-${task.reason_key}`}>
                  <Link href={`/case/${task.case_id}#docs`}>
                    <span className={styles.mono}>{task.application_id}</span>
                  </Link>{" "}
                  <span>{reason(task.reason_key)}</span> <span className={styles.age}>{t("ageDays", { days: task.age_days })}</span>
                </li>
              ))}
            </ul>
          )}
          <p className={styles.more}>
            <Link href="/rb-queue?label=source_unavailable">{t("tasksAll")}</Link>
          </p>
        </section>

        <section className={styles.panel} aria-labelledby="ov-expiring">
          <h2 id="ov-expiring">{t("expiringHeading")}</h2>
          <ul className={styles.windows}>
            {([30, 60, 90] as const).map((days) => (
              <li key={days}>
                <span className={styles.count}>{data.expiring[`d${days}`]}</span> {t("withinDays", { days })}
              </li>
            ))}
          </ul>
          {data.expiring.top.length === 0 ? (
            <p className={styles.empty}>{t("expiringEmpty")}</p>
          ) : (
            <ul className={styles.list}>
              {data.expiring.top.map((e) => (
                <li key={`${e.case_id}-${e.doc_type}`}>
                  <Link href={`/case/${e.case_id}#docs`}>{e.doc_title}</Link> <span className={styles.mono}>{e.application_id}</span>{" "}
                  <span className={styles.age}>{t("daysLeft", { days: e.days_left })}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.panel} aria-labelledby="ov-decisions">
          <h2 id="ov-decisions">{t("decisionsHeading")}</h2>
          {data.recent_decisions.length === 0 ? (
            <p className={styles.empty}>{t("decisionsEmpty")}</p>
          ) : (
            <ul className={styles.list}>
              {data.recent_decisions.map((d) => (
                <li key={d.ledger_no}>
                  <Link href={`/audit?case=${d.case_id}`}>
                    <time dateTime={d.at}>{when.format(new Date(d.at))}</time>
                  </Link>{" "}
                  <span>{t(`action.${d.action}`)}</span> <span className={styles.mono}>{d.application_id}</span>
                </li>
              ))}
            </ul>
          )}
          <p className={styles.more}>
            <Link href="/audit">{t("decisionsAll")}</Link>
          </p>
        </section>

        <section className={styles.panel} aria-labelledby="ov-sources">
          <h2 id="ov-sources">{t("sourcesHeading")}</h2>
          <p className={styles.total}>{t("sourcesAnswering", { n: answering, m: data.sources.length })}</p>
          <ul className={styles.list}>
            {data.sources.map((s) => (
              <li key={s.adapter_id}>
                {t(`source.${s.name_key}` as never)} <span className={styles.age}>{t(`sourceStatus.${s.status}`)}</span>
              </li>
            ))}
          </ul>
          {simulated.length > 0 ? (
            <p className={styles.more}>
              {t("sourcesSimulated", { names: simulated.map((s) => t(`source.${s.name_key}` as never)).join(", ") })} <SourceTag kind="simulated" />
            </p>
          ) : null}
        </section>
      </div>
    </>
  );
}
