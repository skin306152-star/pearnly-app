# -*- coding: utf-8 -*-
"""管家六个只读工具 —— 一律薄封装既有服务层,零新 SQL、零直接写库。

留痕复用是硬约束:对话里查到的东西必须与用户手点看到的同源,所以每个工具都只是「调既有
服务层函数 + 把结果整理成一份小结构」。哪个工具包了谁:
  matrix_overview  services.workorder.matrix.fetch_rows/build      (= /api/tax-profile/matrix)
  client_status    services.workorder.api.list_orders/order_detail  (= /api/workorders/{id})
  workorder_list   services.workorder.api.list_orders               (= /api/workorders)
  push_log_query   services.erp.push_log_queries.list_push_logs     (= /api/erp/push-logs)
  history_query    services.ocr_history.queries.list_ocr_history    (= /api/history)
  client_lookup    services.workspace.store.list_workspace_clients  (= /api/workspace/clients)

工具只出数据,不出文案 —— 人话在 copy.py 按数据渲染(模型不参与任何数字)。
失败一律返回 ToolResult(ok=False, error_code=...),绝不抛给对话层(四态诚实:说不出来就
说为什么说不出来)。
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.agent.contracts import ToolResult
from services.steward import authz, registry
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

_LIST_LIMIT = 20  # 对话里回的清单只给前几条,详情去深链看
_PUSH_SCAN_LIMIT = 100  # 推送日志按时间倒序扫这么多条再按天数过滤(超出如实标 truncated)
_DEFAULT_PUSH_DAYS = 7
_MAX_PUSH_DAYS = 90

ERR_CLIENT_NOT_FOUND = "steward.client_not_found"
ERR_CLIENT_AMBIGUOUS = "steward.client_ambiguous"
ERR_HISTORY_FORBIDDEN = "steward.history_forbidden"
ERR_TOOL_FAILED = "steward.tool_failed"
ERR_UNKNOWN_TOOL = "steward.unknown_tool"


def _cursor():
    from core import db

    return db.get_cursor()


def _scope_ids(ctx: ToolContext) -> Optional[list]:
    """账套作用域 → list(供 DAL 的 restrict_ids)· None = 不限(老板/超管)。"""
    return None if ctx.allowed_client_ids is None else [int(i) for i in ctx.allowed_client_ids]


def _in_scope(ctx: ToolContext, client_id) -> bool:
    return ctx.allowed_client_ids is None or int(client_id) in ctx.allowed_client_ids


def _clients(ctx: ToolContext) -> list[dict]:
    """本租户账套主体名录(一次查询,给名字解析/列表补名共用,防 N+1)。"""
    from services.workspace import store as ws_store

    rows = ws_store.list_workspace_clients(ctx.user_id, ctx.tenant_id, restrict_ids=_scope_ids(ctx))
    return [
        {"id": int(r["id"]), "name": r.get("name") or "", "tax_id": r.get("tax_id")} for r in rows
    ]


def _match_clients(clients: list[dict], keyword: str) -> list[dict]:
    """名字/税号模糊命中(精确同名优先)。纯函数,便于单测。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return []
    exact = [c for c in clients if c["name"].lower() == kw]
    if exact:
        return exact
    return [
        c
        for c in clients
        if kw in c["name"].lower() or (c.get("tax_id") and kw in str(c["tax_id"]))
    ]


def _resolve_client(ctx: ToolContext, keyword: str) -> tuple[Optional[dict], Optional[ToolResult]]:
    """客户名 → 真实名录里的一家。查无/多义都不猜,退回可追问的错误(挂错账套是红线)。"""
    hits = _match_clients(_clients(ctx), keyword)
    if not hits:
        return None, ToolResult(
            ok=False, error_code=ERR_CLIENT_NOT_FOUND, data={"keyword": keyword, "candidates": []}
        )
    if len(hits) > 1:
        return None, ToolResult(
            ok=False,
            error_code=ERR_CLIENT_AMBIGUOUS,
            data={"keyword": keyword, "candidates": hits[:_LIST_LIMIT]},
        )
    return hits[0], None


def _period_or_current(period: Optional[str]) -> str:
    from services.workorder import obligation_engine

    return period or obligation_engine.current_be_period()


# ── 工具实现 ────────────────────────────────────────────────


