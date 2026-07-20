# -*- coding: utf-8 -*-
"""classify 归堆时的票面/EDC 证据快照构造(纯函数,从 classify 抽出 · 单一职责)。

只搬 OCR 读出的原值进 item_classified 事件,不做任何 Decimal 换算/判读——精度交
reconcile/sales_agg。从 classify.py 拆出以守 500 行铁律;逐字段契约与语义不变。
"""

from __future__ import annotations

import re


def money_fields(fields: dict) -> dict:
    """票面钱字段快照(进 item_classified 事件,供 reconcile 回放合计/试算)。Decimal 交给
    reconcile,这里只搬 OCR 原值不做换算——净额/税额/含税额 + 票号税号做证据溯源。

    date/seller_name 是 E1 银行对账候选的日期/供应商锚(佐证层),纯附加字段,不参与 R1/R2
    税额计算(reconcile_gates 只读 subtotal/vat/total_amount)——缺失即为 None,对已有金标零影响。

    buyer_tax 同为纯佐证附加(R4 税号守护闸跨料聚合票面税号用:自家为买方的进项票上,买方
    税号反复出现即锚回真登记税号)——reconcile 不读它,加键对钱面零影响。
    """
    return {
        "subtotal": fields.get("subtotal"),
        "vat": fields.get("vat"),
        "total_amount": fields.get("total_amount"),
        # 折扣纯佐证:reconcile 只读净/税/含税三项,不参与合计。带上是因为它可能是系统
        # 回填的(sanity.infer_missing_discount),审核卡要说得出「补了多少钱」。
        "discount": fields.get("discount"),
        "invoice_number": fields.get("invoice_number"),
        "seller_tax": fields.get("seller_tax"),
        "buyer_tax": fields.get("buyer_tax") or fields.get("buyer_tax_id"),
        "invoice_date": fields.get("date"),
        "vendor": fields.get("seller_name"),
    }


# KBANK 系结算票脚注里的批次/终端号(BATCH# 000186 / TID:62608078 两种写法都在真料出现过)。
_EDC_BATCH_RE = re.compile(r"batch\s*[#:]?\s*(\d{3,})", re.IGNORECASE)
_EDC_TID_RE = re.compile(r"tid\s*[#:]?\s*(\d{4,})", re.IGNORECASE)


def edc_fields(fields: dict) -> dict:
    """EDC 结算票快照(进 item_classified 事件,SA-2b 回放喂 sales_agg 聚合)。字段逐字段
    对齐 services/sales_agg/model.py::EdcSettlement 输入契约(settle_date/gross_amount/
    fee_amount/net_amount/batch_no/terminal_id),不另造形状。

    KBANK 商户联结算票不印手续费/净额 → 两者恒 None 如实缺失(SA-1 对毛额缺失显式点名、
    绝不静默归 0,net+fee 齐才回推);批次/终端号从 notes 脚注拾取,拾不到留空——SA-1
    无锚不算去重指纹,不硬造。这里只搬 OCR 原值,Decimal 化交聚合层。"""
    notes = str(fields.get("notes") or "")
    batch = _EDC_BATCH_RE.search(notes)
    tid = _EDC_TID_RE.search(notes)
    return {
        "settle_date": fields.get("date"),
        "gross_amount": fields.get("total_amount") or fields.get("subtotal"),
        "fee_amount": None,
        "net_amount": None,
        "batch_no": batch.group(1) if batch else "",
        "terminal_id": tid.group(1) if tid else "",
    }
