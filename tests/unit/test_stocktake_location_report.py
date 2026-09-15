"""Location exports compare immutable book places with active count entries."""

from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from unittest import TestCase

from openpyxl import load_workbook

from services.stocktake import reports


class StocktakeLocationReport(TestCase):
    def test_book_actual_comparison_excludes_voids_and_preserves_pairs(self):
        base = dict(
            product_code="001",
            product_name="Product",
            barcode="00001",
            unit="EA",
            warehouse="Book warehouse",
            location="Shelf 01",
            book_qty=Decimal("10"),
        )
        items = [
            dict(base, id="a", actual_qty=Decimal("10")),
            dict(base, id="b", actual_qty=None),
            dict(base, id="c", warehouse="", location="", actual_qty=Decimal("0")),
        ]
        now = datetime.now(UTC)

        def entry(item_id, warehouse, location, voided=False):
            return dict(
                base,
                item_id=item_id,
                warehouse=warehouse,
                location=location,
                quantity=Decimal("0"),
                voided=voided,
                counted_by_name="Counter",
                updated_by_name="Counter",
                counted_at=now,
                updated_at=now,
            )

        entries = [
            entry("a", "Book warehouse", "Shelf 01"),
            entry("a", "Other warehouse", "Shelf 02"),
            entry("a", "Voided warehouse", "Voided shelf", True),
            entry("c", "Actual warehouse", ""),
        ]
        wb = load_workbook(BytesIO(reports.workbook(dict(items=items, entries=entries))))
        summary, detail = wb.worksheets
        self.assertEqual([c.value for c in summary[1]], reports.SUMMARY)
        self.assertEqual(summary["I2"].value, "Book warehouse")
        self.assertEqual(summary["J2"].value, "Book warehouse\nOther warehouse")
        self.assertEqual(summary["K2"].value, "ไม่ตรงกัน")
        self.assertEqual(summary["M2"].value, "Shelf 01\nShelf 02")
        self.assertEqual(summary["N2"].value, "ไม่ตรงกัน")
        self.assertEqual(summary["F2"].value, 10)
        self.assertEqual(summary["K3"].value, "ยังไม่ได้นับ")
        self.assertEqual(summary["N3"].value, "ยังไม่ได้นับ")
        self.assertEqual(summary["F4"].value, 0)
        self.assertEqual(summary["K4"].value, "ไม่ได้ระบุในบัญชี")
        self.assertEqual(summary["N4"].value, "ไม่ได้ระบุในบัญชี")
        self.assertEqual(detail["N2"].value, "ตรงกัน")
        self.assertEqual(detail["P2"].value, "ตรงกัน")
        self.assertEqual(detail["D3"].value, "Other warehouse")
        self.assertEqual(detail["E3"].value, "Shelf 02")
        self.assertEqual(detail["M3"].value, "Book warehouse")
        self.assertEqual(detail["O3"].value, "Shelf 01")
        self.assertEqual(detail["N3"].value, "ไม่ตรงกัน")
        self.assertEqual(detail["J4"].value, "ยกเลิก (ไม่รวมยอด)")
        self.assertEqual(summary["C2"].value, "00001")
        self.assertEqual(summary["J2"].fill.fgColor.rgb, "00FFF2CC")
        self.assertEqual(summary["M2"].fill.fgColor.rgb, "00FFF2CC")
        self.assertEqual(summary["G2"].fill.patternType, None)
        self.assertEqual(summary["G3"].fill.patternType, None)
        self.assertEqual(summary["G4"].fill.fgColor.rgb, "00FFF2CC")
        self.assertEqual(detail["E2"].fill.patternType, None)
        self.assertEqual(detail["E3"].fill.fgColor.rgb, "00FFF2CC")
        self.assertEqual(detail["E4"].fill.patternType, None)
        # Explicit borders survive fills and viewers with gridlines switched off.
        for sheet in (summary, detail):
            for cells in sheet:
                for cell in cells:
                    for side in ("left", "right", "top", "bottom"):
                        self.assertEqual(getattr(cell.border, side).style, "thin")
                        self.assertEqual(getattr(cell.border, side).color.rgb, "00A6ACB3")
        wb.close()
