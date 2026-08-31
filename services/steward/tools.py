# -*- coding: utf-8 -*-
"""管家工具执行层 —— 闭集汇总 + 原六只读工具薄封装既有服务层(零新 SQL、零直接写库)。

留痕复用是硬约束:对话里查到的东西必须与用户手点看到的同源,所以每个工具都只是「调既有
服务层函数 + 把结果整理成一份小结构」。哪个工具包了谁:
  matrix_overview  services.workorder.matrix.fetch_rows/build      (= /api/tax-profile/matrix)
  client_status    services.workorder.api.list_orders/order_detail  (= /api/workorders/{id})
  workorder_list   services.workorder.api.list_orders               (= /api/workorders)
  push_log_query   services.erp.push_log_queries.list_push_logs     (= /api/erp/push-logs)
  history_query    services.ocr_history.queries.list_ocr_history    (= /api/history)
  client_lookup    services.workspace.store.list_workspace_clients  (= /api/workspace/clients)

体积闸(<500 行)下的分居 —— 语义边界不变,闭集与执行入口(prepare/run)一律留在本模块:
  tools_close     月结产线四问(到期义务 / 待审队列 / 应交税额 / 银行对账)
  tools_invoice   单票体检(识别结果 + 推送成败 + 为什么推不进去)
  tools_calc      现场算账(含税↔税前↔税额互算 · 零 I/O 纯 Decimal · 数出自会计原话)
  tools_brief     今天从哪下手(合成到期/待审/推失败三路,只分桶排序不重算)
  tools_signoff   这家这期能不能签(order_detail 五项投影 → 一句结论)
  tools_deliverables 交付物清单 + 每份的真下载链
  tools_period    本期盘点(全所税额表 / 某家某期的票推完了没 · 一律批量读,不逐家回放)
  tools_stockcard 商品收发存查询(services.stockcard.report 记账台账 · 不是 POS 商户库存)
  tools_file      吃这一轮附件的两只(文件转 Excel / 销项报告三查 · 哪个文件由代码定不由模型定)
  tools_doc_qa    读文问答(S2 · 只答文中写了什么,标页码,文中没有的数不许算不许编)
  tools_table     表格生成(S2 · 模型只挑列名/算法规格,数字全由代码 Decimal 实算)
  erp_push_tool   唯一的写工具(请求侧接地 + 执行侧经桥投单两段)
  tool_scope      各工具共用的作用域 / 客户名接地 / 票据定位 / 期间缺省 / 金额规范化

工具只出数据,不出文案 —— 人话在 copy.py 按数据渲染(模型不参与任何数字)。
失败一律返回 ToolResult(ok=False, error_code=...),绝不抛给对话层(四态诚实:说不出来就
说为什么说不出来)。
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.steward.contracts import ToolResult
from services.steward import (
    authz,
    erp_push_tool,
    registry,
    tool_scope,
    tools_brief,
    tools_calc,
    tools_close,
    tools_deliverables,
    tools_doc_qa,
    tools_file,
    tools_invoice,
    tools_period,
    tools_signoff,
    tools_stockcard,
    tools_table,
)
from services.steward.registry import ToolContext
from services.steward.tool_scope import (  # 入口仍在 tools:调用方按 tools.ERR_* 认错误码
    ERR_CLIENT_AMBIGUOUS,  # noqa: F401
    ERR_CLIENT_NOT_FOUND,  # noqa: F401
    ERR_HISTORY_FORBIDDEN,
)

logger = logging.getLogger(__name__)

_LIST_LIMIT = tool_scope.LIST_LIMIT
_PUSH_SCAN_LIMIT = 100  # 推送日志按时间倒序扫这么多条再按天数过滤(超出如实标 truncated)
_DEFAULT_PUSH_DAYS = 7
_MAX_PUSH_DAYS = 90

ERR_TOOL_FAILED = "steward.tool_failed"
# 写工具炸了要单独一个码:只读版兜底文案是"再说一次",而写工具在投单之后还有一整段会抛的
# 代码(轮询桥的写活),那句话落在这里就是在教人双写。
ERR_WRITE_TOOL_FAILED = "steward.write_tool_failed"
ERR_UNKNOWN_TOOL = "steward.unknown_tool"


# ── 工具实现 ────────────────────────────────────────────────


def matrix_overview(ctx: ToolContext, args: dict) -> ToolResult:
    """某期事务所矩阵总览(缺料/待审/进行中/未开单各多少家)。"""
    from services.workorder import matrix

    period = tool_scope.period_or_current(args.get("period"))
    with tool_scope.cursor() as cur:
        rows = matrix.fetch_rows(cur, tenant_id=ctx.tenant_id, period=period)
    rows = [r for r in rows if tool_scope.in_scope(ctx, r["client_id"])]
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

    client, err = tool_scope.resolve_client(ctx, args.get("client_name") or "")
    if err:
        return err
    period = tool_scope.period_or_current(args.get("period"))
    with tool_scope.cursor() as cur:
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
    period = tool_scope.period_or_current(args.get("period"))
    with tool_scope.cursor() as cur:
        listing = wo_api.list_orders(
            cur,
            tenant_id=ctx.tenant_id,
            period=period,
            statuses=statuses or None,
            limit=_LIST_LIMIT,
        )
    names = {c["id"]: c["name"] for c in tool_scope.clients(ctx)}
    orders = [o for o in listing["orders"] if tool_scope.in_scope(ctx, o["workspace_client_id"])]
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
    hits = tool_scope.match_clients(tool_scope.clients(ctx), keyword)
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
    registry.DUE_SOON: tools_close.due_soon,
    registry.REVIEW_QUEUE: tools_close.review_queue,
    registry.TAX_NUMBERS: tools_close.tax_numbers,
    registry.BANK_RECON_STATUS: tools_close.bank_recon_status,
    registry.INVOICE_DETAIL: tools_invoice.invoice_detail,
    registry.TODAY_BRIEF: tools_brief.today_brief,
    registry.CLOSE_READINESS: tools_signoff.close_readiness,
    registry.DELIVERABLES_LIST: tools_deliverables.deliverables_list,
    registry.VAT_CALC: tools_calc.vat_calc,
    registry.TAX_MATRIX: tools_period.tax_matrix,
    registry.PERIOD_INVOICES: tools_period.period_invoices,
    registry.STOCK_CARD_LOOKUP: tools_stockcard.stock_card_lookup,
    registry.ERP_PUSH: erp_push_tool.erp_push,
    registry.FILE_CONVERT: tools_file.file_convert,
    registry.VAT_REPORT_CHECK: tools_file.vat_report_check,
    registry.DOC_READ_QA: tools_doc_qa.doc_read_qa,
    registry.TABLE_GENERATE: tools_table.table_generate,
}

# 铸卡前的接地器(只写工具有):把用户嘴里的目标落成执行级参数 + 卡面事实。见 prepare()。
_PREPARERS = {
    registry.ERP_PUSH: erp_push_tool.prepare,
}


def prepare(name: str, ctx: ToolContext, args: dict) -> erp_push_tool.PrepareResult:
    """写工具铸卡前的接地(orchestrator 调 · 请求侧)。

    为什么必须在铸卡【前】跑:授权卡要说清「对哪个账套做什么、影响几条」,而这些事实要先把
    「那张 7-11 的票」落成一条真实记录才知道;顺带把落定的参数写死进指纹 —— 卡上批的与
    执行时跑的因此逐字节相同。没接地器的工具原样透传(只读路径行为不变)。
    """
    preparer = _PREPARERS.get(name)
    if preparer is None:
        return erp_push_tool.PrepareResult(args=dict(args or {}))
    try:
        return preparer(ctx, dict(args or {}))
    except Exception:  # noqa: BLE001 — 接地炸了是"这活派不出去",不是把异常抛进对话层
        logger.warning("[steward] prepare %s failed", name, exc_info=True)
        return erp_push_tool.PrepareResult(
            error=ToolResult(ok=False, error_code=ERR_TOOL_FAILED, data={"tool": name})
        )


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
        # 写工具:异常可能发生在投单【之后】(轮询桥的写活会抛),此时桥可能已经在落账 ——
        # 只读版的"再说一次"文案会把人直接教成双写,故换一个改口"别重推"的码。
        code = ERR_TOOL_FAILED if spec.readonly else ERR_WRITE_TOOL_FAILED
        return ToolResult(ok=False, error_code=code, data={"tool": name})


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
