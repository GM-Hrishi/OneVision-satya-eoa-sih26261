"use client";
// SourceTag: the honesty marker on data that did not come from a live authority. A small neutral
// tag that opens a tooltip on hover and keyboard focus. It is never hidden behind a filter, and in
// print it becomes plain text. "simulated" for source answers, "testAnchor" for signature chains.
import { useTranslations } from "next-intl";
import { Focusable, Tooltip, TooltipTrigger } from "react-aria-components";
import { Icon } from "./Icon";
import styles from "./SourceTag.module.css";

export type SourceKind = "simulated" | "testAnchor";

export function SourceTag({ kind }: { kind: SourceKind }) {
  const t = useTranslations("source");
  return (
    <>
      <TooltipTrigger delay={300} closeDelay={0}>
        <Focusable>
          <span className={styles.tag} tabIndex={0} data-kind={kind}>
            <Icon name="info-circle" size={12} />
            {t(kind)}
          </span>
        </Focusable>
        <Tooltip className={styles.tip} placement="top" offset={6}>
          {t(`${kind}Tip`)}
        </Tooltip>
      </TooltipTrigger>
      <span className={styles.print}>{t(`${kind}Print`)}</span>
    </>
  );
}
