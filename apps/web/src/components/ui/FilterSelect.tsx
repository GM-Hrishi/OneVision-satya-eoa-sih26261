"use client";
// Styled select for the queue filters (B-31): React Aria Select with a button, popover and list box.
// It submits through a hidden input, so the surrounding GET form and the query parameters keep working.
import { useState } from "react";
import { Button, Label, ListBox, ListBoxItem, Popover, Select, SelectValue } from "react-aria-components";
import { Icon } from "@/components/ui/Icon";
import styles from "./FilterSelect.module.css";

const ALL = "__all__";

export interface FilterOption {
  value: string;
  label: string;
}

export function FilterSelect({
  name,
  label,
  value,
  options,
  testId,
}: {
  name: string;
  label: string;
  value: string;
  /** First option is the "all" entry with value "". */
  options: FilterOption[];
  testId?: string;
}) {
  const [selected, setSelected] = useState(value || ALL);
  const key = (v: string) => v || ALL;
  const current = selected === ALL ? "" : selected;
  return (
    <Select
      className={styles.select}
      selectedKey={selected}
      onSelectionChange={(k) => setSelected(String(k))}
      data-testid={testId}
    >
      <Label className={styles.label}>{label}</Label>
      <input type="hidden" name={name} value={current} />
      <Button className={styles.button} data-testid={testId ? `${testId}-button` : undefined}>
        <SelectValue className={styles.value} />
        <span className={styles.chevron}>
          <Icon name="chevron-down" size={16} />
        </span>
      </Button>
      <Popover className={styles.popover}>
        <ListBox className={styles.list}>
          {options.map((o) => (
            <ListBoxItem key={key(o.value)} id={key(o.value)} textValue={o.label} className={styles.item}>
              {({ isSelected }) => (
                <>
                  <span className={styles.check}>{isSelected ? <Icon name="check" size={16} /> : null}</span>
                  <span>{o.label}</span>
                </>
              )}
            </ListBoxItem>
          ))}
        </ListBox>
      </Popover>
    </Select>
  );
}
