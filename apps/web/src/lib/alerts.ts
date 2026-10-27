// Alert helpers: the three display severities (critical = High, warning = Medium, info = Low), the
// order (unread first, then severity, then newest), the seen-alerts cookie and relative time.
import { cookies } from "next/headers";
import type { AlertItem, AlertSeverity } from "./demo-types";

export const SEEN_COOKIE = "satya_seen_alerts";
export const SEEN_MAX = 40;
export const ALERT_KEY = /^[0-9a-f]{12}$/;

export const TONE: Record<AlertSeverity, "high" | "med" | "low"> = { critical: "high", warning: "med", info: "low" };
const RANK: Record<AlertSeverity, number> = { critical: 0, warning: 1, info: 2 };

export function parseSeen(value: string | undefined): string[] {
  return (value ?? "").split(",").filter((k) => ALERT_KEY.test(k)).slice(-SEEN_MAX);
}

export async function seenKeys(): Promise<Set<string>> {
  return new Set(parseSeen((await cookies()).get(SEEN_COOKIE)?.value));
}

export interface RankedAlert {
  alert: AlertItem;
  unread: boolean;
}

/** Unread first, then severity (High before Medium before Low), then newest first. */
export function rankAlerts(items: AlertItem[], seen: Set<string>): RankedAlert[] {
  return items
    .map((alert) => ({ alert, unread: !seen.has(alert.alert_key) }))
    .sort(
      (a, b) =>
        Number(b.unread) - Number(a.unread) ||
        RANK[a.alert.severity] - RANK[b.alert.severity] ||
        b.alert.created_at.localeCompare(a.alert.created_at),
    );
}

export type Ago = { unit: "now" } | { unit: "min" | "hour" | "day"; n: number };

/** Relative age of a timestamp, in whole minutes, hours or days. */
export function ago(iso: string, nowMs: number): Ago {
  const minutes = Math.max(0, Math.floor((nowMs - new Date(iso).getTime()) / 60_000));
  if (minutes < 1) return { unit: "now" };
  if (minutes < 60) return { unit: "min", n: minutes };
  if (minutes < 60 * 24) return { unit: "hour", n: Math.floor(minutes / 60) };
  return { unit: "day", n: Math.floor(minutes / (60 * 24)) };
}

/** The current time in ms, read once per request by server components (kept out of render bodies). */
export const nowMs = (): number => Date.now();
