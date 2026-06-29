# -*- coding: utf-8 -*-
"""OCR 识别历史 · 写入/编辑/删除/摘要抽取(变更 DAL · REFACTOR-WA)

从 services/ocr_history/store.py 按域拆出写入半边(纯搬家 · 0 逻辑改)。
覆盖:_extract_summary_fields(摘要字段抽取)/ update_ocr_history_pages(会计改字段→重算归档名)/
delete_ocr_history / delete_ocr_history_with_pdf_paths(批量+返 PDF 路径)/ insert_ocr_history(写入+去重校验)。
游标走 db.get_cursor(...)·跨域调用走 db.*(get_archive_template)·store.py 文件头 re-export 回
services.ocr_history.store 命名空间(db.xxx() / store.xxx() 调用点不变)。
"""

import json as _json
from datetime import datetime as _datetime
import logging
from typing import Optional

from core import db

logger = logging.getLogger(__name__)


def _extract_summary_fields(pages: list) -> dict:
    """从 pages 抽出列表展示用的核心字段
    v106.2 修复:多联发票(底单/发票/收据 3 页) Gemini 可能把所有页都标 is_copy=true ·
    导致摘要字段全 None · 列表显示「未识别到 · 金额 · 发票号 · 日期 · 卖方」误报
    改进:先找非副本主页 · 找不到再用 is_duplicate=False 的页 · 最后兜底用第 1 页
    """
    pages = pages or []

    def _build_from_page(p):
        f = p.get("fields") or {}
        raw_date = f.get("date")
        invoice_date = None
        if raw_date:
            try:
                s = str(raw_date).replace("/", "-")[:10]
                _datetime.strptime(s, "%Y-%m-%d")
                invoice_date = s
            except Exception:
                invoice_date = None
        raw_amt = f.get("total_amount")
        total = None
        if raw_amt is not None:
            try:
                total = float(str(raw_amt).replace(",", ""))
            except Exception:
                total = None
        return {
            "invoice_no": (f.get("invoice_number") or "")[:200] or None,
            "invoice_date": invoice_date,
            "seller_name": (f.get("seller_name") or "")[:200] or None,
            "total_amount": total,
        }

    # 1. 优先 · 非副本主页(是非 is_copy 也非 is_duplicate)
    for p in pages:
        if not p.get("is_copy") and not p.get("is_duplicate"):
            f = p.get("fields") or {}
            if f.get("invoice_number") or f.get("total_amount") or f.get("seller_name"):
                return _build_from_page(p)

    # 2. 兜底 · 全部 is_copy/is_duplicate 时 · 选有最多关键字段的那页
    def _score(p):
        f = p.get("fields") or {}
        s = 0
        if f.get("invoice_number"):
            s += 1
        if f.get("total_amount"):
            s += 1
        if f.get("seller_name"):
            s += 1
        if f.get("date"):
            s += 1
        return s

    if pages:
        best = max(pages, key=_score)
        if _score(best) > 0:
            return _build_from_page(best)

    return {"invoice_no": None, "invoice_date": None, "seller_name": None, "total_amount": None}


def update_ocr_history_pages(
    user_id: str, record_id: str, new_pages: list, tenant_id: Optional[str] = None
) -> bool:
    """会计修改字段后保存。同步刷新冗余字段 + v0.7 重算归档名
    v118.14 · tenant_id 给了 → 同 tenant 任意成员可改 · 否则只能改自己的
    """
    summary = _extract_summary_fields(new_pages)

    # v0.7 · 重算归档名(按用户当前模板)
    new_archive_name = None
    new_category_tag = None
    try:
        from services.archive import archive as _archive

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
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
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
            updated = cur.rowcount > 0
        # 反馈闭环 ② · 编辑落库后捕获用户修正 → 沉淀按主体例库(非致命·绝不影响保存:
        # 已 commit·捕获任何异常只告警,不让本函数返 False)
        if updated:
            try:
                from services.ocr.feedback import store as _feedback

                _feedback.record_correction_from_edit(user_id, tenant_id, record_id, new_pages)
            except Exception as _fe:
                logger.warning(f"反馈捕获跳过 (id={record_id}): {_fe}")
        return updated
    except Exception as e:
        logger.error(f"更新历史失败 (id={record_id}): {e}")
        return False