def matrix_overview(ctx: ToolContext, args: dict) -> ToolResult:
    """某期事务所矩阵总览(缺料/待审/进行中/未开单各多少家)。"""
    from services.workorder import matrix

    period = _period_or_current(args.get("period"))
    with _cursor() as cur:
        rows = matrix.fetch_rows(cur, tenant_id=ctx.tenant_id, period=period)
    rows = [r for r in rows if _in_scope(ctx, r["client_id"])]
    view = matrix.build(rows, period=period)
    badges = Counter(c["badge"] for c in view["cells"])
    attention = [
        {
            "client_id": c["client_id"],
            "name": _name_of(view["clients"], c["client_id"]),
            "obligation_code": c["obligation_code"],
            "badge": c["badge"],
        }
        for c in view["cells"]
        if c["badge"] in (matrix.BADGE_MISSING_MATERIALS, matrix.BADGE_PENDING_REVIEW)
    ]
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "client_count": len(view["clients"]),
            "missing_order": sum(1 for c in view["clients"] if c["missing_order"]),
            "badges": {
                "missing_materials": badges.get(matrix.BADGE_MISSING_MATERIALS, 0),
                "pending_review": badges.get(matrix.BADGE_PENDING_REVIEW, 0),
                "in_progress": badges.get(matrix.BADGE_IN_PROGRESS, 0),
                "frozen": badges.get(matrix.BADGE_FROZEN, 0),
                "pending_order": badges.get(matrix.BADGE_PENDING_ORDER, 0),
            },
            "attention": attention[:_LIST_LIMIT],
        },
    )


def _name_of(clients: list[dict], client_id) -> str:
    for c in clients:
        if c["id"] == client_id:
            return c["name"]
    return ""


def client_status(ctx: ToolContext, args: dict) -> ToolResult:
    """某客户某期进度:工单状态 + 当前步骤 + 还缺什么(全部来自工单详情投影)。"""
    from services.workorder import api as wo_api

    client, err = _resolve_client(ctx, args.get("client_name") or "")
    if err:
        return err
    period = _period_or_current(args.get("period"))
    with _cursor() as cur:
        listing = wo_api.list_orders(
            cur,
            tenant_id=ctx.tenant_id,
            workspace_client_id=client["id"],
            period=period,
            limit=1,
        )
        orders = listing["orders"]
        detail = (
            wo_api.order_detail(cur, tenant_id=ctx.tenant_id, work_order_id=str(orders[0]["id"]))
            if orders
            else None
        )
    data = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "has_order": bool(detail),
    }
    if detail:
        data.update(
            {
                "work_order_id": str(detail["id"]),
                "status": detail["status"],
                "current_step": detail["current_step"],
                "material_count": detail["material_count"],
                "needs": detail.get("needs") or [],
                "blocked_reasons": detail.get("blocked_reasons") or [],
                "flagged_count": len(detail.get("flagged") or []),
            }
        )
    return ToolResult(ok=True, data=data)


def workorder_list(ctx: ToolContext, args: dict) -> ToolResult:
    """列工单(按期/按口径)。客户名从名录一次补齐,不逐单查(防 N+1)。

    筛选走 engine.resolve_status_filter 的语义组:问「还没审完」得 stuck+review 两态,
    与矩阵徽章同一口径 —— 否则同屏出现矩阵「待审 2」而这里答「0 张工单」。
    认不出的词一律当没筛(不拿编造的状态去查库)。"""
    from services.workorder import api as wo_api, engine

    status_filter, statuses = engine.resolve_status_filter(args.get("status"))
    period = _period_or_current(args.get("period"))
    with _cursor() as cur:
        listing = wo_api.list_orders(
            cur,
            tenant_id=ctx.tenant_id,
            period=period,
            statuses=statuses or None,
            limit=_LIST_LIMIT,
        )
    names = {c["id"]: c["name"] for c in _clients(ctx)}
    orders = [o for o in listing["orders"] if _in_scope(ctx, o["workspace_client_id"])]
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "status_filter": status_filter,
            "total": listing["count"],
            "counts": dict(Counter(o["status"] for o in orders)),
            "orders": [
                {
                    "work_order_id": str(o["id"]),
                    "client_id": o["workspace_client_id"],
                    "client_name": names.get(o["workspace_client_id"], ""),
                    "status": o["status"],
                    "current_step": o.get("current_step"),
                }
                for o in orders
            ],
        },
    )


def push_log_query(ctx: ToolContext, args: dict) -> ToolResult:
    """推 ERP 成败(近 N 天/某客户/失败原因)。erp_push_logs 是推送状态唯一源,不另建口径。"""
    from services.erp import push_log_queries

    days = _int_or(args.get("days"), _DEFAULT_PUSH_DAYS, 1, _MAX_PUSH_DAYS)
    status = args.get("status") if args.get("status") in ("success", "failed") else None
    res = push_log_queries.list_push_logs(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        status_filter=status,
        limit=_PUSH_SCAN_LIMIT,
        exclude_push_type="id_card",
    )
    since = datetime.now(timezone.utc) - timedelta(days=days)
    items = [it for it in res["items"] if _created_after(it.get("created_at"), since)]
    client_name = (args.get("client_name") or "").strip().lower()
    if client_name:
        items = [it for it in items if client_name in _push_row_subject(it).lower()]
    failed = [it for it in items if (it.get("status") or "") == "failed"]
    return ToolResult(
        ok=True,
        data={
            "days": days,
            "status_filter": status,
            "total": len(items),
            "success": sum(1 for it in items if (it.get("status") or "") == "success"),
            "failed": len(failed),
            "truncated": res["total"] > len(res["items"]),
            "reasons": dict(Counter(it.get("category") or "unknown" for it in failed)),
            "rows": [
                {
                    "invoice_no": it.get("invoice_no"),
                    "subject": _push_row_subject(it),
                    "status": it.get("status"),
                    "error_code": it.get("error_code") or "",
                    "created_at": _iso(it.get("created_at")),
                }
                for it in items[:_LIST_LIMIT]
            ],
        },
    )


