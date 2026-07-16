# -*- coding: utf-8 -*-
"""OCR 识别历史 · 文件哈希批量去重查询(只读 DAL)。

R2B 跨单去重(services/workorder/steps/ocr_reuse):classify 一批 pending 图片调 OCR 前,按文件
哈希一次 SQL 查回既有识别读数,命中即复用、零 OCR、零 ai_usage。单查版 find_ocr_by_hash 仍在
queries.py(主站散单路径),此处只放批量版——queries.py 已达单文件行数上限,新查询单开叶子。
判据与单查逐字节同口径:tenant 内成员共享 / 30 天鲜度窗 / 只认关键字段非空的有效记录 / PO-4
套账隔离(strict_workspace 严格同账套,跨客户绝不串);workspace 子句复用 queries._workspace_clause。
"""

from typing import Dict, List, Optional

from core import db
from services.ocr_history.queries import _workspace_clause

import logging

logger = logging.getLogger(__name__)


def find_ocr_by_hashes(
    user_id: str,
    file_hashes: List[str],
    max_age_hours: int = 24 * 30,
    tenant_id: Optional[str] = None,
    workspace_client_id: Optional[int] = None,
    strict_workspace: bool = False,
) -> Dict[str, dict]:
    """批量按文件哈希查回 → {file_hash: 最新一条有效记录}(每 hash DISTINCT ON 取最新,
    与单查 find_ocr_by_hash 的 ORDER BY created_at DESC LIMIT 1 同口径)。一次往返查整批,
    免逐件 N 次查库。空哈希集 / 查库异常 → {}(全部未命中,照常 OCR,绝不阻断分类)。"""
    hashes = [str(h) for h in file_hashes if h]
    if not hashes:
        return {}
    ws_sql, ws_params = _workspace_clause(workspace_client_id)
    if strict_workspace and workspace_client_id is not None:  # R2B 严格同账套,跨客户绝不串
        ws_sql, ws_params = " AND workspace_client_id = %s", (int(workspace_client_id),)
    hours = int(max_age_hours)
    if tenant_id:
        scope_sql = "user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
        scope_params: tuple = (tenant_id,)
    else:
        scope_sql = "user_id = %s"
        scope_params = (user_id,)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                f"""
                SELECT DISTINCT ON (file_hash)
                       id, filename, page_count, confidence, elapsed_ms, pages,
                       archive_name, category_tag, created_at, file_hash
                FROM ocr_history
                WHERE {scope_sql}
                  AND file_hash = ANY(%s)
                  AND created_at >= NOW() - INTERVAL '{hours} hours'
                  AND pages IS NOT NULL
                  AND jsonb_array_length(pages) > 0
                  AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL OR seller_name IS NOT NULL){ws_sql}
                ORDER BY file_hash, created_at DESC
            """,
                (*scope_params, hashes, *ws_params),
            )
            return {r["file_hash"]: _hash_result_row(r) for r in cur.fetchall()}
    except Exception as e:
        logger.error(f"批量查缓存失败 (n={len(hashes)}): {e}")
        return {}


def _hash_result_row(r) -> dict:
    """一行 ocr_history → 复用读数 dict(与单查 find_ocr_by_hash 的返回投影同键)。"""
    return {
        "id": str(r["id"]),
        "filename": r["filename"],
        "page_count": r["page_count"],
        "confidence": r["confidence"],
        "elapsed_ms": r["elapsed_ms"],
        "pages": r["pages"],
        "archive_name": r.get("archive_name"),
        "category_tag": r.get("category_tag"),
        "created_at": r["created_at"].isoformat(),
    }
