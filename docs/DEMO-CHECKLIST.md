# Demo checklist (before every recording)

## Start
- [ ] `make up` is healthy (`make ps`), then `make demo-reset` finished with "Demo reset" and `chain ok`.
- [ ] The local HTTPS root is trusted (`make trust-ca`, DEV-SETUP). No certificate warning in the browser.
- [ ] Use a normal browser profile on default settings. No flags, no extensions that block workers or scripts.

## Addresses and users
| What | Where |
|---|---|
| Workbench | https://localhost |
| API health | https://localhost/api/v1/health |
| Mock portal | https://portal.localhost |
| Keycloak (sign-in only) | https://auth.localhost |
| Official, Regulation Bureau Southern (queue, case, decisions, audit, alerts) | `rb.southern.demo` |
| Audit user (audit trail only) | `auditor.demo` |
Passwords are in `.env` as `DEMO_USER_PASSWORD`. Do not show `.env` or type the password on camera.

## Screen
- [ ] Browser zoom 100 percent for the queue and case review, 125 percent if the recording is small. Window at least 1280 px wide.
- [ ] Hide bookmarks, other tabs and the address bar history. Close anything that shows a real name, email or institution.
- [ ] Only synthetic names appear: "Demo Institute of Technology NN", "Demo College of Engineering NN", IDs `1-9...`.
- [ ] The strip "Prototype · connected to a mock approval portal · synthetic data only" is visible at least once.

## Console and data
- [ ] Open developer tools once: Console shows no errors on queue, case, audit and alerts. Close it before recording.
- [ ] No file from `data/real-samples/` is open anywhere. The repo has none.
- [ ] `make guard` passes.

## After
- [ ] The demo changes state (decisions, picked documents). Run `make demo-reset` again before the next take.
