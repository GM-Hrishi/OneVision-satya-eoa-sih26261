// Style K motion helpers (prompt section 5). Pure, so they are unit-tested without a DOM.
// A view plays its motion once, on first mount. Under prefers-reduced-motion no animation class is
// produced at all, so the final state is the only state.
export const MOTIONS = ["draw", "pop", "rise", "drop", "growx", "ping", "stamp", "flash"] as const;
export type Motion = (typeof MOTIONS)[number];

/** Total stagger allowed on one view (seconds). */
export const MAX_STAGGER_S = 2.6;

export interface MatchMediaLike {
  matchMedia?: (query: string) => { matches: boolean };
}

/** True when the user asked for reduced motion. Without a browser (server render) animation is off. */
export function prefersReducedMotion(win?: MatchMediaLike): boolean {
  const w = win ?? (typeof window === "undefined" ? undefined : (window as MatchMediaLike));
  if (!w?.matchMedia) return true;
  return w.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Class name for an animation, or "" when motion is off. */
export function motionClass(name: Motion, reduced: boolean): string {
  return reduced ? "" : `m-${name}`;
}

/** Stagger delay for item i of n, spread so the whole sequence never exceeds MAX_STAGGER_S. */
export function staggerDelay(index: number, count: number, stepS = 0.12): string {
  if (count <= 1) return "0s";
  const step = Math.min(stepS, MAX_STAGGER_S / (count - 1));
  return `${(index * step).toFixed(2)}s`;
}
