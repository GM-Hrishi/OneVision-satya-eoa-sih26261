"use client";
// VISUAL 5: replay diff. Headline "Reproduced identically." (stamp) or "Does not reproduce." in red, then a table of
// Original vs Replayed with Same / Different cells (icon + word) and the whole-result row. A Different row is
// named and the audit trail for the case is linked. The stamp plays once on first mount.
import { useTranslations } from "next-intl";
import Link from "next/link";
import { Icon } from "@/components/ui/Icon";
import { useMotion } from "@/components/ui/useMotion";
import type { ReplayVM } from "@/lib/api/k-adapters/replay";
import { inertSnippet } from "@/lib/untrusted";
import styles from "./Audit.module.css";

const fp = (v: string) => (v.length > 40 ? `${v.slice(0, 16)}…${v.slice(-8)}` : v);

export function ReplayDiff({ vm, caseId, fixtureNote }: { vm: ReplayVM; caseId: string; fixtureNote?: boolean }) {
  const t = useTranslations("k.replay");
  const { cls } = useMotion();
  const different = vm.rows.filter((r) => !r.same);
  return (
    <div>
      <h1 className={`k-h1 ${styles.headline}`}>
        <span className={`${styles.stamp} ${vm.reproduced ? cls("stamp") : ""}`} style={vm.reproduced ? undefined : { color: "var(--k-red)" }}>
          {vm.reproduced ? t("headlineOk") : t("headlineBad")}
        </span>
      </h1>
      <p className={styles.note}>{t("intro")}</p>
      {fixtureNote ? <p className={`k-label ${styles.note}`}>{t("fixtureNote")}</p> : null}
      <div className={styles.wrapScroll}>
        <table className={styles.diffTable}>
          <thead>
            <tr>
              <th scope="col" className="k-label">{t("colWhat")}</th>
              <th scope="col" className="k-label">{t("colOriginal")}</th>
              <th scope="col" className="k-label">{t("colReplayed")}</th>
              <th scope="col" className="k-label">{t("colResult")}</th>
            </tr>
          </thead>
          <tbody>
            {vm.rows.map((r) => (
              <tr key={r.key}>
                <th scope="row">{t(`row.${r.key}`)}</th>
                <td className="mono">{fp(r.original)}</td>
                <td className="mono">{fp(r.replayed)}</td>
                <td>
                  <span className={styles.verdict} data-same={r.same}>
                    <Icon name={r.same ? "circle-check" : "circle-x"} size={18} />
                    {r.same ? t("same") : t("different")}
                  </span>
                </td>
              </tr>
            ))}
            <tr>
              <th scope="row">{t("row.whole")}</th>
              <td />
              <td />
              <td>
                <span className={styles.verdict} data-same={vm.reproduced}>
                  <Icon name={vm.reproduced ? "circle-check" : "circle-x"} size={18} />
                  {vm.reproduced ? t("same") : t("different")}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      {!vm.reproduced ? (
        <>
          <h3 className={styles.sectionTitle}>{t("reasonsHeading")}</h3>
          <ul>
            {different.map((r) => (
              <li key={r.key}>{t("differsLine", { what: t(`row.${r.key}`) })}</li>
            ))}
            {vm.reasons.map((reason) => (
              <li key={reason}>{inertSnippet(reason, 200)}</li>
            ))}
          </ul>
          <Link href={`/audit?case=${caseId}`}>{t("auditLink")}</Link>
        </>
      ) : null}
    </div>
  );
}
