# -*- coding: utf-8 -*-
"""台账/流水行抽取(gl_ledger / bank_statement 共用)。

两种行格式统一处理:
  A) 借贷余额三栏(MR.ERP GL):行尾 = debit credit balance
  B) 单金额 + 跑余额两栏(银行/刷卡结算):行尾 = amount balance,借贷方向靠余额变动判

期初余额来源:科目分节标题行的行尾余额,或 "ยอดยกมา / Balance Forward" 行。
守恒校验在 validate.py 做,本模块只负责忠实抽取。
"""

import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from services.fileconv.amounts import MONEY_RE, repair_number_spaces, trailing_money_block
from services.fileconv.model import LedgerRow
from services.recon.field_comparator import parse_date  # พ.ศ. 2 位/4 位年坑已修,不重造

# 行首日期:d/m/y 或 dd/mm/yyyy(佛历年在 validate/日期归一时才转)。ASCII 数字,避开泰数字。
_DATE_RE = re.compile(r"^([0-9]{1,2}[/\-.][0-9]{1,2}[/\-.][0-9]{2,4})\b")
# 科目分节标题:行首科目代码(如 1113-01)+ 随后非数字文字。
_ACCT_RE = re.compile(r"^([0-9]{3,4}(?:-[0-9]{1,3})?)\s+\D")
# 凭证号:字母打头 + 字母数字/斜杠/连字符。
_DOCNO_RE = re.compile(r"[A-Za-z][A-Za-z0-9/\-]{2,}")

# 列头行标记(重复出现于每页,须跳过,不当数据行)。
_COLUMN_HEADER_MARKERS = (
    "เดบิต",
    "เครดิต",
    "ยอดคงเหลือ",
    "คำอธิบาย",
    "debit",
    "credit",
)
# 期初/承前余额行标记。
_OPENING_MARKERS = ("balance forward", "brought forward", "ยอดยกมา", "ยกมา")


def _is_column_header(line: str) -> bool:
    low = line.lower()
    hits = sum(1 for m in _COLUMN_HEADER_MARKERS if m in low or m in line)
    # 两个及以上列名同现 = 列头(单个 "credit" 可能是描述词,不误杀)。
    return hits >= 2


def _is_opening_line(line: str) -> bool:
    low = line.lower()
    return any(m in low or m in line for m in _OPENING_MARKERS)


def _trailing_block_start(line: str) -> int:
    """行尾连续金额块首 token 的起始下标(无金额则返回 len(line))。"""
    matches = list(MONEY_RE.finditer(line))
    if not matches:
        return len(line)
    start = matches[-1].start()
    for prev in reversed(matches[:-1]):
        if line[prev.end() : start].strip():
            break
        start = prev.start()
    return start


def _split_middle(line: str, date: str) -> Tuple[str, str]:
    """从数据行取 (doc_no, description):日期之后、行尾金额块之前的一段。"""
    date_end = line.find(date) + len(date)
    middle = line[date_end : _trailing_block_start(line)].strip()
    m = _DOCNO_RE.search(middle)
    return (m.group(0) if m else ""), middle


def extract_ledger(pages: List[str]) -> Tuple[List[LedgerRow], Dict[str, Decimal]]:
    """抽台账行 + 每科目期初余额。

    返回 (rows, opening) —— rows 按文档顺序,opening[account] = 该科目首见期初余额。
    account 为空串表示单一无编号账户(如英文银行流水)。
    """
    rows: List[LedgerRow] = []
    opening: Dict[str, Decimal] = {}
    account = ""
    line_no = 0

    for page in pages:
        for raw in page.split("\n"):
            line_no += 1
            line = repair_number_spaces(raw.strip())
            if not line:
                continue
            if _is_column_header(line):
                continue

            is_date_row = bool(_DATE_RE.match(line))

            # 科目分节标题(非日期行)→ 记期初,切换当前科目。
            m_acct = _ACCT_RE.match(line)
            if m_acct and not is_date_row:
                account = m_acct.group(1)
                block = trailing_money_block(line)
                opening.setdefault(account, block[-1] if block else Decimal("0"))
                continue

            # 期初/承前余额行(可能带日期)→ 记期初,不计入数据行。
            if _is_opening_line(line):
                block = trailing_money_block(line)
                opening.setdefault(account, block[-1] if block else Decimal("0"))
                continue

            if not is_date_row:
                # 描述换行/页眉页脚等非数据行 —— 跳过,不污染。
                continue

            block = trailing_money_block(line)
            if len(block) < 2:
                continue

            date = _DATE_RE.match(line).group(1)
            ce = parse_date(date)
            date_ce = ce.isoformat() if ce else ""
            doc_no, description = _split_middle(line, date)

            if len(block) >= 3:
                debit, credit, balance = block[-3], block[-2], block[-1]
                rows.append(
                    LedgerRow(
                        line_no=line_no,
                        account=account,
                        date=date,
                        date_ce=date_ce,
                        doc_no=doc_no,
                        description=description,
                        balance=balance,
                        debit=debit,
                        credit=credit,
                    )
                )
            else:
                amount, balance = block[-2], block[-1]
                rows.append(
                    LedgerRow(
                        line_no=line_no,
                        account=account,
                        date=date,
                        date_ce=date_ce,
                        doc_no=doc_no,
                        description=description,
                        balance=balance,
                        amount=amount,
                    )
                )

    return rows, opening


def to_table_rows(rows: List[LedgerRow]) -> List[List]:
    """LedgerRow → xlsx 单元格行。单金额列格式把金额归入余额变动方向。"""
    out: List[List] = []
    for r in rows:
        out.append(
            [
                r.account,
                r.date,
                r.date_ce,
                r.doc_no,
                r.description,
                r.debit,
                r.credit,
                r.amount,
                r.balance,
            ]
        )
    return out


LEDGER_COLUMNS = [
    "รหัสบัญชี / Account",
    "วันที่ / Date",
    "วันที่ (ค.ศ.) / Date CE",
    "เลขที่ / Doc No",
    "คำอธิบาย / Description",
    "เดบิต / Debit",
    "เครดิต / Credit",
    "จำนวนเงิน / Amount",
    "ยอดคงเหลือ / Balance",
]
