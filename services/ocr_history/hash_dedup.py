# -*- coding: utf-8 -*-
"""OCR 识别历史 · 文件哈希去重查询(只读 DAL)。

两版同住(2026-07-23 从 queries.py 收拢):`find_ocr_by_hash` 单查(主站散单上传)与
`find_ocr_by_hashes` 批量(R2B 跨单去重 · services/workorder/steps/ocr_reuse 在整批 OCR 前
一次查回既有读数)。两者判据必须同口径 —— 一处放宽另一处没跟上,同一个文件在散单路和
工单路会得到不同答案;故判据只写在 `_cache_where` 一处,两版拼同一份 WHERE。
"""

from typing import Dict, List, Optional

from core import db
from services.ocr_history.queries import _workspace_clause

import logging

logger = logging.getLogger(__name__)


_CACHE_COLUMNS = """id, filename, page_count, confidence, elapsed_ms, pages,
                       archive_name, category_tag, created_at"""


def _cache_where(
    user_id: str,
    max_age_hours: int,
    tenant_id: Optional[str],
    workspace_client_id: Optional[int],
    strict_workspace: bool,
) -> tuple:
    """单查/批量共用的「这行能不能当缓存复用」判据 → (sql, params)。

    判据只此一处:两版曾各抄一份,加「草稿不当缓存源」时就得改两处、还要靠两条测试盯着
    它们没走散。SQL 里缺的只有 file_hash 那一项 —— 单查用 = %s、批量用 = ANY(%s)。

    · 草稿(staged=TRUE)不当缓存源:识别记录列表按 staged=FALSE 过滤,草稿在界面上看不见、
      也就删不掉,却能一直供 30 天缓存 → 用户重传同一文件永远命中一条自己够不着的旧记录
      (2026-07-23 真实事故:连删日志再重传四次仍全命中)。缓存只认用户看得见、删得掉的
      记录,「删识别记录 = 清缓存」这个等式才成立。
    · 30 天鲜度窗(v92):会计月末才复核上月票,24h 太短。
    · 只认有效结果(v92):识别失败、关键字段全空的记录视为未命中。
    · tenant 给了就同 tenant 成员共享(v118.14 · 省额度);PO-4 套账隔离,strict 时跨客户绝不串。
    """
    ws_sql, ws_params = _workspace_clause(workspace_client_id)
    if strict_workspace and workspace_client_id is not None:
        ws_sql, ws_params = " AND workspace_client_id = %s", (int(workspace_client_id),)
    if tenant_id:
        scope_sql = "user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
        scope_params: tuple = (tenant_id,)
    else:
        scope_sql = "user_id = %s"
        scope_params = (user_id,)
    sql = f"""{scope_sql}
                  AND staged = FALSE
                  AND created_at >= NOW() - INTERVAL '{int(max_age_hours)} hours'
                  AND pages IS NOT NULL
                  AND jsonb_array_length(pages) > 0
                  AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL
                       OR seller_name IS NOT NULL){ws_sql}"""
    return sql, scope_params, ws_params


def _hash_result_row(r) -> dict:
    """一行 ocr_history → 复用读数 dict(单查/批量共用一份键)。"""
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


def find_ocr_by_hash(
    user_id: str,
    file_hash: str,
    max_age_hours: int = 24 * 30,
    tenant_id: Optional[str] = None,
    workspace_client_id: Optional[int] = None,
    strict_workspace: bool = False,
) -> Optional[dict]:
    """按文件哈希查最近一条可复用的识别结果(主站散单上传的缓存命中路)· 判据见 _cache_where。

    命中即复用、零 OCR、零扣费;查不到就照常识别。查库异常 → None(当未命中,绝不阻断上传)。
    """
    if not file_hash:
        return None
    where_sql, scope_params, ws_params = _cache_where(
        user_id, max_age_hours, tenant_id, workspace_client_id, strict_workspace
    )
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                f"""
                SELECT {_CACHE_COLUMNS}
                FROM ocr_history
                WHERE {where_sql}
                  AND file_hash = %s
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (*scope_params, *ws_params, file_hash),
            )
            r = cur.fetchone()
            return _hash_result_row(r) if r else None
    except Exception as e:
        logger.error(f"查缓存失败 (hash={file_hash[:12]}): {e}")
        return None


def find_ocr_by_hashes(
    user_id: str,
    file_hashes: List[str],
    max_age_hours: int = 24 * 30,
    tenant_id: Optional[str] = None,
    workspace_client_id: Optional[int] = None,
    strict_workspace: bool = False,
) -> Dict[str, dict]:
    """批量按文件哈希查回 → {file_hash: 最新一条可复用记录}(每 hash DISTINCT ON 取最新,
    与单查的 ORDER BY created_at DESC LIMIT 1 同口径)· 判据见 _cache_where。

    一次往返查整批,免逐件 N 次查库。空哈希集 / 查库异常 → {}(全部未命中,照常 OCR,绝不阻断分类)。"""
    hashes = [str(h) for h in file_hashes if h]
    if not hashes:
        return {}
    where_sql, scope_params, ws_params = _cache_where(
        user_id, max_age_hours, tenant_id, workspace_client_id, strict_workspace
    )
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                f"""
                SELECT DISTINCT ON (file_hash)
                       {_CACHE_COLUMNS}, file_hash
                FROM ocr_history
                WHERE {where_sql}
                  AND file_hash = ANY(%s)
                ORDER BY file_hash, created_at DESC
            """,
                (*scope_params, *ws_params, hashes),
            )
            return {r["file_hash"]: _hash_result_row(r) for r in cur.fetchall()}
    except Exception as e:
        logger.error(f"批量查缓存失败 (n={len(hashes)}): {e}")
        return {}
