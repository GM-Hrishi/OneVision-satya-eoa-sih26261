// Home for workbench roles whose screens are not in this build yet (no dead navigation).
import Link from "next/link";
import type { Metadata } from "next";
import { forbidden } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";
import { primaryRole, requireSession } from "@/lib/session";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("roleHome");

export default async function RoleHome() {
  const session = await requireSession("/home");
  const role = primaryRole(session);
  if (!role) forbidden();
  const [t, tRoles] = await Promise.all([getTranslations("roleHome"), getTranslations("roles")]);
  return (
    <>
      <PageHeader title={t("heading")} />
      <p>{t("body", { role: tRoles(role) })}</p>
      <p>
        <Link href="/help">{t("help")}</Link>
      </p>
    </>
  );
}
