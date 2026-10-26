"""Enqueue ping on the running stack. Run with `make smoke` (worker-test container on the
compose network) or with SATYA_VALKEY_URL pointing at a reachable Valkey and a running worker."""

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.environ.get("SATYA_VALKEY_URL"), reason="needs SATYA_VALKEY_URL")
def test_ping_round_trip_through_valkey() -> None:
    from satya_worker.tasks import ping

    assert ping.delay().get(timeout=30) == "pong"
