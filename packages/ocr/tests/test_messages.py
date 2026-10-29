"""The Python sentences and the workbench message keys stay in step."""

import json
from pathlib import Path

from satya_ocr.reasons import REASON_CODES, WHY

MESSAGES = Path(__file__).resolve().parents[3] / "apps" / "web" / "messages"


def test_every_variant_has_a_workbench_message_in_both_languages() -> None:
    for name in ("en.json", "hi.json"):
        why = json.loads((MESSAGES / name).read_text("utf-8"))["demo"]["ocr"]["why"]
        assert set(why) == set(WHY), name


def test_hindi_keys_are_listed_for_review() -> None:
    review = json.loads((MESSAGES / "hi.review.json").read_text("utf-8"))
    for variant in WHY:
        assert f"demo.ocr.why.{variant}" in review
    for code in REASON_CODES:
        assert f"verification.reason.{code}" in review and f"overview.reason.{code}" in review
