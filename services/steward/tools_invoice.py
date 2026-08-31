# -*- coding: utf-8 -*-
"""管家单票体检 invoice_detail(B4 第二步 · 只读薄封装)。

回答会计最常问的一句:「这张票怎么了 / 为什么推不进 Express」。以前只能在识别记录页看识别
结果、再切到推送日志页按票号翻,两处对不上就只能猜。这里把两份既有读侧一次给全:
  票面 services.ocr_history.queries.get_ocr_history_detail (= /api/history/{id})
  推送 services.erp.push_log_queries.list_push_logs(history_id=…) (= /api/erp/push-logs)

定位走 tool_scope.resolve_invoice —— 与写工具 erp_push 是同一段代码、同一套错误码。
「先查清楚再推」的下一步就是那个写工具,两边对同一句话给出不同的候选集会让人无从下手。

posting_kind(上传时声明的过账去向)必须原样带出来:它缺失正是推送被转人工的头号原因,而
产品里补不了,只能重传。答复层据此指路,不装作"再试一次就好"。
"""

from __future__ import annotations

from typing import Optional

from services.steward.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext

_PUSH_LIMIT = 10  # 一张票的推送尝试;超过这个数说明在反复重推,前几条足够看清失败原因


def invoice_detail(ctx: ToolContext, args: dict) -> ToolResult:
    """一张票的识别结果 + 推送成败 + 卡在哪。查无/多义都退回可追问的错误,绝不"就近"挑一张。"""
    keyword = str(args.get("keyword") or "").strip()
    row, err = tool_scope.resolve_invoice(ctx, keyword)
    if err:
        return err

    history_id = str(row.get("id") or "")
    detail = _load_detail(ctx, history_id) or dict(row)
    workspace_client_id = detail.get("workspace_client_id")
    if workspace_client_id and not tool_scope.in_scope(ctx, workspace_client_id):
        # 关键词命中了作用域外的票(名录过滤只管客户名,识别记录按可见性另算):当作查无,
        # 不泄露"存在但你看不到"这件事本身。
        return ToolResult(
            ok=False, error_code=tool_scope.ERR_INVOICE_NOT_FOUND, data={"keyword": keyword}
        )
    return ToolResult(
        ok=True,
        data={
            "history_id": history_id,
            "keyword": keyword,
            "filename": detail.get("filename") or "",
            "invoice_no": detail.get("invoice_no") or "",
            "seller_name": detail.get("seller_name") or "",
            "invoice_date": detail.get("invoice_date") or "",
            "total_amount": tool_scope.money(detail.get("total_amount")),
            "posting_kind": detail.get("posting_kind") or "",
            "confidence": detail.get("confidence"),
            "edited": bool(detail.get("edited")),
            **_push_history(ctx, history_id),
        },
    )


def _load_detail(ctx: ToolContext, history_id: str) -> Optional[dict]:
    from services.ocr_history import queries as history_queries

    return history_queries.get_ocr_history_detail(ctx.user_id, history_id, tenant_id=ctx.tenant_id)


def _push_history(ctx: ToolContext, history_id: str) -> dict:
    """这张票推过几次、最后一次什么结果。一次都没推过是常见答案,如实给 0 不当异常。"""
    from services.erp import push_log_queries

    res = push_log_queries.list_push_logs(
        user_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        history_id=history_id,
        limit=_PUSH_LIMIT,
    )
    items = list(res.get("items") or [])
    latest = items[0] if items else {}
    return {
        "push_count": res.get("total", len(items)),
        "push_status": latest.get("status") or "",
        "push_error_code": latest.get("error_code") or "",
        "push_category": latest.get("category") or "",
        "push_at": _iso(latest.get("created_at")),
        "push_rows": [
            {
                "created_at": _iso(it.get("created_at")) or "",
                "status": it.get("status") or "",
                "error_code": it.get("error_code") or "",
                "category": it.get("category") or "",
            }
            for it in items
        ],
    }


def _iso(value) -> Optional[str]:
    return value.isoformat() if hasattr(value, "isoformat") else (value or None)
