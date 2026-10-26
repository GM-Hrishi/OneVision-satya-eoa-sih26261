import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import { pageMetadata } from "@/lib/page";
import { currentSession } from "@/lib/session";
import { SignInRedirect } from "./SignInRedirect";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("signin");

type Props = { searchParams: Promise<{ callbackUrl?: string; error?: string }> };

function safePath(value: string | undefined): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/";
}

export default async function SignInPage({ searchParams }: Props) {
  const params = await searchParams;
  const callbackUrl = safePath(params.callbackUrl);
  if (await currentSession()) redirect(callbackUrl);
  const t = await getTranslations("signin");
  return (
    <>
      <PageHeader title={t("heading")} />
      <SignInRedirect
        callbackUrl={callbackUrl}
        auto={!params.error}
        message={params.error ? t("failed") : t("redirecting")}
        button={t("button")}
      />
    </>
  );
}
