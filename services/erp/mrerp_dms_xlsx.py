# -*- coding: utf-8 -*-
"""
services/erp/mrerp_dms_xlsx.py

Byte-faithful clone of DMS' own impcarbookcon/example.xlsx with only row-2
cells edited (CLAUDE.md/CLAUDE.md §8 — preserve the official workbook, never
regenerate with a fresh openpyxl book; DMS rejected a freshly-built workbook
as "not enough 8 columns").

Lineage:
    Ported verbatim from the lab builder
    D:\\pearnly-dms-adapter-lab\\src\\dms_adapter\\xlsx_import.py.

Verified 2026-05-31 against the LIVE template downloaded from
    https://www.mrerp4sme.com/dms/impcarbookcon/example.xlsx (11184 bytes):
    row 2 cells reference shared-string indexes
        A2→8 (booking_no)  B2→13 (advisor)  D2→38 (car code)
        E2→16 (paint)      G2→21 (first)    H2→26 (last)
    and C2/F2 are date serials. The indexes below match exactly.

    Header row 1: A=เลขที่ใบจอง B=ที่ปรึกษาการขาย C=วันที่ออกใบจอง D=รุ่นรถ
    E=สีรถ F=วันที่คาดว่าจะส่งมอบ G=ชื่อลูกค้า(first) H=นามสกุล(last).

⚠️ Import selection: the importer is driven by `cbimportdata[]=2` (row 2 only),
so the template's example rows 3-6 are NOT imported. The live booking smoke
MUST confirm exactly one booking is created (no example junk) — see
mrerp_dms_client.import_booking_from_xlsx.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"m": SHEET_NS}
ET.register_namespace("", SHEET_NS)


@dataclass(frozen=True)
class BookingImportRow:
    booking_no: str
    advisor_code: str
    advisor_name: str
    doc_date_serial: int
    car_code: str
    paint_code: str
    delivery_date_serial: int
    customer_first_name: str
    customer_last_name: str


class DMSBookingImportXlsxBuilder:
    """Clone DMS' own example.xlsx and edit row 2 in-place.

    The DMS PHP importer accepted the official workbook but rejected a
    fresh openpyxl workbook. The stable path is preserving the original
    package shape and only changing shared-string cells used by row 2.
    """

    ROW2_SHARED_STRING_INDEXES = {
        "booking_no": 8,
        "advisor": 13,
        "car": 38,
        "paint": 16,
        "customer_first_name": 21,
        "customer_last_name": 26,
    }

    def build(self, template_bytes: bytes, row: BookingImportRow) -> bytes:
        with ZipFile(BytesIO(template_bytes), "r") as zin:
            files = {name: zin.read(name) for name in zin.namelist()}

        shared_strings = ET.fromstring(files["xl/sharedStrings.xml"])
        items = shared_strings.findall("m:si", NS)

        self._set_shared_string(items, "booking_no", row.booking_no)
        self._set_shared_string(items, "advisor", f"{row.advisor_code} {row.advisor_name}".strip())
        self._set_shared_string(items, "car", row.car_code)
        self._set_shared_string(items, "paint", row.paint_code)
        self._set_shared_string(items, "customer_first_name", row.customer_first_name)
        self._set_shared_string(items, "customer_last_name", row.customer_last_name)

        files["xl/sharedStrings.xml"] = ET.tostring(
            shared_strings,
            encoding="utf-8",
            xml_declaration=True,
        )

        sheet = ET.fromstring(files["xl/worksheets/sheet1.xml"])
        self._set_cell_number(sheet, "C2", row.doc_date_serial)
        self._set_cell_number(sheet, "F2", row.delivery_date_serial)
        files["xl/worksheets/sheet1.xml"] = ET.tostring(
            sheet,
            encoding="utf-8",
            xml_declaration=True,
        )

        out = BytesIO()
        with ZipFile(out, "w", ZIP_DEFLATED) as zout:
            for name, data in files.items():
                zout.writestr(name, data)
        return out.getvalue()

    def _set_shared_string(self, items, key: str, value: str) -> None:
        idx = self.ROW2_SHARED_STRING_INDEXES[key]
        item = items[idx]
        for child in list(item):
            item.remove(child)
        text = ET.SubElement(item, f"{{{SHEET_NS}}}t")
        text.text = str(value)

    def _set_cell_number(self, sheet, cell_ref: str, value: int) -> None:
        cell = sheet.find(f".//m:c[@r='{cell_ref}']", NS)
        if cell is None:
            raise ValueError(f"template missing {cell_ref}")
        value_node = cell.find("m:v", NS)
        if value_node is None:
            value_node = ET.SubElement(cell, f"{{{SHEET_NS}}}v")
        value_node.text = str(value)
