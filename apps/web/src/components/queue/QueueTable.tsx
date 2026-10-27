"use client";
// The validation queue table (RB-02) on React Aria Table. Sortable columns: Application, Awaiting,
// Submitted, Last activity. Sorting changes the URL, the server asks the API for the new order (risk
// band groups stay first, the sort applies inside each group) and a polite live region says what
// changed. Cell content is rendered on the server and passed in, so this file only holds the table
// behaviour.
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Cell, Column, Row, Table, TableBody, TableHeader, type SortDescriptor } from "react-aria-components";
import { SortIndicator } from "@/components/ui/SortIndicator";
import type { SortDir, SortKey } from "@/lib/demo-types";
import styles from "./QueueTable.module.css";

export interface QueueTableRow {
  id: string;
  band: ReactNode;
  application: ReactNode;
  labels: ReactNode;
  awaiting: ReactNode;
  submitted: ReactNode;
  last: ReactNode;
  status: ReactNode;
  reasons: ReactNode;
  open: ReactNode;
}

export interface QueueTableText {
  caption: string;
  band: string;
  application: string;
  labels: string;
  awaiting: string;
  submitted: string;
  last: string;
  status: string;
  reasons: string;
  open: string;
  /** "Sorted by {column}, {dir}" with {column} and {dir} replaced here. */
  announce: string;
  ascending: string;
  descending: string;
}

const SORT_COLUMN: Record<string, SortKey> = {
  application: "application_id",
  awaiting: "undisposed_flags",
  submitted: "submitted_at",
  last: "last_activity_at",
};
const COLUMN_OF = Object.fromEntries(Object.entries(SORT_COLUMN).map(([column, key]) => [key, column])) as Record<SortKey, string>;

export function QueueTable({ rows, text, sort }: { rows: QueueTableRow[]; text: QueueTableText; sort: { key: SortKey; dir: SortDir } | null }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [announcement, setAnnouncement] = useState("");
  const descriptor: SortDescriptor | undefined = sort
    ? { column: COLUMN_OF[sort.key], direction: sort.dir === "asc" ? "ascending" : "descending" }
    : undefined;

  const onSortChange = (next: SortDescriptor) => {
    const key = SORT_COLUMN[String(next.column)];
    if (!key) return;
    const dir: SortDir = next.direction === "descending" ? "desc" : "asc";
    const url = new URLSearchParams(params.toString());
    url.set("sort", key);
    url.set("dir", dir);
    const name = text[String(next.column) as keyof QueueTableText];
    setAnnouncement(
      text.announce.replace("{column}", name).replace("{dir}", dir === "asc" ? text.ascending : text.descending),
    );
    router.replace(`${pathname}?${url.toString()}`, { scroll: false });
  };

  const sortable = (id: keyof typeof SORT_COLUMN, label: string, rowHeader = false) => (
    <Column id={id} allowsSorting isRowHeader={rowHeader} className={styles.th}>
      {({ sortDirection }) => (
        <span className={styles.head}>
          {label}
          <SortIndicator direction={sortDirection} />
        </span>
      )}
    </Column>
  );
  const plain = (id: string, label: string) => (
    <Column id={id} className={styles.th}>
      <span className={styles.head}>{label}</span>
    </Column>
  );

  return (
    <div className={styles.wrap}>
      <Table aria-label={text.caption} className={styles.table} sortDescriptor={descriptor} onSortChange={onSortChange}>
        <TableHeader>
          {plain("band", text.band)}
          {sortable("application", text.application, true)}
          {plain("labels", text.labels)}
          {sortable("awaiting", text.awaiting)}
          {sortable("submitted", text.submitted)}
          {sortable("last", text.last)}
          {plain("status", text.status)}
          {plain("reasons", text.reasons)}
          {plain("open", text.open)}
        </TableHeader>
        <TableBody items={rows}>
          {(row) => (
            <Row id={row.id} className={styles.row}>
              <Cell className={styles.td}>{row.band}</Cell>
              <Cell className={`${styles.td} ${styles.nowrap}`}>{row.application}</Cell>
              <Cell className={styles.td}>{row.labels}</Cell>
              <Cell className={`${styles.td} ${styles.num}`}>{row.awaiting}</Cell>
              <Cell className={styles.td}>{row.submitted}</Cell>
              <Cell className={styles.td}>{row.last}</Cell>
              <Cell className={styles.td}>{row.status}</Cell>
              <Cell className={styles.td}>{row.reasons}</Cell>
              <Cell className={`${styles.td} ${styles.nowrap}`}>{row.open}</Cell>
            </Row>
          )}
        </TableBody>
      </Table>
      <div className={styles.live} role="status" aria-live="polite">
        {announcement}
      </div>
    </div>
  );
}

