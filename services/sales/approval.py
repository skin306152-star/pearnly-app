# -*- coding: utf-8 -*-
"""开具审批工作流(docs/16 §F · 纯状态迁移叶子)。

会计事务所代多家公司开票:有的要老板审批、有的图快直接开。审批是每租户/账套可开关的
策略(approval_mode,落 sales_settings),本模块只管单据的状态迁移,不判角色——角色
(审批人)由路由层 require_perm("sales.doc.approve") 把关,不在此自造权限体系。

状态机(在 document 的 draft/issued/void 基础上加):
    draft ──提交──> pending_approval ──批准──> (取号) issued
                          └──驳回──> rejected ──改──> draft

取号 / §86/4 完整性闸在「批准开出」那一刻跑(复用 document.finalize_issue),驳回的草稿
不占号。错误码(路由层映射):not_found / not_draft / not_pending + 继承 finalize 的闸码。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from services.sales import document as doc_svc


def submit_for_approval(cur, *, tenant_id: str, doc_id) -> Optional[str]:
    """提交审批:draft / rejected → pending_approval。返回错误码或 None。"""
    status = doc_svc._status_of(cur, tenant_id, doc_id, lock=True)
    if status is None:
        return "not_found"
    if status not in doc_svc.EDITABLE_STATUSES:
        return "not_draft"
    cur.execute(
        "UPDATE sales_documents SET status=%s, updated_at=now() WHERE tenant_id=%s AND id=%s",
        (doc_svc.STATUS_PENDING, tenant_id, doc_id),
    )
    return None


def approve(
    cur, *, tenant_id: str, doc_id, approver: Optional[str], prefix, reset: str, on: date, start=1
) -> tuple[Optional[dict], Optional[str]]:
    """审批通过:pending_approval → 取号开出 + 记审批人。返回 (doc, error_code)。"""
    row = doc_svc.lock_for_issue(cur, tenant_id, doc_id)
    if not row:
        return None, "not_found"
    if row["status"] != doc_svc.STATUS_PENDING:
        return None, "not_pending"
    return doc_svc.finalize_issue(
        cur,
        tenant_id=tenant_id,
        doc_id=doc_id,
        row=row,
        prefix=prefix,
        reset=reset,
        on=on,
        start=start,
        approved_by=approver or "",
    )


def reject(cur, *, tenant_id: str, doc_id, reason: Optional[str] = None) -> Optional[str]:
    """驳回:pending_approval → rejected(留驳回理由)。返回错误码或 None。"""
    status = doc_svc._status_of(cur, tenant_id, doc_id, lock=True)
    if status is None:
        return "not_found"
    if status != doc_svc.STATUS_PENDING:
        return "not_pending"
    cur.execute(
        "UPDATE sales_documents SET status=%s, rejected_reason=%s, updated_at=now() "
        "WHERE tenant_id=%s AND id=%s",
        (doc_svc.STATUS_REJECTED, reason, tenant_id, doc_id),
    )
    return None
