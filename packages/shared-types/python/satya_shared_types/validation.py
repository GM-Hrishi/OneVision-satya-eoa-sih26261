"""JSON Schema validation against the generated contract bundle (source of truth: schemas/)."""

import json
from functools import cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


@cache
def bundle() -> dict[str, Any]:
    """The bundled schema with every contract under $defs."""
    text = files("satya_shared_types.generated").joinpath("bundle.schema.json").read_text("utf-8")
    loaded: dict[str, Any] = json.loads(text)
    return loaded


@cache
def validator(definition: str) -> Draft202012Validator:
    """A validator for one contract, e.g. validator("EventEnvelope")."""
    defs = bundle()["$defs"]
    if definition not in defs:
        raise KeyError(f"Unknown contract {definition!r}")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": f"#/$defs/{definition}",
        "$defs": defs,
    }
    return Draft202012Validator(schema, format_checker=FormatChecker())
