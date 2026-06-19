# -*- coding: utf-8 -*-
"""图片指纹 → 已录单据(P1G-Perf · LINE 图片票早期去重短路)。

同一张照片再次发来时,据 image_sha256 找到上次建的单据,直接重发它的当前状态卡,
不重跑 Vision/Gemini/分类(治「重复票仍跑满 60s」)。dedupe_key 是内容指纹(需先 OCR
出字段才能算),救不了时间;image_sha256 是图片字节指纹,下载即可算 → 在 OCR 前短路。

隔离:每句 WHERE tenant_id + workspace_client_id;值全 %s 参数化。调用方管事务。
"""

from __future__ import annotations

from typing import Optional

# 短路只认「近期」单据:超期的同图(如去年同张票重发)宁可重跑也不复活旧单(避免误指向
# 已归档/语义已变的远期记录)。窗口足够覆盖「连发两次 / 当天重发」的真实场景。
_RECENT_DAYS = 30


def set_sha(cur, *, tenant_id, workspace_client_id, doc_id, image_sha256) -> None:
    """把图片字节指纹挂到单据(建单后调一次)。空 sha → no-op。"""
    if not image_sha256:
        return
    cur.execute(
        "UPDATE purchase_docs SET image_sha256 = %s "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (image_sha256, tenant_id, workspace_client_id, doc_id),
    )


def find_recent(cur, *, tenant_id, workspace_client_id, image_sha256) -> Optional[dict]:
    """按图片指纹查近期单据(同套账)。返回 {id, status} 或 None。

    取最近一条(同图可能在改错/作废后又重发);草稿被删则查不到 → 调用方回落正常 OCR。
    """
    if not image_sha256:
        return None
    cur.execute(
        "SELECT id, status FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND image_sha256 = %s "
        "AND status <> 'discarded' "  # 草稿软删=视同删除 → 同图重发回落正常 OCR(不短路重发已删卡)
        "AND created_at >= now() - make_interval(days => %s) "
        "ORDER BY created_at DESC LIMIT 1",
        (tenant_id, workspace_client_id, image_sha256, _RECENT_DAYS),
    )
    row = cur.fetchone()
    return {"id": str(row["id"]), "status": row["status"]} if row else None
