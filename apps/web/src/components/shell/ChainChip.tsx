// Footer chain chip (prompt 7.9): "Chain intact" or "Chain broken at entry N", with the entry count.
// Reads the chain-verify answer (cached for a minute per session, never blocking the page: it is rendered
// inside Suspense) and falls back to the chain block of /v1/audit. Hidden when neither answers.
import { getTranslations } from "next-intl/server";
import { apiGetQuiet } from "@/lib/api";
import { AUDIT_VERIFY } from "@/lib/api/pending-endpoints";
import { fromAudit, fromVerify, type ChainStatus } from "@/lib/api/k-adapters/chain";
import { Icon } from "@/components/ui/Icon";
import styles from "./AppShell.module.css";

const TTL_MS = 60_000;

export async function chainStatus(): Promise<ChainStatus | null> {
  const verified = fromVerify(await apiGetQuiet<unknown>(AUDIT_VERIFY, TTL_MS));
  if (verified) return verified;
  return fromAudit(await apiGetQuiet<unknown>("/v1/audit", TTL_MS));
}

export async function ChainChip() {
  const status = await chainStatus();
  if (!status || status.state === "unknown") return null;
  const t = await getTranslations("chain");
  const broken = status.state === "broken";
  const text = broken ? t("broken", { entry: status.firstBadEntry ?? 0 }) : t("intact");
  return (
    <p className={styles.chain} data-state={status.state}>
      <Icon name={broken ? "circle-x" : "circle-check"} />
      <span>{text}</span>
      {status.entries !== null && <span className={styles.chainCount}>{t("entries", { count: status.entries })}</span>}
    </p>
  );
}
