# -*- coding: utf-8 -*-
"""GL vs 销项税报告对账任务 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


def ensure_gl_vat_task_table():
    """v118.32.5 · GL对账任务表 · 单表存任务元数据 + 明细JSON + 汇总JSON"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gl_vat_task (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    gl_filename TEXT,
                    vat_filename TEXT,
                    gl_row_count INT DEFAULT 0,
                    vat_row_count INT DEFAULT 0,
                    matched_count INT DEFAULT 0,
                    unmatched_count INT DEFAULT 0,
                    diff_count INT DEFAULT 0,
                    detail_json JSONB,
                    summary_json JSONB,
                    status TEXT DEFAULT 'done',
                    error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gl_vat_task_user ON gl_vat_task(user_id, created_at DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gl_vat_task_tenant ON gl_vat_task(tenant_id, created_at DESC)"
            )
        logger.info("[v118.32.5] gl_vat_task 表就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.32.5] gl_vat_task 建表失败: {e}")
        return False


def create_gl_vat_task(
    user_id: str,
    tenant_id,
    gl_filename: str,
    vat_filename: str,
    gl_row_count: int,
    vat_row_count: int,
    detail_json: list,
    summary_json: dict,
    matched_count: int = 0,
    unmatched_count: int = 0,
    diff_count: int = 0,
) -> Optional[int]:
    """落库 GL 对账任务结果 · 返回 task_id"""
    import json as _j

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO gl_vat_task (
                    user_id, tenant_id, gl_filename, vat_filename,
                    gl_row_count, vat_row_count,
                    matched_count, unmatched_count, diff_count,
                    detail_json, summary_json, status
                ) VALUES (
                    %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, 'done'
                )
                RETURNING id
            """,
                (
                    str(user_id),
                    str(tenant_id) if tenant_id else None,
                    gl_filename,
                    vat_filename,
                    int(gl_row_count or 0),
                    int(vat_row_count or 0),
                    int(matched_count or 0),
                    int(unmatched_count or 0),
                    int(diff_count or 0),
                    _j.dumps(detail_json or [], ensure_ascii=False, default=str),
                    _j.dumps(summary_json or {}, ensure_ascii=False, default=str),
                ),
            )
            row = cur.fetchone()
            return int(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_gl_vat_task failed: {e}")
        return None


def get_gl_vat_task(task_id: int, user_id: str, tenant_id=None) -> Optional[Dict[str, Any]]:
    """v118.35.0.29 P0 安全 (体检 2026-05-21 风险 1):
    旧签名 (task_id) 无任何权限校验 · 任何登录用户可读任意 tenant 的对账任务 ·
    现强制 caller 传 user_id · 可选 tenant_id 走 Dual-Key 模式 ·
    DB 层 fail-safe · caller 不传 scope 物理拿不到 row"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    "SELECT * FROM gl_vat_task WHERE id = %s AND tenant_id = %s::uuid",
                    (task_id, tenant_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM gl_vat_task WHERE id = %s AND user_id = %s::uuid",
                    (task_id, user_id),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_gl_vat_task failed: {e}")
        return None


def list_gl_vat_tasks(user_id: str, tenant_id=None, limit: int = 50) -> List[Dict[str, Any]]:
    """列出最近的 GL 对账任务（不返回 detail_json/summary_json 减小数据量）"""
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, gl_filename, vat_filename,
                           gl_row_count, vat_row_count,
                           matched_count, unmatched_count, diff_count,
                           status, created_at
                    FROM gl_vat_task
                    WHERE tenant_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """,
                    (str(tenant_id), int(limit)),
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, tenant_id, gl_filename, vat_filename,
                           gl_row_count, vat_row_count,
                           matched_count, unmatched_count, diff_count,
                           status, created_at
                    FROM gl_vat_task
                    WHERE user_id = %s::uuid
                    ORDER BY created_at DESC LIMIT %s
                """,
                    (str(user_id), int(limit)),
                )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"list_gl_vat_tasks failed: {e}")
        return []


def delete_gl_vat_task(task_id: int, user_id: str) -> bool:
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM gl_vat_task WHERE id = %s AND user_id = %s::uuid",
                (task_id, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"delete_gl_vat_task failed: {e}")
        return False


# v118.32.5.5.20 · 批量删除 GL 对账任务
def delete_gl_vat_tasks_batch(ids: list, user_id: str) -> int:
    """删除多个 GL 对账任务 · 返回成功删除条数。仅限本人任务。"""
    if not ids:
        return 0
    try:
        clean_ids = [int(i) for i in ids if str(i).isdigit() or isinstance(i, int)]
        if not clean_ids:
            return 0
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM gl_vat_task WHERE id = ANY(%s) AND user_id = %s::uuid",
                (clean_ids, str(user_id)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.error(f"delete_gl_vat_tasks_batch failed: {e}")
        return 0
