"use client";
// StatusLabel: the one component for the six verification labels (Portal spec §2.6.3). Icon,
// sentence-case text and an optional count, in a tinted pill. Never colour alone: the text always
// says the label. In tables the short text is used and the full name opens in a tooltip.
import { useTranslations } from "next-intl";
import { Focusable, Tooltip, TooltipTrigger } from "react-aria-components";
import type { VerificationLabel } from "@satya/shared-types";
import { Icon, type IconName } from "./Icon";
import styles from "./StatusLabel.module.css";

const ICON: Record<VerificationLabel, IconName> = {
  verified: "circle-check",
  mismatch_detected: "circle-x",
  expired: "calendar-x",
  verification_pending: "hourglass",
  source_unavailable: "plug-connected-x",
  manual_review_required: "user-search",
};

export interface StatusLabelProps {
  label: VerificationLabel;
  /** md for the case page and cards, sm for table rows. */
  size?: "md" | "sm";
  count?: number;
  /** Use the short text and show the full name in a tooltip (table rows). */
  short?: boolean;
}

export function StatusLabel({ label, size = "md", count, short = false }: StatusLabelProps) {
  const t = useTranslations("status");
  const full = t(`label.${label}`);
  const text = short ? t(`short.${label}`) : full;
  const zero = count === 0;
  const aria = count === undefined ? undefined : t("countAria", { label: full, count });
  const pill = (
    <span
      className={styles.pill}
      data-label={label}
      data-size={size}
      data-zero={zero ? "true" : undefined}
      aria-label={aria}
      role={aria ? "group" : undefined}
    >
      <Icon name={ICON[label]} />
      <span className={styles.text}>{text}</span>
      {count === undefined ? null : <span className={styles.count}>{count}</span>}
    </span>
  );
  if (!short) return pill;
  return (
    <TooltipTrigger delay={300} closeDelay={0}>
      <Focusable>
        <span className={styles.focus} tabIndex={0}>
          {pill}
        </span>
      </Focusable>
      <Tooltip className={styles.tip} placement="top" offset={6}>
        {full}
      </Tooltip>
    </TooltipTrigger>
  );
}