def update_history_official_name(
    record_id: str,
    official_name: str,
    user_id: str,
    tenant_id: Optional[str] = None,
) -> bool:
    """官方名核验 ③ · 后台回填税局 RD 官方抬头(并存·不动 AI 名)。

    专用窄更新:绝不走 update_ocr_history_pages(那会触发反馈捕获 + 冒充用户编辑 bump
    edit_count)。仅写 seller_name_official + 置 seller_name_verified=TRUE。非致命。"""
    if not official_name or not str(official_name).strip():
        return False
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                "UPDATE ocr_history "
                "SET seller_name_official = %s, seller_name_verified = TRUE, updated_at = NOW() "
                "WHERE id = %s::uuid",
                (str(official_name).strip(), record_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.warning(f"update_history_official_name skip (id={record_id}): {e}")
        return False


def delete_ocr_history(user_id: str, record_id: str, tenant_id: Optional[str] = None) -> bool:
    """v118.14 · tenant_id 给了 → 同 tenant 任意成员可删 · 否则只能删自己的
    v118.20.4.4 · 修 UUID cast(id 列是 UUID · 字符串需 ::uuid)"""
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
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
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
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


def update_ocr_history_pdf_storage(
    record_ids: list,
    pdf_storage_path: str,
    pdf_size_bytes: Optional[int],
    user_id: str,
    tenant_id: Optional[str] = None,
) -> int:
    """REFACTOR-WA-OCRPERF Step1 · 后台回填 PDF 留底路径。

    searchable PDF 生成挪出响应主路径后,响应返回再后台生成 + 调本函数补写 pdf_storage_path/
    pdf_size_bytes(前端 has_pdf 届时显示下载)。**tenant/user 锁**(同
    delete_ocr_history_with_pdf_paths 口径)防越权回填别 tenant/user 的记录。
    Returns: 回填行数(无 record_ids / 无 path / 异常 → 0 · 绝不抛 · 留底失败不影响识别)。
    """
    if not record_ids or not pdf_storage_path:
        return 0
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "UPDATE ocr_history SET pdf_storage_path = %s, pdf_size_bytes = %s "
                    "WHERE id = ANY(%s::uuid[]) "
                    "AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)",
                    (pdf_storage_path, pdf_size_bytes, record_ids, tenant_id),
                )
            else:
                cur.execute(
                    "UPDATE ocr_history SET pdf_storage_path = %s, pdf_size_bytes = %s "
                    "WHERE id = ANY(%s::uuid[]) AND user_id = %s::uuid",
                    (pdf_storage_path, pdf_size_bytes, record_ids, user_id),
                )
            return cur.rowcount
    except Exception as e:
        logger.error(f"update_ocr_history_pdf_storage failed: {e}")
        return 0


