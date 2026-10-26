import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("about");

export default async function AboutPage() {
  const t = await getTranslations("about");
  return (
    <>
      <PageHeader title={t("heading")} />
      <p>{t("body1")}</p>
      <p>{t("body2")}</p>
      <p>{t("body3")}</p>
    </>
  );
}
