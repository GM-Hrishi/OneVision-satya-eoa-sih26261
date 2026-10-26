// SH-09: 403 "Not assigned to you" (rendered with status 403 via forbidden()). forbidden() is only
// called from pages inside the (shell) route group, whose layout already draws the AppShell.
import Link from "next/link";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";
import { currentSession } from "@/lib/session";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("forbidden");

export default async function Forbidden() {
  const [t, session] = await Promise.all([getTranslations("forbidden"), currentSession()]);
  const institution = session?.user.roles.includes("INS") && session.user.roles.length === 1;
  return (
    <>
      <PageHeader title={t("heading")} />
      <p>{institution ? t("institution") : t("body")}</p>
      <p>
        <Link href="/">{t("home")}</Link>
      </p>
    </>
  );
}
