# -*- coding: utf-8 -*-
"""销售票 → 日记账分录腿(确定性,不过模型)。

每张票三腿:借「收到钱的地方」含税额 / 贷销售收入 净额 / 贷销项税 税额。
借方是银行还是现金由**票面付款方式**决定,不写死 —— 票面写 Bank Transfer 却记进现金,
账是平的但对不上银行流水,月底对账要找一天。读不出付款方式的票不出分录,进待判。

amount_kind 是给写表侧用的:表里那一格写的是公式(按票号 SUMIF 回明细),
这里给的 Decimal 是权威值 —— 回执里报的、测试断言的都是它。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Sequence, Tuple

from services.ledger.accounts import (
    ROLE_BANK,
    ROLE_CASH,
    ROLE_OUTPUT_VAT,
    ROLE_REVENUE,
    AccountRef,
    ChartResolution,
)
from services.ledger.models import SETTLE_CASH, SalesDoc

SIDE_DEBIT = "debit"
SIDE_CREDIT = "credit"

# 表里那一格的公式按哪种口径从明细算出来
AMOUNT_GROSS = "gross"
AMOUNT_NET = "net"
AMOUNT_VAT = "vat"

_MEMO_RECEIPT = {
    ROLE_CASH: "รับเงินสดค่าขายสินค้า บิลเลขที่ {inv}",
    ROLE_BANK: "รับเงินโอนค่าขายสินค้า บิลเลขที่ {inv}",
}
_MEMO_REVENUE = "บันทึกรายได้ค่าขายสินค้า บิลเลขที่ {inv}"
_MEMO_VAT = "บันทึกภาษีขาย บิลเลขที่ {inv}"

ZERO = Decimal("0")


@dataclass(frozen=True)
class JournalLeg:
    """日记账一行。account 已是解析后的科目(码可能来自账套桥,也可能是退回的通用码)。"""

    doc: SalesDoc
    account: AccountRef
    side: str
    amount: Decimal
    amount_kind: str
    memo: str

    @property
    def debit(self) -> Decimal:
        return self.amount if self.side == SIDE_DEBIT else ZERO

    @property
    def credit(self) -> Decimal:
        return self.amount if self.side == SIDE_CREDIT else ZERO


def settlement_role(doc: SalesDoc) -> str:
    return ROLE_CASH if doc.settlement == SETTLE_CASH else ROLE_BANK


def legs_for(doc: SalesDoc, chart: ChartResolution) -> List[JournalLeg]:
    """一张票的三腿。顺序固定:先借收款科目,再贷收入,最后贷销项税(会计读账的顺序)。"""
    role = settlement_role(doc)
    inv = doc.invoice_number
    return [
        JournalLeg(
            doc=doc,
            account=chart.of(role),
            side=SIDE_DEBIT,
            amount=doc.gross,
            amount_kind=AMOUNT_GROSS,
            memo=_MEMO_RECEIPT[role].format(inv=inv),
        ),
        JournalLeg(
            doc=doc,
            account=chart.of(ROLE_REVENUE),
            side=SIDE_CREDIT,
            amount=doc.net,
            amount_kind=AMOUNT_NET,
            memo=_MEMO_REVENUE.format(inv=inv),
        ),
        JournalLeg(
            doc=doc,
            account=chart.of(ROLE_OUTPUT_VAT),
            side=SIDE_CREDIT,
            amount=doc.vat,
            amount_kind=AMOUNT_VAT,
            memo=_MEMO_VAT.format(inv=inv),
        ),
    ]


def build_legs(docs: Sequence[SalesDoc], chart: ChartResolution) -> List[JournalLeg]:
    """全部可入账的票的分录腿。待判票不出分录 —— 方向/日期没定就记账,记的是错账。"""
    legs: List[JournalLeg] = []
    for doc in docs:
        if doc.bookable:
            legs.extend(legs_for(doc, chart))
    return legs


def ledger_accounts(legs: Sequence[JournalLeg]) -> List[AccountRef]:
    """分类账要开几个 T 字账 —— 按分录里出现的顺序去重,不预先摆一堆空科目。"""
    seen: dict[str, AccountRef] = {}
    for leg in legs:
        seen.setdefault(leg.account.label, leg.account)
    return list(seen.values())


def totals(legs: Sequence[JournalLeg]) -> Tuple[Decimal, Decimal]:
    return (
        sum((leg.debit for leg in legs), ZERO),
        sum((leg.credit for leg in legs), ZERO),
    )
