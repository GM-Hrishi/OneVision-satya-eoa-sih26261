// Add a synthetic PDF to a case (upload) or reuse a seeded one (pick). The file is hashed, the M5
// and M6 checks run again and the results are stored against the case.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { CaseTabs } from "@/components/case/CaseTabs";
import { UploadForms } from "@/components/demo/UploadForms";
import { PageHeader } from "@/components/ui/PageHeader";
import { queue } from "@/lib/demo";
import { requireRole } from "@/lib/session";
import { Note } from "@/components/ui/Note";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("demo");
  return { title: t("upload.title"), description: t("upload.description") };
}

export default async function UploadPage({ params }: Props) {
  const { id } = await params;
  const base = `/case/${id}/upload`;
  await requireRole("RB", base);
  const { items } = await queue(base);
  const t = await getTranslations("demo");
  const td = await getTranslations("diff");
  return (
    <>
      <PageHeader title={t("upload.heading")}>
        <Note>{td("advisory")}</Note>
        <CaseTabs caseId={id} current="upload" />
      </PageHeader>
      <p>{t("upload.intro")}</p>
      <UploadForms
        caseId={id}
        sources={items.filter((c) => c.case_id !== id).map((c) => ({ id: c.case_id, name: c.institution_name ?? c.application_id }))}
      />
    </>
  );
}
