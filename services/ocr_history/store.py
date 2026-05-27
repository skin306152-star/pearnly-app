# -*- coding: utf-8 -*-
"""OCR 识别历史(ocr_history 表)· 读取/分页/详情/编辑/删除 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
覆盖:list_ocr_history(分页+多租户+客户过滤)/ get_ocr_history_detail / update_ocr_history_pages
(会计改字段→重算归档名)/ delete_ocr_history / delete_ocr_history_with_pdf_paths(批量+返 PDF 路径)。
游标走 db.get_cursor(...)·跨域调用走 db.*(find_user_by_id / _extract_summary_fields / get_archive_template)·
确保测试 mock.patch("db.get_cursor") 等仍生效。db.py 文件尾 re-export 回本命名空间(db.xxx() 调用点不变)。
注:insert_ocr_history / 去重(find_ocr_by_hash·check_duplicate_invoice)/ cleanup_expired_history 仍在 db.py(后续单独搬)。
"""

import json as _json
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


def update_ocr_history_pages(
    user_id: str, record_id: str, new_pages: list, tenant_id: Optional[str] = None
) -> bool:
    """会计修改字段后保存。同步刷新冗余字段 + v0.7 重算归档名
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可改 · 否则只能改自己的
    """
    summary = db._extract_summary_fields(new_pages)

    # v0.7 · 重算归档名(按用户当前模板)
    new_archive_name = None
    new_category_tag = None
    try:
        import archive as _archive

        merged = {}
        for p in new_pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            merged = p.get("fields") or {}
            break
        template = db.get_archive_template(user_id) or _archive.DEFAULT_TEMPLATE
        new_archive_name = _archive.preview_name(merged, template)
        new_category_tag = (merged.get("category") or "").strip() or None
    except Exception as e:
        logger.warning(f"重算归档名失败(不影响保存): {e}")

    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                where_sql = "id = %s AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
                where_params = [record_id, tenant_id]
            else:
                where_sql = "id = %s AND user_id = %s"
                where_params = [record_id, user_id]
            cur.execute(
                f"""
                UPDATE ocr_history
                SET pages = %s::jsonb,
                    invoice_no = %s,
                    invoice_date = %s,
                    seller_name = %s,
                    total_amount = %s,
                    archive_name = COALESCE(%s, archive_name),
                    category_tag = COALESCE(%s, category_tag),
                    archived_at = CASE WHEN %s IS NOT NULL THEN NOW() ELSE archived_at END,
                    fields_edited_at = NOW(),
                    edit_count = edit_count + 1,
                    updated_at = NOW()
                WHERE {where_sql}
            """,
                (
                    _json.dumps(new_pages, ensure_ascii=False),
                    summary["invoice_no"],
                    summary["invoice_date"],
                    summary["seller_name"],
                    summary["total_amount"],
                    new_archive_name,
                    new_category_tag,
                    new_archive_name,
                    *where_params,
                ),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"更新历史失败 (id={record_id}): {e}")
        return False


def delete_ocr_history(user_id: str, record_id: str, tenant_id: Optional[str] = None) -> bool:
    """v118.14 · tenant_id 给了 → 同 tenant 任意成员可删 · 否则只能删自己的
    v118.20.4.4 · 修 UUID cast(id 列是 UUID · 字符串需 ::uuid)"""
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = %s::uuid AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
                    (record_id, tenant_id),
                )
            else:
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = %s::uuid AND user_id = %s::uuid",
                    (record_id, user_id),
                )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"删除历史失败 (id={record_id}): {e}")
        return False


def delete_ocr_history_with_pdf_paths(
    user_id: str, record_ids: list, tenant_id: Optional[str] = None
) -> tuple:
    """
    v114 · 批量删除 + 返回被删记录的 PDF 路径列表(给上层清理本地文件)
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可删
    v118.20.4.4 · 修 UUID cast(id 列是 UUID · text[] 需 ::uuid[])
    Returns: (deleted_count, [pdf_path1, pdf_path2, ...])
    """
    if not record_ids:
        return 0, []
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                # 先查路径
                cur.execute(
                    "SELECT pdf_storage_path FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid) AND pdf_storage_path IS NOT NULL",
                    (record_ids, tenant_id),
                )
                paths = [r["pdf_storage_path"] for r in cur.fetchall() if r.get("pdf_storage_path")]
                # 再删
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
                    (record_ids, tenant_id),
                )
            else:
                cur.execute(
                    "SELECT pdf_storage_path FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid AND pdf_storage_path IS NOT NULL",
                    (record_ids, user_id),
                )
                paths = [r["pdf_storage_path"] for r in cur.fetchall() if r.get("pdf_storage_path")]
                cur.execute(
                    "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid",
                    (record_ids, user_id),
                )
            return cur.rowcount, paths
    except Exception as e:
        logger.error(f"批量删除历史失败: {e}")
        return 0, []