def insert_ocr_history(
    user_id: str,
    filename: str,
    page_count: int,
    pages: list,
    confidence: str,
    elapsed_ms: int,
    file_size_kb: Optional[int] = None,
    file_hash: Optional[str] = None,
    archive_name: Optional[str] = None,
    category_tag: Optional[str] = None,
    # v0.11 · 多发票拆分字段
    source_pdf_id: Optional[str] = None,
    source_page_indices: Optional[list] = None,
    source_index: Optional[int] = None,
    source_total: Optional[int] = None,
    # v0.17 · M6 · 来源标识
    source: str = "manual",
    source_ref: Optional[str] = None,
    # v114 · PDF 留底
    pdf_storage_path: Optional[str] = None,
    pdf_size_bytes: Optional[int] = None,
    # v27.8.1.13a · 上传时自动归属客户(右上角客户切换器选中 / 文件夹绑定 / 邮件别名等)
    client_id: Optional[int] = None,
    # 2026-05-24 · 多租户:历史归属租户(原缺失 → tenant_id 恒 NULL → 按租户查历史/对账漏)
    tenant_id: Optional[str] = None,
    # B1 相 1 (2026-05-26) · workspace 账套主体归属(在为哪家公司做账)· 可选 · 带不上 NULL ·
    # 与 client_id(买方)是两个独立字段 · 非强制(缺失不报错·不拦上传)。
    workspace_client_id: Optional[int] = None,
    # 反馈闭环 ② · AI/系统首存基线(永不改 · 用户编辑后据此算修正 diff)。
    # 缺省 None → 落库时自动取 pages(= 各入口首存内容)→ 全 OCR 入口普适留底,无需逐调用方传。
    ai_raw: Optional[list] = None,
) -> Optional[str]:
    """写入一条历史记录,返回新记录的 id(失败返回 None,不影响主流程)"""
    summary = _extract_summary_fields(pages)
    # v27.8.1.13a · 客户归属:校验 client_id 真属于该 user 的 tenant,防越权
    safe_client_id = None
    if client_id is not None:
        try:
            cid = int(client_id)
            with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
                cur.execute(
                    """
                    SELECT id FROM clients
                    WHERE id = %s
                      AND user_id IN (
                          SELECT id FROM users
                          WHERE tenant_id = (SELECT tenant_id FROM users WHERE id = %s)
                            OR id = %s
                      )
                    LIMIT 1
                """,
                    (cid, user_id, user_id),
                )
                if cur.fetchone():
                    safe_client_id = cid
        except Exception as e:
            logger.warning(
                f"insert_ocr_history client_id 校验失败 (user_id={user_id}, client_id={client_id}): {e}"
            )
    # B1 相 1 · workspace 账套归属校验(防越权:只接受属本 tenant/自己的 workspace)·
    # 校验不过/缺失 → NULL · 绝不报错、不拦上传、不碰 client_id(买方)。
    safe_workspace_client_id = None
    if workspace_client_id is not None:
        try:
            wid = int(workspace_client_id)
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM workspace_clients
                    WHERE id = %s
                      AND (
                          (tenant_id IS NOT NULL
                           AND tenant_id = (SELECT tenant_id FROM users WHERE id = %s))
                          OR (tenant_id IS NULL AND user_id = %s)
                      )
                    LIMIT 1
                    """,
                    (wid, user_id, user_id),
                )
                if cur.fetchone():
                    safe_workspace_client_id = wid
        except Exception as e:
            logger.warning(
                f"insert_ocr_history workspace_client_id 校验失败 "
                f"(user_id={user_id}, workspace_client_id={workspace_client_id}): {e}"
            )
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            cur.execute(
                """
                INSERT INTO ocr_history (
                    user_id, tenant_id, filename, page_count, file_size_kb, file_hash,
                    pages, confidence, elapsed_ms,
                    invoice_no, invoice_date, seller_name, total_amount,
                    archive_name, category_tag, archived_at,
                    source_pdf_id, source_page_indices, source_index, source_total,
                    source, source_ref,
                    pdf_storage_path, pdf_size_bytes,
                    client_id, workspace_client_id, ai_raw
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, CASE WHEN %s IS NOT NULL THEN NOW() ELSE NULL END,
                    %s, %s::jsonb, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s::jsonb
                )
                RETURNING id
            """,
                (
                    user_id,
                    str(tenant_id) if tenant_id else None,
                    filename,
                    page_count,
                    file_size_kb,
                    file_hash,
                    _json.dumps(pages, ensure_ascii=False),
                    confidence,
                    elapsed_ms,
                    summary["invoice_no"],
                    summary["invoice_date"],
                    summary["seller_name"],
                    summary["total_amount"],
                    archive_name,
                    category_tag,
                    archive_name,
                    source_pdf_id,
                    _json.dumps(source_page_indices) if source_page_indices else None,
                    source_index,
                    source_total,
                    source,
                    source_ref,
                    pdf_storage_path,
                    pdf_size_bytes,
                    safe_client_id,
                    safe_workspace_client_id,
                    _json.dumps(ai_raw if ai_raw is not None else pages, ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
            new_id = str(row["id"]) if row else None
        # ③ 官方名核验 · 落库后后台按卖方税号查税局 RD 官方抬头回填(全 OCR 入口普适·
        # 有运行 loop 才调度·无 loop 的线程优雅跳过·非致命)。
        if new_id:
            _schedule_official_name(new_id, pages, user_id, tenant_id)
        return new_id
    except Exception as e:
        logger.error(f"写入历史记录失败 (user_id={user_id}, file={filename}): {e}")
        return None


def _schedule_official_name(history_id: str, pages: list, user_id: str, tenant_id: Optional[str]):
    try:
        fields = (pages or [{}])[0].get("fields") or {}
        seller_tax = fields.get("seller_tax")
        if not seller_tax:
            return
        from services.rd import official_name

        official_name.schedule([(history_id, seller_tax)], user_id, tenant_id)
    except Exception as e:
        logger.warning(f"official-name schedule skip (id={history_id}): {e}")
