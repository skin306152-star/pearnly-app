# -*- coding: utf-8 -*-
"""跨轮锚点的采集与消费(loop 收集 / 图片路挂钩 / executor._locate_doc 兜底)。

collect:工具成功后从 result.data 抽对象 id 进 ctx.anchors(纯内存,持久化在 bridge)。
record_image_docs:图片路出卡后锚定该单(直接落库·图片轮没有 agent ctx)。
resolve_history:锚点指向的单据读时必复核 —— 识别记录锚用与列表同一套归属/可见性口径重取;
图片单锚重查单据状态(posted/draft 才认·discarded 死单不认),经 doc_fallback 载体机制
拼推送机械认识的 hist。失效一律 None 回落「最近一张」,绝不盲信旧 id。
闸(agent_anchor_memory)关时锚点全程不流动,线上行为逐字节不变。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.agent.contracts import AgentContext, ToolResult

logger = logging.getLogger(__name__)

LAST_HISTORY_ID = "last_history_id"
LAST_PUSHED_ENDPOINT_ID = "last_pushed_endpoint_id"
LAST_IMAGE_DOC_ID = "last_image_doc_id"
LAST_IMAGE_DOC_WS = "last_image_doc_ws"


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


def record_image_docs(user, tenant_id, line_user_id, ingests, workspace_client_id) -> None:
    """图片单出卡后锚定「刚才那张」(记账租户图片单不写识别记录,没有锚就定位不到——
    真机雷 2026-07-03:发图后说"推它"命中了旧载体 PS2-0702)。

    只在唯一一张时锚(多张=歧义不猜);新图接管指代,清掉旧识别记录锚。
    闸关/缺参/任何故障 = no-op,绝不挡图片主路。
    """
    try:
        from core import feature_flags
        from services.line_binding import line_anchor_store

        one = (ingests[0] if len(ingests or []) == 1 else None) or {}
        if not (one.get("doc_id") and tenant_id and line_user_id):
            return
        if not feature_flags.agent_anchor_enabled_for(str((user or {}).get("id") or "") or None):
            return
        anchors = line_anchor_store.get_anchors(tenant_id, line_user_id)
        anchors.pop(LAST_HISTORY_ID, None)
        anchors[LAST_IMAGE_DOC_ID] = str(one["doc_id"])
        anchors[LAST_IMAGE_DOC_WS] = workspace_client_id
        line_anchor_store.set_anchors(tenant_id, line_user_id, anchors)
    except Exception:
        logger.warning("[anchors] record_image_docs failed; skipped", exc_info=True)


def resolve_history(ctx: AgentContext, *, allow_carrier_insert: bool = False) -> Optional[dict]:
    """锚点指向的单据,复核后返回(shape 兼容 _locate_doc 的 hist 消费:id/seller_name/
    total_amount/invoice_no)。锚空/查无/可见性不符 → None(回落最近一张)。
    allow_carrier_insert 随 _locate_doc 的 allow_doc_fallback:查状态等纯读不许插载体行。"""
    from core import db

    hid = (ctx.anchors or {}).get(LAST_HISTORY_ID)
    if hid:
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
    doc_id = (ctx.anchors or {}).get(LAST_IMAGE_DOC_ID)
    if doc_id:
        return _resolve_image_doc(
            ctx,
            str(doc_id),
            (ctx.anchors or {}).get(LAST_IMAGE_DOC_WS),
            allow_carrier_insert=allow_carrier_insert,
        )
    return None


def _resolve_image_doc(ctx, doc_id, ws, *, allow_carrier_insert: bool) -> Optional[dict]:
    """图片单锚 → 读时复核状态(posted/draft 才认·ทิ้ง/撤销的死单不认)→ 载体 hist。
    任何故障 → None 维持回落口径。"""
    try:
        from core import db
        from services.agent import doc_fallback
        from services.purchase import docs as docs_svc

        ws = ws or ctx.workspace_client_id
        if not (ctx.tenant_id and ws):
            return None
        with db.get_cursor_rls(ctx.tenant_id, workspace_client_id=ws) as cur:
            detail = docs_svc.get_doc(
                cur, tenant_id=ctx.tenant_id, workspace_client_id=ws, doc_id=doc_id
            )
        if not detail or (detail.get("doc") or {}).get("status") not in ("posted", "draft"):
            return None
        return doc_fallback.carrier_hist_for_detail(ctx, ws, detail, insert=allow_carrier_insert)
    except Exception:
        logger.warning("[anchors] image-doc resolve failed; fall back", exc_info=True)
        return None
