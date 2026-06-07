# -*- coding: utf-8 -*-
"""vat_recon_tasks · Excel 销项税对账任务持久化 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional

from core import db

logger = logging.getLogger(__name__)


def _ws_clause(workspace_client_id: Optional[int]) -> tuple:
    """PO-6c 套账隔离过滤子句 + 参数(rollout-safe 含 IS NULL · PO-1 已回填 · 残留 NULL 仅废租户)。"""
    if workspace_client_id is None:
        return "", ()
    return " AND (workspace_client_id = %s OR workspace_client_id IS NULL)", (
        int(workspace_client_id),
    )


def ensure_vat_recon_tasks_table():
    """幂等建表 · 启动时调用"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vat_recon_tasks (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id       UUID,
                    user_id         UUID NOT NULL,
                    client_name     TEXT,
                    period          TEXT,
                    invoice_count   INTEGER NOT NULL DEFAULT 0,
                    report_count    INTEGER NOT NULL DEFAULT 0,
                    matched         INTEGER NOT NULL DEFAULT 0,
                    mismatched      INTEGER NOT NULL DEFAULT 0,
                    mismatch_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
                    status          TEXT NOT NULL DEFAULT 'done',
                    elapsed_seconds NUMERIC(8,2),
                    excel_path      TEXT,
                    raw_data_json   JSONB,
                    lang            TEXT NOT NULL DEFAULT 'th',
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_created
                    ON vat_recon_tasks(tenant_id, created_at DESC)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_period
                    ON vat_recon_tasks(tenant_id, period)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_tenant_status
                    ON vat_recon_tasks(tenant_id, status)
                    WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vrt_user
                    ON vat_recon_tasks(user_id);
            """)
        logger.info("✅ vat_recon_tasks 表已就绪 (v118.32.4.10.0)")
    except Exception as e:
        logger.error(f"ensure_vat_recon_tasks_table failed: {e}")


def create_vat_recon_task(
    tenant_id,
    user_id: str,
    client_name: str,
    period: str,
    invoice_count: int,
    report_count: int,
    matched: int,
    mismatched: int,
    mismatch_amount: float,
    elapsed_seconds: float,
    excel_path,
    raw_data_json,
    lang: str = "th",
    workspace_client_id: Optional[int] = None,
):
    """INSERT · 返回新 task UUID"""
    import json as _json

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO vat_recon_tasks
                    (tenant_id, user_id, client_name, period,
                     invoice_count, report_count, matched, mismatched,
                     mismatch_amount, elapsed_seconds, excel_path, raw_data_json, lang,
                     workspace_client_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    str(tenant_id) if tenant_id else None,
                    str(user_id),
                    client_name or "",
                    period or "",
                    invoice_count,
                    report_count,
                    matched,
                    mismatched,
                    round(float(mismatch_amount or 0), 2),
                    round(float(elapsed_seconds or 0), 2),
                    excel_path,
                    _json.dumps(raw_data_json, ensure_ascii=False) if raw_data_json else None,
                    lang,
                    workspace_client_id,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_vat_recon_task failed: {e}")
        return None


def list_vat_recon_tasks(
    tenant_id,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    status=None,
    period=None,
    workspace_client_id: Optional[int] = None,
):
    """列表查询 · 带分页 · tenant 隔离(PO-6c:再叠套账过滤 rollout-safe)"""
    try:
        where = []
        params = []
        if tenant_id:
            where.append("tenant_id = %s")
            params.append(str(tenant_id))
        else:
            where.append("user_id = %s::uuid")
            params.append(str(user_id))
        if workspace_client_id is not None:
            where.append("(workspace_client_id = %s OR workspace_client_id IS NULL)")
            params.append(int(workspace_client_id))
        if status:
            where.append("status = %s")
            params.append(status)
        if period:
            where.append("period = %s")
            params.append(period)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        offset = (max(page, 1) - 1) * page_size

        with db.get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM vat_recon_tasks {where_sql}", params)
            total = int(cur.fetchone()["n"] or 0)
            cur.execute(
                f"""
                SELECT id, tenant_id, user_id, client_name, period,
                       invoice_count, report_count, matched, mismatched,
                       mismatch_amount, status, elapsed_seconds, excel_path,
                       lang, created_at, updated_at
                FROM vat_recon_tasks
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
                params + [page_size, offset],
            )
            rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.error(f"list_vat_recon_tasks failed: {e}")
        return {"rows": [], "total": 0, "page": page, "page_size": page_size}


