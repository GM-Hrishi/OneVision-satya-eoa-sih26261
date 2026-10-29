// Local inline icons in the Tabler outline style (24px grid, 2px stroke, round caps). No icon
// library: only the shapes this build uses. Always decorative (aria-hidden); text carries meaning.
import type { ReactNode } from "react";

const CIRCLE = "M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0";
const SHIELD = "M11.46 20.846a12 12 0 0 1 -7.96 -14.846a12 12 0 0 0 8.5 -3a12 12 0 0 0 8.5 3a12 12 0 0 1 -.09 7.06";
const SIGN = "M3 17c3.333 -3.333 5 -6 5 -8c0 -3 -1 -3 -2 -3s-2.032 1.085 -2 3c.034 2.048 1.658 4.877 2.5 6c1.5 2 2.5 2.5 3.5 1l2 -3c.333 2.667 1.333 4 3 4c.53 0 2.639 -2 3 -2c.517 0 1.517 .667 3 2";

const PATHS = {
  "circle-check": [CIRCLE, "M9 12l2 2l4 -4"],
  "circle-x": [CIRCLE, "M10 10l4 4m0 -4l-4 4"],
  "calendar-x": [
    "M13 21h-7a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v7",
    "M16 3v4",
    "M8 3v4",
    "M4 11h16",
    "M22 22l-5 -5",
    "M17 22l5 -5",
  ],
  hourglass: [
    "M6.5 7h11",
    "M6.5 17h11",
    "M6 20v-2a6 6 0 1 1 12 0v2a1 1 0 0 1 -1 1h-10a1 1 0 0 1 -1 -1z",
    "M6 4v2a6 6 0 1 0 12 0v-2a1 1 0 0 0 -1 -1h-10a1 1 0 0 0 -1 1z",
  ],
  "plug-connected-x": [
    "M7 12l5 5l-1.5 1.5a3.536 3.536 0 1 1 -5 -5l1.5 -1.5z",
    "M17 12l-5 -5l1.5 -1.5a3.536 3.536 0 1 1 5 5l-1.5 1.5z",
    "M3 21l2.5 -2.5",
    "M18.5 5.5l2.5 -2.5",
    "M10 11l-2 2",
    "M13 14l-2 2",
    "M16 16l5 5",
    "M21 16l-5 5",
  ],
  "user-search": ["M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0", "M6 21v-2a4 4 0 0 1 4 -4h1", "M15 18a3 3 0 1 0 6 0a3 3 0 1 0 -6 0", "M20.2 20.2l1.8 1.8"],
  "shield-check": [SHIELD, "M15 19l2 2l4 -4"],
  "shield-x": [SHIELD, "M22 22l-5 -5", "M17 22l5 -5"],
  photo: [
    "M15 8h.01",
    "M3 6a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v12a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3v-12z",
    "M3 16l5 -5c.928 -.893 2.072 -.893 3 0l5 5",
    "M14 14l1 -1c.928 -.893 2.072 -.893 3 0l3 3",
  ],
  "writing-sign": ["M3 19c3.333 -2 5 -4 5 -6c0 -3 -1 -3 -2 -3s-2.032 1.085 -2 3c.034 2.048 1.658 2.877 2.5 4c1.5 2 2.5 2.5 3.5 1l2 -3c.333 2.667 1.333 4 3 4c.53 0 2.639 -2 3 -2c.517 0 1.517 .667 3 2", "M3 21h18"],
  signature: [SIGN, "M3 21h18"],
  "signature-off": [SIGN, "M3 3l18 18"],
  "info-circle": [CIRCLE, "M12 9h.01", "M11 12h1v4h1"],
  "alert-circle": [CIRCLE, "M12 8v4", "M12 16h.01"],
  "alert-triangle": ["M12 9v4", "M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z", "M12 16h.01"],
  "chevron-down": ["M6 9l6 6l6 -6"],
  check: ["M5 12l5 5l10 -10"],
} as const satisfies Record<string, readonly string[]>;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 14 }: { name: IconName; size?: number }): ReactNode {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ flex: "none" }}
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
