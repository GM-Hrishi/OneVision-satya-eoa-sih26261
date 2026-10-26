"""Synthetic Tamil Nadu institutions for the M5 test set and demo (test-set plan §4).

Every value is invented (data/synthetic/README.md): Demo Institute/College names, `1-9…` IDs, demo
place names, Bay-of-Bengal coordinates, trust and signatory names that are obviously synthetic. The
generator is seeded, so the same profile number always gives the same institution.
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

SYNTHETIC_NOTE = (
    "SYNTHETIC FIXTURE. Invented values for the SATYA-EoA demo and tests. Not a real institution, "
    "person, application or document."
)

# Profile number -> (kind, number). 03, 05, 07, 11 are dev seeds; 09, 13, 15, 17 are held out.
PROFILES: dict[int, str] = {
    3: "Demo Institute of Technology 03",
    5: "Demo College of Engineering 05",
    7: "Demo College of Engineering 07",
    11: "Demo Institute of Technology 11",
    9: "Demo College of Engineering 09",
    13: "Demo Institute of Technology 13",
    15: "Demo College of Engineering 15",
    17: "Demo Institute of Technology 17",
}
DEV_PROFILES = (3, 5, 7, 11)
HELD_OUT_PROFILES = (9, 13, 15, 17)

ADMIN_TYPES = [
    ("Principal Office", 30),
    ("Board Room", 40),
    ("Office All Inclusive", 150),
    ("Department Office", 30),
    ("Central Store", 30),
    ("Exam Control Office", 30),
    ("Placement Office", 30),
]
AMENITY_TYPES = [
    ("Toilets", 120),
    ("Boys Common Room", 75),
    ("Girls Common Room", 75),
    ("Cafeteria", 150),
    ("Stationery Store", 15),
    ("First Aid cum Sick Room", 10),
]
INSTRUCTIONAL_TYPES = [
    ("Class Room", 66),
    ("Tutorial Room", 33),
    ("Laboratory", 66),
    ("Workshop", 200),
    ("Drawing Hall", 132),
]
COMMON_TYPES = [
    ("Library and Reading Room", 400),
    ("Seminar Hall", 132),
    ("Language Laboratory", 66),
    ("Computer Centre", 150),
]


@dataclass(frozen=True)
class Institution:
    profile: int
    case: dict[str, Any]
    snapshot: dict[str, Any]


def _room(prefix: str, number: int, room_type: str, area: float) -> dict[str, Any]:
    return {
        "room_id": f"{prefix}-{number}",
        "room_type": room_type,
        "carpet_area_m2": area,
        "flooring": "Ready",
        "walls_painting": "Ready",
        "electrification": "Ready",
    }


def _rooms(rng: random.Random, profile: int) -> dict[str, list[dict[str, Any]]]:
    def block(
        prefix: str, start: int, types: list[tuple[str, int]], low: int, high: int
    ) -> list[dict[str, Any]]:
        count = rng.randint(low, high)
        rows = []
        for i in range(count):
            room_type, area = types[i % len(types)]
            rows.append(_room(prefix, start + i, room_type, float(area)))
        return rows

    if profile == 3:  # the demo case: fixed tables so the demo script can name them
        return {
            "administrative": [
                _room("A", 101, "Principal Office", 30.0),
                _room("A", 102, "Board Room", 40.0),
                _room("A", 103, "Office All Inclusive", 150.0),
                _room("A", 104, "Exam Control Office", 30.0),
            ],
            "amenities": [
                _room("M", 101, "Toilets", 120.0),
                _room("M", 102, "Girls Common Room", 75.0),
                _room("M", 103, "Cafeteria", 150.0),
            ],
            "instructional": [
                _room("I", 201, "Class Room", 66.0),
                _room("I", 202, "Class Room", 66.0),
                _room("I", 203, "Laboratory", 66.0),
                _room("I", 204, "Workshop", 200.0),
            ],
            "instructional_common": [
                _room("C", 301, "Library and Reading Room", 400.0),
                _room("C", 302, "Seminar Hall", 132.0),
                _room("C", 303, "Computer Centre", 150.0),
            ],
        }
    return {
        "administrative": block("A", 101, ADMIN_TYPES, 4, 6),
        "amenities": block("M", 101, AMENITY_TYPES, 3, 5),
        "instructional": block("I", 201, INSTRUCTIONAL_TYPES, 4, 6),
        "instructional_common": block("C", 301, COMMON_TYPES, 3, 4),
    }


def _deeds(
    rng: random.Random, profile: int, trust: str, town: str, district: str
) -> list[dict[str, Any]]:
    place = f"{town} / {district}"
    if profile == 3:
        return [
            {
                "holder": trust,
                "document_no": "DEMO-DEED-0301",
                "registration_date": "2009-06-15",
                "plot_no": "DEMO-PLOT-11",
                "village_district": place,
                "area_acre": 8.0,
            },
            {
                "holder": trust,
                "document_no": "DEMO-DEED-0302",
                "registration_date": "2012-02-20",
                "plot_no": "DEMO-PLOT-12",
                "village_district": place,
                "area_acre": 4.5,
            },
        ]
    deeds = []
    for i in range(rng.randint(1, 3)):
        reg = date(rng.randint(1998, 2015), rng.randint(1, 12), 1) + timedelta(
            days=rng.randint(0, 27)
        )
        if (
            i == 0 and reg.day <= 12
        ):  # at least one deed date with day > 12 (MM/DD fallback control)
            reg = reg.replace(day=reg.day + 13)
        deeds.append(
            {
                "holder": trust,
                "document_no": f"DEMO-DEED-{profile:02d}{i + 1:02d}",
                "registration_date": reg.isoformat(),
                "plot_no": f"DEMO-PLOT-{profile:02d}{i + 1}",
                "village_district": place,
                "area_acre": round(rng.choice([2.5, 3.0, 4.25, 5.0, 6.5, 7.75, 10.0]), 2),
            }
        )
    return deeds


def institution(profile: int, ay: str = "2026-27") -> Institution:
    """One synthetic institution: case metadata (incl. the draft header) + ApplicationSnapshot."""
    if profile not in PROFILES:
        raise KeyError(f"unknown synthetic profile {profile}")
    rng = random.Random(f"satya-m5-profile-{profile}")
    name = PROFILES[profile]
    trust = f"Demo Educational Trust {profile:02d}"
    town = f"Demo Town {profile:02d}"
    district = f"Demo District {(profile % 9) + 1:02d}"
    if profile == 3:
        district = "Demo District 07"
    aid = f"1-900000{profile:02d}1{profile:02d}"  # e.g. 1-90000005105
    if profile == 3:
        aid = "1-90000004217"
    pid = f"1-90003{profile:02d}"
    if profile == 3:
        pid = "1-9000317"
    deeds = _deeds(rng, profile, trust, town, district)
    total = round(sum(d["area_acre"] for d in deeds), 2)
    start_year = int(ay[:4])
    application_date = date(start_year, 11, 20) - timedelta(days=rng.randint(0, 15))
    if profile == 3:
        application_date = date(start_year, 11, 20)
    category_set = ["EoA Only"]
    case_id = f"cas_01JD3M5A00000000000000{'DT' if 'Technology' in name else 'CE'}{profile:02d}"
    snapshot: dict[str, Any] = {
        "ay": ay,
        "captured_at": f"{application_date.isoformat()}T11:05:00+05:30",
        "basic": {
            "application_id": aid,
            "permanent_id": pid,
            "institution_type": "Private-Self Financing",
            "status": "Submitted",
            "application_date": application_date.isoformat(),
            "submission_date": (application_date + timedelta(days=4)).isoformat(),
            "regional_office": "Southern",
            "overall_deficiency": "no",
        },
        "trust": {"name": trust, "registration_ref": f"DEMO-TRUST-REG-{profile:04d}"},
        "authorised_signatory": {"name": f"Demo Trustee {profile:02d}", "designation": "chairman"},
        "courses": [
            {
                "programme": "Engineering and Technology",
                "level": "UG",
                "course": "Computer Science and Engineering",
                "intake_approved": [
                    {"ay": f"{start_year - 2}-{str(start_year - 1)[2:]}", "intake": 120},
                    {"ay": f"{start_year - 1}-{str(start_year)[2:]}", "intake": 120},
                ],
                "intake_applied": 120,
            }
        ],
        "land": {
            "total_area": total,
            "unit": "acre",
            "pieces": len(deeds),
            "max_distance_km": 0.4 if len(deeds) > 1 else 0.0,
            "coordinates": {
                "lat": {"deg": 12, "min": 30 + profile, "sec": 0, "hemisphere": "N"},
                "lon": {"deg": 81, "min": 30 + profile, "sec": 0, "hemisphere": "E"},
            },
            "deeds": deeds,
        },
        "buildings": [
            {
                "block": "Academic Block A",
                "sanctioned_area_m2": 9800,
                "constructed_area_m2": 9800,
                "approving_authority": f"Demo Local Planning Authority {profile:02d}",
                "approval_date": "2010-03-01",
            }
        ],
        "rooms": _rooms(rng, profile),
        "declaration": {
            "items": {"a": True, "b": True, "c": True, "d": True, "e": True, "f": True},
            "category_list": category_set,
        },
        "deficiency_report": {
            "template_year": ay,
            "sections": [{"section": "Principal eligibility", "deficiency": "no"}],
            "overall": "no",
            "principal_eligibility": "yes",
        },
    }
    case: dict[str, Any] = {
        "_synthetic": SYNTHETIC_NOTE,
        "case_id": case_id,
        "application_id": aid,
        "permanent_id": pid,
        "ay": ay,
        "regional_office": "Southern",
        "state": "Tamil Nadu",
        "route": "self_disclosure",
        "stage": "2",
        "category_set": category_set,
        "institution_name": name,
        "affidavit_draft": {
            "template_id": "aff2-portal-2024-27",
            "ay": ay,
            "category_set": category_set,
            "header": {
                "institution_name": name,
                "address": f"{town}, {district}, Tamil Nadu",
                "town": town,
            },
        },
        "stamp": {
            "certificate_no": f"IN-TN9{profile:02d}{application_date:%y%m%d}{4217 + profile:05d}Q"[
                :20
            ],
            "instrument": "e-stamp",
            "article": "Article 4 Affidavit",
            "second_party": "AICTE NEW DELHI",
            "duty": 100,
            "issued": (application_date + timedelta(days=1)).isoformat(),
            "notarised": (application_date + timedelta(days=2)).isoformat(),
            "notary_reg_no": f"DEMO-NOT-{profile:04d}",
            "notary_valid_till": f"{start_year + 1}-12-31",
        },
    }
    return Institution(profile=profile, case=case, snapshot=snapshot)
