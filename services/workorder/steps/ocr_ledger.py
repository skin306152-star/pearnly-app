# -*- coding: utf-8 -*-
"""工单 OCR ↔ ocr_history 识别台账双写(MC2-A2 ② · 件 1)。

classify 每件 OCR 落库时把读值双写一条 ocr_history(主站识别台账据此看得见工单侧识别),
并回填 work_order_items.ocr_history_id。从 classify 抽出(单文件 <500 铁律 + 单一职责):
classify 只管归堆/查重/落事件,台账双写是旁路,失败只留 NULL 绝不拖垮主步。

归属:ocr_history.user_id NOT NULL + FK users,工单无交互 user,故借账套 owner user 落库
(与汇总批量建单 3759f2dd 用发起人 user 同理)。source=workorder_classify 与主站散单/汇总
批量台账分得开;成本归因已在 classify._ocr_safe 落 ai_usage,这里纯搬读值不重复计费。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def resolve_owner(ctx) -> Optional[dict]:
    """双写归属:工单 → workspace_client → {owner user_id, workspace_client_id, tenant_id}。

    未绑客户 / 查不到 owner user / 查询出错 → None(双写整体优雅跳过,item.ocr_history_id 如实
    留 NULL)。走 ctx.cur 同事务只读;整步解析一次(逐件复用,不 N 次查库)。归属解析失败绝不
    拖垮 classify——台账是旁路,主步(归堆/查重/落事件)不受影响。"""
    try:
        wo = ctx.store.get_work_order(
            ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
        )
        client_id = (wo or {}).get("workspace_client_id")
        if not client_id:
            return None
        ctx.cur.execute(
            "SELECT user_id FROM workspace_clients "
            "WHERE id = %s AND (tenant_id = %s OR tenant_id IS NULL)",
            (client_id, ctx.tenant_id),
        )
        row = ctx.cur.fetchone()
    except Exception as exc:  # noqa: BLE001 - 归属解析失败=无台账归属,旁路优雅跳过不拖垮主步
        logger.debug("workorder ocr_history 归属解析跳过: %s", exc)
        return None
    if not row:
        return None
    user_id = row["user_id"] if isinstance(row, dict) else row[0]
    if not user_id:
        return None
    return {
        "user_id": str(user_id),
        "workspace_client_id": int(client_id),
        "tenant_id": str(ctx.tenant_id),
    }


def record(item: dict, fields: dict, owner: Optional[dict]) -> Optional[str]:
    """一件 OCR 读值 → 一条 ocr_history 识别台账,返回 history_id 供回填 item。

    owner=None(未绑客户/无 owner)或写库失败 → None,item.ocr_history_id 如实留 NULL,绝不拖垮
    classify。pages.fields 剥内部下划线字段,与事件流 item_classified 的钱字段同源同值
    (classify._money_fields 取的也是这份 fields)。insert_ocr_history 自管 RLS 事务。"""
    if not owner:
        return None
    clean = {k: v for k, v in (fields or {}).items() if not str(k).startswith("_")}
    name = item.get("original_name") or Path(item.get("file_ref") or "").name or "workorder-item"
    try:
        from core import db

        return db.insert_ocr_history(
            user_id=owner["user_id"],
            filename=name,
            page_count=1,
            pages=[{"fields": clean, "is_copy": False, "is_duplicate": False}],
            confidence=fields.get("_confidence_band") or "high",
            elapsed_ms=0,
            source="workorder_classify",
            source_ref=str(item.get("id")),
            tenant_id=owner.get("tenant_id"),
            workspace_client_id=owner.get("workspace_client_id"),
        )
    except Exception as exc:  # noqa: BLE001 - 台账双写是旁路,失败只留 NULL,绝不拖垮 classify
        logger.warning("workorder ocr_history 双写跳过 (item=%s): %s", item.get("id"), exc)
        return None
