import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("policies");

const SECTIONS = ["privacy", "cookies", "security", "use"] as const;

export default async function PoliciesPage() {
  const t = await getTranslations("policies");
  return (
    <>
      <PageHeader title={t("heading")} />
      {SECTIONS.map((s) => (
        <section key={s} aria-labelledby={`policy-${s}`}>
          <h2 id={`policy-${s}`}>{t(`${s}Heading`)}</h2>
          <p>{t(`${s}Body`)}</p>
        </section>
      ))}
    </>
  );
}