def get_vat_recon_task(task_id: str, tenant_id, user_id: str, workspace_client_id=None):
    """单条详情 · 含 raw_data_json · tenant 隔离(PO-6c:再叠套账过滤 rollout-safe)"""
    ws_sql, ws_params = _ws_clause(workspace_client_id)
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    f"SELECT * FROM vat_recon_tasks WHERE id = %s::uuid AND tenant_id = %s{ws_sql}",
                    (task_id, str(tenant_id), *ws_params),
                )
            else:
                cur.execute(
                    f"SELECT * FROM vat_recon_tasks WHERE id = %s::uuid AND user_id = %s::uuid{ws_sql}",
                    (task_id, str(user_id), *ws_params),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_vat_recon_task failed: {e}")
        return None


def delete_vat_recon_task(task_id: str, tenant_id, user_id: str):
    """DELETE · 返回 excel_path 供调用方删文件"""
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    "DELETE FROM vat_recon_tasks WHERE id = %s::uuid AND tenant_id = %s RETURNING excel_path",
                    (task_id, str(tenant_id)),
                )
            else:
                cur.execute(
                    "DELETE FROM vat_recon_tasks WHERE id = %s::uuid AND user_id = %s::uuid RETURNING excel_path",
                    (task_id, str(user_id)),
                )
            row = cur.fetchone()
            return row["excel_path"] if row else None
    except Exception as e:
        logger.error(f"delete_vat_recon_task failed: {e}")
        return None


def delete_vat_recon_tasks_older_than(days: int, tenant_id, user_id: str):
    """删除 days 天前的任务 · tenant 隔离 · 返回 (deleted_count, excel_paths[])"""
    try:
        with db.get_cursor(commit=True) as cur:
            if tenant_id:
                cur.execute(
                    """
                    DELETE FROM vat_recon_tasks
                    WHERE tenant_id = %s
                      AND created_at < NOW() - (%s || ' days')::interval
                    RETURNING excel_path
                """,
                    (str(tenant_id), str(int(days))),
                )
            else:
                cur.execute(
                    """
                    DELETE FROM vat_recon_tasks
                    WHERE user_id = %s::uuid
                      AND created_at < NOW() - (%s || ' days')::interval
                    RETURNING excel_path
                """,
                    (str(user_id), str(int(days))),
                )
            rows = cur.fetchall()
            paths = [r["excel_path"] for r in rows if r.get("excel_path")]
            return len(rows), paths
    except Exception as e:
        logger.error(f"delete_vat_recon_tasks_older_than failed: {e}")
        return 0, []


def get_vat_recon_tasks_kpi(tenant_id, user_id: str, workspace_client_id=None):
    """本月 KPI: total / running / done / failed(PO-6c:再叠套账过滤 rollout-safe)"""
    ws_sql, ws_params = _ws_clause(workspace_client_id)
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    f"""
                    SELECT
                        COUNT(*) FILTER (WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())) AS this_month,
                        COUNT(*) FILTER (WHERE status = 'running') AS running,
                        COUNT(*) FILTER (WHERE status = 'done') AS done,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed
                    FROM vat_recon_tasks WHERE tenant_id = %s{ws_sql}
                """,
                    (str(tenant_id), *ws_params),
                )
            else:
                cur.execute(
                    f"""
                    SELECT
                        COUNT(*) FILTER (WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())) AS this_month,
                        COUNT(*) FILTER (WHERE status = 'running') AS running,
                        COUNT(*) FILTER (WHERE status = 'done') AS done,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed
                    FROM vat_recon_tasks WHERE user_id = %s::uuid{ws_sql}
                """,
                    (str(user_id), *ws_params),
                )
            row = cur.fetchone()
            if row:
                return {k: int(row[k] or 0) for k in ("this_month", "running", "done", "failed")}
            return {"this_month": 0, "running": 0, "done": 0, "failed": 0}
    except Exception as e:
        logger.error(f"get_vat_recon_tasks_kpi failed: {e}")
        return {"this_month": 0, "running": 0, "done": 0, "failed": 0}
