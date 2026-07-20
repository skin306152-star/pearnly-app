# -*- coding: utf-8 -*-
"""人工填销项(W4 补料流)。从 api.py 抽出的独立单元:校验 → 落件 → 落事件,不碰其他编排。

落的是与 classify 直读同构的 item_classified(sales_summary)事件,sales_read 载荷带单行合成
表 —— reconcile 的 _replay_sales_reads/aggregate_sales 原样回放解锁 R2,引擎/steps 不改一行。

store 由调用方注入(api 传它自己的模块级绑定),本件不 import store:api 的测试替身换的是
api.store,注入才让替换一路生效,也让这层能脱库单测。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from services.workorder import kinds

SALES_KIND = kinds.SALES_SUMMARY
MANUAL_SOURCE = "manual"
MANUAL_SALES_DEDUPE = "manual:sales_summary"
MANUAL_ENTRY = "manual_entry"
MAX_NOTE_LEN = 500
MAX_SOURCE_LABEL_LEN = 60
# aggregate_sales 靠表头关键词认「销售额列 / 销项税列」;人工填的两个合计以泰文规范列名 +
# 单数据行合成表落库,与真实汇总表直读产出的 sales_read 形状一致(不另造契约)。
SALES_HEADER = "ยอดขาย"
OUTPUT_VAT_HEADER = "ภาษีขาย"

_EVT_CLASSIFIED = "item_classified"


def valid_amount(raw, error) -> str:
    """销项金额校验:十进制字符串、有限、非负。返回规范化字符串(全程 str/Decimal,禁 float)。
    去千分位后交 Decimal,解不出/负数/非有限一律拒。error 是调用方的异常类型(HTTP 码映射在那侧)。"""
    if raw is None:
        raise error("workorder.sales_summary_invalid")
    s = str(raw).strip().replace(",", "")
    if not s:
        raise error("workorder.sales_summary_invalid")
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise error("workorder.sales_summary_invalid") from exc
    if not value.is_finite() or value < 0:
        raise error("workorder.sales_summary_invalid")
    return format(value, "f")


def valid_source_label(raw, error) -> Optional[str]:
    """来源标识规范化:去首尾空白、折叠内部空白;空 → None(= 不分来源的向后兼容路)。"""
    if raw is None:
        return None
    label = " ".join(str(raw).split())
    if not label:
        return None
    if len(label) > MAX_SOURCE_LABEL_LEN:
        raise error("workorder.sales_summary_source_too_long")
    return label


def record(
    cur,
    *,
    store,
    error,
    tenant_id: str,
    work_order_id: str,
    sales_amount,
    output_vat,
    note: Optional[str],
    actor: str,
    source_label: Optional[str] = None,
) -> dict:
    """落一条人工销项。凭据备注随载荷留底(状态诚实:交付包据此标注「来源=人工申报」,
    不与直读混淆)。

    幂等按来源分槽:source_label 参与 dedupe_key,不同来源各占一条 item,aggregate_sales 天然
    相加(冰厂实测一个月要自开票 + 7-11 + Big C 三条并存);同来源重填 latest-wins 覆盖旧值,
    不重复计入。source_label 省略 = 现状那一条固定槽,行为逐字节不变。
    """
    sales_s = valid_amount(sales_amount, error)
    vat_s = valid_amount(output_vat, error)
    note_s = (note or "").strip()
    if len(note_s) > MAX_NOTE_LEN:
        raise error("workorder.sales_summary_note_too_long")
    label = valid_source_label(source_label, error)

    item = store.add_item(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        source=MANUAL_SOURCE,
        kind=SALES_KIND,
        status="ok",
        dedupe_key=MANUAL_SALES_DEDUPE if label is None else f"{MANUAL_SALES_DEDUPE}:{label}",
    )
    sales_read = {
        "headers": [SALES_HEADER, OUTPUT_VAT_HEADER],
        "rows": [{"cells": [sales_s, vat_s], "is_summary": False}],
        "source": MANUAL_ENTRY,
        "note": note_s,
    }
    if label is not None:
        sales_read["source_label"] = label
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step="classify",
        event_type=_EVT_CLASSIFIED,
        payload={
            "item_id": item["id"],
            "kind": SALES_KIND,
            "status": "ok",
            "sales_read": sales_read,
        },
        actor=actor,
    )
