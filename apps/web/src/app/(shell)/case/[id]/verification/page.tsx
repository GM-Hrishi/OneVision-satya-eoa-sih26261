// RB-06 Verification panel (UI spec §2.2, §6.4, §7.2): every document of the case with exactly one of
// the six labels, both signature badges and the source checked. M6 (P-4, P-18) fills it in slice 2;
// source adapters (M7, P-5) join later. Advisory only (guard rail 1).
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { CaseTabs } from "@/components/case/CaseTabs";
import styles from "@/components/diff/DiffView.module.css";
import { PageHeader } from "@/components/ui/PageHeader";
import { VerificationPanel } from "@/components/verification/VerificationPanel";
import { affidavitDiff, caseVerification } from "@/lib/cases";
import { requireRole } from "@/lib/session";
import { Note } from "@/components/ui/Note";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("verification");
  const { id } = await params;
  return { title: t("title"), description: t("description", { case: id.slice(-4) }) };
}

export default async function VerificationPage({ params }: Props) {
  const { id } = await params;
  const base = `/case/${id}/verification`;
  await requireRole("RB", base);
  const [data, diff] = await Promise.all([caseVerification(id, base), affidavitDiff(id, base)]);
  const t = await getTranslations("verification");
  const td = await getTranslations("diff");
  const c = diff.case;
  return (
    <>
      <PageHeader title={t("heading")}>
        <p className={styles.caseLine}>
          {td("caseLine", { aid: c.application_id, institution: c.institution_name ?? td("none"), ay: c.ay })}
        </p>
        <p className={styles.caseMeta}>
          {td("caseMeta", {
            route: td(`route.${c.route}`),
            stage: td(`stage.${c.stage}`),
            region: c.regional_office,
            categories: c.category_set.join("; "),
          })}
        </p>
        <Note>{td("advisory")}</Note>
        <CaseTabs caseId={id} current="verification" />
      </PageHeader>
      <VerificationPanel data={data} />
    </>
  );
}
