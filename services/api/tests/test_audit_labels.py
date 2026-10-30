"""D5 of B-43: every ledger event kind the API can write has a plain label in the workbench."""

import ast
import json
import re
from pathlib import Path

from satya_api import replay, workflow
from satya_shared_types import constants

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "services" / "api" / "src" / "satya_api"
KIND = re.compile(r"^[a-z]+(\.[a-z_]+)$")


def _kind_constants(path: Path) -> set[str]:
    """Module-level string constants shaped like an event kind (`document.uploaded`)."""
    out: set[str] = set()
    for node in ast.parse(path.read_text("utf-8")).body:
        if isinstance(node, ast.Assign) and not isinstance(node.value, ast.Call):
            for value in ast.walk(node.value):
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and KIND.match(value.value)
                    and value.value != "seed.demo"
                ):
                    out.add(value.value)
    return out


def _written_kinds() -> set[str]:
    kinds = {
        workflow.UPLOADED,
        workflow.CHECKED,
        workflow.SOURCE,
        workflow.TASK,
        workflow.DISPOSED,
        workflow.READ,
        workflow.NOTE,
        replay.REPLAYED,
        *constants.INBOUND_EVENT_TYPES,
    }
    # a new constant in the API modules must be labelled too
    for name in ("workflow.py", "replay.py"):
        kinds |= _kind_constants(SRC / name)
    return kinds


def test_every_event_kind_has_an_english_and_a_hindi_label() -> None:
    kinds = _written_kinds()
    assert len(kinds) >= 25
    for locale in ("en", "hi"):
        messages = json.loads(
            (ROOT / "apps" / "web" / "messages" / f"{locale}.json").read_text("utf-8")
        )
        labels = messages["demo"]["audit"]["event"]
        for kind in sorted(kinds):
            key = kind.replace(".", "_")
            assert labels.get(key, "").strip(), f"no {locale} label for the ledger event {kind}"