def history_query(ctx: ToolContext, args: dict) -> ToolResult:
    """在识别记录里找票(与 /api/history 同一个 DAL、同一套保留期与可见性口径)。"""
    from core import db
    from core.route_helpers import _check_history_access
    from fastapi import HTTPException
    from services.ocr_history import queries as history_queries

    try:
        retention = _check_history_access(ctx.user)
    except HTTPException:
        return ToolResult(ok=False, error_code=ERR_HISTORY_FORBIDDEN)
    res = history_queries.list_ocr_history(
        user_id=ctx.user_id,
        retention_days=retention,
        keyword=(args.get("keyword") or "").strip() or None,
        limit=_LIST_LIMIT,
        tenant_id=ctx.tenant_id,
        restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
    )
    return ToolResult(
        ok=True,
        data={
            "keyword": args.get("keyword") or "",
            "total": res["total"],
            "rows": [
                {
                    "id": it["id"],
                    "filename": it.get("filename"),
                    "invoice_no": it.get("invoice_no"),
                    "seller_name": it.get("seller_name"),
                    "invoice_date": it.get("invoice_date"),
                    "status": it.get("status"),
                }
                for it in res["items"]
            ],
        },
    )


def client_lookup(ctx: ToolContext, args: dict) -> ToolResult:
    """客户名/税号模糊查(参数接地用:先对上名录里真有的那家,再谈别的)。"""
    keyword = args.get("keyword") or ""
    hits = _match_clients(_clients(ctx), keyword)
    return ToolResult(
        ok=True,
        data={"keyword": keyword, "total": len(hits), "clients": hits[:_LIST_LIMIT]},
    )


# ── 执行入口(闭集:表外的名字物理调不到)────────────────────

_HANDLERS = {
    registry.MATRIX_OVERVIEW: matrix_overview,
    registry.CLIENT_STATUS: client_status,
    registry.WORKORDER_LIST: workorder_list,
    registry.PUSH_LOG_QUERY: push_log_query,
    registry.HISTORY_QUERY: history_query,
    registry.CLIENT_LOOKUP: client_lookup,
}


def run(name: str, ctx: ToolContext, args: dict, grant=None) -> ToolResult:
    """按名执行。注册表外的名字 / 注册表与执行器不同步 → 拒绝,绝不放行未知能力。

    写/危险工具在这里物理设闸(B3):没有已批准、且盖着当前参数指纹的批文(grant =
    任务 payload.authorization)一律拒 —— 授权不是前端不显示按钮,是执行层进不去。
    """
    spec = registry.get(name)
    handler = _HANDLERS.get(name) if spec else None
    if handler is None:
        return ToolResult(ok=False, error_code=ERR_UNKNOWN_TOOL, data={"tool": name})
    denial = authz.execution_error(spec, grant, tool=name, args=args or {})
    if denial:
        return ToolResult(ok=False, error_code=denial, data={"tool": name})
    try:
        return handler(ctx, args or {})
    except Exception:  # noqa: BLE001 — 工具炸了是"这条查不出来",不是整个对话崩
        logger.warning("[steward] tool %s failed", name, exc_info=True)
        return ToolResult(ok=False, error_code=ERR_TOOL_FAILED, data={"tool": name})


def _int_or(value, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(int(str(value).strip()), high))
    except (TypeError, ValueError):
        return default


def _iso(value) -> Optional[str]:
    return value.isoformat() if hasattr(value, "isoformat") else (value or None)


def _created_after(value, since: datetime) -> bool:
    """时间窗过滤。裸时间戳(无时区)按 UTC 解释,与 created_at 落库口径一致。"""
    if not isinstance(value, datetime):
        return True  # 读不出时间就不因此丢行(宁可多给一条,也不静默吞数据)
    stamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return stamp >= since


def _push_row_subject(row: dict) -> str:
    """这条推送是谁的:优先账套名,退回买方客户名/卖方名(供按客户过滤与展示)。"""
    for key in ("workspace_name", "client_name", "seller_name"):
        if (row.get(key) or "").strip():
            return str(row[key]).strip()
    return ""
