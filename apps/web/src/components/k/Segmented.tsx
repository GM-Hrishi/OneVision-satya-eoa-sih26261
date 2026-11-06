"use client";
// Segmented control: a square ink-bordered group built on the React Aria radio group (real radio
// semantics, arrow-key navigation). The selected item is filled ink with white text.
import { Label, Radio, RadioGroup } from "react-aria-components";
import styles from "./K.module.css";

export interface SegmentedOption {
  id: string;
  label: string;
}

export interface SegmentedProps {
  label: string;
  options: SegmentedOption[];
  value: string;
  onChange: (id: string) => void;
  /** Hide the visible label (it stays for screen readers). */
  hideLabel?: boolean;
  name?: string;
}

export function Segmented({ label, options, value, onChange, hideLabel = false, name }: SegmentedProps) {
  return (
    <RadioGroup className={styles.seg} value={value} onChange={onChange} orientation="horizontal" name={name}>
      <Label className={hideLabel ? "visually-hidden" : `k-label ${styles.segLabel}`}>{label}</Label>
      <div className={styles.segGroup}>
        {options.map((o) => (
          <Radio key={o.id} value={o.id} className={styles.segItem}>
            {o.label}
          </Radio>
        ))}
      </div>
    </RadioGroup>
  );
}
