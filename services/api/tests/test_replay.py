"""Deterministic replay (P-11): GET /v1/cases/{id}/replay, ledger records, tamper detection.

Synthetic data only. The archived rule pack is built in a temp folder from the current files.
"""

import dataclasses
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from satya_api.auth import TokenVerifier
from satya_api.cases import FixtureCaseRepository
from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.rulepacks import current_pack
from satya_api.store import MemoryStore

from .test_workbench_api import (
    CASES,
    DCE05,
    DIT03,
    ISSUER,
    TOKEN_KEY,
    _jwks,
    _ok,
    auth,
    token,
)

RULES = CASES.parents[2] / "packages" / "rules"
SEEDED = [p.name for p in sorted(CASES.iterdir())]
OLD_PACK = "m5-affidavit@0.0.9+m6-signatures@0.1.0"
PACK = current_pack().pack_id


class Harness:
    def __init__(self, client: TestClient, store: MemoryStore, cases_dir: Path) -> None:
        self.client, self.store, self.cases_dir = client, store, cases_dir

    def check(self, case_id: str) -> None:
        flow = self.client.app.state.workflow  # type: ignore[attr-defined]
        self.client.portal.call(flow.record_check, case_id, "tester", "seed")  # type: ignore[union-attr]

    def replay(self, case_id: str, version: str | None = None, **kw: Any) -> Any:
        params = {"rule_version": version} if version else None
        url = f"/v1/cases/{case_id}/replay"
        return self.client.get(url, params=params, headers=kw.pop("headers", auth(token())))


def _archive(root: Path) -> Path:
    """An older rule pack: M5 0.0.9 with AFF-DECL-CHANGED rated as a warning (version 0.0.9)."""
    folder = root / OLD_PACK
    folder.mkdir(parents=True)
    m5 = (RULES / "m5-affidavit.yaml").read_text("utf-8")
    m5 = re.sub(r'^version: "0.1.0"', 'version: "0.0.9"', m5, count=1, flags=re.M)
    block = re.search(r"(  - rule_id: AFF-DECL-CHANGED\n.*?)(?=\n  - rule_id:)", m5, re.S)
    assert block
    old = block.group(1).replace("severity: critical", "severity: warning")
    old = old.replace('version: "0.1.0"', 'version: "0.0.9"')
    (folder / "m5-affidavit.yaml").write_text(m5.replace(block.group(1), old), "utf-8")
    shutil.copy(RULES / "m6-signatures.yaml", folder / "m6-signatures.yaml")
    return root


@pytest.fixture
def h(tmp_path: Path) -> Iterator[Harness]:
    data = tmp_path / "synthetic"
    shutil.copytree(CASES.parent, data)
    store = MemoryStore()

    async def fetch() -> dict:  # type: ignore[type-arg]
        return _jwks()

    settings = Settings(
        env="test",
        rate_limit="1000/minute",
        user_rate_limit="1000/minute",
        replay_rate_limit="1000/minute",
        upload_dir=str(tmp_path / "uploads"),
        rules_archive_dir=str(_archive(tmp_path / "archive")),
    )
    app = create_app(
        settings,
        store=store,
        checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
        cases=FixtureCaseRepository(data / "cases", TOKEN_KEY),
        verifier=TokenVerifier(ISSUER, "satya-web", fetch),
    )
    with TestClient(app) as client:
        yield Harness(client, store, data / "cases")


def _case_ids() -> list[str]:
    import json

    return [json.loads((CASES / d / "case.json").read_text())["case_id"] for d in SEEDED]


@pytest.mark.parametrize("case_id", _case_ids())
def test_replay_at_original_version_is_identical(h: Harness, case_id: str) -> None:
    h.check(case_id)
    body = h.replay(case_id).json()
    assert body["reproducible"] is True and body["reasons"] == []
    assert body["identical_to_original"] is True
    assert body["rule_version"] == body["original"]["rule_version"] == PACK
    assert body["replayed_flags"] == body["original_flags"]
    assert body["diff"] == {"added": [], "removed": [], "changed": []}
    assert body["advisory"] is True and body["regulatory_effect"] == "none"


def test_check_run_records_rule_pack_flags_and_hashes(h: Harness) -> None:
    h.check(DIT03)
    row = next(r for r in h.store.rows if r.event_type == "check.run")
    import json

    d = json.loads(row.detail_json or "")["detail"]
    assert d["rule_pack"] == PACK and d["engines"]["ruleset_m5"].startswith("m5-affidavit@")
    assert len(d["flags"]) == 7 and all(f["rule_version"] for f in d["flags"])
    assert d["doc_hashes"] and d["checked_at"] and "source_responses" in d


