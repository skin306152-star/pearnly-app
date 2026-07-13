# -*- coding: utf-8 -*-
"""销项聚合(SA-1)三渠道输入契约:EDC 结算单 / 银行入账 / 销售税票·小票。

字段名与工单事件流既有 payload 对齐,SA-2 事件流适配零翻译:
- sales_doc 直接吃 classify._money_fields 的 money 快照(subtotal/vat/total_amount/
  invoice_number/seller_tax/invoice_date/vendor);
- bank_credit 直接吃 workorder_recon_adapter._tx_dict 的流水字典(tx_date/amount/
  description/direction/_tx_id,指纹即 bank_recon_types.StatementRow.row_hash);
- edc_settlement 仓库尚无先例 payload,本文件即规范定义(settle_date/gross_amount/
  fee_amount/net_amount/batch_no/terminal_id)。

适配层单一职责:普通 dict → 类型化行 + 逐字段缺失点名(issue 码交聚合层落 conflicts)。
钱一律 Decimal;缺失是 None 不是 0——毛额缺失静默归 0 会直接吃掉销项,「解不出」必须
显式上报,绝不静默吞(与 reconcile_gates.to_dec 的归 0 语义刻意不同)。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.recon.field_comparator import parse_date

# 三渠道 issue 码(聚合层拼渠道前缀落 conflicts,如 edc_gross_unresolved)。
ISSUE_DATE = "date_unresolved"
ISSUE_GROSS = "gross_unresolved"
ISSUE_GROSS_DERIVED = "gross_derived_from_net_plus_fee"
ISSUE_AMOUNT = "amount_unresolved"
ISSUE_NOT_CREDIT = "not_credit"


def to_money(value) -> Optional[Decimal]:
    """任意值 → Decimal;空/解不出 → None。

    float 不做算术、只经 str 转换止损(JSON 数字上游应以 Decimal 解析,见 cli.py);
    bool 是 int 子类但绝非金额,显式拒收。
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).replace(",", "").replace("฿", "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_day(value) -> Optional[date]:
    """任意日期值 → date。字符串走 field_comparator.parse_date(佛历/2位年单一事实源)。"""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return parse_date(value)


@dataclass(frozen=True)
class EdcSettlement:
    """一张 EDC 卡机结算单(日切):毛额 ยอดขาย 是销项口径,净额=毛额−手续费=银行到账。"""

    ref: str
    day: Optional[date]
    gross: Optional[Decimal]
    fee: Optional[Decimal]
    net: Optional[Decimal]
    batch_no: str
    terminal_id: str
    gross_derived: bool = False

    @classmethod
    def adapt(cls, payload: dict, index: int) -> tuple["EdcSettlement", list[str]]:
        issues: list[str] = []
        day = parse_day(payload.get("settle_date") or payload.get("date"))
        if day is None:
            issues.append(ISSUE_DATE)
        gross = to_money(payload.get("gross_amount"))
        fee = to_money(payload.get("fee_amount"))
        net = to_money(payload.get("net_amount"))
        derived = False
        if gross is None:
            # 毛额缺失但净额+手续费在手 → 按恒等式回推,仍点名让会计知道这数是推的。
            if net is not None and fee is not None:
                gross = net + fee
                derived = True
                issues.append(ISSUE_GROSS_DERIVED)
            else:
                issues.append(ISSUE_GROSS)
        return (
            cls(
                ref=_ref(payload, "edc", index),
                day=day,
                gross=gross,
                fee=fee,
                net=net,
                batch_no=str(payload.get("batch_no") or "").strip(),
                terminal_id=str(payload.get("terminal_id") or "").strip(),
                gross_derived=derived,
            ),
            issues,
        )

    @property
    def usable(self) -> bool:
        return self.day is not None and self.gross is not None


@dataclass(frozen=True)
class BankCredit:
    """一笔银行入账。只当交叉核对与缺口探测,永不计入销售(计入即与 EDC 毛额双计)。"""

    ref: str
    day: Optional[date]
    amount: Optional[Decimal]
    description: str
    tx_id: str
    is_credit: bool = True

    @classmethod
    def adapt(cls, payload: dict, index: int) -> tuple["BankCredit", list[str]]:
        issues: list[str] = []
        is_credit = str(payload.get("direction") or "IN").upper() != "OUT"
        if not is_credit:
            issues.append(ISSUE_NOT_CREDIT)
        day = parse_day(payload.get("tx_date") or payload.get("date"))
        if day is None:
            issues.append(ISSUE_DATE)
        amount = to_money(payload["amount"] if "amount" in payload else payload.get("deposit"))
        if amount is None:
            issues.append(ISSUE_AMOUNT)
        return (
            cls(
                ref=_ref(payload, "bank", index),
                day=day,
                amount=amount,
                description=str(payload.get("description") or ""),
                tx_id=str(
                    payload.get("_tx_id") or payload.get("tx_id") or payload.get("row_hash") or ""
                ),
                is_credit=is_credit,
            ),
            issues,
        )

    @property
    def usable(self) -> bool:
        return self.is_credit and self.day is not None and self.amount is not None


@dataclass(frozen=True)
class SalesDoc:
    """一张全额税票/销售小票(票面钱字段快照,与 item_classified 事件 money 同形)。"""

    ref: str
    day: Optional[date]
    net: Optional[Decimal]
    vat: Optional[Decimal]
    gross: Optional[Decimal]
    invoice_no: str

    @classmethod
    def adapt(cls, payload: dict, index: int) -> tuple["SalesDoc", list[str]]:
        issues: list[str] = []
        day = parse_day(payload.get("invoice_date") or payload.get("date"))
        if day is None:
            issues.append(ISSUE_DATE)
        net = to_money(payload.get("subtotal"))
        vat = to_money(payload.get("vat"))
        gross = to_money(payload.get("total_amount"))
        if gross is None:
            # 含税额缺失用 净+税 兜底 —— 与 sales_aggregate.aggregate_invoice_sales 同口径。
            if net is not None and vat is not None:
                gross = net + vat
            else:
                issues.append(ISSUE_GROSS)
        return (
            cls(
                ref=_ref(payload, "doc", index),
                day=day,
                net=net,
                vat=vat,
                gross=gross,
                invoice_no=str(payload.get("invoice_number") or "").strip(),
            ),
            issues,
        )

    @property
    def usable(self) -> bool:
        return self.day is not None and self.gross is not None


def _ref(payload: dict, channel: str, index: int) -> str:
    """源行引用:优先调用方给的 ref/item_id(SA-2 传工单 item id),缺省按渠道序号。"""
    return str(payload.get("ref") or payload.get("item_id") or f"{channel}:{index}")
