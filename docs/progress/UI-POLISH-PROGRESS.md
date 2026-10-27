# UI polish v0.8 progress

Branch `ui-polish`. Mark `[x]` with one line on what changed.

- [x] 1. Tokens: add v0.8 tokens, remove prototype-strip tokens. Added `raw` token group (unprefixed names) to tokens.json + generator; removed prototype-strip tokens and their hex from the spec §8 summary line.
- [x] 2. StatusLabel component + i18n keys + unit tests; replace every status chip. Added Icon, StatusLabel (client, tooltip on short form), status.* i18n, unit tests; replaced chips in queue, case page, verification panel, FlagCard, stamp. Alerts follow in step 8.
- [x] 3. SignatureBadge neutral restyle. Neutral pill with Tabler-style icon and sentence-case text, new signature.* copy.
- [x] 4. SourceTag component; place everywhere; remove MOCK / TEST TRUST ANCHOR strings. SourceTag (client, tooltip, print text) in panel, FlagCard, viewer bar, audit rows, case page, SignatureBadge; all MOCK SOURCE / TEST TRUST ANCHOR strings removed from web and API copy. Alerts and Overview tags follow in steps 8 and 10.
- [x] 5. Sortable headers (SortIndicator, aria-sort, announcement, sort within band, API sort params, Reset sort). React Aria Table queue, SortIndicator, aria-sort, live announcement, API sort/dir with echo and tests, Reset sort. Also covers the filter half of step 11.
- [x] 6. Header context text + UserMenu; remove prototype strip and old chips and links. New AppShell header (context text, search by application ID or institution, UserMenu with language, accessibility, sign out), prototype strip, chips and rail language links removed.
- [x] 7. One-line footer; remove all "prototype" strings. One-line footer done in step 6; reworded every prototype/mock/demo string in en and hi, added a messages test that bans those words and em dashes.
- [x] 8. Alerts page severity cards + rail notification card. AlertCard (tint, full border, icon, severity word), grouped unread first, rail card, seen cookie, API alert fields and tests.
- [x] 9. API `GET /v1/overview` + tests. Endpoint, quota, whitelists, scoping, 5 tests.
- [x] 10. `/overview` page, default landing, rail entry, remove ?view=overview. /overview page (7 sections, skeleton, layout role check), / redirects RB there, rail entry, sitemap, ?view=overview removed.
- [x] 11. Queue filters from Overview links. band, label, status (and q) accepted by the queue and linked from Overview; done with step 5.
- [x] 12. Update tests and docs (tests/e2e, DEMO-NOTES, DEMO-CHECKLIST). All five scripts updated, new tests/e2e/polish.cjs added to make e2e, DEMO-NOTES, DEMO-CHECKLIST, DEMO-SCRIPT, README, CLAUDE.md updated. Verified against a local harness (real API app on fixtures plus a built web app with a session cookie); Keycloak login, sign-out and institution 403 steps can only run in CI.
- [x] 13. Checks: keyboard, axe, greyscale screenshot, greps, full suite. axe (wcag2a, 2aa, 21a, 21aa, best-practice) zero violations on overview, queue, sorted queue, case, verification, affidavit, alerts, audit, help, accessibility; keyboard pass in polish.cjs; greyscale shots in docs/screens/ui-polish; greps clean; lint, typecheck, make test, synth-check, guard green.
- [ ] 14. Open the pull request (not merged); watch CI.
