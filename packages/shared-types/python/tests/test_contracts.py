"""One valid synthetic example per schema passes, one invalid fails (JSON Schema + Pydantic)."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from satya_shared_types import constants, models, validator

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
NAMES = [*constants.SCHEMA_TITLES, "Check"]


def load(kind: str, name: str) -> Any:
    return json.loads((EXAMPLES / kind / f"{name}.json").read_text("utf-8"))


@pytest.mark.parametrize("name", NAMES)
def test_valid_example_passes(name: str) -> None:
    data = load("valid", name)
    errors = list(validator(name).iter_errors(data))
    assert errors == [], [e.message for e in errors]
    TypeAdapter(getattr(models, name)).validate_python(data)


@pytest.mark.parametrize("name", NAMES)
def test_invalid_example_fails(name: str) -> None:
    data = load("invalid", name)
    assert list(validator(name).iter_errors(data)), f"{name} invalid example unexpectedly passed"
    with pytest.raises(ValidationError):
        TypeAdapter(getattr(models, name)).validate_python(data)


def test_label_precedence_is_a_permutation_of_the_labels() -> None:
    assert sorted(constants.LABEL_PRECEDENCE) == sorted(constants.VERIFICATION_LABELS)
    assert constants.LABEL_PRECEDENCE[0] == "mismatch_detected"
    assert constants.LABEL_PRECEDENCE[-1] == "verified"


def test_event_types_are_inbound_plus_outbound() -> None:
    assert set(constants.EVENT_TYPES) == set(constants.INBOUND_EVENT_TYPES) | set(
        constants.OUTBOUND_EVENT_TYPES
    )
    assert "observation.withdrawn" in constants.OUTBOUND_EVENT_TYPES


def test_outbound_event_must_be_advisory() -> None:
    outbound = {"type": "case.validation_completed", "producer": "satya"}
    env = load("valid", "EventEnvelope") | outbound
    assert list(validator("EventEnvelope").iter_errors(env)), "outbound passed without advisory"
    env |= {"advisory": True, "regulatory_effect": "none"}
    assert list(validator("EventEnvelope").iter_errors(env)) == []
    env["regulatory_effect"] = "approval"
    assert list(validator("EventEnvelope").iter_errors(env))


def test_alert_subtype_must_match_type() -> None:
    alert = load("valid", "Alert") | {"type": "missing_info", "subtype": "source_unavailable"}
    assert list(validator("Alert").iter_errors(alert))
    assert set(constants.ALERT_SUBTYPES) == set(constants.ALERT_TYPES)


def test_snapshot_fields_all_annotated_and_x_fields_absent() -> None:
    handling = constants.SNAPSHOT_FIELD_HANDLING
    assert handling, "no snapshot fields found"
    assert set(handling.values()) <= {"K", "T", "R"}, "X fields must not exist in the model"
    for rejected in constants.SNAPSHOT_REJECTED_FIELDS:
        assert rejected not in handling, f"rejected field {rejected} is present in the model"
    for path, token_field in constants.SNAPSHOT_TOKEN_FIELDS.items():
        assert handling[path] == "T", path
        assert token_field.endswith("_token")


@pytest.mark.parametrize(
    "path", ["hoi", "bank.account_number", "faculty.pan", "faculty.mobile", "faculty.email"]
)
def test_each_rejected_field_is_refused(path: str) -> None:
    snap = load("valid", "ApplicationSnapshot")
    group, _, leaf = path.partition(".")
    if not leaf:
        snap[group] = {"name": "Demo Principal 03"}
    elif isinstance(snap[group], list):
        snap[group][0][leaf] = "DEMO-VALUE"
    else:
        snap[group][leaf] = "DEMO-VALUE"
    assert list(validator("ApplicationSnapshot").iter_errors(snap))
    with pytest.raises(ValidationError):
        models.ApplicationSnapshot.model_validate(snap)


def test_pydantic_fields_carry_handling_metadata() -> None:
    field = models.SnapshotTrustee.model_fields["name"]
    assert field.json_schema_extra == {"handling": "T", "token-field": "trustee_token"}


def test_timestamp_without_offset_is_rejected() -> None:
    env = load("valid", "EventEnvelope") | {"occurred_at": "2026-12-14T11:05:42"}
    assert list(validator("EventEnvelope").iter_errors(env))
