import Link from "next/link";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { currentPath, pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("notFound");

export default async function NotFound() {
  const t = await getTranslations("notFound");
  return (
    <AppShell path={await currentPath()}>
      <PageHeader title={t("heading")} />
      <p>{t("body")}</p>
      <p>
        <Link href="/">{t("home")}</Link>
      </p>
    </AppShell>
  );
}
