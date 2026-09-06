"""Thai product totals and count-location detail exported from one locked snapshot."""

from datetime import UTC
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

SUMMARY = [
    "รหัสสินค้า",
    "ชื่อสินค้า",
    "บาร์โค้ด / รหัส QR",
    "หน่วย",
    "จำนวนตามบัญชี",
    "จำนวนที่นับได้รวม",
    "ผลต่าง",
    "ผลการตรวจนับ",
]
DETAIL = [
    "รหัสสินค้า",
    "ชื่อสินค้า",
    "บาร์โค้ด / รหัส QR",
    "คลังสินค้า",
    "ตำแหน่งจัดเก็บ",
    "หน่วย",
    "จำนวนที่นับครั้งนี้",
    "ผู้ตรวจนับ",
    "เวลาที่นับ (UTC)",
    "สถานะรายการ",
    "ผู้แก้ไขล่าสุด",
    "เวลาแก้ไข (UTC)",
]


def _append(sheet, values):
    sheet.append(values)
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, Decimal) and len(cell.value.as_tuple().digits) > 15:
            cell.value = str(cell.value)
        if isinstance(cell.value, str):
            cell.data_type = "s"


def workbook(task):
    wb = Workbook()
    summary = wb.active
    summary.title = "สรุปผลตรวจนับ"
    _append(summary, SUMMARY)
    for row in task["items"]:
        actual = row["actual_qty"]
        difference = None if actual is None else actual - row["book_qty"]
        result = (
            "ยังไม่ได้นับ"
            if actual is None
            else ("ตรงกัน" if difference == 0 else "เกินบัญชี" if difference > 0 else "ขาดบัญชี")
        )
        _append(
            summary,
            [
                row["product_code"],
                row["product_name"],
                row["barcode"],
                row["unit"],
                row["book_qty"],
                actual,
                difference,
                result,
            ],
        )
    detail = wb.create_sheet("รายละเอียดการนับ")
    _append(detail, DETAIL)
    for entry in task["entries"]:
        _append(
            detail,
            [
                entry["product_code"],
                entry["product_name"],
                entry["barcode"],
                entry["warehouse"],
                entry["location"],
                entry["unit"],
                entry["quantity"],
                entry["counted_by_name"],
                entry["counted_at"].astimezone(UTC).isoformat(),
                "ยกเลิก (ไม่รวมยอด)" if entry["voided"] else "รวมยอด",
                entry["updated_by_name"],
                entry["updated_at"].astimezone(UTC).isoformat(),
            ],
        )
    for sheet in wb:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="202033")
            cell.fill = PatternFill("solid", fgColor="EAF0FF")
            sheet.column_dimensions[cell.column_letter].width = 25
        sheet.column_dimensions["B"].width = 36
        sheet.row_dimensions[1].height = 26
    out = BytesIO()
    wb.save(out)
    return out.getvalue()
