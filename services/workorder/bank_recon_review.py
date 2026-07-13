# -*- coding: utf-8 -*-
"""银行对账人审裁决写回(MC1-b3 · E2 记的债:review 清单逐笔接受/拒绝)。

review 清单(60-85 分待人审,api.bank_recon_raw 的 recon.review)逐笔「接受候选/拒绝」落
human_decision 事件——payload 用 statement_tx_id(工单事件流→银行对账候选适配器给每笔
流水的内容指纹,见 services/recon/workorder_recon_adapter.tx_from_statement_row)取代
item_id(流水行不是 work_order_item,没有 items 表身份)。复用 api.record_decision 同族
的裁决范式:append-only、latest-wins 回放(改判=再落一条,读侧 evidence.
bank_recon_decisions 取最后一条),不另造 dedupe_key——与 record_decision 对 item 的
human_decision 同一套幂等哲学(存量多条按落库顺序回放,不是 DB 层去重)。

只改佐证呈现层:落库前校验 statement_tx_id 确实在当前 review 清单里、accept 的
candidate_id 确实是该笔的候选之一——防止裁决落在早已被税额路径抛开的银行对账佐证之外。
R1/R2/R4 税额路径、R3 材料存在性判定一行不碰。冻结后只读:路由层复用
archive.assert_mutable(同 record_decision/batch_decisions 惯例)。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import api, decisions, evidence, store

_DECISION_STEP = "reconcile"
_EVT_DECISION = "human_decision"

_ACTION_TO_DECISION = {
    "accept": decisions.BANK_RECON_ACCEPT,
    "reject": decisions.BANK_RECON_REJECT,
}


def record_bank_decision(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    statement_tx_id: str,
    action: str,
    candidate_id: Optional[str],
    actor: str,
) -> dict:
    """落一笔银行对账 review 人审裁决。accept 必须带 candidate_id 且须在该笔候选集内;
    reject 忽略 candidate_id(否掉全部候选,不采信任何一个)。statement_tx_id 必须确实
    落在当前 review 清单——tx 不在人审桶(已自动匹配/缺票/对账闸关)一律拒,不接受裁决
    落在佐证清单之外。"""
    decision = _ACTION_TO_DECISION.get(action)
    if decision is None:
        raise api.WorkOrderApiError("workorder.bank_recon_action_invalid")
    review_tx = _find_review_tx(cur, tenant_id, work_order_id, statement_tx_id)
    if review_tx is None:
        raise api.WorkOrderApiError("workorder.bank_recon_tx_not_found")
    if decision == decisions.BANK_RECON_ACCEPT:
        candidate_ids = {c.get("candidate_id") for c in review_tx.get("candidates") or []}
        if not candidate_id or candidate_id not in candidate_ids:
            raise api.WorkOrderApiError("workorder.bank_recon_candidate_invalid")
    else:
        candidate_id = None
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_DECISION_STEP,
        event_type=_EVT_DECISION,
        payload={
            "statement_tx_id": statement_tx_id,
            "decision": decision,
            "candidate_id": candidate_id,
        },
        actor=actor,
    )


def _find_review_tx(
    cur, tenant_id: str, work_order_id: str, statement_tx_id: str
) -> Optional[dict]:
    """从当前 recon.review 清单里找这笔流水(未找到——空 id / tx 不在人审桶 / 对账闸关
    / 尚未跑到 reconcile,一律 None,调用方据此统一拒)。

    效率5:窄取 reconcile 步最后一条 step_done payload(store.last_step_done_payload)取 recon,
    不再 list_events 全量回放整条事件流——recon 只藏在 step_done 里,一张 SQL 直取即可。recon
    提取判定复用 evidence.bank_recon_from_step_done(与 api.bank_recon_raw 同一份,不另写)。"""
    if not statement_tx_id:
        return None
    payload = store.last_step_done_payload(
        cur, tenant_id=tenant_id, work_order_id=work_order_id, step=_DECISION_STEP
    )
    recon = evidence.bank_recon_from_step_done(payload)
    if not recon:
        return None
    for entry in recon.get("review") or []:
        if (entry.get("tx") or {}).get("statement_tx_id") == statement_tx_id:
            return entry
    return None
