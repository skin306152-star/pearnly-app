# -*- coding: utf-8 -*-
"""管家交付物清单 deliverables_list(B5 · 只读薄封装,零新 SQL)。

月末把报表包发给客户是每家每月的固定动作(几十家 × 近十类交付物)。以前要先切客户、再进
#/client/<id>/pkg、再逐个点开;问管家还得先知道 client_id。这里一句话到位:哪几份出了、
哪几份还没出、出了的直接给下载链。

包的是 services.workorder.api.list_deliverables(= /api/workorder/orders/{id}/deliverables),
下载链是工单页在用的那个真 GET(routes/workorder_financials_routes.py 的
/api/workorder/orders/{id}/deliverables/{kind})—— 不新造深链。编一个点开 404 的按钮是这个
仓库摔过的跟头,所以只有库里登记了 artifact_path(has_file=True)的那几份才给链。

不走 order_detail:那条路要回放整条事件流(5s 轮询热路径的重活),而这里只需要工单 id
加一张交付物表。
"""

from __future__ import annotations

from urllib.parse import quote

from services.steward.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext

# 交付包各件的展示次序,按会计翻包的顺序:先申报表、再报表与底稿、最后索引与导出。
# 表外的新件按机器名排在后面照样显示 —— 没登记进这张表不代表不该给人看。
_ORDER = (
    "pp30_draft",
    "pnd3_prep_txt",
    "pnd3_keying_xlsx",
    "pnd53_prep_txt",
    "pnd53_keying_xlsx",
    "financials_report",
    "ledger_workpaper",
    "bank_workpaper",
    "shadow_workpaper",
    "missing_doc_memo",
    "evidence_index",
    "entries_export",
)


def deliverables_list(ctx: ToolContext, args: dict) -> ToolResult:
    """某家某期的交付物清单 + 每份的下载链。还没开工单就诚实说没有,不给一张空表。"""
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
        work_order_id = str(orders[0]["id"]) if orders else ""
        rows = (
            wo_api.list_deliverables(cur, tenant_id=ctx.tenant_id, work_order_id=work_order_id)
            if work_order_id
            else []
        )
    rows = sorted(rows, key=_sort_key)
    ready = sum(1 for r in rows if r.get("has_file"))
    return ToolResult(
        ok=True,
        data={
            "client_id": client["id"],
            "client_name": client["name"],
            "period": period,
            "has_order": bool(work_order_id),
            "work_order_id": work_order_id,
            "total": len(rows),
            "ready": ready,
            "pending": len(rows) - ready,
            "rows": [
                {
                    "kind": r.get("kind") or "",
                    "has_file": bool(r.get("has_file")),
                    "href": (
                        download_href(work_order_id, r.get("kind") or "")
                        if r.get("has_file")
                        else ""
                    ),
                }
                for r in rows[: tool_scope.LIST_LIMIT]
            ],
        },
    )


def _sort_key(row: dict) -> tuple:
    kind = row.get("kind") or ""
    return (_ORDER.index(kind) if kind in _ORDER else len(_ORDER), kind)


def download_href(work_order_id: str, kind: str) -> str:
    """交付物下载端点。越权由那条路由自己的 _authorize/_load_order 拦(链出现在答复里不等于
    有权下载);这里只负责把地址拼对 —— 两段都转义,safe="" 才连斜杠一起转,免得将来带斜杠
    的 kind 把路径拼歪(quote 默认放行 /)。"""
    return (
        f"/api/workorder/orders/{quote(work_order_id, safe='')}"
        f"/deliverables/{quote(kind, safe='')}"
    )
