# -*- coding: utf-8 -*-
"""开出前的闸(docs/16 §J · 从 document.py 拆出 · 控行数)。

这一族的共同点:在【取号之前】跑,不过就返错误码,不占连号 —— 占了号再退回去就是跳号,
税局那边跳号要解释。纯函数叶子:只读传进来的那一行,不连库、不写库。

买方完整性(§B)不在这里,它在 services.sales.buyer.validate_buyer。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

# 收据 / 合并单开出前必须已收款(docs/16 §J3:收钱凭证无款不开)。
REQUIRE_PAYMENT = ("receipt", "tax_invoice_receipt")
PAYMENT_STATUSES = ("unpaid", "partial", "paid")

# 金额为 0 不许开出的单据 —— 全是"钱已经或将要易手"的凭证。
# 报价单不在内:它不是税务凭证,也不动货,฿0 的报价顶多是没写完。
REQUIRE_AMOUNT = ("tax_invoice", "tax_invoice_simple", "tax_invoice_receipt", "receipt")


def payment_gate(row: dict) -> Optional[str]:
    """§J3:收据/合并单开出时必须已收款(状态非 unpaid + 方式/日期齐)。"""
    if row["doc_type"] not in REQUIRE_PAYMENT:
        return None
    if (row.get("payment_status") or "unpaid") == "unpaid":
        return "payment_required"
    if not row.get("payment_method") or not row.get("payment_date"):
        return "payment_required"
    return None


def amount_gate(row: dict) -> Optional[str]:
    """合计 ≤ 0 的税票/收据不许开出。

    ฿0 的税票没有第二种成因:要么某一行的价没填(前端把"没设价"当 0 发了过来),要么走错了
    单据。两种都得当场停住 —— 一旦取到号、盖上 issued,这张票就进了 ภ.พ.30 的销项,货已经
    出门而票面写着 0,月底谁都对不出来,连"少收了一笔"这件事本身都没有痕迹。

    真的免费(赠品/试用装)照旧开得出:那是整单里的某一行为 0,合计仍然 > 0。整单为 0 的
    "全部免费"不是税票该干的事,出货单才是。同一条口径前端也有一份(sales-wizard-calc.priced
    → compliance.ckPrice),这里是最后一道:直调 API 的、以后换个前端的,都得过这一关。
    """
    if row["doc_type"] not in REQUIRE_AMOUNT:
        return None
    try:
        total = Decimal(str(row.get("grand_total") or 0))
    except (InvalidOperation, ValueError):
        # 合计读不出来 ≠ 合计没问题。宁可拦住让人看见,也不能蒙着头取号。
        return "zero_amount"
    return None if total > 0 else "zero_amount"
