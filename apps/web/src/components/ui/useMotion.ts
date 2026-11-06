"use client";
// Reduced-motion hook for client components that carry an animation (evidence map, journey, replay, stamp).
import { useCallback, useState, useSyncExternalStore } from "react";
import { motionClass, prefersReducedMotion, type Motion } from "@/lib/motion";

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(onChange: () => void) {
  const mq = window.matchMedia(QUERY);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

/** Server render and first paint report "reduced" (no animation class); the client then reports the real value. */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, () => prefersReducedMotion(), () => true);
}

/** `cls("draw")` gives the animation class or "". `replay()` bumps `runKey`; use it as the component `key`. */
export function useMotion() {
  const reduced = useReducedMotion();
  const [runKey, setRunKey] = useState(0);
  const replay = useCallback(() => setRunKey((k) => k + 1), []);
  const cls = useCallback((name: Motion) => motionClass(name, reduced), [reduced]);
  return { reduced, cls, runKey, replay };
}
