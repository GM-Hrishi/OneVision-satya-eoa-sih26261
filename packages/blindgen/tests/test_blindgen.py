"""Blind generator and evaluator: small-N smoke, determinism, independence, tuning guard."""

import ast
import json
import subprocess
from pathlib import Path

import pytest

from satya_blindgen.evaluate import evaluate, manifest_sha
from satya_blindgen.generate import generate

SRC = Path(__file__).resolve().parents[1] / "src" / "satya_blindgen"
REPO = Path(__file__).resolve().parents[3]


def test_small_set_generates_and_reports(tmp_path: Path) -> None:
    root = tmp_path / "set"
    manifest = json.loads(generate(root, (11, 12), 12).read_text("utf-8"))
    apps = manifest["applications"]
    assert len(apps) == 12 and sum(a["clean"] for a in apps) >= 5  # at least 40% clean
    result = evaluate(root, tmp_path / "docs")
    report = (tmp_path / "docs" / "BLIND-REPORT.md").read_text("utf-8")
    assert "Not real AICTE data" in report and manifest_sha(root / "manifest.json") in report
    body = json.loads((tmp_path / "docs" / "blind-results.json").read_text("utf-8"))
    assert body["applications"] == 12 and result["crashes"] == []
    assert "clean applications wrongly flagged" in report.lower()


def test_generation_is_deterministic(tmp_path: Path) -> None:
    a = generate(tmp_path / "a", (5,), 3)
    b = generate(tmp_path / "b", (5,), 3)
    assert manifest_sha(a) == manifest_sha(b)


def test_generator_does_not_import_the_existing_case_definitions() -> None:
    allowed = {"satya_forensics.synth.signing"}
    for path in SRC.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [f"{node.module}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            for name in names:
                if ".synth" in name and not any(name.startswith(a) for a in allowed):
                    pytest.fail(f"{path.name} imports {name}")


def test_blind_results_and_rule_files_do_not_change_in_the_same_commit() -> None:
    """Guard (BR-9): a commit that changes a rule file must not also change blind results."""
    try:
        files = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],  # noqa: S607
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("no git history available")
    rules = [f for f in files if f.startswith("packages/rules/") and f.endswith(".yaml")]
    blind = [f for f in files if f in ("docs/eval/BLIND-REPORT.md", "docs/eval/blind-results.json")]
    assert not (rules and blind), f"rules {rules} changed together with blind results {blind}"
