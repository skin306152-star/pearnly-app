# -*- coding: utf-8 -*-
"""执行器(M1-SOCKET-DESIGN §6)—— 以用户身份调现成 service。

每个 handler 一个方法,全程真实身份:复用 core.db 门面背后的 get_cursor_rls / 权限 / 计费,
绝不 bypass RLS、绝不绕计费。Agent 只能做该用户本就有权做的事。

M1 只实现 A 档只读方法;B 档(写操作)留桩到 M3,样板见 push_to_erp。
工具增多致本文件超 500 行时,按域拆 executor_readonly.py / executor_write.py,本文件只做聚合 re-export。
"""

from __future__ import annotations

from typing import Optional

from core import db
from services.agent import copy_map
from services.agent.contracts import AgentContext, ToolResult


def _retention(user: dict) -> Optional[int]:
    """用户的历史保留天数(None → list_ocr_history 自动按 user 表兜底)。"""
    v = (user or {}).get("history_retention_days")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


class AgentToolset:
    # ── A 档:只读(无需确认) ──────────────────────────────────────────

    def list_ocr_history(self, ctx: AgentContext, *, keyword=None, status=None) -> ToolResult:
        res = db.list_ocr_history(
            user_id=str(ctx.user["id"]),
            tenant_id=ctx.tenant_id,
            keyword=keyword,
            status_filter=status,
            workspace_client_id=ctx.workspace_client_id,
            limit=20,
            offset=0,
            retention_days=_retention(ctx.user),
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
        )
        items = res.get("items", []) if isinstance(res, dict) else []
        total = int(res.get("total", 0)) if isinstance(res, dict) else 0
        return ToolResult(ok=True, data=res, receipt=copy_map.history_receipt(items, total))

    def summarize_ocr_history(self, ctx: AgentContext) -> ToolResult:
        # status_counts 是全量分布(不受 limit 影响),只取它做汇总。
        res = db.list_ocr_history(
            user_id=str(ctx.user["id"]),
            tenant_id=ctx.tenant_id,
            workspace_client_id=ctx.workspace_client_id,
            limit=1,
            offset=0,
            retention_days=_retention(ctx.user),
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
        )
        counts = res.get("status_counts", {}) if isinstance(res, dict) else {}
        return ToolResult(ok=True, data=counts, receipt=copy_map.history_summary_receipt(counts))

    def get_balance(self, ctx: AgentContext) -> ToolResult:
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        return ToolResult(ok=True, data=b, receipt=copy_map.balance_receipt(b))

    def get_usage_this_month(self, ctx: AgentContext) -> ToolResult:
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        return ToolResult(ok=True, data=b, receipt=copy_map.usage_receipt(b))

    def list_notification_logs(self, ctx: AgentContext) -> ToolResult:
        logs = db.list_notification_logs(str(ctx.user["id"]), tenant_id=ctx.tenant_id, limit=20)
        return ToolResult(ok=True, data=logs, receipt=copy_map.notifications_receipt(logs))

    # ── B 档:写操作(M3 才开)· 样板留桩,展示确认前置 + 幂等 + 权限的形状 ──

    def push_to_erp(self, ctx: AgentContext, *, history_id=None, endpoint_id=None) -> ToolResult:
        return ToolResult(ok=False, error_code="not_implemented_m1")
