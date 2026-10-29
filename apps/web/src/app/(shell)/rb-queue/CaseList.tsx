// RB-02 validation queue: one row per case with its risk band (text chip), label counts, how many
// findings await a decision, when the case arrived and last moved, its status and the top reasons.
// The API orders the rows: risk band groups first, the chosen sort inside each group. Filters work
// through the URL (band, label, status), so Overview links land on a filtered queue and the page
// works without client scripts. The band orders review only; it is not a finding (UI spec §5).
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { RiskBand } from "@/components/demo/RiskBand";
import demo from "@/components/demo/Demo.module.css";
import styles from "@/components/diff/DiffView.module.css";
import { QueueTable, type QueueTableRow } from "@/components/queue/QueueTable";
import { FilterSelect } from "@/components/ui/FilterSelect";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { LABEL_ORDER } from "@/lib/labels";
import { BANDS, SORT_KEYS, STATUSES, type Band, type QueueRow, type SortDir, type SortKey, type Status } from "@/lib/demo-types";
import type { VerificationLabel } from "@satya/shared-types";

export interface QueueQuery {
  band: Band | "";
  label: VerificationLabel | "";
  status: Status | "";
  q: string;
  sort: { key: SortKey; dir: SortDir } | null;
}

/** Whitelist every query parameter; anything else is dropped. */
export function parseQuery(params: Record<string, string | undefined>): QueueQuery {
  const pick = <T extends string>(value: string | undefined, allowed: readonly T[]): T | "" =>
    allowed.includes(value as T) ? (value as T) : "";
  const key = pick(params.sort, SORT_KEYS);
  return {
    band: pick(params.band, BANDS),
    label: pick(params.label, LABEL_ORDER),
    status: pick(params.status, STATUSES),
    q: /^[\w .\-]{1,40}$/.test(params.q ?? "") ? (params.q ?? "").trim() : "",
    sort: key ? { key, dir: params.dir === "desc" ? "desc" : "asc" } : null,
  };
}

export function applyFilters(rows: QueueRow[], q: QueueQuery): QueueRow[] {
  const needle = q.q.toLowerCase();
  return rows.filter(
    (r) =>
      (!q.band || r.risk_band === q.band) &&
      (!q.status || r.status === q.status) &&
      (!q.label || r.label_counts[q.label] > 0) &&
      (!needle || r.application_id.toLowerCase().includes(needle) || (r.institution_name ?? "").toLowerCase().includes(needle)),
  );
}

function href(q: QueueQuery, over: Partial<{ band: string; label: string; status: string; q: string; sort: boolean }>): string {
  const p = new URLSearchParams();
  const n = { band: q.band, label: q.label, status: q.status, q: q.q, sort: true, ...over };
  if (n.band) p.set("band", n.band);
  if (n.label) p.set("label", n.label);
  if (n.status) p.set("status", n.status);
  if (n.q) p.set("q", n.q);
  if (n.sort && q.sort) {
    p.set("sort", q.sort.key);
    p.set("dir", q.sort.dir);
  }
  const query = p.toString();
  return query ? `/rb-queue?${query}` : "/rb-queue";
}

