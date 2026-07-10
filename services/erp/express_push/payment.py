# -*- coding: utf-8 -*-
"""付款判据簇(Express/MR.ERP 共用 · 六级漏斗的家)。

从 common.py 拆出(体积闸 · 单一职责):现/赊判定的所有层级常量 + 判据函数都住这里。
common.py 经 re-export 对外暴露,既有全仓消费方(mapper/sales_mapper/routing/preflight 等)
零改动。钱一律 decimal,借贷/税额由确定性代码算(见 [[line-accounting-honest-status-boundary]])。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# 付款字段里代表"已付/现金"的信号(归一小写匹配)。
_PAID_TOKENS = ("paid", "cash", "qr", "promptpay", "prompt_pay", "transfer", "เงินสด", "จ่ายแล้ว")

SRC_MANUAL = "manual"  # F5 · 复核屏人工裁决(posting_payment_manual)· 最高优先级
SRC_EXPLICIT = "explicit"  # 票面付款字段(payment_status/method)直接给出
SRC_DOC_TYPE = "doc_type"  # 无付款字段 · 靠票种会计判据(收据=已付/税票=赊)推
SRC_PROFILE = "profile"  # F4 · 供应商过账档案默认(default_payment · 仅进项)
SRC_BANK = "bank"  # F6 · 银行流水命中同金额/方向/±7天交易(只加固已付,不反证未付)
SRC_NONE = ""  # 全无信号 · 留给各 mapper 的固定默认

# 合成票种来源标记 · producer=services/summary_import/mapping.py(批次「含VAT」勾选框合成
# document_type,非票面 OCR 证据)。payment_verdict 见此标记跳过票种判据层,防误摊现/赊。
DOC_TYPE_SOURCE_SYNTHETIC = "vat_checkbox"


def payment_verdict(
    fields: Dict[str, Any],
    *,
    profile: Optional[Dict[str, Any]] = None,
    bank_index: Optional[List[Dict[str, Any]]] = None,
    direction: str = "purchase",
    invoice_date: Any = None,
    total: Any = None,
) -> tuple[Optional[bool], str]:
    """票面是否已付 + 裁决来源(六级漏斗,可查哪层定的 · 验收/排障用)。

    优先级:① 人工裁决(posting_payment_manual · F5 复核屏显式改)> ② 票面显式付款字段
    (payment_status/method)> ③ 票种语义(收据在场=已收/已付,仅税票/贷项凭证=赊)>
    ④ 供应商过账档案默认(default_payment · F4 · 仅进项传 profile 才生效)> ⑤ 银行流水佐证
    (F6 · 命中同金额/方向/±7天交易即已付,不命中不反证未付,继续落空)> ⑥ 无信号
    (交各 mapper 的固定默认,如 Express 进项 RR / 销项 IV)。

    invoice_date/total 给 bank 佐证对账用:仓库惯例是 history 顶层字段权威(invoice_date/
    total_amount · 见 mapper 的 be_dates/amounts 取法),fields 常无 date/total_amount 两键,
    只读 fields 会静默不命中 —— 调用方传已解析的权威值,缺省才回落 fields 键。
    """
    manual = str(fields.get("posting_payment_manual") or "").strip().lower()
    if manual == "cash":
        return True, SRC_MANUAL
    if manual == "credit":
        return False, SRC_MANUAL

    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "paid":
        return True, SRC_EXPLICIT
    if status in ("unpaid", "credit"):
        return False, SRC_EXPLICIT
    method = str(fields.get("payment_method") or "").strip().lower()
    if method and any(tok in method for tok in _PAID_TOKENS):
        return True, SRC_EXPLICIT

    # document_type_source == DOC_TYPE_SOURCE_SYNTHETIC:汇总表批量建单场景下 document_type
    # 是用户「含VAT」勾选框合成的代理值(见 services/summary_import/mapping.py),不是票面
    # OCR 读出的真实票种证据 —— 不能当付款判据摊派现/赊,跳过本层落到档案/银行/默认层。真
    # OCR 票(无此标记)照旧吃票种语义。
    if fields.get("document_type_source") != DOC_TYPE_SOURCE_SYNTHETIC:
        from services.purchase.intake import doc_type_payment_hint

        hint = doc_type_payment_hint(fields.get("document_type"))
        if hint is not None:
            return hint, SRC_DOC_TYPE

    if profile:
        default_payment = str(profile.get("default_payment") or "").strip().lower()
        if default_payment == "cash":
            return True, SRC_PROFILE
        if default_payment == "credit":
            return False, SRC_PROFILE

    if bank_index:
        from services.erp.express_push.bank_evidence import bank_paid_match

        matched = bank_paid_match(
            bank_index,
            amount=(
                total if total is not None else (fields.get("total_amount") or fields.get("total"))
            ),
            invoice_date=invoice_date if invoice_date is not None else fields.get("date"),
            direction=direction,
        )
        if matched:
            return True, SRC_BANK

    return None, SRC_NONE


def payment_is_paid(fields: Dict[str, Any]) -> Optional[bool]:
    """票面是否已付:True 已付 / False 未付 / None 无信号(由各 mapper 定默认)。

    薄壳(不带 profile/bank_index)· 既有消费方零改动 · 六级漏斗前四级同旧行为。
    """
    return payment_verdict(fields)[0]


def payment_verdict_for(
    flat: Dict[str, Any],
    fields: Dict[str, Any],
    mappings: Optional[Dict[str, Any]],
    *,
    direction: str,
    total: Any = None,
) -> tuple[Optional[bool], str]:
    """payment_verdict 调用前的证据装配(mapper/sales_mapper/routing 三处调用点共用样板)。

    从 mappings 取供应商过账档案(仅 direction=="purchase" 传 profile · 档案锚是卖方税号,
    销项无此维度)+ 银行流水索引;invoice_date/total 按仓库惯例(flat 顶层权威值优先,
    fields 缺省才回落)—— total 调用方已传(mapper/sales_mapper 已求出的自洽金额)则不覆盖。
    """
    m = mappings or {}
    profile = m.get("_supplier_profile") if direction == "purchase" else None
    if total is None:
        total = flat.get("total_amount") or fields.get("total_amount")
    return payment_verdict(
        fields,
        profile=profile,
        bank_index=m.get("_bank_index"),
        direction=direction,
        invoice_date=flat.get("invoice_date") or fields.get("date"),
        total=total,
    )
