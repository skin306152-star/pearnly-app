# -*- coding: utf-8 -*-
"""管家写工具 erp_push 的留痕腿:推送日志一行 + 操作审计一条。

从 erp_push_tool 拆出(体积闸 <500 行)· 语义上也确实是另一件事:那边管「接地 → 投单 →
等结果」,这边只管「不管结果如何,都得留下谁在什么时候往哪个账套写过什么」。

两条留痕都不许把已经发生的写回滚掉 —— 桥那边可能已经落账,吞掉状态才是真事故,所以
两个函数各自 try/except 到底,失败只 warning。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from services.steward import tool_scope
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

_money = tool_scope.money  # 钱不过 float:卡上印的、比对的、审计的必须同一个值

AUDIT_SUBMITTED = "steward.erp_push_submitted"
AUDIT_REFUSED = "steward.erp_push_refused"

# 在途那一行的占位租约。Express 旧推送腿的队列 = 本表 status='pending' 且
# (lease_owner IS NULL OR lease_expires_at < NOW()) 的行(agent_store.lease_pending),
# 而这份载荷的 account_set 恰好过得了它的白名单 —— 不占住租约,桥这边还在写,小助手就把
# 同一份载荷领走再写一遍,ack 还会把如实记的「在途」抹成「已完成」。
_PENDING_LEASE_OWNER = "steward-bridge"
_PENDING_LEASE_S = 10 * 365 * 24 * 3600  # 十年 = 实际上永不释放(这行不是给人领的活)


def log_push(
    ctx: ToolContext,
    endpoint: dict,
    history: dict,
    payload: dict,
    status: str,
    data: dict,
    *,
    http_status: int = 202,
    leased: bool = False,
    code: str = "",
) -> None:
    """落 erp_push_logs 一行(推送状态唯一事实源;不落的话管家自己的推送查询看不见这次)。

    不设 next_retry_at:重试队列是给旧 pending 路径用的,桥直写的单绝不由后台自动重推。
    leased=True(在途那一行)另钉一个远期占位租约:pending 是 Express 旧队列的保留态,
    不占住租约,小助手会把同一份载荷领走再写一遍 —— 防的不是重试扫描,是 lease_pending。
    审计/日志写挂不回滚已经发生的写 —— 桥那边可能已经落账,吞掉状态才是真事故。

    code(桥的机器码)按 `[CODE] 人话` 落 error_msg —— 这是推送日志前端唯一认得的包装
    (guide_links.extractReasonCode)。此前只落桥那句人话,码丢在半路:卡片翻不出文案就把
    桥的原文(英文/中文)裸奔给泰国会计,教程深链也一并失效。
    """
    from core import db

    try:
        db.insert_push_log(
            user_id=ctx.user_id,
            endpoint_id=str(endpoint.get("id") or ""),
            history_id=str(history.get("id") or ""),
            invoice_no=payload.get("ref_no"),
            seller_name=str(history.get("seller_name") or ""),
            total_amount=Decimal(_money(payload.get("total_amount"))),
            status=status,
            http_status=http_status,
            request_body=payload,
            response_body=None,
            error_msg=error_msg(code, data.get("reason")),
            attempt=1,
            elapsed_ms=0,
            trigger="steward",
            lease_owner=_PENDING_LEASE_OWNER if leased else None,
            lease_seconds=_PENDING_LEASE_S if leased else 0,
        )
    except Exception:  # noqa: BLE001 — 日志写失败不改变桥那边的既成事实
        logger.warning("[steward.erp_push] push log write failed job=%s", data.get("job_id"))


def error_msg(code: str, reason: Optional[str]) -> Optional[str]:
    """`[CODE] 人话` —— 推送日志前端按这个形状抽码翻文案 + 挂教程深链;两者缺一都算没落地。"""
    text = str(reason or "").strip()
    if not code:
        return text or None
    return f"[{code}] {text}".strip() if text else f"[{code}]"


def audit(
    ctx: ToolContext,
    history: dict,
    payload: dict,
    job_id: str,
    *,
    action: str = AUDIT_SUBMITTED,
    reason: str = "",
) -> None:
    """写操作留痕:谁把哪张票投进了哪个账套(投单即记,不等结果 —— 结果可能永远等不到)。
    桥没收下的那两条走 AUDIT_REFUSED:没写进去也要有「谁在什么时候试图往哪个账套写」。"""
    try:
        from services.audit import store as audit_store

        audit_store.insert_operation_log(
            tenant_id=ctx.tenant_id,
            actor_user_id=ctx.user_id,
            actor_username=ctx.user.get("username"),
            actor_is_super=bool(ctx.user.get("is_super_admin")),
            action=action,
            target_type="ocr_history",
            target_id=str(history.get("id") or ""),
            target_name=payload.get("ref_no"),
            details={
                "job_id": job_id,
                "account_set": payload.get("account_set"),
                "direction": payload.get("direction"),
                "doctype": payload.get("doctype"),
                "total_amount": payload.get("total_amount"),
                # 载荷里只有逐行 item_mode,过账去向的原始声明在票上 —— 审计要留的是声明。
                "posting_kind": str(history.get("posting_kind") or ""),
                "reason": reason,
            },
        )
    except Exception:  # noqa: BLE001 — 审计挂不阻断已投出去的写活
        logger.warning("[steward.erp_push] audit write failed job=%s", job_id, exc_info=True)
