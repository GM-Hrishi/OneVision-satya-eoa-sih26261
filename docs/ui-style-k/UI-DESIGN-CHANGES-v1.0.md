# Change list for SATYA-UI-design.md v1.0 (style K)

Apply these to the UI spec when the branch merges. Nothing here changes behaviour, roles or routes that exist.

1. §3.1 Shell: the left rail is retired. Top bar: product mark SATYA, accent dot, EoA; nav per role; plain context text; user menu. Below 1024px the nav is a menu button. The rail alert card is gone; alerts live on the Alerts page. RB nav adds Manual checks and Rules.
2. §3.1 Footer: left, the chain status chip (Chain intact, or Chain broken at entry N, with the entry count); right, the advisory line and the updated date.
3. §4.4 StatusLabel: icon and word in the label ink, no pill and no fill. Same six labels, same six icons.
4. §5 Risk chip: square corners; text caps in Public Sans 800 kept.
5. §8 Design tokens: new `k` palette (desk, paper, hover, ink, muted, rule, accent, red, status inks), `dur` and `ease` groups; Archivo variable for display and body, JetBrains Mono for IDs and labels. All pairs measured in `CONTRAST.md`.
6. §8.9 Mismatch emphasis: unchanged (bold mono red ink on tint). Only mismatch, expired and High carry colour.
7. New page patterns: one plain sentence as the h1; huge condensed numerals for the critical numbers; hairline tables; documents as white paper; numbered pins; the decision strip is the last block of a case view; "What this does not prove" under findings when the API supplies the text.
8. §7.1 Overview: sentence headline, four numerals, Start here band, Next in line table, "Where SATYA sits" paragraph; the existing panels remain below.
9. §7.2 Queue: sentence headline, count per band, Timeline | List switch (List is the default).
10. §7.3 Case: three-column workspace (pinned findings, document as paper, other documents), then Ladder | Map | Journey, then the decision strip.
11. §7.4 Affidavit: sentence headline from the declaration counts, three numerals, Table | Tie lines.
12. New §7.5a Document evidence: `/case/[id]/documents/[docId]`.
13. New §7.6a Manual checks list (`/manual`), without the resolve panel until the backend has the contract.
14. New §7.7a Rules: `/rules` and `/rules/[ruleId]` read only.
15. §7.9 Audit: entry count, chain statement, linked entry blocks, `/audit/integrity`, `/audit/replay` (replay diff).
16. Motion: eight CSS primitives (draw, pop, rise, drop, growx, ping, stamp, flash); played once on first mount; none under reduced motion.
