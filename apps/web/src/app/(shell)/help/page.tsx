import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("help");

const SECTIONS = ["what", "labels", "risk", "data", "keys"] as const;

export default async function HelpPage() {
  const t = await getTranslations("help");
  return (
    <>
      <PageHeader title={t("heading")} />
      {SECTIONS.map((s) => (
        <section key={s} aria-labelledby={`help-${s}`}>
          <h2 id={`help-${s}`}>{t(`${s}Heading`)}</h2>
          <p>{t(`${s}Body`)}</p>
        </section>
      ))}
    </>
  );
}
