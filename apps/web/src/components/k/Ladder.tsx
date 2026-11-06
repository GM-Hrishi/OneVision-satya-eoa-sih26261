// Ladder view of "How far each document was checked" (the section heading and the view switch live in ProofViews): documents x five checks, with an icon cell per check (each state has
// its own shape, an aria-label and a legend, so colour is never the only signal) and a one-sentence verdict.
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Icon, type IconName } from "@/components/ui/Icon";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { LADDER_COLUMNS, type LadderRow, type LadderState } from "@/lib/api/k-adapters/case";
import styles from "./Ladder.module.css";

const ICON: Record<LadderState, IconName> = {
  agrees: "circle-check",
  disagrees: "circle-x",
  waiting: "hourglass",
  check: "user-search",
  na: "minus",
};
const STATES: LadderState[] = ["agrees", "disagrees", "waiting", "check", "na"];

export async function Ladder({ rows, caseId }: { rows: LadderRow[]; caseId: string }) {
  const t = await getTranslations("k.ladder");
  if (rows.length === 0) return null;
  return (
    <div>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <caption className="k-label">{t("caption")}</caption>
          <thead>
            <tr>
              <th scope="col" className="k-label">
                {t("colDocument")}
              </th>
              {LADDER_COLUMNS.map((c) => (
                <th key={c} scope="col" className="k-label">
                  {t(`col.${c}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.docId}>
                <th scope="row">
                  <Link className={styles.docTitle} href={`/case/${caseId}/documents/${row.docId}`}>
                    {row.title}
                  </Link>
                  <br />
                  <StatusLabel label={row.label} size="sm" />
                  <p className={styles.verdict}>{row.verdictText ?? t(`verdict.${row.label}`, { title: row.title })}</p>
                </th>
                {LADDER_COLUMNS.map((c) => (
                  <td key={c}>
                    <span className={styles.cell} data-state={row.cells[c]} role="img" aria-label={t("cell", { column: t(`col.${c}`), state: t(`state.${row.cells[c]}`) })}>
                      <Icon name={ICON[row.cells[c]]} size={26} />
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className={styles.legend} aria-hidden="true">
        {STATES.map((s) => (
          <li key={s}>
            <Icon name={ICON[s]} size={16} />
            {t(`state.${s}`)}
          </li>
        ))}
      </ul>
    </div>
  );
}
