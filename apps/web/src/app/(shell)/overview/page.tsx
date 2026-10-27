// RB-01 Overview: where the Regulation Bureau lands after sign-in. Equal plain panels, no charts and
// no KPI cards. Every count links to the queue (or the audit trail) already filtered. Advisory
// only: nothing here approves, rejects or clears anything.
import type { Metadata } from "next";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { RiskBand } from "@/components/demo/RiskBand";
import styles from "@/components/overview/Overview.module.css";
import { PageHeader } from "@/components/ui/PageHeader";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { overview } from "@/lib/demo";
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
  const [t, tq, tr, tx, locale, data] = await Promise.all([
    getTranslations("overview"),
    getTranslations("demo"),
    getTranslations("regions"),
    getTranslations("status"),
    getLocale(),
    overview("/overview", AY),
  ]);
  const intl = locale === "hi" ? "hi-IN" : "en-IN";
  const asOf = new Intl.DateTimeFormat(intl, { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" }).format(new Date(data.as_of));
  const when = new Intl.DateTimeFormat(intl, { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" });
  const region = data.region === "southern" || data.region === "national" ? tr(data.region) : tr("none");
  const answering = data.sources.filter((s) => s.status === "answering").length;
  const simulated = data.sources.filter((s) => s.mode === "mock");
  const reason = (code: string) => (t.has(`reason.${code}` as never) ? t(`reason.${code}` as never) : code);
  return (
    <>
      <PageHeader title={t("heading")}>
        <p className={styles.context}>{t("context", { ay: data.ay, region, asOf })}</p>
        <p>
          <Link className={styles.primary} href="/rb-queue">
            {t("openQueue")}
          </Link>
        </p>
      </PageHeader>

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
