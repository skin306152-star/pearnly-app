# -*- coding: utf-8 -*-
"""
services/recon/bank_stmt_legacy_parsers.py · Pearnly

Per-bank text-layer statement parsers (KBank / SCB / BBL / generic) plus the
Gemini-vision fallback stub, and the ParsedStatement / BankTransaction shapes
they emit. Extracted verbatim from bank_recon_v2.py.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from services.recon.bank_stmt_legacy_fields import (
    _looks_like_outflow,
    _parse_amount,
    _normalize_thai_date,
    _find_account_last4,
    _find_period,
    _find_opening_closing,
    _month_of,
    _guess_channel,
)

# -----------------------------------------------------------------------------
# v118.34 - LEGACY BANK RECONCILIATION (migrated from bank_reconcile.py)
# Bank-statement-vs-invoice matching pipeline. Different product from
# bank_recon_v2's primary bank-statement-vs-GL reconciliation above -
# kept here so the project has a single home for bank reconciliation code.
# Used by /api/bank-recon/* routes in app.py.
# -----------------------------------------------------------------------------


@dataclass
class BankTransaction:
    """一条银行流水(解析后的标准结构)"""

    row_no: int
    tx_date: Optional[str]  # YYYY-MM-DD 字符串
    value_date: Optional[str]
    direction: str  # "IN" / "OUT"
    amount: float
    balance_after: Optional[float]
    description: str
    counterparty: Optional[str] = None
    ref_no: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class ParsedStatement:
    """对账单完整解析结果"""

    bank_code: str  # KBANK / SCB / BBL / OTHER
    account_last4: Optional[str]
    statement_month: Optional[str]  # YYYY-MM-01
    period_start: Optional[str]
    period_end: Optional[str]
    opening_balance: Optional[float]
    closing_balance: Optional[float]
    total_inflow: float
    total_outflow: float
    transactions: List[BankTransaction]
    pages: int
    parse_method: str  # "text_layer" / "gemini_vision"

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["transactions"] = [asdict(t) for t in self.transactions]
        return d


# ============================================================
# KBank 模板 · 列顺序:Date | Description | Cheque No | Deposit | Withdrawal | Balance
# ============================================================
# 示例行:01/12/24  TRANSFER FROM XXXX1234  5,000.00  123,456.78
# KBank 对账单一般是 DD/MM/YY 或 DD/MM/YYYY
_KBANK_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"  # date
    r"(.+?)\s+"  # description
    r"(?:([\d,]+\.\d{2})\s+)?"  # deposit (optional)
    r"(?:([\d,]+\.\d{2})\s+)?"  # withdrawal (optional)
    r"([\d,]+\.\d{2})"  # balance
)


def _parse_kbank_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening  # 用余额差推方向

    for i, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line:
            continue
        m = _KBANK_ROW.search(line)
        if not m:
            continue
        d_str, desc, dep, wdr, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        deposit = _parse_amount(dep)
        withdraw = _parse_amount(wdr)
        balance = _parse_amount(bal)

        # 先按"存款/取款"列判断(两列都有时用金额非零的那个)
        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        # 当有 2 个非零金额 · 或只有 1 个金额 · 用"余额差"兜底推方向
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                # 余额没变 · 看金额列
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            # 首行没有 prev_balance · 用关键词 + 金额列
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                # 都有金额,默认按第一个
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(
            BankTransaction(
                row_no=len(txs) + 1,
                tx_date=tx_date,
                value_date=tx_date,
                direction=direction,
                amount=amount,
                balance_after=balance,
                description=desc.strip(),
                channel=_guess_channel(desc),
            )
        )
        prev_balance = balance

    return ParsedStatement(
        bank_code="KBANK",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# SCB 模板 · 列顺序:Date | Time | Code | Channel | Description | Debit | Credit | Balance
# ============================================================
_SCB_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"  # date
    r"(?:\d{1,2}:\d{2}\s+)?"  # time (optional)
    r"(?:([A-Z]{2,}\d*)\s+)?"  # code (optional, like X0)
    r"(.+?)\s+"  # description
    r"(?:([\d,]+\.\d{2})\s+)?"  # debit
    r"(?:([\d,]+\.\d{2})\s+)?"  # credit
    r"([\d,]+\.\d{2})"  # balance
)


def _parse_scb_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _SCB_ROW.search(line)
        if not m:
            continue
        d_str, code, desc, debit, credit, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        dr = _parse_amount(debit)
        cr = _parse_amount(credit)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (cr, dr) if v and v > 0]
        if not amount_pool:
            continue

        # 余额差兜底(当 PDF 文本空白被压缩导致列错位时尤为重要)
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if cr and cr > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif cr and cr > 0 and not (dr and dr > 0):
                direction = "IN"
                amount = cr
            elif dr and dr > 0 and not (cr and cr > 0):
                direction = "OUT"
                amount = dr
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(
            BankTransaction(
                row_no=len(txs) + 1,
                tx_date=tx_date,
                value_date=tx_date,
                direction=direction,
                amount=amount,
                balance_after=balance,
                description=desc.strip(),
                channel=code or _guess_channel(desc),
            )
        )
        prev_balance = balance

    return ParsedStatement(
        bank_code="SCB",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# BBL 模板 · 列顺序和 KBank 接近
# ============================================================
_BBL_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"([A-Z]{2,5})?\s*"  # channel code(可选)
    r"(.+?)\s+"
    r"(?:([\d,]+\.\d{2})\s+)?"  # withdrawal
    r"(?:([\d,]+\.\d{2})\s+)?"  # deposit
    r"([\d,]+\.\d{2})"  # balance
)


def _parse_bbl_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _BBL_ROW.search(line)
        if not m:
            continue
        d_str, channel, desc, wdr, dep, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        withdraw = _parse_amount(wdr)
        deposit = _parse_amount(dep)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(
            BankTransaction(
                row_no=len(txs) + 1,
                tx_date=tx_date,
                value_date=tx_date,
                direction=direction,
                amount=amount,
                balance_after=balance,
                description=desc.strip(),
                channel=channel or _guess_channel(desc),
            )
        )
        prev_balance = balance

    return ParsedStatement(
        bank_code="BBL",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 其他银行 · 通用正则(找 日期 + 金额 + 余额 的行)
# ============================================================
_GENERIC_ROW = re.compile(
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s+"
    r"(.+?)\s+"
    r"(-?[\d,]+\.\d{2})\s+"  # 金额(可带负号)
    r"([\d,]+\.\d{2})"  # 余额
)


def _parse_generic_text(text: str, pages: int, bank_code: str) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _GENERIC_ROW.search(line)
        if not m:
            continue
        d_str, desc, amt_str, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        amt = _parse_amount(amt_str)
        balance = _parse_amount(bal)
        if not amt:
            continue

        direction = "OUT" if amt < 0 else "IN"
        amount = abs(amt)
        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(
            BankTransaction(
                row_no=len(txs) + 1,
                tx_date=tx_date,
                value_date=tx_date,
                direction=direction,
                amount=amount,
                balance_after=balance,
                description=desc.strip(),
                channel=_guess_channel(desc),
            )
        )

    return ParsedStatement(
        bank_code=bank_code,
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 扫描件 · Gemini vision 兜底(M10 轮 2 会真接通 · 本轮留 placeholder)
# ============================================================
def _parse_via_gemini(pdf_bytes: bytes, pages: int) -> ParsedStatement:
    """
    TODO M10 轮 2:接入 gemini_engine.recognize_pdf 的 vision 模式
    用一个专用 prompt 让 Gemini 输出 JSON:
    {
      "bank_code": "...",
      "account_last4": "...",
      "period_start": "YYYY-MM-DD",
      "transactions": [{"tx_date":"...","direction":"IN","amount":1000,"description":"..."}]
    }
    本轮:返回空结果 + 错误提示 · 让前端显示"扫描件暂不支持 · 请上传带文字层的 PDF"
    """
    return ParsedStatement(
        bank_code="OTHER",
        account_last4=None,
        statement_month=None,
        period_start=None,
        period_end=None,
        opening_balance=None,
        closing_balance=None,
        total_inflow=0.0,
        total_outflow=0.0,
        transactions=[],
        pages=pages,
        parse_method="gemini_vision_pending",
    )
