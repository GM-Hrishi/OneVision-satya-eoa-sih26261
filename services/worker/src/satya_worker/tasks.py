"""Worker tasks. Slice 0: ping and the daily-sweep placeholder only."""

import logging

from satya_worker.app import app

log = logging.getLogger("satya.worker")


@app.task(name="satya.ping")
def ping() -> str:
    return "pong"


@app.task(name="satya.daily_sweep")
def daily_sweep() -> dict[str, object]:
    # TODO(P-7, P-8, P-11): expiry sweeps, compliance windows, trust-anchor re-validation,
    # 30-day dedupe purge. No logic in slice 0.
    log.info("daily sweep placeholder ran; no checks implemented yet")
    return {"checks_run": 0, "note": "placeholder (slice 0)"}
