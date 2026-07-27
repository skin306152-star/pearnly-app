# -*- coding: utf-8 -*-
"""日记账:每票三腿(借 收款科目 含税额 / 贷 销售收入 净额 / 贷 销项税 税额)。

金额一格都不写死 —— 全部按**本行自己的票号**SUMIF 回明细表。这样两件事同时成立:
会计在明细里改一个行金额,分录当场跟着动;她把核对无误的明细行删掉,这里只是数变小,
不会 #REF!。

借方是银行还是现金由票面付款方式决定(见 services/ledger/entries),不写死。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from services.excel import xlsx_style as sty
from services.ledger import xlsx_common as xc
from services.ledger.entries import AMOUNT_GROSS, AMOUNT_NET, JournalLeg, SIDE_DEBIT
from services.ledger.sheets.detail import DetailRefs

SHEET_JOURNAL = "สมุดรายวันทั่วไป"

COL_DATE = 1
COL_INVOICE = 2
COL_MEMO = 3
COL_ACCOUNT = 4
COL_DEBIT = 5
COL_CREDIT = 6

_HEADERS: Tuple[str, ...] = (
    "วันที่",
    "เลขที่บิล",
    "รายละเอียด",
    "เลขที่บัญชี",
    "เดบิต (บาท)",
    "เครดิต (บาท)",
)
_WIDTHS: Tuple[int, ...] = (14, 16, 46, 34, 16, 16)
_TOTAL_LABEL = "รวม"


@dataclass(frozen=True)
class JournalRefs:
    """试算平衡向日记账取数的唯一入口。三个区间都是**区间**不是单格,删行不炸。"""

    sheet: str
    account_range: str
    debit_range: str
    credit_range: str


def amount_formula(refs: DetailRefs, kind: str, criteria: str) -> str:
    """一格分录金额的公式。三种口径都从明细的行金额派生,同一条链上。"""
    if kind == AMOUNT_GROSS:
        return f"={refs.gross(criteria)}"
    if kind == AMOUNT_NET:
        return f"={refs.net(criteria)}"
    return f"={refs.vat(criteria)}"


def write_journal_sheet(
    ws, legs: Sequence[JournalLeg], refs: DetailRefs, *, title: str, banner: str
) -> JournalRefs:
    xc.write_title(ws, f"{title} · {SHEET_JOURNAL} (General Journal)", banner=banner)
    xc.write_header(ws, _HEADERS, _WIDTHS)

    row = xc.FIRST_DATA_ROW
    for leg in legs:
        xc.date_cell(ws, row, COL_DATE, leg.doc.doc_date)
        inv = xc.text_cell(ws, row, COL_INVOICE, leg.doc.invoice_number, align=sty.center())
        xc.text_cell(ws, row, COL_MEMO, leg.memo)
        xc.text_cell(ws, row, COL_ACCOUNT, leg.account.label)
        formula = amount_formula(refs, leg.amount_kind, inv.coordinate)
        target = COL_DEBIT if leg.side == SIDE_DEBIT else COL_CREDIT
        other = COL_CREDIT if target == COL_DEBIT else COL_DEBIT
        xc.money_cell(ws, row, target, formula)
        xc.money_cell(ws, row, other, None)
        row += 1

    last = max(row - 1, xc.FIRST_DATA_ROW)
    xc.text_cell(ws, row, COL_MEMO, _TOTAL_LABEL, align=sty.right())
    for col, letter in ((COL_DEBIT, "E"), (COL_CREDIT, "F")):
        xc.money_cell(ws, row, col, f"=SUM({letter}{xc.FIRST_DATA_ROW}:{letter}{last})")
    xc.bold_row(ws, row, (COL_MEMO, COL_DEBIT, COL_CREDIT))

    return JournalRefs(
        sheet=SHEET_JOURNAL,
        account_range=xc.abs_range(SHEET_JOURNAL, COL_ACCOUNT, xc.FIRST_DATA_ROW, last),
        debit_range=xc.abs_range(SHEET_JOURNAL, COL_DEBIT, xc.FIRST_DATA_ROW, last),
        credit_range=xc.abs_range(SHEET_JOURNAL, COL_CREDIT, xc.FIRST_DATA_ROW, last),
    )
