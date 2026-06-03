# -*- coding: utf-8 -*-
"""Bank Reconciliation v2(Statement vs GL)对账任务 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def ensure_bank_recon_v2_table():
    """幂等 DDL · 建 bank_recon_v2_task 表（首次启动时调用）"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bank_recon_v2_task (
                    id          SERIAL PRIMARY KEY,
                    user_id     UUID NOT NULL,
                    tenant_id   UUID,
                    bank_code   TEXT,
                    gl_account  TEXT,
                    stmt_files  TEXT,
                    gl_files    TEXT,
                    stmt_row_count  INTEGER DEFAULT 0,
                    gl_row_count    INTEGER DEFAULT 0,
                    matched_count   INTEGER DEFAULT 0,
                    unmatched_gl    INTEGER DEFAULT 0,
                    unmatched_stmt  INTEGER DEFAULT 0,
                    stmt_opening    NUMERIC(18,2) DEFAULT 0,
                    stmt_closing    NUMERIC(18,2) DEFAULT 0,
                    gl_opening      NUMERIC(18,2) DEFAULT 0,
                    gl_closing      NUMERIC(18,2) DEFAULT 0,
                    formula_diff    NUMERIC(18,2) DEFAULT 0,
                    detail_json     JSONB,
                    summary_json    JSONB,
                    status      TEXT DEFAULT 'done',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_bank_recon_v2_user
                ON bank_recon_v2_task(user_id, created_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_bank_recon_v2_tenant
                ON bank_recon_v2_task(tenant_id, created_at DESC)
                WHERE tenant_id IS NOT NULL
            """)
            logger.info("[v118.33.6] bank_recon_v2_task 表已就绪")
    except Exception as e:
        logger.warning(f"ensure_bank_recon_v2_table failed: {e}")


def create_bank_recon_v2_task(
    user_id: str,
    tenant_id,
    bank_code: str,
    gl_account: str,
    stmt_files: str,
    gl_files: str,
    stmt_row_count: int,
    gl_row_count: int,
    matched_count: int,
    unmatched_gl: int,
    unmatched_stmt: int,
    stmt_opening: float,
    stmt_closing: float,
    gl_opening: float,
    gl_closing: float,
    formula_diff: float,
    detail_json: list,
    summary_json: dict,
) -> Optional[int]:
    import json as _j

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO bank_recon_v2_task (
                    user_id, tenant_id, bank_code, gl_account,
                    stmt_files, gl_files,
                    stmt_row_count, gl_row_count,
                    matched_count, unmatched_gl, unmatched_stmt,
                    stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                    detail_json, summary_json, status
                ) VALUES (
                    %s::uuid, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, 'done'
                ) RETURNING id
            """,
                (
                    str(user_id),
                    str(tenant_id) if tenant_id else None,
                    bank_code or "",
                    gl_account or "",
                    stmt_files or "",
                    gl_files or "",
                    int(stmt_row_count or 0),
                    int(gl_row_count or 0),
                    int(matched_count or 0),
                    int(unmatched_gl or 0),
                    int(unmatched_stmt or 0),
                    float(stmt_opening or 0),
                    float(stmt_closing or 0),
                    float(gl_opening or 0),
                    float(gl_closing or 0),
                    float(formula_diff or 0),
                    _j.dumps(detail_json or [], ensure_ascii=False, default=str),
                    _j.dumps(summary_json or {}, ensure_ascii=False, default=str),
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_bank_recon_v2_task failed: {e}")
        return None


def get_bank_recon_v2_task(task_id: int, user_id: str, tenant_id=None) -> Optional[Dict[str, Any]]:
    """v118.35.0.29 P0 安全 (体检 2026-05-21 风险 2):
    镜像 get_gl_vat_task · 旧签名无权限校验 · 现强制 user_id + 可选 tenant_id ·
    Dual-Key 模式 · DB 层 fail-safe"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT * FROM bank_recon_v2_task WHERE id = %s AND tenant_id = %s::uuid",
                    (task_id, tenant_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM bank_recon_v2_task WHERE id = %s AND user_id = %s::uuid",
                    (task_id, user_id),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_bank_recon_v2_task failed: {e}")
        return None


def list_bank_recon_v2_tasks(user_id: str, tenant_id=None, limit: int = 50) -> List[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, bank_code, gl_account,
                           stmt_files, gl_files,
                           stmt_row_count, gl_row_count,
                           matched_count, unmatched_gl, unmatched_stmt,
                           stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                           status, created_at
                    FROM bank_recon_v2_task
                    WHERE tenant_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """,
                    (str(tenant_id), int(limit)),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, bank_code, gl_account,
                           stmt_files, gl_files,
                           stmt_row_count, gl_row_count,
                           matched_count, unmatched_gl, unmatched_stmt,
                           stmt_opening, stmt_closing, gl_opening, gl_closing, formula_diff,
                           status, created_at
                    FROM bank_recon_v2_task
                    WHERE user_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """,
                    (str(user_id), int(limit)),
                )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_bank_recon_v2_tasks failed: {e}")
        return []


def delete_bank_recon_v2_task(task_id: int, user_id: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM bank_recon_v2_task WHERE id = %s AND user_id = %s::uuid",
                (task_id, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_bank_recon_v2_task failed: {e}")
        return False


def delete_bank_recon_v2_tasks_batch(ids: list, user_id: str) -> int:
    if not ids:
        return 0
    try:
        clean_ids = [int(i) for i in ids if str(i).isdigit() or isinstance(i, int)]
        if not clean_ids:
            return 0
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM bank_recon_v2_task WHERE id = ANY(%s) AND user_id = %s::uuid",
                (clean_ids, str(user_id)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_bank_recon_v2_tasks_batch failed: {e}")
        return 0
