# -*- coding: utf-8 -*-
"""分类账:按科目的 T 字账,逐笔 + 递推余额。

余额口径与 services/accounting/books.py 一致:期末 = 期初 + 借 − 贷(带符号,借方为正)。
贷方常余额科目(收入/负债)因此显示为负数 —— 这是全仓一贯的口径,不在这里另立一套,
两套口径并存时对账没人说得清哪个对。科目标题行注明「เดบิตปกติ / เครดิตปกติ」。

借贷两列同样是按票号 SUMIF 回明细,不引用日记账的单元格 —— 引用日记账的格子,会计一删
日记账的行就 #REF!。
"""

from __future__ import annotations

from typing import Sequence, Tuple

from services.excel import xlsx_style as sty
from services.ledger import xlsx_common as xc
from services.ledger.entries import SIDE_DEBIT, JournalLeg, ledger_accounts
from services.ledger.sheets.detail import DetailRefs
from services.ledger.sheets.journal import amount_formula

SHEET_LEDGER = "บัญชีแยกประเภท"

COL_DATE = 1
COL_INVOICE = 2
COL_MEMO = 3
COL_DEBIT = 4
COL_CREDIT = 5
COL_BALANCE = 6

_HEADERS: Tuple[str, ...] = (
    "วันที่",
    "เลขที่บิล",
    "คำอธิบายรายการ",
    "เดบิต (บาท)",
    "เครดิต (บาท)",
    "ยอดคงเหลือ (บาท)",
)
_WIDTHS: Tuple[int, ...] = (14, 16, 46, 16, 16, 18)

_NORMAL_SIDE = {True: "เดบิตปกติ", False: "เครดิตปกติ"}
_CLOSING_LABEL = "รวม / ยอดคงเหลือปลายงวด"


def _write_account_block(
    ws, account, legs: Sequence[JournalLeg], refs: DetailRefs, row: int
) -> int:
    """写一个科目的 T 字账,返回下一个可用行号。"""
    title = ws.cell(
        row=row,
        column=COL_DATE,
        value=f"บัญชี {account.label} - {_NORMAL_SIDE[account.debit_normal]}",
    )
    title.font = sty.Font(bold=True)
    header_row = row + 1
    xc.write_header(ws, _HEADERS, _WIDTHS, row=header_row, freeze=False)

    first = header_row + 1
    cursor = first
    for leg in legs:
        xc.date_cell(ws, cursor, COL_DATE, leg.doc.doc_date)
        inv = xc.text_cell(ws, cursor, COL_INVOICE, leg.doc.invoice_number, align=sty.center())
        xc.text_cell(ws, cursor, COL_MEMO, leg.memo)
        formula = amount_formula(refs, leg.amount_kind, inv.coordinate)
        target = COL_DEBIT if leg.side == SIDE_DEBIT else COL_CREDIT
        other = COL_CREDIT if target == COL_DEBIT else COL_DEBIT
        xc.money_cell(ws, cursor, target, formula)
        xc.money_cell(ws, cursor, other, None)
        carry = f"F{cursor - 1}+" if cursor > first else ""
        xc.money_cell(ws, cursor, COL_BALANCE, f"={carry}D{cursor}-E{cursor}")
        cursor += 1

    last = cursor - 1
    xc.text_cell(ws, cursor, COL_MEMO, _CLOSING_LABEL, align=sty.right())
    xc.money_cell(ws, cursor, COL_DEBIT, f"=SUM(D{first}:D{last})")
    xc.money_cell(ws, cursor, COL_CREDIT, f"=SUM(E{first}:E{last})")
    xc.money_cell(ws, cursor, COL_BALANCE, f"=F{last}")
    xc.bold_row(ws, cursor, (COL_MEMO, COL_DEBIT, COL_CREDIT, COL_BALANCE))
    return cursor + 2  # 空一行再开下一个科目


def write_ledger_sheet(
    ws, legs: Sequence[JournalLeg], refs: DetailRefs, *, title: str, banner: str
) -> None:
    xc.write_title(ws, f"{title} · {SHEET_LEDGER} (General Ledger)", banner=banner)
    row = xc.HEADER_ROW
    for account in ledger_accounts(legs):
        row = _write_account_block(
            ws, account, [lg for lg in legs if lg.account.label == account.label], refs, row
        )
