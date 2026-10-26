"""Read the sworn Affidavit 2 structure from the extracted text layer (design B1 row 1, D3, D4).

Order of a sworn copy: optional stamp page(s) → heading + AY line → opening block (header fields,
numbered category list) → affirmation → 19 core declarations (+ committee bullets) → "FOR EXISTING
INSTITUTES" + 5 declarations → land table → 4 room tables → verification and notary. Any other
heading inside the declarations is an extra block (e.g. a 2023-24-style Increase-in-Intake block).
The parser only reads; every comparison happens in diff.py and reconcile.py.
"""

import re
from dataclasses import dataclass, field

from satya_affidavit.extract import Box, Extracted, Line, Page, Table
from satya_affidavit.normalise import ay_short, clean, join_wrapped, squash
from satya_affidavit.template import Template

_AY = re.compile(r"ACADEMIC\s*YEAR\s*[-\u2013]?\s*(\d{4})\s*-\s*(\d{4})", re.IGNORECASE)
_NUMBERED = re.compile(r"^(\d{1,2})\s*[.)]\s*(.*)$")
# Bullets as printed; pdfminer reports an unmapped bullet glyph as "(cid:N)".
_BULLET = re.compile(r"^(?:[\u2022\u00b7\u25aa\u25e6\-\u2013]|\(cid:\d+\))\s*(.*)$")
_FOOTER = re.compile(r"(Application\s+Number\s*:|Page\s+\d+\s+of\s+\d+)", re.IGNORECASE)
_HEADINGS = ("AFFIDAVIT", "UNDERTAKING")


@dataclass
class Located:
    text: str
    page: int
    box: Box


@dataclass
class SwornDeclaration:
    position: int
    printed_no: int | None
    block: str
    text: str
    page: int
    box: Box
    struck_words: int = 0
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class SwornRow:
    cells: list[str | None]
    page: int
    box: Box


@dataclass
class SwornTable:
    name: str
    caption: str
    page: int | None
    rows: list[SwornRow] = field(default_factory=list)
    printed_total: str | None = None


@dataclass
class SwornDoc:
    heading: str | None
    heading_page: int | None
    ay: str | None
    ay_text: str | None
    header: dict[str, Located]
    category_label: Located | None
    categories: list[Located]
    declarations: list[SwornDeclaration]
    extra_blocks: list[Located]
    tables: dict[str, SwornTable]
    pages: dict[int, Page]
    hyphens_rejoined: int = 0
    struck_words: int = 0


def _events(ex: Extracted) -> list[tuple[int, float, Line | Table]]:
    items: list[tuple[int, float, Line | Table]] = []
    for page in ex.pages:
        for line in page.lines:
            if _FOOTER.search(line.raw):
                continue
            items.append((page.number, line.box.top, line))
        for table in page.tables:
            items.append((page.number, table.box.top, table))
    items.sort(key=lambda e: (e[0], e[1]))
    return items


