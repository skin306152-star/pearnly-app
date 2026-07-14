# -*- coding: utf-8 -*-
"""银行倒推销项行级人裁写回(SA-3a · 漏斗第 3 层)。

倒推建议清单里逐行「销售 / 非销售 / 待定」的人工改判落 human_decision 事件——payload 用
bank_sales_row(行指纹)取代 item_id(银行流水行不是 work_order_item,没有 items 表身份),
与 record_decision 对 item 的裁决、bank_recon_review 对 statement_tx_id 的裁决三者按载荷键
天然互斥(照 evidence.bank_recon_decisions 同款纪律)。

只改建议呈现层:落库前校验行指纹确实是本工单某条银行流水行,防裁决落在不存在的行上。
append-only、latest-wins(改判=再落一条,读侧 bank_sales_suggest.human_overlay 取最后一条),
不写申报数、不碰 R1/R2/R4 税额路径一个字。冻结后只读:路由层复用 archive.assert_mutable。
"""

from __future__ import annotations

from services.workorder import api, store
from services.workorder.steps import bank_sales_suggest as engine

_EVT_DECISION = "human_decision"
_VERDICTS = frozenset({engine.SALES, engine.NON_SALES, engine.PENDING})


def record_bank_sales_decision(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    fingerprint: str,
    verdict: str,
    actor: str,
) -> dict:
    """落一条银行倒推销项行级人裁。verdict ∈ {sales, non_sales, pending};fingerprint 必须确实是
    本工单某条银行流水行的指纹——不在流水行集(空指纹 / 野指纹 / 无银行料)一律拒。"""
    if verdict not in _VERDICTS:
        raise api.WorkOrderApiError("workorder.bank_sales_verdict_invalid")
    if not fingerprint or not _row_exists(cur, tenant_id, work_order_id, fingerprint):
        raise api.WorkOrderApiError("workorder.bank_sales_row_not_found")
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=engine.STEP,
        event_type=_EVT_DECISION,
        payload={engine.HUMAN_ROW_KEY: fingerprint, engine.HUMAN_VERDICT_KEY: verdict},
        actor=actor,
    )


def _row_exists(cur, tenant_id: str, work_order_id: str, fingerprint: str) -> bool:
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    return any(r["fingerprint"] == fingerprint for r in engine.parsed_rows_from_events(events))
