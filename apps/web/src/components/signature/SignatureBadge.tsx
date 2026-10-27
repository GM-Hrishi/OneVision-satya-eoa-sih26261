// SignatureBadge (UI spec §4.3, X-11; design C3; v0.8 neutral variant): two independent badges per
// document, separate from the six labels. A neutral pill with an icon and sentence-case text; the
// text carries the meaning (never colour alone) and a detail line says why (chain to the trust
// anchor and signer role, or the reason a check failed). A printed "digitally signed" mark without
// /ByteRange is always IMAGE ONLY and never verified.
import type { SignatureCheck } from "@satya/shared-types";
import { getTranslations } from "next-intl/server";
import { Icon, type IconName } from "@/components/ui/Icon";
import { SourceTag } from "@/components/ui/SourceTag";
import styles from "./SignatureBadge.module.css";

function icon(sig: SignatureCheck): IconName {
  if (sig.state === "image_only") return "photo";
  if (sig.state === "absent_required") return "signature-off";
  if (sig.state === "not_digital") return "writing-sign";
  if (sig.state === "not_applicable") return "info-circle";
  if (sig.reason_code && sig.reason_code !== "SIG_VALID") return "shield-x";
  if (sig.state === "verified") return "shield-check";
  if (sig.state === "present") return "signature";
  return "shield-x";
}

// Every signature chain in this deployment is checked against a test root (the API has no
// trust_anchor.kind field yet), so every performed signature check carries the Test trust anchor tag.
const UNCHECKED = new Set(["not_digital", "not_applicable", "absent_required"]);

export async function SignatureBadge({ sig }: { sig: SignatureCheck | null | undefined }) {
  const t = await getTranslations("signature");
  const tv = await getTranslations("verification");
  if (!sig) {
    return (
      <span className={styles.wrap}>
        <span className={styles.badge}>
          <Icon name="info-circle" size={13} />
          {t("notChecked")}
        </span>
      </span>
    );
  }
  const text = sig.role === "issuer" ? t(`issuer.${sig.state}` as never) : t(`uploader.${sig.state}` as never);
  const details: string[] = [];
  const reason = sig.reason_code ? `reason.${sig.reason_code}` : null;
  if (sig.reason_code === "SIG_VALID" && sig.trust_anchor_label) {
    details.push(t("chainOk"));
    if (sig.signer_role) details.push(t(`signerRole.${sig.signer_role}`));
  } else if (reason && tv.has(reason as never)) {
    details.push(tv(reason as never));
  }
  if (sig.page) details.push(t("onPage", { page: sig.page }));
  return (
    <span className={styles.wrap}>
      <span className={styles.badge}>
        <Icon name={icon(sig)} size={13} />
        {text}
      </span>
      {details.length ? <span className={styles.detail}>{details.join(" · ")}</span> : null}
      {UNCHECKED.has(sig.state) ? null : <SourceTag kind="testAnchor" />}
    </span>
  );
}
