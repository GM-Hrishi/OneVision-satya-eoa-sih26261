# Documentation index

One line per document. Synthetic data only; advisory only; mock approval portal. Some documents use internal short codes for modules and backlog items (for example M5 or P-3); the backlog in [ISSUES.md](ISSUES.md) explains them.

## Guides and design
- [DEV-SETUP.md](DEV-SETUP.md): local setup on Windows (WSL2), Linux and macOS, trusting the local HTTPS CA, everyday commands.
- [ARCHITECTURE.md](ARCHITECTURE.md): services, networks, signed event path, sign-in path, security layers and the check pipelines.
- [STACK-VERSIONS.md](STACK-VERSIONS.md): pinned versions of every image, tool and library.
- [DEMO-NOTES.md](DEMO-NOTES.md): click path through the synthetic demo cases and what each screen shows.
- [DEMO-CHECKLIST.md](DEMO-CHECKLIST.md): checklist for preparing a demo, including how to verify the OCR engine.
- [SYNTHETIC-TESTSET-PLAN.md](SYNTHETIC-TESTSET-PLAN.md): how each rule is measured on synthetic test sets.
- [ISSUES.md](ISSUES.md): backlog of planned work, generated from `backlog/promises.json`.
- [backlog/promises.json](backlog/promises.json): machine-readable backlog and build priority.

## Specifications
- [specs/VERSIONS.md](specs/VERSIONS.md): which spec versions are copied here and when.
- [specs/00-BUILD-CONTEXT.md](specs/00-BUILD-CONTEXT.md): guard rails, decisions and the promise list.
- [specs/01-design-v2.2.1.md](specs/01-design-v2.2.1.md): core product design.
- [specs/02-problem-statement-SIH26261.md](specs/02-problem-statement-SIH26261.md): the problem statement.
- [specs/03-APH-digest.md](specs/03-APH-digest.md): digest of the Approval Process Handbook 2024-27 clauses used by the rules.
- [specs/04-portal-integration-spec.md](specs/04-portal-integration-spec.md): event, schema and signature contracts for a portal.
- [specs/05-ui-design-spec.md](specs/05-ui-design-spec.md): workbench design system and screens.

## Screenshots
- [screens/ui-polish/](screens/ui-polish/): synthetic workbench screenshots (queue in colour and greyscale, overview in greyscale).

## Progress and decision logs ([progress/](progress/))
- [progress/PROGRESS.md](progress/PROGRESS.md), [PROGRESS-SLICE-1.md](progress/PROGRESS-SLICE-1.md), [PROGRESS-SLICE-2.md](progress/PROGRESS-SLICE-2.md): step tables for the foundation, affidavit comparison and signature work.
- [progress/DEMO-SLICE-PROGRESS.md](progress/DEMO-SLICE-PROGRESS.md): step table for the demo flow.
- [progress/OCR-SLICE-PROGRESS.md](progress/OCR-SLICE-PROGRESS.md): step table for the scan fallback.
- [progress/UI-POLISH-PROGRESS.md](progress/UI-POLISH-PROGRESS.md): step table for the interface polish.
- [progress/DECISIONS-SLICE-0.md](progress/DECISIONS-SLICE-0.md), [DECISIONS-SLICE-1.md](progress/DECISIONS-SLICE-1.md), [DECISIONS-SLICE-2.md](progress/DECISIONS-SLICE-2.md), [DECISIONS-SLICE-D.md](progress/DECISIONS-SLICE-D.md): non-obvious choices for each slice.
- [progress/DECISIONS-OCR-SLICE.md](progress/DECISIONS-OCR-SLICE.md): scan fallback choices, thresholds, dependencies and licences.
- [progress/DECISIONS-UI-POLISH.md](progress/DECISIONS-UI-POLISH.md): interface polish choices.
- [progress/DECISIONS-BLIND-REPLAY.md](progress/DECISIONS-BLIND-REPLAY.md): choices for the independent test-set generator and case replay.
- [progress/DEFERRED.md](progress/DEFERRED.md): ideas and known defects kept out of scope on purpose.

Some progress and decision logs link to documents that are not part of this repository; those links do not resolve.
