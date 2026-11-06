"use client";
// "How far each document was checked": one section with a segmented switch Ladder | Map | Journey.
// The ladder is server-rendered and passed in; the map and journey are client visuals fed by adapters.
import { useTranslations } from "next-intl";
import { useState, type ReactNode } from "react";
import type { EvidenceGraph } from "@/lib/api/k-adapters/graph";
import type { JourneyRow } from "@/lib/api/k-adapters/journey";
import { EvidenceMap, type MapFinding } from "./EvidenceMap";
import { Journey } from "./Journey";
import { Segmented } from "./Segmented";
import styles from "./Proof.module.css";

type View = "ladder" | "map" | "journey";

export function ProofViews({ caseId, ladder, graph, findings, journey }: { caseId: string; ladder: ReactNode; graph: EvidenceGraph; findings: MapFinding[]; journey: JourneyRow[] }) {
  const t = useTranslations("k");
  const [view, setView] = useState<View>("ladder");
  return (
    <section className={styles.wrap} aria-labelledby="k-proof">
      <h2 id="k-proof" className={styles.title}>
        {t("case.ladderHeading")}
      </h2>
      <div className={styles.bar}>
        <Segmented
          label={t("ladder.viewLabel")}
          value={view}
          onChange={(v) => setView(v as View)}
          options={[
            { id: "ladder", label: t("ladder.viewLadder") },
            { id: "map", label: t("ladder.viewMap") },
            { id: "journey", label: t("ladder.viewJourney") },
          ]}
        />
      </div>
      {view === "ladder" ? ladder : null}
      {view === "map" ? <EvidenceMap graph={graph} findings={findings} caseId={caseId} /> : null}
      {view === "journey" ? <Journey rows={journey} /> : null}
    </section>
  );
}
