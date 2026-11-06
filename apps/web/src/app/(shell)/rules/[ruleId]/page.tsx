// Rule detail (read only). Reads GET /v1/rules/{rule_id}, which is on the backend branch only (NOT ON MAIN UNTIL PR #15
// MERGES); until then the page says so. The limitation note appears only when the API supplies text.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound, forbidden } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { LimitationNote } from "@/components/k/LimitationNote";
import dk from "@/components/k/Doc.module.css";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { apiGetOptional } from "@/lib/api";
import { fromRuleDetail } from "@/lib/api/k-adapters/rules";
import { ruleDetail } from "@/lib/api/pending-endpoints";
import { requireRole } from "@/lib/session";

type Props = { params: Promise<{ ruleId: string }> };
const RULE_ID = /^[A-Z0-9][A-Z0-9_.-]{1,63}$/;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("k.rules");
  const { ruleId } = await params;
  return { title: t("detailTitle", { id: decodeURIComponent(ruleId).slice(0, 64) }), description: t("detailDescription") };
}

export default async function RuleDetailPage({ params }: Props) {
  const id = decodeURIComponent((await params).ruleId);
  if (!RULE_ID.test(id)) notFound();
  const path = `/rules/${encodeURIComponent(id)}`;
  await requireRole("RB", path);
  const t = await getTranslations("k.rules");
  const td = await getTranslations("demo");
  const answer = await apiGetOptional<unknown>(ruleDetail(id), path);
  if (answer.status === "forbidden") forbidden();
  const vm = answer.status === "ok" ? fromRuleDetail(answer.data) : null;
  return (
    <>
      <header>
        <h1>{vm ? t("detailHeadline", { id: vm.ruleId, clause: vm.clause ?? t("clauseUnconfirmed") }) : t("detailTitle", { id })}</h1>
        <p>
          <Link href="/rules">{t("back")}</Link>
        </p>
      </header>
      {vm ? (
        <>
          {vm.version && vm.edition ? <p className="k-label">{t("version", { version: vm.version, edition: vm.edition })}</p> : null}
          <section className={dk.section} aria-labelledby="rule-fails">
            <h2 id="rule-fails" className={dk.sectionTitle}>
              {t("failsHeading")}
            </h2>
            <p>{t("failsLine")}</p>
            <p className={dk.status}>
              {vm.label ? <StatusLabel label={vm.label} /> : null}
              {vm.severity ? (
                <>
                  {" "}
                  <span className="k-label">{t("severityLabel")}</span> <strong>{td(`severity.${vm.severity}`)}</strong>
                </>
              ) : null}
            </p>
          </section>
          <LimitationNote text={vm.limitation} />
        </>
      ) : (
        <p role="status">{answer.status === "error" ? t("detailError") : t("detailUnavailable")}</p>
      )}
      <p>
        <Link className="k-btn k-btn-2" href={path}>
          {t("retry")}
        </Link>
      </p>
    </>
  );
}
