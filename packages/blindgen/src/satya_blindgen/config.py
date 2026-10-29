"""blind.config.yaml: seeds, size, minimum clean share."""

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT = Path(__file__).resolve().parents[2] / "blind.config.yaml"


@dataclass(frozen=True)
class BlindConfig:
    seeds: tuple[int, ...]
    applications: int
    clean_fraction_min: float


def load_config(path: Path | None = None, applications: int | None = None) -> BlindConfig:
    raw = yaml.safe_load((path or DEFAULT).read_text("utf-8"))
    return BlindConfig(
        seeds=tuple(int(s) for s in raw["seeds"]),
        applications=int(applications if applications is not None else raw["applications"]),
        clean_fraction_min=float(raw["clean_fraction_min"]),
    )
