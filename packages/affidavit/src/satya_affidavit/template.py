"""Template profile (year-versioned) and the expected portal draft for one AID and AY.

The portal sends `affidavit_draft{template_id, ay, category_set[], text_ref}` with
`application.submitted` (Portal spec §2.4). The draft is the template filled with this
application's header and its ApplicationSnapshot land and room data, so it is rebuilt here
deterministically from the same inputs; tables in the draft therefore equal the snapshot by
construction.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from typing import Any

import yaml

from satya_affidavit.normalise import OPTION_MARKUP, OptionGroup, ay_long, format_date, option_token
from satya_affidavit.paths import templates_dir

ROOM_TABLES = ("room_admin", "room_amenities", "room_instructional", "room_common")
ROOM_FIELDS = (
    "room_id",
    "room_type",
    "carpet_area_m2",
    "flooring",
    "walls_painting",
    "electrification",
)
LAND_FIELDS = (
    "holder",
    "document_no",
    "registration_date",
    "plot_no",
    "village_district",
    "area_acre",
)
CORE_COUNT = 19
EXISTING_COUNT = 5


class TemplateError(ValueError):
    pass


@dataclass(frozen=True)
class Template:
    template_id: str
    aph_edition: str
    valid_ays: tuple[str, ...]
    heading: str
    ay_line: str
    date_order: str
    header_fields: tuple[tuple[str, str], ...]
    category_label: str
    affirmation: str
    existing_heading: str
    declarations: tuple[dict[str, Any], ...]
    land_caption: str
    land_columns: tuple[tuple[str, str], ...]
    land_total_label: str
    rooms_heading: str
    room_columns: tuple[tuple[str, str], ...]
    room_tables: tuple[tuple[str, str, str], ...]  # (table, snapshot_block, caption)
    verification: str

    def caption_of(self, table: str) -> str:
        if table == "land":
            return self.land_caption
        return next(c for t, _, c in self.room_tables if t == table)


@cache
def load_template(template_id: str) -> Template:
    if not re.fullmatch(r"[a-z0-9-]{1,80}", template_id):
        raise TemplateError(f"bad template id {template_id!r}")
    matches = list(templates_dir().glob(f"*/{template_id}.yaml"))
    if len(matches) != 1:
        raise TemplateError(f"template {template_id} not found")
    raw = yaml.safe_load(matches[0].read_text("utf-8"))
    tables = raw["tables"]
    template = Template(
        template_id=raw["template_id"],
        aph_edition=str(raw["aph_edition"]),
        valid_ays=tuple(raw["valid_ays"]),
        heading=raw["heading"],
        ay_line=raw["ay_line"],
        date_order=raw["date_order"],
        header_fields=tuple((f["key"], f["label"]) for f in raw["header_fields"]),
        category_label=raw["category_label"],
        affirmation=" ".join(raw["affirmation"].split()),
        existing_heading=raw["existing_institute_heading"],
        declarations=tuple(raw["declarations"]),
        land_caption=tables["land"]["caption"],
        land_columns=tuple((c["key"], c["label"]) for c in tables["land"]["columns"]),
        land_total_label=tables["land"]["total_label"],
        rooms_heading=tables["rooms_heading"],
        room_columns=tuple((c["key"], c["label"]) for c in tables["room_columns"]),
        room_tables=tuple(
            (t["table"], t["snapshot_block"], t["caption"]) for t in tables["room_tables"]
        ),
        verification=" ".join(raw["verification"].split()),
    )
    blocks = [d["block"] for d in template.declarations]
    if blocks.count("core") != CORE_COUNT or blocks.count("existing_institute") != EXISTING_COUNT:
        raise TemplateError(f"{template_id}: expected 19 core + 5 existing-institute declarations")
    return template


@dataclass(frozen=True)
class DraftHeader:
    pid: str
    aid: str
    ay: str
    institution_name: str
    address: str
    institution_type: str
    region: str
    application_date: date
    trust_name: str
    signatory_designation: str
    town: str


@dataclass(frozen=True)
class DraftDeclaration:
    no: int  # canonical position 1..24
    printed_no: int
    block: str
    markup: str  # text with [[group: a|b]] markup, placeholders filled
    bullets: tuple[str, ...]
    groups: tuple[OptionGroup, ...]

    @property
    def display(self) -> str:
        """As the portal prints it: options as "a / b", bullets appended."""
        text = OPTION_MARKUP.sub(
            lambda m: " / ".join(c.strip() for c in m[2].split("|")), self.markup
        )
        return " ".join([text, *self.bullets])

    @property
    def tokenised(self) -> str:
        """Option groups replaced by their tokens (the expected side of the comparison)."""
        text = OPTION_MARKUP.sub(lambda m: f" {option_token(m[1])} ", self.markup)
        return " ".join([text, *self.bullets])


@dataclass(frozen=True)
class LandRow:
    holder: str
    document_no: str
    registration_date: date
    plot_no: str
    village_district: str
    area_acre: float
    deed_token: str | None = None


@dataclass(frozen=True)
class RoomRow:
    room_id: str
    room_type: str
    carpet_area_m2: float
    flooring: str
    walls_painting: str
    electrification: str


@dataclass(frozen=True)
class Draft:
    template: Template
    header: DraftHeader
    category_list: tuple[str, ...]
    declarations: tuple[DraftDeclaration, ...]
    land_rows: tuple[LandRow, ...]
    land_total_acres: float | None
    rooms: dict[str, tuple[RoomRow, ...]] = field(default_factory=dict)

    @property
    def affirmation(self) -> str:
        return self.template.affirmation.format(**_fill(self.header))

    @property
    def ay_line(self) -> str:
        return self.template.ay_line.format(**_fill(self.header))

    def header_value(self, key: str) -> str:
        if key == "application_date":
            return format_date(self.header.application_date, self.template.date_order)
        return str(getattr(self.header, key))

    def entities(self) -> dict[str, str]:
        """Names and IDs substituted before comparing (UI spec §7.1, "names substituted")."""
        h = self.header
        return {
            "institution_name": h.institution_name,
            "trust_name": h.trust_name,
            "aid": h.aid,
            "pid": h.pid,
            "ay_long": ay_long(h.ay),
        }


def _fill(h: DraftHeader) -> dict[str, str]:
    return {
        "ay_long": ay_long(h.ay),
        "institution_name": h.institution_name,
        "trust_name": h.trust_name,
        "signatory_designation": h.signatory_designation,
        "town": h.town,
    }


_ACRE_PER = {
    "acre": 1.0,
    "acres": 1.0,
    "hectare": 2.4710538147,
    "ha": 2.4710538147,
    "sq_m": 1 / 4046.8564224,
}


def to_acres(value: float, unit: str) -> float:
    try:
        return value * _ACRE_PER[unit.casefold()]
    except KeyError:
        raise TemplateError(f"unknown land unit {unit!r}") from None


def render_draft(
    template: Template, header: DraftHeader, category_set: list[str], snapshot: dict[str, Any]
) -> Draft:
    """The portal draft for this AID and AY: template text + header + snapshot tables."""
    if header.ay not in template.valid_ays:
        raise TemplateError(f"{template.template_id} does not cover AY {header.ay}")
    fill = _fill(header)
    declarations = []
    for position, decl in enumerate(template.declarations, start=1):
        markup = " ".join(decl["text"].split()).format(**fill)
        groups = tuple(
            OptionGroup(m[1], tuple(c.strip() for c in m[2].split("|")))
            for m in OPTION_MARKUP.finditer(markup)
        )
        declarations.append(
            DraftDeclaration(
                no=position,
                printed_no=int(decl["number"]),
                block=decl["block"],
                markup=markup,
                bullets=tuple(decl.get("bullets", ())),
                groups=groups,
            )
        )
    land = snapshot.get("land", {})
    land_rows = tuple(
        LandRow(
            holder=d.get("holder", ""),
            document_no=d.get("document_no", ""),
            registration_date=date.fromisoformat(d["registration_date"]),
            plot_no=d.get("plot_no", ""),
            village_district=d.get("village_district", ""),
            area_acre=float(d["area_acre"]),
            deed_token=d.get("deed_token"),
        )
        for d in land.get("deeds", [])
    )
    total = land.get("total_area")
    total_acres = to_acres(float(total), land.get("unit", "acre")) if total is not None else None
    rooms_raw = snapshot.get("rooms", {})
    rooms = {
        table: tuple(
            RoomRow(
                room_id=r["room_id"],
                room_type=r["room_type"],
                carpet_area_m2=float(r["carpet_area_m2"]),
                flooring=r.get("flooring", ""),
                walls_painting=r.get("walls_painting", ""),
                electrification=r.get("electrification", ""),
            )
            for r in rooms_raw.get(block, [])
        )
        for table, block, _ in template.room_tables
    }
    return Draft(
        template=template,
        header=header,
        category_list=tuple(category_set),
        declarations=tuple(declarations),
        land_rows=land_rows,
        land_total_acres=total_acres,
        rooms=rooms,
    )


def draft_header(case: dict[str, Any], snapshot: dict[str, Any]) -> DraftHeader:
    """Header of the portal draft from the case's draft metadata and the snapshot."""
    meta = case["affidavit_draft"]["header"]
    basic = snapshot["basic"]
    designation = snapshot.get("authorised_signatory", {}).get("designation", "authorised_person")
    return DraftHeader(
        pid=basic.get("permanent_id", ""),
        aid=basic["application_id"],
        ay=snapshot["ay"],
        institution_name=meta["institution_name"],
        address=meta["address"],
        institution_type=basic.get("institution_type", ""),
        region=basic["regional_office"],
        application_date=date.fromisoformat(basic["application_date"]),
        trust_name=snapshot.get("trust", {}).get("name", ""),
        signatory_designation=designation.replace("_", " ").title(),
        town=meta["town"],
    )
