// RB-02 validation queue: one row per case with its risk band (text chip), label counts, status and
// the top reasons. Sortable by column and filterable by band and status through the URL, so it works
// without client scripts. The band orders review only; it is not a finding (UI spec §5).
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { RiskBand } from "@/components/demo/RiskBand";
import demo from "@/components/demo/Demo.module.css";
import { Label, labelTone } from "@/components/diff/DiffView";
import styles from "@/components/diff/DiffView.module.css";
import { LABEL_ORDER } from "@/lib/labels";
import { BANDS, STATUSES, type Band, type QueueRow, type Status } from "@/lib/demo";

export type SortKey = "band" | "institution" | "findings" | "status";
export const SORTS: readonly SortKey[] = ["band", "institution", "findings", "status"];
const BAND_RANK: Record<Band, number> = { high: 0, medium: 1, low: 2 };
const STATUS_RANK: Record<Status, number> = { awaiting_review: 0, in_review: 1, reviewed: 2, no_findings: 3 };

export interface QueueQuery {
  band: Band | "";
  status: Status | "";
  sort: SortKey;
  dir: "asc" | "desc";
}

export function parseQuery(params: Record<string, string | undefined>): QueueQuery {
  const pick = <T extends string>(value: string | undefined, allowed: readonly T[]): T | "" =>
    allowed.includes(value as T) ? (value as T) : "";
  return {
    band: pick(params.band, BANDS),
    status: pick(params.status, STATUSES),
    sort: (pick(params.sort, SORTS) || "band") as SortKey,
    dir: params.dir === "desc" ? "desc" : "asc",
  };
}

export function applyQuery(rows: QueueRow[], q: QueueQuery): QueueRow[] {
  const out = rows.filter((r) => (!q.band || r.risk_band === q.band) && (!q.status || r.status === q.status));
  const key = (r: QueueRow): number | string =>
    q.sort === "band" ? BAND_RANK[r.risk_band] : q.sort === "status" ? STATUS_RANK[r.status] : q.sort === "findings" ? r.open_flags : (r.institution_name ?? "");
  out.sort((a, b) => {
    const [x, y] = [key(a), key(b)];
    const base = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y));
    return (q.dir === "desc" ? -base : base) || a.application_id.localeCompare(b.application_id);
  });
  return out;
}

function href(q: QueueQuery, over: Partial<QueueQuery>): string {
  const n = { ...q, ...over };
  const p = new URLSearchParams();
  if (n.band) p.set("band", n.band);
  if (n.status) p.set("status", n.status);
  p.set("sort", n.sort);
  p.set("dir", n.dir);
  return `/rb-queue?${p.toString()}`;
}

export async function CaseList({ items, total, query }: { items: QueueRow[]; total: number; query: QueueQuery }) {
  const t = await getTranslations("queue");
  const tq = await getTranslations("demo");
  const td = await getTranslations("diff");
  const header = (key: SortKey, label: string) => {
    const active = query.sort === key;
    const next = active && query.dir === "asc" ? "desc" : "asc";
    return (
      <th scope="col" aria-sort={active ? (query.dir === "asc" ? "ascending" : "descending") : "none"}>
        <Link href={href(query, { sort: key, dir: next })} className={demo.sortLink} aria-current={active ? "true" : undefined}>
          {label}
          {active ? ` (${query.dir === "asc" ? tq("queue.asc") : tq("queue.desc")})` : ""}
        </Link>
      </th>
    );
  };
  return (
    <section className={styles.section} aria-labelledby="case-list">
      <h2 id="case-list">{t("listHeading")}</h2>
      <p className={styles.note}>{tq("queue.intro")}</p>
      <form method="get" action="/rb-queue" className={demo.filters} aria-label={tq("queue.filters")}>
        <input type="hidden" name="sort" value={query.sort} />
        <input type="hidden" name="dir" value={query.dir} />
        <label>
          {tq("queue.filterBand")}
          <select name="band" defaultValue={query.band}>
            <option value="">{tq("queue.all")}</option>
            {BANDS.map((b) => (
              <option key={b} value={b}>
                {tq(`band.${b}`)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tq("queue.filterStatus")}
          <select name="status" defaultValue={query.status}>
            <option value="">{tq("queue.all")}</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {tq(`status.${s}`)}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className={demo.button}>
          {tq("queue.apply")}
        </button>
        <Link href="/rb-queue">{tq("queue.clear")}</Link>
      </form>
      <p className={styles.note} role="status">
        {tq("queue.shown", { shown: items.length, total })}
      </p>
      {items.length === 0 ? (
        <p>{tq("queue.noMatch")}</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {header("band", tq("queue.colBand"))}
                <th scope="col">{t("colApplication")}</th>
                {header("institution", t("colInstitution"))}
                <th scope="col">{tq("queue.colLabels")}</th>
                {header("findings", t("colFindings"))}
                {header("status", tq("queue.colStatus"))}
                <th scope="col">{tq("queue.colReasons")}</th>
                <th scope="col">{t("colOpen")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.case_id}>
                  <td>
                    <RiskBand band={c.risk_band} />
                  </td>
                  <td className={styles.mono}>{c.application_id}</td>
                  <td>{c.institution_name ?? td("none")}</td>
                  <td>
                    <ul className={demo.counts}>
                      {LABEL_ORDER.filter((l) => c.label_counts[l] > 0).map((l) => (
                        <li key={l}>
                          <Label tone={labelTone(l)}>{td(`labels.${l}`)}</Label> {c.label_counts[l]}
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td className={styles.num}>{t("findings", { count: c.open_flags })}</td>
                  <td>
                    {tq(`status.${c.status}`)}
                    {c.manual_tasks > 0 ? <p className={styles.note}>{tq("queue.tasks", { count: c.manual_tasks })}</p> : null}
                  </td>
                  <td>
                    <ul className={demo.reasons}>
                      {c.top_reasons.map((r) => (
                        <li key={r.flag_id}>
                          {[r.rule_id, " (", r.aph_clause ?? tq("flags.verify"), ")"].join("")}
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td>
                    <Link href={`/case/${c.case_id}`} aria-label={tq("queue.openAria", { aid: c.application_id })}>
                      {tq("queue.open")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className={styles.note}>{tq("queue.bandNote")}</p>
    </section>
  );
}
