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
from core.route_helpers import _plan_permissions
from services.agent import copy_map
from services.agent.contracts import AgentContext, ToolResult


def _retention(user: dict) -> Optional[int]:
    """历史保留天数 —— 与网页 history_routes._check_history_access 同口径(按套餐,非原始字段)。

    此前误读 user["history_retention_days"](对多数号=0=不可查)→ Agent 一律返 0,与网页
    (按套餐给 7/90/365)矛盾。改走套餐权限:不给看历史返 0,否则返套餐保留天数。
    """
    p = _plan_permissions((user or {}).get("plan"))
    if not p.get("can_view_history"):
        return 0
    return int(p.get("history_retention_days", 7))


class AgentToolset:
    # ── A 档:只读(无需确认) ──────────────────────────────────────────

    def list_ocr_history(self, ctx: AgentContext, *, keyword=None, status=None) -> ToolResult:
        # workspace_client_id=None:跨该租户可见的全部套账聚合(LINE 无顶栏切换器,查询默认聚合;
        # 否则只看默认套账,数据在别的套账就查不到)。RLS + restrict_client_ids 仍锁租户/可见客户。
        res = db.list_ocr_history(
            user_id=str(ctx.user["id"]),
            tenant_id=ctx.tenant_id,
            keyword=keyword,
            status_filter=status,
            workspace_client_id=None,
            limit=20,
            offset=0,
            retention_days=_retention(ctx.user),
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
        )
        items = res.get("items", []) if isinstance(res, dict) else []
        total = int(res.get("total", 0)) if isinstance(res, dict) else 0
        return ToolResult(ok=True, data=res, receipt=copy_map.history_receipt(items, total))

    def summarize_ocr_history(self, ctx: AgentContext) -> ToolResult:
        # 汇总走保留期窗口(与 list 同口径,数字对得上),非严格本月。
        ov = self._overview(ctx, this_month=False)
        return ToolResult(ok=True, data=ov, receipt=copy_map.history_summary_receipt(ov))

    def get_balance(self, ctx: AgentContext) -> ToolResult:
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        return ToolResult(ok=True, data=b, receipt=copy_map.balance_receipt(b))

    def get_usage_this_month(self, ctx: AgentContext) -> ToolResult:
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        # 用量是计费口径 → 本月;张数陪着页数一起本月。
        ov = self._overview(ctx, this_month=True, include_categories=False)
        docs = int(ov.get("doc_count") or 0)
        return ToolResult(
            ok=True, data={"billing": b, "docs": docs}, receipt=copy_map.usage_receipt(b, docs)
        )

    def _overview(
        self, ctx: AgentContext, *, this_month: bool, include_categories: bool = True
    ) -> dict:
        return db.docs_overview(
            str(ctx.user["id"]),
            ctx.tenant_id,
            workspace_client_id=None,
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
            retention_days=_retention(ctx.user),
            this_month=this_month,
            include_categories=include_categories,
        )

    def list_notification_logs(self, ctx: AgentContext) -> ToolResult:
        logs = db.list_notification_logs(str(ctx.user["id"]), tenant_id=ctx.tenant_id, limit=20)
        return ToolResult(ok=True, data=logs, receipt=copy_map.notifications_receipt(logs))

    # ── 套账(workspace):LINE 会话态「当前套账」列表/切换 ──
    def list_workspaces(self, ctx: AgentContext) -> ToolResult:
        from services.line_binding import line_workspace

        with db.get_cursor_rls(tenant_id=ctx.tenant_id, user_id=str(ctx.user["id"])) as cur:
            rows = line_workspace.list_active(cur, tenant_id=ctx.tenant_id)
            cur_id = line_workspace.current_workspace_id(cur, line_user_id=ctx.line_user_id)
        return ToolResult(ok=True, data={"workspaces": rows, "current_id": cur_id})

    def switch_workspace(self, ctx: AgentContext, *, name=None) -> ToolResult:
        from services.line_binding import line_workspace

        if not name:
            return ToolResult(ok=False, error_code="missing_name")
        with db.get_cursor_rls(
            tenant_id=ctx.tenant_id, user_id=str(ctx.user["id"]), commit=True
        ) as cur:
            match = line_workspace.match_by_name(cur, tenant_id=ctx.tenant_id, name=name)
            if not match:
                rows = line_workspace.list_active(cur, tenant_id=ctx.tenant_id)
                return ToolResult(
                    ok=False, error_code="workspace_not_found", data={"workspaces": rows}
                )
            hit = line_workspace.set_current(
                cur, line_user_id=ctx.line_user_id, workspace_client_id=match["id"]
            )
        if not hit:  # 没命中绑定行 → 别谎报成功
            return ToolResult(ok=False, error_code="not_bound")
        return ToolResult(ok=True, data={"switched_to": match})

    # ── B 档:写操作(M3 才开)· 样板留桩,展示确认前置 + 幂等 + 权限的形状 ──

    def push_to_erp(self, ctx: AgentContext, *, history_id=None, endpoint_id=None) -> ToolResult:
        return ToolResult(ok=False, error_code="not_implemented_m1")
