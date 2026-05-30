# -*- coding: utf-8 -*-
"""OCR 识别历史 · 读取/分页/详情/PDF 留底/去重查询(只读 DAL · REFACTOR-WA)

从 services/ocr_history/store.py 按域拆出读取半边(纯搬家 · 0 逻辑改)。
覆盖:list_ocr_history(分页+多租户+客户过滤)/ get_ocr_history_detail /
get_history_pdf_info / find_ocr_by_hash / check_duplicate_invoice。
游标走 db.get_cursor(...)·跨域调用走 db.*(find_user_by_id)·store.py 文件头 re-export 回
services.ocr_history.store 命名空间(db.xxx() / store.xxx() 调用点不变)。
"""

import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


def list_ocr_history(
    user_id: str,
    retention_days: Optional[int] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant_id: Optional[str] = None,
    client_id: Optional[int] = None,
    restrict_client_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    分页列表查询。
    retention_days: None=自动从 user 表拉(向后兼容老调用方漏传)
                    0=不可查 / 90=Plus 90 天 / -1=Pro 永久
    keyword: 在 filename / invoice_no / seller_name 里模糊匹配
    v118.14 · tenant_id 给了 → 多租户共享:看同 tenant 所有用户的发票(老板看员工的)
              没给 → 老逻辑:只看自己的(向前兼容)
    v118.28.0 · client_id 给了 → 仅看该客户的发票(顶栏客户切换器)· None 则不过滤
    v118.28.1 · restrict_client_ids: List[int] = 员工只能看分到的客户;None = 不限制
                空列表 = 没分到任何客户(只能看自己上传未归属的)
    v118.27.7.1 · retention_days 改 Optional · 兼容 reports_router 等老调用方漏传
                  None 时从 user 表 history_retention_days 字段自动拉(权限不被绕过)
    """
    # v118.27.7.1 · 自动 fallback:调用方漏传 retention_days 时从 user 表拉真实保留期
    if retention_days is None:
        try:
            user = db.find_user_by_id(user_id)
            if user and user.get("history_retention_days") is not None:
                retention_days = int(user["history_retention_days"])
            else:
                # 兜底:90 天(平衡安全 + 可用 · 比 -1 永久全开稳)
                retention_days = 90
                logger.warning(
                    f"list_ocr_history 自动 fallback: user_id={user_id} 没填 history_retention_days · 用 90 天兜底"
                )
        except Exception as e:
            logger.error(f"list_ocr_history 自动拉 retention_days 失败 (user_id={user_id}): {e}")
            retention_days = 90

    if retention_days == 0:
        return {"items": [], "total": 0}

    # v118.14 · 多租户过滤:tenant 视图(同 tenant 所有人共享)优先 · 否则 fallback 单 user
    if tenant_id:
        where = ["user_id IN (SELECT id FROM users WHERE tenant_id = %s)"]
        params: list = [tenant_id]
    else:
        where = ["user_id = %s"]
        params: list = [user_id]

    if retention_days > 0:
        where.append("created_at >= NOW() - INTERVAL '%s days'" % int(retention_days))

    if keyword:
        where.append("(filename ILIKE %s OR invoice_no ILIKE %s OR seller_name ILIKE %s)")
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])

    # v118.28.0 · 客户切换器过滤
    if client_id is not None:
        where.append("client_id = %s")
        params.append(int(client_id))

    # v118.28.1 · 员工分配过滤(restrict_client_ids = 员工分到的客户;None = 不限制)
    if restrict_client_ids is not None:
        if len(restrict_client_ids) == 0:
            # 没分到任何客户 · 只能看自己上传的未归属发票
            where.append("(user_id = %s AND client_id IS NULL)")
            params.append(user_id)
        else:
            where.append("(client_id = ANY(%s::bigint[]) OR (user_id = %s AND client_id IS NULL))")
            params.append([int(c) for c in restrict_client_ids])
            params.append(user_id)

    where_sql = " AND ".join(where)

    try:
        with db.get_cursor() as cur:
            # 总数
            cur.execute(f"SELECT COUNT(*) AS c FROM ocr_history WHERE {where_sql}", params)
            total = cur.fetchone()["c"]

            # 列表(不带 pages 字段,省流量)
            cur.execute(
                f"""
                SELECT id, filename, page_count, confidence, elapsed_ms,
                       invoice_no, invoice_date, seller_name, total_amount,
                       archive_name, category_tag,
                       fields_edited_at, edit_count, created_at,
                       source_pdf_id, source_index, source_total,
                       source, source_ref,
                       pdf_storage_path
                FROM ocr_history
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
                params + [limit, offset],
            )
            items = []
            for r in cur.fetchall():
                items.append(
                    {
                        "id": str(r["id"]),
                        "filename": r["filename"],
                        "page_count": r["page_count"],
                        "confidence": r["confidence"],
                        "elapsed_ms": r["elapsed_ms"],
                        "invoice_no": r["invoice_no"],
                        "invoice_date": (
                            r["invoice_date"].isoformat() if r["invoice_date"] else None
                        ),
                        "seller_name": r["seller_name"],
                        "total_amount": (
                            float(r["total_amount"]) if r["total_amount"] is not None else None
                        ),
                        "archive_name": r["archive_name"],
                        "category_tag": r["category_tag"],
                        "edited": r["fields_edited_at"] is not None,
                        "edit_count": r["edit_count"],
                        "created_at": r["created_at"].isoformat(),
                        # v0.11 · 多发票拆分字段
                        "source_pdf_id": (
                            str(r["source_pdf_id"]) if r.get("source_pdf_id") else None
                        ),
                        "source_index": r.get("source_index"),
                        "source_total": r.get("source_total"),
                        # v95 · 来源标识
                        "source": r.get("source") or "manual",
                        "source_ref": r.get("source_ref"),
                        # v114 · 是否有 PDF 留底(前端用来决定是否显示「下载 PDF」按钮)
                        "has_pdf": bool(r.get("pdf_storage_path")),
                    }
                )
            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"查询历史失败 (user_id={user_id}): {e}")
        return {"items": [], "total": 0}


