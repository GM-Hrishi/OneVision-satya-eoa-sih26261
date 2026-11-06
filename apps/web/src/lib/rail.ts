// Left-rail destinations per role (UI spec §3.1). Only screens that exist in this build are listed,
// so there is no dead navigation; P1 screens join as their slices land, P2 screens stay hidden.
import type { Role } from "./auth";

export interface RailItem {
  href: string;
  labelKey: string; // key in the "nav" namespace
}

const RB: RailItem[] = [
  { href: "/overview", labelKey: "overview" },
  { href: "/rb-queue", labelKey: "queue" },
  { href: "/manual", labelKey: "manual" },
  { href: "/alerts", labelKey: "alerts" },
  { href: "/rules", labelKey: "rules" },
  { href: "/audit", labelKey: "audit" },
  // P2 hidden: evc-selection, monitoring.
];
const AU: RailItem[] = [{ href: "/audit", labelKey: "audit" }];

export const RAIL: Partial<Record<Role, RailItem[]>> = { RB, AU };

export const UTILITY: RailItem[] = [{ href: "/help", labelKey: "help" }];

export interface Crumb {
  labelKey: string; // key in the "nav" namespace
  href?: string; // set for ancestors that are real pages; the last crumb is the current page
}

/** Breadcrumb trail for a path: fixed routes from CRUMBS, case routes by pattern. */
export function crumbsFor(pathname: string): Crumb[] {
  const docView = /^\/case\/([^/]+)\/documents\/[^/]+$/.exec(pathname);
  if (docView?.[1]) return [{ labelKey: "queue", href: "/rb-queue" }, { labelKey: "caseOverview", href: `/case/${docView[1]}` }, { labelKey: "documentEvidence" }];
  const caseView = /^\/case\/[^/]+\/(affidavit|verification|upload)$/.exec(pathname);
  if (caseView?.[1]) {
    return [{ labelKey: "queue", href: "/rb-queue" }, { labelKey: caseView[1] }];
  }
  if (/^\/case\/[^/]+$/.test(pathname)) return [{ labelKey: "queue", href: "/rb-queue" }, { labelKey: "caseOverview" }];
  const rule = /^\/rules\/[^/]+$/.exec(pathname);
  if (rule) return [{ labelKey: "rules", href: "/rules" }, { labelKey: "ruleDetail" }];
  const audit = /^\/audit\/(replay|integrity)$/.exec(pathname);
  if (audit?.[1]) return [{ labelKey: "audit", href: "/audit" }, { labelKey: audit[1] === "replay" ? "auditReplay" : "auditIntegrity" }];
  const keys = CRUMBS[pathname] ?? [];
  return keys.map((labelKey) => ({ labelKey }));
}

/** Breadcrumb trail labels (nav namespace) for each route. */
export const CRUMBS: Record<string, string[]> = {
  "/overview": ["overview"],
  "/rb-queue": ["queue"],
  "/manual": ["manual"],
  "/rules": ["rules"],
  "/alerts": ["alerts"],
  "/audit": ["audit"],
  "/help": ["help"],
  "/accessibility": ["accessibility"],
  "/about": ["about"],
  "/policies": ["policies"],
  "/sitemap": ["sitemap"],
  "/signin": ["signin"],
  "/home": ["roleHome"],
};
