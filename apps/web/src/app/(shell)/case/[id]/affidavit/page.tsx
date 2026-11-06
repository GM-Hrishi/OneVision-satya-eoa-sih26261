// RB-05 Affidavit DiffView (UI spec §2.2, §6.3, §7.1): the sworn Affidavit 2 against the portal draft
// for this AID and AY, and its tables against the Application Report data. Advisory only: no control
// here approves, rejects or clears anything (guard rail 1).
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { CaseTabs } from "@/components/case/CaseTabs";
import { DiffView } from "@/components/diff/DiffView";
import styles from "@/components/diff/DiffView.module.css";
import Link from "next/link";
import { AffidavitViews } from "@/components/k/AffidavitViews";
import { Numeral } from "@/components/k/Numeral";
import { affidavitSummary, tieRows, wasCompared } from "@/lib/api/k-adapters/affidavit";
import { affidavitDiff } from "@/lib/cases";
import { requireRole } from "@/lib/session";
import { Note } from "@/components/ui/Note";

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ all?: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("diff");
  const { id } = await params;
  return { title: t("title"), description: t("description", { case: id.slice(-4) }) };
}

export default async function AffidavitDiffPage({ params, searchParams }: Props) {
  const { id } = await params;
  const showAll = (await searchParams).all === "1";
  const base = `/case/${id}/affidavit`;
  await requireRole("RB", base);
  const diff = await affidavitDiff(id, base);
  const t = await getTranslations("diff");
  const tk = await getTranslations("k.affidavit");
  const sum = affidavitSummary(diff);
  const compared = wasCompared(diff);
  const c = diff.case;
  return (
    <>
      <header>
        <h1>{sum.notComparable > 0 ? tk("headlineNotCompared") : tk("headlineCompared", { match: sum.match, total: sum.total, rest: sum.differ + sum.missing })}</h1>
        <ul className={styles.numerals} aria-label={tk("numeralsLabel")}>
          <li>
            <Numeral value={sum.notComparable > 0 ? sum.notComparable : sum.match} caption={sum.notComparable > 0 ? tk("notComparable") : tk("match")} tone="ink" />
          </li>
          <li>
            <Numeral value={sum.differ} caption={tk("differ")} tone="red" />
          </li>
          <li>
            <Numeral value={sum.missing} caption={tk("missing")} tone="ink" />
          </li>
        </ul>
        <p>
          <Link href={`/case/${id}`}>{tk("backToCase")}</Link>
        </p>
        <p className={styles.caseLine}>
          {t("caseLine", {
            aid: c.application_id,
            institution: c.institution_name ?? t("none"),
            ay: c.ay,
          })}
        </p>
        <p className={styles.caseMeta}>
          {t("caseMeta", {
            route: t(`route.${c.route}`),
            stage: t(`stage.${c.stage}`),
            region: c.regional_office,
            categories: c.category_set.join("; "),
          })}
        </p>
        <Note>{t("advisory")}</Note>
        <CaseTabs caseId={id} current="affidavit" />
      </header>
      <AffidavitViews
        rows={tieRows(diff)}
        compared={compared}
        table={
      <DiffView
        diff={diff}
        showAll={showAll}
        allHref={`${base}?all=1`}
        changedHref={base}
        verificationHref={`/case/${id}/verification`}
      />
        }
      />
    </>
  );
}
