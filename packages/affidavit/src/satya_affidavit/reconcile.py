"""Reconcile the sworn land and room tables with the ApplicationSnapshot (design C3 step 3).

Land rows are matched on the deed document number through its keyed token (a T field, Portal spec
§2.6.1), so the raw number is never compared or shown: holder and document number cells are masked.
Room rows are matched on the room ID inside each of the four tables. Room IDs must also be unique
across the four tables (design D5.10). The portal leaves the land total blank, so the total is
computed from the sworn rows and compared with land.total_area.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from satya_affidavit.extract import Box
from satya_affidavit.flags import TEXT_LAYER_CONFIDENCE, FlagFactory
from satya_affidavit.ids import mask, token
from satya_affidavit.normalise import parse_date, parse_number, squash
from satya_affidavit.parse import SwornDoc, SwornRow
from satya_affidavit.template import LAND_FIELDS, ROOM_FIELDS, Draft, LandRow, RoomRow

HOLDER_MASK = "•••••"
POSITION_CONFIDENCE = 0.85
ROW_CONFIDENCE = 0.9
SNAPSHOT_LAND = "Application Report: land.deeds"
SNAPSHOT_ROOMS = "Application Report: rooms"


@dataclass
class Reconciled:
    tables: list[dict[str, Any]] = field(default_factory=list)
    flags: list[dict[str, Any]] = field(default_factory=list)
    date_fallbacks: int = 0


@dataclass
class _Ctx:
    doc: SwornDoc
    draft: Draft
    factory: FlagFactory
    token_key: bytes
    out: Reconciled

    def region(self, page: int | None, box: Box | None) -> list[dict[str, float]]:
        if page is None or box is None or page not in self.doc.pages:
            return []
        return [self.doc.pages[page].region(box)]


def _fmt_area(value: float | None) -> str | None:
    return None if value is None else f"{value:.2f}"


def _fmt_room_area(value: float | None) -> str | None:
    return None if value is None else f"{value:g}"


def _deed_token(row: LandRow, key: bytes) -> str:
    return row.deed_token or token(key, row.document_no, identifier=True)


def reconcile_land(ctx: _Ctx) -> None:
    order = ctx.draft.template.date_order
    tol = ctx.factory.ruleset["LAND-AREA-RECON"].tolerance
    sworn = ctx.doc.tables["land"].rows
    expected = list(ctx.draft.land_rows)
    by_token = {_deed_token(r, ctx.token_key): i for i, r in enumerate(expected)}
    pairs: list[tuple[int | None, int | None, float]] = []
    used_e: set[int] = set()
    used_s: set[int] = set()
    for si, row in enumerate(sworn):
        doc_no = row.cells[1] if len(row.cells) > 1 else None
        ei = by_token.get(token(ctx.token_key, doc_no, identifier=True)) if doc_no else None
        if ei is not None and ei not in used_e:
            pairs.append((ei, si, TEXT_LAYER_CONFIDENCE))
            used_e.add(ei)
            used_s.add(si)
    left_e = [i for i in range(len(expected)) if i not in used_e]
    left_s = [i for i in range(len(sworn)) if i not in used_s]
    for e_left, s_left in zip(left_e, left_s, strict=False):  # doc no. differs: use position
        pairs.append((e_left, s_left, POSITION_CONFIDENCE))
    pairs += [(ei, None, ROW_CONFIDENCE) for ei in left_e[len(left_s) :]]
    pairs += [(None, si, ROW_CONFIDENCE) for si in left_s[len(left_e) :]]
    pairs.sort(key=lambda p: (p[0] if p[0] is not None else 999, p[1] if p[1] is not None else 999))

    rows_out = []
    total = 0.0
    last_row: SwornRow | None = None
    extra_no = 0
    for e_idx, s_idx, conf in pairs:
        e = expected[e_idx] if e_idx is not None else None
        s = sworn[s_idx] if s_idx is not None else None
        if s is not None:
            last_row = s
        if e_idx is not None:
            key = str(e_idx + 1)
        else:
            extra_no += 1
            key = f"extra-{extra_no}"
        page, box = (s.page, s.box) if s else (ctx.doc.tables["land"].page, None)
        regions = ctx.region(page, box)
        flag_ids: list[str] = []
        sworn_cells: list[str | None] = [None] * 6
        report_cells: list[str | None] = [None] * 6
        match: list[bool | None] = [None] * 6
        delta = None
        if s is not None:
            cells = (s.cells + [None] * 6)[:6]
            area = parse_number(cells[5])
            reg, fallback = parse_date(cells[2], order)
            ctx.out.date_fallbacks += int(fallback)
            total += area or 0.0
            sworn_cells = [
                HOLDER_MASK if cells[0] else None,
                mask(cells[1]),
                reg.isoformat() if reg else cells[2],
                cells[3],
                cells[4],
                _fmt_area(area) if area is not None else cells[5],
            ]
        if e is not None:
            report_cells = [
                HOLDER_MASK,
                mask(e.document_no) if e.document_no else "token",
                e.registration_date.isoformat(),
                e.plot_no,
                e.village_district,
                _fmt_area(e.area_acre),
            ]
        if s is not None and e is not None:
            cells = (s.cells + [None] * 6)[:6]
            area = parse_number(cells[5])
            reg, _ = parse_date(cells[2], order)
            match = [
                bool(cells[0])
                and token(ctx.token_key, cells[0] or "") == token(ctx.token_key, e.holder),
                bool(cells[1])
                and token(ctx.token_key, cells[1] or "", identifier=True)
                == _deed_token(e, ctx.token_key),
                reg == e.registration_date,
                squash(cells[3] or "") == squash(e.plot_no),
                squash(cells[4] or "") == squash(e.village_district),
                area is not None and abs(area - e.area_acre) <= tol,
            ]
            for field_name, ok, got, want in zip(
                LAND_FIELDS, match, sworn_cells, report_cells, strict=True
            ):
                if ok:
                    continue
                if field_name == "area_acre":
                    delta = round(area - e.area_acre, 4) if area is not None else None
                    flag = ctx.factory.make(
                        "LAND-AREA-RECON",
                        f"land:{key}:area_acre",
                        page=page,
                        regions=regions,
                        extracted=area,
                        expected=e.area_acre,
                        unit="acre",
                        delta=delta,
                        row=key,
                        expected_label=f"{SNAPSHOT_LAND}[{key}].area_acre",
                        confidence=conf,
                    )
                else:
                    flag = ctx.factory.make(
                        "LAND-ROW-RECON",
                        f"land:{key}:{field_name}",
                        page=page,
                        regions=regions,
                        extracted=got,
                        expected=want,
                        row=key,
                        expected_label=f"{SNAPSHOT_LAND}[{key}].{field_name}",
                        confidence=conf,
                    )
                ctx.out.flags.append(flag)
                flag_ids.append(flag["flag_id"])
            state = "matched" if all(match) else "differs"
        else:
            state = "missing_in_sworn" if s is None else "extra_in_sworn"
            flag = ctx.factory.make(
                "LAND-ROW-RECON",
                f"land:{key}:row",
                page=page,
                regions=regions,
                extracted=None if s is None else f"row {key}",
                expected=None if e is None else f"deed row {key}",
                row=key,
                expected_label=SNAPSHOT_LAND,
                confidence=conf,
            )
            ctx.out.flags.append(flag)
            flag_ids.append(flag["flag_id"])
        rows_out.append(
            {
                "key": key,
                "state": state,
                "page": page,
                "region": regions[0] if regions else None,
                "sworn_cells": sworn_cells,
                "application_report_cells": report_cells,
                "cell_match": match,
                "delta": delta,
                "flag_ids": flag_ids,
            }
        )
    expected_total = ctx.draft.land_total_acres
    computed = round(total, 4) if sworn else None
    if (
        expected_total is not None
        and computed is not None
        and abs(computed - expected_total) > 0.005
    ):
        page = last_row.page if last_row else ctx.doc.tables["land"].page
        flag = ctx.factory.make(
            "LAND-AREA-RECON",
            "land:total",
            page=page,
            regions=ctx.region(page, last_row.box if last_row else None),
            extracted=round(computed, 2),
            expected=round(expected_total, 2),
            unit="acre",
            delta=computed - expected_total,
            row="Total",
            expected_label="Application Report: land.total_area",
            confidence=TEXT_LAYER_CONFIDENCE,
        )
        ctx.out.flags.append(flag)
    ctx.out.tables.append(
        {
            "table": "land",
            "columns": list(LAND_FIELDS),
            "rows": rows_out,
            "total_rows": len(rows_out),
            "computed_total_acres": None if computed is None else round(computed, 2),
            "expected_total_acres": None if expected_total is None else round(expected_total, 2),
            "room_id_duplicates": [],
        }
    )


def _room_cells(row: RoomRow) -> list[str | None]:
    return [
        row.room_id,
        row.room_type,
        _fmt_room_area(row.carpet_area_m2),
        row.flooring,
        row.walls_painting,
        row.electrification,
    ]


def reconcile_rooms(ctx: _Ctx) -> None:
    tol = ctx.factory.ruleset["ROOM-RECON"].tolerance
    occurrences: dict[str, list[tuple[str, SwornRow]]] = defaultdict(list)
    for table, _, _ in ctx.draft.template.room_tables:
        for row in ctx.doc.tables[table].rows:
            if row.cells and row.cells[0]:
                occurrences[squash(row.cells[0])].append((table, row))
    duplicates = {k: v for k, v in occurrences.items() if len(v) > 1}
    dup_ids = [v[0][1].cells[0] or k for k, v in duplicates.items()]
    for table, _, _ in ctx.draft.template.room_tables:
        sworn = ctx.doc.tables[table].rows
        expected = list(ctx.draft.rooms.get(table, ()))
        queue: dict[str, list[int]] = defaultdict(list)
        for i, r in enumerate(expected):
            queue[squash(r.room_id)].append(i)
        pairs: list[tuple[int | None, int | None, float]] = []
        left_s = []
        for si, row in enumerate(sworn):
            ids = queue.get(squash(row.cells[0] or ""), [])
            if ids:
                pairs.append((ids.pop(0), si, TEXT_LAYER_CONFIDENCE))
            else:
                left_s.append(si)
        left_e = sorted(i for ids in queue.values() for i in ids)
        for e_left, s_left in zip(left_e, left_s, strict=False):
            pairs.append((e_left, s_left, POSITION_CONFIDENCE))
        pairs += [(ei, None, ROW_CONFIDENCE) for ei in left_e[len(left_s) :]]
        pairs += [(None, si, ROW_CONFIDENCE) for si in left_s[len(left_e) :]]
        pairs.sort(
            key=lambda p: (p[1] if p[1] is not None else 999, p[0] if p[0] is not None else 999)
        )
        rows_out = []
        for e_idx, s_idx, conf in pairs:
            e = expected[e_idx] if e_idx is not None else None
            s = sworn[s_idx] if s_idx is not None else None
            key = (s.cells[0] if s and s.cells[0] else None) or (e.room_id if e else "?")
            page, box = (s.page, s.box) if s else (ctx.doc.tables[table].page, None)
            regions = ctx.region(page, box)
            sworn_cells: list[str | None] = [None] * 6
            report_cells: list[str | None] = [None] * 6
            match: list[bool | None] = [None] * 6
            flag_ids: list[str] = []
            delta = None
            if s is not None:
                cells = (s.cells + [None] * 6)[:6]
                area = parse_number(cells[2])
                sworn_cells = [
                    cells[0],
                    cells[1],
                    _fmt_room_area(area) if area is not None else cells[2],
                    *cells[3:],
                ]
            if e is not None:
                report_cells = _room_cells(e)
            if s is not None and e is not None:
                cells = (s.cells + [None] * 6)[:6]
                area = parse_number(cells[2])
                match = [
                    squash(cells[0] or "") == squash(e.room_id),
                    squash(cells[1] or "") == squash(e.room_type),
                    area is not None and abs(area - e.carpet_area_m2) <= tol,
                    squash(cells[3] or "") == squash(e.flooring),
                    squash(cells[4] or "") == squash(e.walls_painting),
                    squash(cells[5] or "") == squash(e.electrification),
                ]
                for field_name, ok, got, want in zip(
                    ROOM_FIELDS, match, sworn_cells, report_cells, strict=True
                ):
                    if ok:
                        continue
                    numeric = field_name == "carpet_area_m2"
                    if numeric and area is not None:
                        delta = round(area - e.carpet_area_m2, 4)
                    flag = ctx.factory.make(
                        "ROOM-RECON",
                        f"{table}:{e.room_id}:{field_name}",
                        page=page,
                        regions=regions,
                        extracted=area if numeric else got,
                        expected=e.carpet_area_m2 if numeric else want,
                        unit="m2" if numeric else None,
                        delta=delta if numeric else None,
                        row=f"{table}:{e.room_id}",
                        expected_label=f"{SNAPSHOT_ROOMS}.{table}[{e.room_id}].{field_name}",
                        confidence=conf,
                    )
                    ctx.out.flags.append(flag)
                    flag_ids.append(flag["flag_id"])
                state = "matched" if all(match) else "differs"
            else:
                state = "missing_in_sworn" if s is None else "extra_in_sworn"
                flag = ctx.factory.make(
                    "ROOM-RECON",
                    f"{table}:{key}:row",
                    page=page,
                    regions=regions,
                    extracted=None if s is None else key,
                    expected=None if e is None else e.room_id,
                    row=f"{table}:{key}",
                    expected_label=f"{SNAPSHOT_ROOMS}.{table}",
                    confidence=conf,
                )
                ctx.out.flags.append(flag)
                flag_ids.append(flag["flag_id"])
            rows_out.append(
                {
                    "key": key,
                    "state": state,
                    "page": page,
                    "region": regions[0] if regions else None,
                    "sworn_cells": sworn_cells,
                    "application_report_cells": report_cells,
                    "cell_match": match,
                    "delta": delta,
                    "flag_ids": flag_ids,
                }
            )
        in_table = {squash(r.cells[0] or "") for r in sworn}
        ctx.out.tables.append(
            {
                "table": table,
                "columns": list(ROOM_FIELDS),
                "rows": rows_out,
                "total_rows": len(rows_out),
                "computed_total_acres": None,
                "expected_total_acres": None,
                "room_id_duplicates": [d for d in dup_ids if squash(d) in in_table],
            }
        )
    for squashed, places in duplicates.items():
        room_id = places[0][1].cells[0] or squashed
        page = places[-1][1].page
        regions = [ctx.doc.pages[page].region(row.box) for _, row in places if row.page == page]
        flag = ctx.factory.make(
            "ROOM-ID-DUP",
            f"room_id:{room_id}",
            page=page,
            regions=regions,
            extracted=room_id,
            expected=None,
            row=", ".join(t for t, _ in places),
            expected_label="Unique room IDs across the four room tables",
            confidence=TEXT_LAYER_CONFIDENCE,
        )
        ctx.out.flags.append(flag)
        for table_out in ctx.out.tables:
            for row_out in table_out["rows"]:
                if table_out["table"] != "land" and squash(row_out["key"]) == squashed:
                    row_out["flag_ids"].append(flag["flag_id"])


def reconcile(doc: SwornDoc, draft: Draft, factory: FlagFactory, token_key: bytes) -> Reconciled:
    out = Reconciled()
    ctx = _Ctx(doc, draft, factory, token_key, out)
    reconcile_land(ctx)
    reconcile_rooms(ctx)
    return out
