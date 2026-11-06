"use client";
// Table | Tie lines switch on the affidavit page. The table is the existing server-rendered DiffView, passed in.
import { useTranslations } from "next-intl";
import { useState, type ReactNode } from "react";
import type { TieRow } from "@/lib/api/k-adapters/affidavit";
import { Segmented } from "./Segmented";
import { TieLines } from "./TieLines";
import styles from "./Tie.module.css";

export function AffidavitViews({ table, rows, compared }: { table: ReactNode; rows: TieRow[]; compared: boolean }) {
  const t = useTranslations("k.affidavit");
  const [view, setView] = useState<"table" | "tie">("table");
  return (
    <>
      <div className={styles.bar}>
        <Segmented
          label={t("viewLabel")}
          value={view}
          onChange={(v) => setView(v === "tie" ? "tie" : "table")}
          options={[
            { id: "table", label: t("viewTable") },
            { id: "tie", label: t("viewTie") },
          ]}
        />
      </div>
      {view === "table" ? table : <TieLines rows={rows} compared={compared} onUseTable={() => setView("table")} />}
    </>
  );
}
