// SignatureBadge (UI spec §4.3, X-11; design C3): two independent badges per document, separate from
// the six labels. The text on the badge carries the meaning (never colour alone); a detail line says
// why (chain to the trust anchor and signer role, or the reason a check failed). A printed
// "digitally signed" mark without /ByteRange is always IMAGE ONLY and never verified.
import type { SignatureCheck } from "@satya/shared-types";
import { getTranslations } from "next-intl/server";
import styles from "./SignatureBadge.module.css";

type Tone = "verified" | "present" | "image" | "broken" | "absent" | "neutral";

function tone(sig: SignatureCheck): Tone {
  if (sig.state === "image_only") return "image";
  if (sig.state === "absent_required") return "absent";
  if (sig.state === "not_digital" || sig.state === "not_applicable") return "neutral";
  if (sig.reason_code && sig.reason_code !== "SIG_VALID") return "broken";
  if (sig.state === "verified") return "verified";
  if (sig.state === "present") return "present";
  return "broken";
}

export async function SignatureBadge({ sig, anchor }: { sig: SignatureCheck | null | undefined; anchor: string }) {
  const t = await getTranslations("signature");
  const tv = await getTranslations("verification");
  if (!sig) {
    return (
      <span className={styles.wrap}>
        <span className={styles.badge} data-tone="neutral">
          {t("notChecked")}
        </span>
      </span>
    );
  }
  const text = sig.role === "issuer" ? t(`issuer.${sig.state}` as never) : t(`uploader.${sig.state}` as never);
  const details: string[] = [];
  const reason = sig.reason_code ? `reason.${sig.reason_code}` : null;
  if (sig.reason_code === "SIG_VALID" && sig.trust_anchor_label) {
    details.push(t("chainOk", { anchor: sig.trust_anchor_label || anchor }));
    if (sig.signer_role) details.push(t(`signerRole.${sig.signer_role}`));
  } else if (reason && tv.has(reason as never)) {
    details.push(tv(reason as never));
  }
  if (sig.page) details.push(t("onPage", { page: sig.page }));
  return (
    <span className={styles.wrap}>
      <span className={styles.badge} data-tone={tone(sig)}>
        {text}
      </span>
      {details.length ? <span className={styles.detail}>{details.join(" · ")}</span> : null}
    </span>
  );
}
