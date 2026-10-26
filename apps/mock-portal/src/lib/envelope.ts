// Builds a synthetic application.precheck_requested event (Portal spec §2.3, §2.4). The snapshot is
// the shared synthetic example (Demo Institute of Technology 03, AY 2026-27, Southern).
import type { ApplicationSnapshot, EventEnvelope } from "@satya/shared-types";
import snapshotExample from "@satya/shared-types/examples/valid/ApplicationSnapshot.json";
import { ulid } from "./ulid";

let sequence = 0;

export function precheckEnvelope(now: Date = new Date()): EventEnvelope {
  // JSON imports widen tuples; this file is validated against the schema in shared-types tests.
  const snapshot = snapshotExample as unknown as ApplicationSnapshot;
  sequence += 1;
  return {
    spec: "satya.event/1",
    event_id: `evt_${ulid(now.getTime())}`,
    type: "application.precheck_requested",
    occurred_at: now.toISOString(),
    producer: "mock-portal",
    subject: {
      application_id: snapshot.basic.application_id,
      permanent_id: snapshot.basic.permanent_id,
      ay: snapshot.ay,
    },
    sequence,
    correlation_id: `cor_${ulid(now.getTime())}`,
    data: {
      snapshot,
      deficiency_report: snapshot.deficiency_report,
      prior: { eoa_letters: [], snapshot_ref: null },
      documents: [],
    },
  };
}
