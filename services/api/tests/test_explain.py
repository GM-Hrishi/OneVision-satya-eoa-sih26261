"""T1: limitation keys, catalogue wording lint and the limitation field on flags and rules."""

import re

import pytest
from fastapi.testclient import TestClient

from satya_affidavit.catalogue import LOCALES, load_catalogue
from satya_api.explain import limitation_for, rule_detail
from satya_api.rulepacks import current_pack

from .test_demo_flow import DIT03, flow, rb  # noqa: F401

BANNED = re.compile(
    r"\b(forged|forgery|forge|fake|fakes|fraud|fraudulent|tampered|tampering|cheat|cheating|guilty)\b",
    re.IGNORECASE,
)


def all_rules():
    pack = current_pack()
    return [*pack.m5.rules.values(), *pack.m6.rules.values()]


def test_every_rule_has_a_limitation_key_in_both_catalogues() -> None:
    for rule in all_rules():
        assert rule.limitation_key, rule.rule_id
        for locale in LOCALES:
            assert rule.limitation_key in load_catalogue(locale).limitation, (rule.rule_id, locale)


def test_english_texts_have_no_banned_words() -> None:
    texts = [r.description for r in all_rules()]
    catalogue = load_catalogue("en")
    texts += [e.text for e in catalogue.limitation.values()]
    texts += [e.text for e in catalogue.why.values()]
    assert texts
    for text in texts:
        assert not BANNED.search(text), text


def test_limitation_texts_say_what_is_not_proved() -> None:
    for key, entry in load_catalogue("en").limitation.items():
        assert entry.text.startswith("This does not show"), key
        assert len(entry.text.split(". ")) <= 2, key


def test_hindi_entries_are_marked_for_review_and_cover_english_keys() -> None:
    en, hi = load_catalogue("en"), load_catalogue("hi")
    assert set(hi.limitation) == set(en.limitation)
    assert all(e.review for e in hi.limitation.values())
    assert not any(e.review for e in en.limitation.values())


def test_limitation_for_flag_and_unknown_rule() -> None:
    got = limitation_for({"rule_id": "LAND-AREA-RECON"})
    assert got and got["key"] == "limitation.entry_slip" and got["text"].startswith("This does not")
    assert limitation_for({"rule_id": "NO-SUCH"}) is None
    assert limitation_for({"rule_id": "LAND-AREA-RECON"}, "hi")["text"] != got["text"]  # type: ignore[index]


def test_review_flags_carry_limitation(flow: TestClient) -> None:  # noqa: F811
    view = flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()
    assert view["flags"]
    for flag in view["flags"]:
        assert flag["limitation"] and flag["limitation"]["text"], flag["rule_id"]
        assert isinstance(flag["why"], str)  # existing field unchanged


def test_rule_detail_endpoint(flow: TestClient) -> None:  # noqa: F811
    body = flow.get("/v1/rules/SIG-DIGEST", headers=rb()).json()
    assert body["limitation_key"] == "resave_changes_bytes"
    assert body["limitation"]["key"] == "limitation.resave_changes_bytes"
    assert body["advisory"] is True
    assert rule_detail("SIG-DIGEST") == {k: v for k, v in body.items()}
    assert flow.get("/v1/rules/NOPE-1", headers=rb()).status_code == 404
    assert flow.get("/v1/rules/bad id", headers=rb()).status_code == 404
    assert flow.get("/v1/rules/SIG-DIGEST").status_code == 401


@pytest.mark.parametrize("rule_id", ["AFF-HEADER", "UDIN-REUSE", "STAMP-REUSE"])
def test_rule_detail_limitation_present(rule_id: str) -> None:
    assert rule_detail(rule_id)["limitation"]["text"]  # type: ignore[index]
