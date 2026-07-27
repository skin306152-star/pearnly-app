# -*- coding: utf-8 -*-
"""试算平衡:借贷汇总 + 平不平。

两处与同类工作簿的金标不同,都是本仓踩过的坑:

1. 金标用 `='สมุดรายวันทั่วไป'!$E$13` 直指日记账的合计格 —— 会计一删日记账的行就 #REF!,
   整张表废。这里改成按**科目名**SUMIF 日记账的借贷两列,删行只让结果变小。
2. 「ถูกต้อง (Balanced)」那一格**只给眼睛看,不是闸**。它能在结果已错时显示绿(金标就会:
   改了行金额而 VAT 是死值,借贷仍相等)。权威判定由回导时我们的代码重算并写进回执。
   格子下面把这句话明写出来,不让它冒充结论。
"""

from __future__ import annotations

from typing import Sequence, Tuple

from services.excel import xlsx_style as sty
from services.ledger import xlsx_common as xc
from services.ledger.accounts import AccountRef
from services.ledger.sheets.journal import JournalRefs

SHEET_TRIAL_BALANCE = "งบทดลอง"

COL_ACCOUNT = 1
COL_DEBIT = 2
COL_CREDIT = 3

_HEADERS: Tuple[str, ...] = ("เลขที่บัญชี / ชื่อบัญชี", "เดบิต (บาท)", "เครดิต (บาท)")
_WIDTHS: Tuple[int, ...] = (44, 18, 18)
_TOTAL_LABEL = "รวม"
_CHECK_LABEL = "ตรวจสอบ: เดบิต = เครดิต หรือไม่"
_BALANCED = "ถูกต้อง (Balanced)"
_UNBALANCED = "ไม่ถูกต้อง"
_DISCLAIMER = (
    "ช่องตรวจสอบด้านบนใช้ดูด้วยตาเท่านั้น · ผลที่ถือเป็นทางการมาจากใบตอบรับของระบบ"
    "เมื่อนำไฟล์นี้กลับเข้าระบบ (自检格仅供参考 · 以系统回执为准)"
)


def _net_side(refs: JournalRefs, criteria: str, *, debit_side: bool) -> str:
    """该科目在这一侧的净额。两侧都发生过的科目按净额落在应落的一侧,与 books.py 同口径。"""
    plus = refs.debit_range if debit_side else refs.credit_range
    minus = refs.credit_range if debit_side else refs.debit_range
    return (
        f"=MAX(0,{xc.sumif(refs.account_range, criteria, plus)}"
        f"-{xc.sumif(refs.account_range, criteria, minus)})"
    )


def write_trial_balance_sheet(
    ws,
    accounts: Sequence[AccountRef],
    refs: JournalRefs,
    *,
    title: str,
    banner: str,
    period_label: str = "",
) -> None:
    heading = f"{title} · {SHEET_TRIAL_BALANCE} (Trial Balance)"
    xc.write_title(ws, f"{heading} {period_label}".strip(), banner=banner)
    xc.write_header(ws, _HEADERS, _WIDTHS)

    row = xc.FIRST_DATA_ROW
    for account in accounts:
        cell = xc.text_cell(ws, row, COL_ACCOUNT, account.label)
        criteria = f"${cell.column_letter}${row}"
        xc.money_cell(ws, row, COL_DEBIT, _net_side(refs, criteria, debit_side=True))
        xc.money_cell(ws, row, COL_CREDIT, _net_side(refs, criteria, debit_side=False))
        row += 1

    first, last = xc.FIRST_DATA_ROW, row - 1
    total_row = row
    xc.text_cell(ws, total_row, COL_ACCOUNT, _TOTAL_LABEL)
    for col, letter in ((COL_DEBIT, "B"), (COL_CREDIT, "C")):
        value = f"=SUM({letter}{first}:{letter}{last})" if accounts else 0
        xc.money_cell(ws, total_row, col, value)
    xc.bold_row(ws, total_row, (COL_ACCOUNT, COL_DEBIT, COL_CREDIT))

    check_row = total_row + 2
    xc.text_cell(ws, check_row, COL_ACCOUNT, _CHECK_LABEL)
    check = ws.cell(
        row=check_row,
        column=COL_DEBIT,
        value=f'=IF(ROUND(B{total_row}-C{total_row},2)=0,"{_BALANCED}","{_UNBALANCED}")',
    )
    sty.style_cell(check, align=sty.center())
    note = ws.cell(row=check_row + 1, column=COL_ACCOUNT, value=_DISCLAIMER)
    note.font = sty.Font(italic=True, color="9C4221")
    note.alignment = sty.left()
