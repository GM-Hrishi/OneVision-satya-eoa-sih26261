"""Where template profiles and rule files live.

`SATYA_TEMPLATES_DIR` / `SATYA_RULES_DIR` win (the container image sets them); otherwise the repo's
packages/templates and packages/rules are found by walking up from this file (dev and tests).
"""

import os
from pathlib import Path


def _repo_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "packages" / name
        if candidate.is_dir() and (parent / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(f"packages/{name} not found; set SATYA_{name.upper()}_DIR")


def templates_dir() -> Path:
    env = os.environ.get("SATYA_TEMPLATES_DIR")
    return Path(env) if env else _repo_dir("templates")


def rules_dir() -> Path:
    env = os.environ.get("SATYA_RULES_DIR")
    return Path(env) if env else _repo_dir("rules")