def test_replay_at_older_rule_version_diffs_the_changed_rule(h: Harness) -> None:
    h.check(DIT03)
    body = h.replay(DIT03, OLD_PACK).json()
    assert body["reproducible"] is True and body["identical_to_original"] is False
    changed = body["diff"]["changed"]
    assert changed and {c["rule_id"] for c in changed} == {"AFF-DECL-CHANGED"}
    c = changed[0]
    assert c["fields"] == ["rule_version", "severity"]
    assert c["original"]["severity"] == "critical" and c["replayed"]["severity"] == "warning"
    assert c["evidence"]["doc_id"] and c["evidence"]["evidence_sha256"]
    assert body["diff"]["added"] == [] and body["diff"]["removed"] == []
    # a case without that rule is untouched
    h.check(DCE05)
    assert h.replay(DCE05, OLD_PACK).json()["diff"]["changed"] == []


def test_replay_writes_one_ledger_entry_and_nothing_else(h: Harness) -> None:
    h.check(DCE05)
    before = len(h.store.rows)
    h.replay(DCE05)
    assert len(h.store.rows) == before + 1
    row = h.store.rows[-1]
    assert row.event_type == "case.replay" and row.actor == "user-rb-southern-demo"


def test_tampered_document_is_hash_mismatch_not_500(h: Harness) -> None:
    h.check(DIT03)
    meta = h.cases_dir / "dit03-2026-27" / "affidavit-sworn.pdf"
    meta.write_bytes(meta.read_bytes() + b"\n%tampered")
    res = h.replay(DIT03)
    assert res.status_code == 200
    body = res.json()
    assert body["reproducible"] is False
    assert body["reasons"][0]["code"] == "HASH_MISMATCH" and body["reasons"][0]["ref"].startswith(
        "doc_"
    )


def test_broken_ledger_chain_is_hash_mismatch(h: Harness) -> None:
    h.check(DCE05)
    rows = h.store.rows
    rows[0] = dataclasses.replace(rows[0], hash="f" * 64)
    res = h.replay(DCE05)
    assert res.status_code == 200
    body = res.json()
    assert body["reproducible"] is False
    assert body["reasons"][0] == {"code": "HASH_MISMATCH", "ref": "ledger:1"}


def test_case_without_a_recorded_run_and_old_records_are_not_replayable(h: Harness) -> None:
    body = h.replay(DCE05).json()
    assert body["reproducible"] is False and body["reasons"][0]["code"] == "NO_ORIGINAL_RECORD"
    # a check.run written before rule packs were recorded reads as unknown
    flow = h.client.app.state.workflow  # type: ignore[attr-defined]
    h.client.portal.call(  # type: ignore[union-attr]
        flow.store.append, "check.run", DCE05, "old", {"trigger": "seed", "engines": {}}
    )
    body = h.replay(DCE05).json()
    assert body["original"]["rule_version"] == "unknown"
    assert body["reasons"][0]["code"] == "ORIGINAL_UNKNOWN" and body["replayed_flags"] == []


def test_access_control_and_parameter_validation(h: Harness) -> None:
    h.check(DCE05)
    url = f"/v1/cases/{DCE05}/replay"
    assert h.client.get(url).status_code == 401
    assert h.client.get(url, headers=auth(token(roles=["INS"]))).status_code == 403
    assert h.client.get(url, headers=auth(token(groups=["/regions/northern"]))).status_code == 403
    assert h.client.get("/v1/cases/not-a-case/replay", headers=auth(token())).status_code == 404
    for bad in ("../../etc/passwd", "m5-affidavit@9.9.9+m6-signatures@9.9.9", "x" * 500):
        res = h.client.get(url, params={"rule_version": bad}, headers=auth(token()))
        assert res.status_code == 422 and "etc" not in res.text
    assert h.client.post(url, headers=auth(token())).status_code == 405


def test_replay_is_rate_limited(tmp_path: Path) -> None:
    async def fetch() -> dict:  # type: ignore[type-arg]
        return _jwks()

    app = create_app(
        Settings(
            env="test",
            rate_limit="1000/minute",
            user_rate_limit="1000/minute",
            replay_rate_limit="2/minute",
            rules_archive_dir=str(tmp_path),
        ),
        store=MemoryStore(),
        checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
        cases=FixtureCaseRepository(CASES, TOKEN_KEY),
        verifier=TokenVerifier(ISSUER, "satya-web", fetch),
    )
    with TestClient(app) as client:
        codes = [
            client.get(f"/v1/cases/{DCE05}/replay", headers=auth(token())).status_code
            for _ in range(3)
        ]
    assert codes[:2] != [429, 429] and codes[-1] == 429
