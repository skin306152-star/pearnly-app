# -*- coding: utf-8 -*-
"""待判表:日期跨月、付款方式读不出、金额对不上的票 —— 不入账,但也不丢。

空表照写表头。会计打开发现没有这张表,分不清是「没有待判的」还是「这版没这功能」;
行数为 0 才是诚实的空态。

表名故意不叫 rt.SHEET_PENDING(「รอจำแนก」):那个名字是复核工作簿回导规格的一部分,
读侧按 Sheet 名判方向。这张表不进那条回导路,同名会让将来的读侧半命中。
"""

from __future__ import annotations

from typing import Sequence, Tuple

from services.excel import xlsx_style as sty
from services.ledger import xlsx_common as xc
from services.ledger.models import SalesDoc

SHEET_PENDING = "รายการรอจำแนก"

COL_DATE = 1
COL_INVOICE = 2
COL_CUSTOMER = 3
COL_TOTAL = 4
COL_PAYMENT = 5
COL_REASON = 6
COL_ROW_KEY = 7

_HEADERS: Tuple[str, ...] = (
    "วันที่",
    "เลขที่",
    "ลูกค้า",
    "รวมทั้งสิ้น",
    "วิธีชำระเงินบนเอกสาร",
    "เหตุผลที่ยังลงบัญชีไม่ได้",
    "รหัสอ้างอิงระบบ",
)
_WIDTHS: Tuple[int, ...] = (14, 16, 28, 16, 22, 52, 26)


def write_pending_sheet(ws, docs: Sequence[SalesDoc], *, title: str, banner: str) -> None:
    xc.write_title(ws, f"{title} · {SHEET_PENDING}", banner=banner)
    xc.write_header(ws, _HEADERS, _WIDTHS)
    xc.hide_column(ws, COL_ROW_KEY)

    fill = sty.fill_pending()
    row = xc.FIRST_DATA_ROW
    for doc in docs:
        xc.date_cell(ws, row, COL_DATE, doc.doc_date)
        xc.text_cell(ws, row, COL_INVOICE, doc.invoice_number, align=sty.center())
        xc.text_cell(ws, row, COL_CUSTOMER, doc.customer_name)
        cell = xc.money_cell(ws, row, COL_TOTAL, doc.gross)
        cell.fill = fill
        xc.text_cell(ws, row, COL_PAYMENT, doc.payment_method_raw or "-", align=sty.center())
        xc.text_cell(ws, row, COL_REASON, doc.pending_reason)
        xc.text_cell(ws, row, COL_ROW_KEY, doc.row_key)
        row += 1
