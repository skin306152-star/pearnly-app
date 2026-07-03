# -*- coding: utf-8 -*-
"""跨轮锚点的采集与消费(loop 收集 / executor._locate_doc 兜底)。

collect:工具成功后从 result.data 抽对象 id 进 ctx.anchors(纯内存,持久化在 bridge)。
resolve_history:锚点指向的单据读时必复核 —— 用与列表同一套归属/可见性口径重取,
已删/越权/过期一律 None 回落「最近一张」,绝不盲信旧 id(死单事故先例见 line_stale_ref)。
闸(agent_anchor_memory)关时 ctx.anchors_enabled=False:collect no-op、锚点恒空,
_locate_doc 分支惰性不触发,线上行为逐字节不变。
"""

from __future__ import annotations

from typing import Optional

from services.agent.contracts import AgentContext, ToolResult

LAST_HISTORY_ID = "last_history_id"
LAST_PUSHED_ENDPOINT_ID = "last_pushed_endpoint_id"


def collect(ctx: AgentContext, tool: str, result: ToolResult) -> None:
    """从成功的工具结果里记下"刚才碰过的对象"。

    list_history 仅在唯一命中时锚定(多命中=用户还没挑,锚了就是替用户猜);
    push_to_erp 备料成功即锚定该单据与端点(确认卡上就是它)。
    """
    if not ctx.anchors_enabled or not getattr(result, "ok", False):
        return
    data = result.data if isinstance(result.data, dict) else {}
    if tool == "list_history":
        items = data.get("items") or []
        if len(items) == 1 and items[0].get("id"):
            ctx.anchors[LAST_HISTORY_ID] = str(items[0]["id"])
    elif tool == "push_to_erp":
        push = data.get("push") or {}
        if push.get("history_id"):
            ctx.anchors[LAST_HISTORY_ID] = str(push["history_id"])
        if push.get("endpoint_id"):
            ctx.anchors[LAST_PUSHED_ENDPOINT_ID] = str(push["endpoint_id"])


def resolve_history(ctx: AgentContext) -> Optional[dict]:
    """锚点指向的单据,复核后返回(shape 兼容 _locate_doc 的 hist 消费:id/seller_name/
    total_amount/invoice_no)。锚空/查无/可见性不符 → None(回落最近一张)。"""
    from core import db

    hid = (ctx.anchors or {}).get(LAST_HISTORY_ID)
    if not hid:
        return None
    doc = db.get_ocr_history_detail(str(ctx.user["id"]), str(hid), tenant_id=ctx.tenant_id)
    if not doc:
        return None
    # 镜像 list_ocr_history 的员工可见性口径:限定名单时,归属外客户的单不认锚
    # (未归属 NULL 行放行 —— 锚点来自该用户几分钟前亲眼所见的受限列表)。
    visible = db.get_visible_client_ids_for_user(ctx.user)
    if visible is not None and doc.get("client_id") is not None:
        if doc["client_id"] not in {int(c) for c in visible}:
            return None
    return doc
