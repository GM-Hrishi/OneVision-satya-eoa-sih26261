// Chain integrity: how the ledger chain is checked and what the gateway found on this visit. Advisory; read only.
import type { Metadata } from "next";
import Link from "next/link";
import { forbidden } from "next/navigation";
import { getLocale, getTranslations } from "next-intl/server";
import ak from "@/components/k/Audit.module.css";
import { Numeral } from "@/components/k/Numeral";
import { Icon } from "@/components/ui/Icon";
import { audit } from "@/lib/demo";
import { requireSession } from "@/lib/session";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("k.audit");
  return { title: t("integrityHeadline"), description: t("integrityBody") };
}

export default async function IntegrityPage() {
  const session = await requireSession("/audit/integrity");
  if (!session.user.roles.some((r) => r === "RB" || r === "AU")) forbidden();
  const data = await audit("/audit/integrity");
  const t = await getTranslations("k.audit");
  const locale = await getLocale();
  const fmt = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "medium" });
  return (
    <>
      <header className={ak.head}>
        <Numeral value={data.chain.rows} caption={t("countCaption")} />
        <div>
          <h1 className="k-h1">{t("integrityHeadline")}</h1>
          <p className={ak.state} data-state={data.chain.ok ? "intact" : "broken"}>
            <Icon name={data.chain.ok ? "circle-check" : "circle-x"} size={20} />
            {data.chain.ok ? t("intact") : t("broken", { entry: data.chain.broken_at ?? 0 })}
          </p>
          <p>{t("checkedAt", { time: fmt.format(new Date(data.chain.recomputed_at)) })}</p>
        </div>
      </header>
      <p className={ak.note}>{t("integrityBody")}</p>
      <p className={`k-mono ${ak.note}`}>{t("integrityMethod", { method: data.chain.method })}</p>
      <div className={ak.actions}>
        <Link className="k-btn k-btn-2" href="/audit/integrity">
          {t("verifyAgain")}
        </Link>
        <Link className="k-btn k-btn-2" href="/audit">
          {t("tableHeading")}
        </Link>
      </div>
    </>
  );
}