def _is_heading(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 6 and all(c.isupper() for c in letters) and not _NUMBERED.match(text)


def _cell(value: str | None) -> str | None:
    if value is None:
        return None
    joined = clean(value.replace("\n", " "))
    return joined or None


def parse(ex: Extracted, template: Template, vocabulary: set[str]) -> SwornDoc:
    header_labels = {squash(label): key for key, label in template.header_fields}
    captions = {squash(template.land_caption): "land"}
    captions |= {squash(caption): table for table, _, caption in template.room_tables}
    existing_heading = squash(template.existing_heading)
    rooms_heading = squash(template.rooms_heading)
    category_label = squash(template.category_label)
    land_header = squash(template.land_columns[0][1])
    room_header = squash(template.room_columns[0][1])
    total_label = squash(template.land_total_label)

    doc = SwornDoc(
        heading=None,
        heading_page=None,
        ay=None,
        ay_text=None,
        header={},
        category_label=None,
        categories=[],
        declarations=[],
        extra_blocks=[],
        tables={
            name: SwornTable(name, cap, None) for cap, name in ((c, n) for c, n in captions.items())
        },
        pages={p.number: p for p in ex.pages},
    )
    for name in doc.tables:
        doc.tables[name].caption = template.caption_of(name)

    mode = "before"
    block = "core"
    current: SwornDeclaration | None = None
    current_table: str | None = None

    def close() -> None:
        nonlocal current
        if current is not None:
            current.text = clean(current.text)
            doc.declarations.append(current)
            current = None

    for page_no, _top, item in _events(ex):
        if isinstance(item, Table):
            if current_table is None:
                continue
            target = doc.tables[current_table]
            target.page = target.page or page_no
            for cells, box in zip(item.rows, item.row_boxes, strict=False):
                values = [_cell(c) for c in cells]
                first = squash(values[0] or "")
                if first in (land_header, room_header):
                    continue  # header row (repeated on every page)
                if current_table == "land" and first.startswith(total_label):
                    target.printed_total = next((v for v in values[1:] if v), None)
                    continue
                if not any(values):
                    continue
                target.rows.append(SwornRow(values, page_no, box))
            continue

        line = item
        text = clean(line.text)
        key = squash(text)
        if not text:
            continue
        if mode == "before":
            if key in (h.casefold() for h in _HEADINGS):
                doc.heading, doc.heading_page = text.upper(), page_no
                mode = "opening"
            continue
        if mode == "opening":
            ay = _AY.search(text)
            if ay and doc.ay_text is None:
                doc.ay_text = text
                doc.ay = ay_short(int(ay[1]), int(ay[2]))
                continue
            label, sep, value = text.partition(":")
            if sep and squash(label) in header_labels:
                doc.header[header_labels[squash(label)]] = Located(clean(value), page_no, line.box)
                continue
            if sep and squash(label) == category_label:
                doc.category_label = Located(text, page_no, line.box)
                mode = "categories"
                if clean(value):
                    doc.categories.append(Located(clean(value), page_no, line.box))
                continue
            if "affirm" in key or key.startswith("i,"):
                mode = "affirmation"
            else:
                continue
        if mode == "categories":
            numbered = _NUMBERED.match(text)
            if numbered:
                doc.categories.append(Located(clean(numbered[2]), page_no, line.box))
                continue
            mode = "affirmation"
        if mode == "affirmation":
            if key.endswith("asunder:") or key.endswith("asunder"):
                mode = "declarations"
            continue
        if mode == "declarations":
            if key in captions or key == rooms_heading:
                close()
                mode = "tables"
            elif key.startswith("verification"):
                close()
                mode = "after"
                continue
            elif key == existing_heading:
                close()
                block = "existing_institute"
                continue
            elif _is_heading(text) and not _BULLET.match(text):
                close()
                block = "extra"
                doc.extra_blocks.append(Located(text, page_no, line.box))
                continue
            else:
                numbered = _NUMBERED.match(text)
                bullet = _BULLET.match(text)
                doc.struck_words += line.struck
                if numbered:
                    close()
                    current = SwornDeclaration(
                        position=len(doc.declarations) + 1,
                        printed_no=int(numbered[1]),
                        block=block,
                        text=numbered[2],
                        page=page_no,
                        box=line.box,
                        struck_words=line.struck,
                        raw_lines=[line.raw],
                    )
                elif current is not None:
                    addition = bullet[1] if bullet else text
                    if bullet:
                        current.text = f"{current.text} {addition}"
                    else:
                        current.text, rejoined = join_wrapped(current.text, addition, vocabulary)
                        doc.hyphens_rejoined += int(rejoined)
                    current.box = (
                        current.box.union(line.box) if line.page == current.page else current.box
                    )
                    current.struck_words += line.struck
                    current.raw_lines.append(line.raw)
                continue
        if mode == "tables":
            if key in captions:
                current_table = captions[key]
                target = doc.tables[current_table]
                target.page = target.page or page_no
            elif key.startswith("verification"):
                mode = "after"
            continue
    close()
    return doc