def get_ocr_history_detail(
    user_id: str, record_id: str, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """取单条详情(含完整 pages)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可查 · 否则只能查自己的
    """
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id, workspace_client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """,
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms,
                           pages, invoice_no, invoice_date, seller_name, total_amount,
                           archive_name, category_tag,
                           fields_edited_at, edit_count, created_at, updated_at,
                           client_id, workspace_client_id
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """,
                    (record_id, user_id),
                )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "filename": r["filename"],
                "page_count": r["page_count"],
                "confidence": r["confidence"],
                "elapsed_ms": r["elapsed_ms"],
                "pages": r["pages"],
                "invoice_no": r["invoice_no"],
                "invoice_date": r["invoice_date"].isoformat() if r["invoice_date"] else None,
                "seller_name": r["seller_name"],
                "total_amount": float(r["total_amount"]) if r["total_amount"] is not None else None,
                "archive_name": r["archive_name"],
                "category_tag": r["category_tag"],
                "edited": r["fields_edited_at"] is not None,
                "edit_count": r["edit_count"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat(),
                # v107 · 客户归属
                "client_id": int(r["client_id"]) if r.get("client_id") else None,
                # P1d · 卖方账套归属(智能分拣路由读它定目标 endpoint)
                "workspace_client_id": (
                    int(r["workspace_client_id"]) if r.get("workspace_client_id") else None
                ),
            }
    except Exception as e:
        logger.error(f"查询历史详情失败 (id={record_id}): {e}")
        return None


def get_history_pdf_info(
    user_id: str, record_id: str, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """v114 · 取一条历史的 PDF 留底信息(只查路径 · 鉴权用 user_id)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可下载 PDF
    """
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    LIMIT 1
                """,
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    """
                    SELECT pdf_storage_path, pdf_size_bytes, filename
                    FROM ocr_history
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """,
                    (record_id, user_id),
                )
            r = cur.fetchone()
            if not r or not r.get("pdf_storage_path"):
                return None
            return {
                "pdf_storage_path": r["pdf_storage_path"],
                "pdf_size_bytes": r.get("pdf_size_bytes"),
                "filename": r.get("filename"),
            }
    except Exception as e:
        logger.error(f"get_history_pdf_info 失败 (record_id={record_id}): {e}")
        return None


def find_ocr_by_hash(
    user_id: str, file_hash: str, max_age_hours: int = 24 * 30, tenant_id: Optional[str] = None
) -> Optional[dict]:
    """
    按文件哈希查最近的识别结果。
    用于避免重复识别相同文件(省 Gemini 额度)

    v92 · 窗口从 24h 扩到 30 天 · 会计真实场景下月末才会复核上月票 · 24h 太短
    v92 · 只返回有效结果 · 识别失败(关键字段全空)的记录视为未命中 · 配合第 1 层防御
    v118.14 · tenant_id 给了 → 同 tenant 内任意成员上传过此文件就能复用结果(省额度)
    """
    if not file_hash:
        return None
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms, pages,
                           archive_name, category_tag, created_at
                    FROM ocr_history
                    WHERE user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                      AND file_hash = %s
                      AND created_at >= NOW() - INTERVAL '%s hours'
                      AND pages IS NOT NULL
                      AND jsonb_array_length(pages) > 0
                      AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL OR seller_name IS NOT NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                """ % ("%s", "%s", int(max_age_hours)),
                    (tenant_id, file_hash),
                )
            else:
                cur.execute(
                    """
                    SELECT id, filename, page_count, confidence, elapsed_ms, pages,
                           archive_name, category_tag, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND file_hash = %s
                      AND created_at >= NOW() - INTERVAL '%s hours'
                      AND pages IS NOT NULL
                      AND jsonb_array_length(pages) > 0
                      AND (total_amount IS NOT NULL OR invoice_no IS NOT NULL OR seller_name IS NOT NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                """ % ("%s", "%s", int(max_age_hours)),
                    (user_id, file_hash),
                )
            r = cur.fetchone()
            if not r:
                return None
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
    except Exception as e:
        logger.error(f"查缓存失败 (hash={file_hash[:12]}): {e}")
        return None


