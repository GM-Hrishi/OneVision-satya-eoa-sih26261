"use client";
// Timeline | List switch for the queue. The list (the existing table with filters and sort) is server-rendered
// and passed in; the timeline is a client visual. Default is the List so URLs and e2e keep their meaning.
import { useTranslations } from "next-intl";
import { useState, type ReactNode } from "react";
import type { Timeline } from "@/lib/api/k-adapters/timeline";
import { QueueTimeline } from "./QueueTimeline";
import { Segmented } from "./Segmented";
import styles from "./QueueTimeline.module.css";

export function QueueViews({ timeline, list }: { timeline: Timeline; list: ReactNode }) {
  const t = useTranslations("k.queue");
  const [view, setView] = useState<"list" | "timeline">("list");
  return (
    <>
      <div className={styles.bar}>
        <Segmented
          label={t("viewLabel")}
          value={view}
          onChange={(v) => setView(v === "timeline" ? "timeline" : "list")}
          options={[
            { id: "timeline", label: t("viewTimeline") },
            { id: "list", label: t("viewList") },
          ]}
        />
      </div>
      {view === "timeline" ? <QueueTimeline timeline={timeline} /> : list}
    </>
  );
}
