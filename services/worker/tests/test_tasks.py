"""Unit tests run tasks eagerly, without a broker."""

from satya_worker.app import _result_url, app
from satya_worker.tasks import daily_sweep, ping


def test_ping_returns_pong() -> None:
    app.conf.task_always_eager = True
    try:
        assert ping.delay().get(timeout=5) == "pong"
    finally:
        app.conf.task_always_eager = False


def test_daily_sweep_is_scheduled_and_inert() -> None:
    assert app.conf.beat_schedule["daily-sweep"]["task"] == "satya.daily_sweep"
    assert daily_sweep() == {"checks_run": 0, "note": "placeholder (slice 0)"}


def test_only_json_is_accepted() -> None:
    assert app.conf.accept_content == ["json"]


def test_results_use_a_separate_database() -> None:
    assert _result_url("redis://:pw@valkey:6379/0") == "redis://:pw@valkey:6379/1"
