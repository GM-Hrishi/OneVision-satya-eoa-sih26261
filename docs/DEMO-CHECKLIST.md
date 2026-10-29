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
| Official, Regulation Bureau Southern (overview, queue, case, decisions, audit, alerts) | `rb.southern.demo` |
| Audit user (audit trail only) | `auditor.demo` |
Passwords are in `.env` as `DEMO_USER_PASSWORD`. Do not show `.env` or type the password on camera.

## Screen
- [ ] Browser zoom 100 percent for the queue and case review, 125 percent if the recording is small. Window at least 1280 px wide.
- [ ] Hide bookmarks, other tabs and the address bar history. Close anything that shows a real name, email or institution.
- [ ] Only synthetic names appear: "Demo Institute of Technology NN", "Demo College of Engineering NN", IDs `1-9...`.
- [ ] The mock portal's own banner ("Approval Portal (Mock, for demo)") is visible at least once. The workbench has no banner; its honesty comes from the Simulated source and Test trust anchor tags, so hover one tag on camera.
- [ ] Signing in lands on Overview. Case deep links still open the case.

## OCR engine (B-28), once per laptop and after any rebuild
The cloud session could not download the OCR models, so the real engine was never run there. On the laptop:
- [ ] `make up` builds the api image with `WITH_OCR=1` (the compose default; needs network at build time only). Set `WITH_OCR=0` for a fast build without the engine.
- [ ] Models are baked in: `docker compose --env-file .env -f infra/docker-compose.yml run --rm --no-deps --entrypoint sh api -c 'ls /opt/ocr-models/det /opt/ocr-models/rec'` lists model files.
- [ ] Offline at runtime: stop the network (or `docker network disconnect`) and run `docker compose --env-file .env -f infra/docker-compose.yml exec api python -c "from satya_ocr.engine import PaddleOcrEngine; print(PaddleOcrEngine().available())"`. It prints `True`.
- [ ] Real engine test, from the repo (the tests are not in the image): copy the models out with `docker create --name ocrm satya/api:dev && docker cp ocrm:/opt/ocr-models ./.logs/ocr-models && docker rm ocrm`, then `uv sync --all-packages && uv pip install -r packages/ocr/requirements-ocr.txt && SATYA_OCR_MODEL_DIR=$PWD/.logs/ocr-models uv run pytest packages/ocr/tests/test_real_engine.py -v`. It must not be skipped.
- [ ] After `make demo-reset`, open `1-90000013113`: the affidavit says "read by OCR (confidence NN%)" for every page. Open `1-90000015115`: it says the text is not reliable (OCR_LOW_CONFIDENCE). If both say "not available", the image was built without the engine or the models are missing.
- [ ] Memory: the api container now has 2560 MB (`make mem-check` shows the total under 8 GiB). First OCR after start is slower while the models load.
- [ ] Record what you saw (confidence figures, any misread) in `docs/progress/OCR-SLICE-PROGRESS.md` under "Real engine verification".

## Console and data
- [ ] Open developer tools once: Console shows no errors on overview, queue, case, audit and alerts. Close it before recording.
- [ ] No file from `data/real-samples/` is open anywhere. The repo has none.
- [ ] `make guard` passes.

## After
- [ ] The demo changes state (decisions, picked documents). Run `make demo-reset` again before the next take.