def check_duplicate_invoice(
    user_id: str,
    invoice_no: Optional[str],
    invoice_date: Optional[str],
    seller_name: Optional[str],
    total_amount: Optional[float],
    exclude_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    v0.13 · 重复发票检测 · 仅当前用户的历史
    返回 None 表示无重复 · 返回 dict 表示有重复 · 含:
      {
        "level": "exact" | "likely",   # exact=发票号严格匹配 / likely=字段组合匹配
        "match": { id, filename, invoice_no, invoice_date, seller_name, total_amount, created_at },
        "matched_fields": [...]         # 匹配上的字段
      }

    第 1 层 · invoice_no 严格匹配(大小写不敏感)
    第 2 层 · 发票号缺失时 · 用 (date+seller+amount) 三字段匹配
    """
    try:
        with db.get_cursor() as cur:
            # ─────────────────────────────────────────
            # 第 1 层 · 发票号严格匹配
            # ─────────────────────────────────────────
            inv = (invoice_no or "").strip()
            if inv:
                where_extra = ""
                params = [user_id, inv.lower()]
                if exclude_id:
                    where_extra = " AND id != %s"
                    params.append(exclude_id)
                cur.execute(
                    f"""
                    SELECT id, filename, invoice_no, invoice_date, seller_name,
                           total_amount, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND invoice_no IS NOT NULL
                      AND invoice_no != ''
                      AND LOWER(invoice_no) = %s
                      {where_extra}
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    params,
                )
                row = cur.fetchone()
                if row:
                    return {
                        "level": "exact",
                        "matched_fields": ["invoice_no"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": (
                                row["invoice_date"].isoformat() if row["invoice_date"] else None
                            ),
                            "seller_name": row["seller_name"],
                            "total_amount": (
                                float(row["total_amount"])
                                if row["total_amount"] is not None
                                else None
                            ),
                            "created_at": row["created_at"].isoformat(),
                        },
                    }

            # ─────────────────────────────────────────
            # 第 2 层 · 字段组合(发票号缺失时)
            # 必须 3 个字段都有 · 才查
            # ─────────────────────────────────────────
            if invoice_date and total_amount is not None and (seller_name or "").strip():
                where_extra = ""
                params = [user_id, invoice_date, float(total_amount), (seller_name or "").strip()]
                if exclude_id:
                    where_extra = " AND id != %s"
                    params.append(exclude_id)
                cur.execute(
                    f"""
                    SELECT id, filename, invoice_no, invoice_date, seller_name,
                           total_amount, created_at
                    FROM ocr_history
                    WHERE user_id = %s
                      AND invoice_date = %s
                      AND total_amount = %s
                      AND seller_name IS NOT NULL
                      AND LOWER(seller_name) = LOWER(%s)
                      {where_extra}
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    params,
                )
                row = cur.fetchone()
                if row:
                    return {
                        "level": "likely",
                        "matched_fields": ["invoice_date", "seller_name", "total_amount"],
                        "match": {
                            "id": str(row["id"]),
                            "filename": row["filename"],
                            "invoice_no": row["invoice_no"],
                            "invoice_date": (
                                row["invoice_date"].isoformat() if row["invoice_date"] else None
                            ),
                            "seller_name": row["seller_name"],
                            "total_amount": (
                                float(row["total_amount"])
                                if row["total_amount"] is not None
                                else None
                            ),
                            "created_at": row["created_at"].isoformat(),
                        },
                    }
        return None
    except Exception as e:
        logger.warning(f"重复检测失败(不影响识别): {e}")
        return None
