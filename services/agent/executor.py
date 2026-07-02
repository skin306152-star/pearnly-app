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

    # ── A 档:M4 扩充(推送状态 / 税号核验 / 我的套餐) ──

    def _locate_doc(self, ctx: AgentContext, keyword):
        """按关键词定位一张单据(推送状态/推 ERP 共用锚点步)。
        返回 (hist, None) 或 (None, 失败 ToolResult):零命中→not_found;
        带词多命中→候选喂回让用户挑(绝不猜);无词→最近一张。"""
        res = db.list_ocr_history(
            user_id=str(ctx.user["id"]),
            tenant_id=ctx.tenant_id,
            keyword=keyword,
            workspace_client_id=None,
            limit=5,
            offset=0,
            retention_days=_retention(ctx.user),
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
        )
        items = res.get("items", []) if isinstance(res, dict) else []
        if not items:
            return None, ToolResult(ok=False, error_code="history_not_found")
        if keyword and len(items) > 1:
            cands = [
                {"vendor": i.get("seller_name") or "", "amount": i.get("total_amount")}
                for i in items
            ]
            return None, ToolResult(
                ok=False, error_code="ambiguous_doc", data={"candidates": cands}
            )
        return items[0], None

    def get_push_status(self, ctx: AgentContext, *, keyword=None) -> ToolResult:
        """某张单据推没推 ERP(镜像 erp_push_log_routes 的查询口径·erp_push_logs 唯一状态源)。

        keyword 定位单据:唯一命中查最新推送日志;多命中回候选让模型请用户挑(不猜);
        无 keyword 取最近一张。failed/未推绝不说成推送成功(状态诚实红线)。
        """
        p = _plan_permissions((ctx.user or {}).get("plan"))
        if not p.get("can_push_erp"):
            return ToolResult(ok=False, error_code="forbidden")
        hist, fail = self._locate_doc(ctx, keyword)
        if fail is not None:
            return fail
        logs = db.list_push_logs(
            str(ctx.user["id"]), history_id=str(hist.get("id")), limit=1, tenant_id=ctx.tenant_id
        )
        log = ((logs or {}).get("items") or [None])[0]
        status = (log or {}).get("status") or ""
        return ToolResult(
            ok=True,
            data={
                "doc": {
                    "vendor": hist.get("seller_name") or "",
                    "amount": hist.get("total_amount"),
                    "invoice_no": hist.get("invoice_no") or "",
                },
                "pushed": bool(log) and db.counts_as_endpoint_success(status),
                "status": status or "never_pushed",
                "endpoint": (log or {}).get("endpoint_name") or "",
                "when": str((log or {}).get("created_at") or ""),
                "error": (log or {}).get("error_msg") or "",
            },
        )

    def rd_lookup(self, ctx: AgentContext, *, tax_id=None) -> ToolResult:
        """税号 → 税局(RD)注册信息。tax_id 槽 user_text 接地:13 位必须出现在用户原话里。"""
        from services.rd import rd_api

        res = rd_api.lookup_vat(str(tax_id or ""))
        if not res.get("ok"):
            code = res.get("error") or "query_failed"
            mapped = {"invalid_format": "rd_invalid_tax_id", "not_found": "rd_not_found"}
            return ToolResult(ok=False, error_code=mapped.get(code, "query_failed"))
        return ToolResult(ok=True, data=res.get("data") or {})

    def get_my_plan(self, ctx: AgentContext) -> ToolResult:
        """当前套餐/权限/订阅一览(只读聚合,shape 变动用 .get 容忍)。"""
        from services.billing import subscription as sub_svc

        plan = (ctx.user or {}).get("plan") or "free"
        perms = _plan_permissions(plan)
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        sub = None
        try:
            row = sub_svc.get_active_subscription(ctx.tenant_id)
            if row:
                sub = {
                    "plan": row.get("plan_key") or row.get("plan") or "",
                    "period_end": str(row.get("current_period_end") or ""),
                }
        except Exception:  # 订阅读不到不挡套餐信息(只读聚合,残缺好过报错)
            sub = None
        return ToolResult(
            ok=True,
            data={
                "plan": plan,
                "balance_thb": (b or {}).get("balance_thb"),
                "retention_days": _retention(ctx.user),
                "subscription": sub,
            },
        )

    # ── B 档:写操作(M3 · confirm=True 先复述后执行) ──

    def record_expense(
        self, ctx: AgentContext, *, amount=None, vendor_name="", note="", date="", expense_type=""
    ) -> ToolResult:
        """记账工具:把模型抽取的字段建成草稿(纯构建,不落库)。

        金额走 to_draft 的 amount_grounded 唯一钱闸——编造的金额被置空 → ok=False(缺金额,
        调用方追问),绝不凭空入账。落库在用户确认后由 LINE 入口 pop 待办 → _do_record 完成。
        """
        from services.expense.line_l2 import to_draft

        data = {
            "amount": amount,
            "vendor_name": vendor_name,
            "note": note,
            "date": date,
            "expense_type": expense_type,
        }
        draft = to_draft(data, ctx.user_text or "")
        if not draft.has_amount():
            return ToolResult(ok=False, error_code="amount_ungrounded")
        return ToolResult(ok=True, data={"draft": draft})

    def undo_entry(self, ctx: AgentContext) -> ToolResult:
        """撤销:目标定位(引用卡/「上一笔」)与不明确时的反问全在 reply_undo 确定性侧,
        这里只把决策权交出去——模型没有任何目标猜测权。"""
        return ToolResult(ok=True, data={})

    def edit_entry(
        self, ctx: AgentContext, *, amount=None, vendor_name="", date="", note=""
    ) -> ToolResult:
        """改错:槽位已过接地闸(新金额必在原话),拼成旧大脑同构的字段包交
        line_correct.request_correct(定位/风险三档/是/否确认全复用,一行不改)。"""
        u = {
            "intent": "edit",
            "amount": amount,
            "vendor_name": vendor_name,
            "date": date,
            "note": note,
        }
        return ToolResult(ok=True, data={"u": u})

    def push_to_erp(self, ctx: AgentContext, *, doc_keyword=None, endpoint_name=None) -> ToolResult:
        """推 ERP 备料(confirm=True:这里只定位+选端点+预检,【绝不执行推送】)。

        ok=True 的 data["push"] 交 write_sink 出确认卡;真推送要等用户点卡上的确认按钮
        (services/agent/push_confirm)。定位模糊/无端点/已推过 → ok=False 喂回观测,
        由模型追问或诚实告知,绝不猜目标、绝不重复推。
        """
        p = _plan_permissions((ctx.user or {}).get("plan"))
        if not p.get("can_push_erp"):
            return ToolResult(ok=False, error_code="forbidden")
        hist, fail = self._locate_doc(ctx, doc_keyword)
        if fail is not None:
            return fail

        endpoints = [
            e for e in (db.list_erp_endpoints(str(ctx.user["id"])) or []) if e.get("enabled", True)
        ]
        endpoint = None
        if endpoint_name:
            q = "".join(str(endpoint_name).lower().split())
            hits = [e for e in endpoints if q in "".join(str(e.get("name") or "").lower().split())]
            endpoint = hits[0] if len(hits) == 1 else None
        else:
            # 列表已按 is_default DESC, created ASC 排序且滤过 enabled → 首行即默认端点
            endpoint = endpoints[0] if endpoints else None
        if not endpoint:
            names = [e.get("name") or "" for e in endpoints]
            return ToolResult(ok=False, error_code="no_endpoint", data={"endpoints": names})

        prior = db.has_recent_successful_push(
            str(hist.get("id")), endpoint["id"], str(ctx.user["id"])
        )
        if prior:
            return ToolResult(
                ok=False,
                error_code="already_pushed",
                data={"pushed_endpoint": endpoint.get("name") or "ERP"},
            )
        return ToolResult(
            ok=True,
            data={
                "push": {
                    "history_id": str(hist.get("id")),
                    "endpoint_id": str(endpoint["id"]),
                    "endpoint_name": endpoint.get("name") or "ERP",
                    "invoice_no": hist.get("invoice_no") or "",
                    "vendor": hist.get("seller_name") or "",
                    "amount": hist.get("total_amount"),
                }
            },
        )