export async function CaseList({ items, total, query }: { items: QueueRow[]; total: number; query: QueueQuery }) {
  const t = await getTranslations("queue");
  const tq = await getTranslations("demo");
  const td = await getTranslations("diff");
  const ts = await getTranslations("status");
  const locale = await getLocale();
  const when = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" });
  const rows: QueueTableRow[] = items.map((c) => ({
    id: c.case_id,
    band: <RiskBand band={c.risk_band} />,
    application: (
      <>
        <span className={styles.mono}>{c.application_id}</span>
        <br />
        <span className={styles.muted}>{c.institution_name ?? td("none")}</span>
      </>
    ),
    labels: (
      <ul className={demo.counts} aria-label={tq("queue.colLabels")}>
        {LABEL_ORDER.filter((l) => c.label_counts[l] > 0).map((l) => (
          <li key={l}>
            <StatusLabel label={l} size="sm" short count={c.label_counts[l]} />
          </li>
        ))}
      </ul>
    ),
    awaiting: (
      <span aria-label={tq("queue.awaitingAria", { count: c.undisposed_flags, total: c.open_flags })}>
        {tq("queue.awaiting", { count: c.undisposed_flags, total: c.open_flags })}
      </span>
    ),
    submitted: <time dateTime={c.submitted_at}>{when.format(new Date(c.submitted_at))}</time>,
    last: <time dateTime={c.last_activity_at}>{when.format(new Date(c.last_activity_at))}</time>,
    status: (
      <>
        {tq(`status.${c.status}`)}
        {c.manual_tasks > 0 ? <p className={styles.note}>{tq("queue.tasks", { count: c.manual_tasks })}</p> : null}
      </>
    ),
    reasons: (
      <ul className={demo.reasons}>
        {c.top_reasons.map((r) => (
          <li key={r.flag_id}>{[r.rule_id, " (", r.aph_clause ?? tq("flags.verify"), ")"].join("")}</li>
        ))}
      </ul>
    ),
    open: (
      <Link href={`/case/${c.case_id}`} aria-label={tq("queue.openAria", { aid: c.application_id })}>
        {tq("queue.open")}
      </Link>
    ),
  }));
  const filtered = Boolean(query.band || query.label || query.status || query.q);
  return (
    <section className={styles.section} aria-labelledby="case-list">
      <h2 id="case-list">{t("listHeading")}</h2>
      <p className={styles.note}>{tq("queue.intro")}</p>
      <form method="get" action="/rb-queue" className={demo.filters} aria-label={tq("queue.filters")}>
        {query.q ? <input type="hidden" name="q" value={query.q} /> : null}
        {query.sort ? (
          <>
            <input type="hidden" name="sort" value={query.sort.key} />
            <input type="hidden" name="dir" value={query.sort.dir} />
          </>
        ) : null}
        <FilterSelect
          name="band"
          label={tq("queue.filterBand")}
          value={query.band}
          testId="filter-band"
          options={[{ value: "", label: tq("queue.all") }, ...BANDS.map((b) => ({ value: b, label: tq(`band.${b}`) }))]}
        />
        <FilterSelect
          name="label"
          label={tq("queue.filterLabel")}
          value={query.label}
          testId="filter-label"
          options={[{ value: "", label: tq("queue.all") }, ...LABEL_ORDER.map((l) => ({ value: l, label: ts(`label.${l}`) }))]}
        />
        <FilterSelect
          name="status"
          label={tq("queue.filterStatus")}
          value={query.status}
          testId="filter-status"
          options={[{ value: "", label: tq("queue.all") }, ...STATUSES.map((s) => ({ value: s, label: tq(`status.${s}`) }))]}
        />
        <button type="submit" className={demo.button}>
          {tq("queue.apply")}
        </button>
        {filtered ? <Link href={href(query, { band: "", label: "", status: "", q: "" })}>{tq("queue.clear")}</Link> : null}
        {query.sort ? <Link href={href(query, { sort: false })}>{tq("queue.resetSort")}</Link> : null}
      </form>
      <p className={styles.note} role="status">
        {tq("queue.shown", { shown: items.length, total })}
        {query.q ? ` ${tq("queue.searchNote", { q: query.q })}` : ""}
      </p>
      {items.length === 0 ? (
        <p>{tq("queue.noMatch")}</p>
      ) : (
        <QueueTable
          rows={rows}
          sort={query.sort}
          text={{
            caption: tq("queue.caption"),
            band: tq("queue.colBand"),
            application: t("colApplication"),
            labels: tq("queue.colLabels"),
            awaiting: tq("queue.colAwaiting"),
            submitted: tq("queue.colSubmitted"),
            last: tq("queue.colLastActivity"),
            status: tq("queue.colStatus"),
            reasons: tq("queue.colReasons"),
            open: t("colOpen"),
            announce: tq("queue.sortAnnounce", { column: "{column}", dir: "{dir}" }),
            ascending: tq("queue.asc"),
            descending: tq("queue.desc"),
          }}
        />
      )}
      <p className={styles.note}>{tq("queue.bandNote")}</p>
    </section>
  );
}
