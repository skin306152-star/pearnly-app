# -*- coding: utf-8 -*-
"""DMS 改写审批申请 DAL(波4)。

销售(dms_role='sales')对老客户的字段改写不直写,落一张变更申请,由管理员在 LINE 上
批准后以**批准人自己的凭据**执行——DMS 侧审计因此显示真实批准人。

状态机:pending →(管理员点批)processing →(DMS 写成功)approved / (写失败)回 pending
可重试;pending →(点拒)rejected;过期惰性判(expires_at 过即视同 expired,读时落库)。
processing 是「正在执行」租约:防两个管理员同点双写;卡死(执行进程崩)超过租约窗自动
视同 pending 可再批。first-wins 由 claim 的条件 UPDATE 原子保证。

建表照 line_dms/store 范式:prod 无 alembic 钩子 → 首用 ensure 幂等自愈(0084 留档)。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 执行租约窗:processing 超过此时长视同回到 pending(执行方崩溃自愈)。
PROCESSING_LEASE_MINUTES = 10
DEFAULT_TTL_HOURS = 24

_TABLE = "dms_change_requests"

_DDL = """
CREATE TABLE IF NOT EXISTS dms_change_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    operator_user_id uuid NOT NULL,
    endpoint_id text,
    customer_id text NOT NULL,
    customer_name text,
    field_diffs jsonb NOT NULL,
    draft jsonb NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    target_user_id uuid,
    decided_by uuid,
    decided_at timestamptz,
    processing_at timestamptz,
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz NOT NULL
)
"""


def ensure_tables() -> None:
    """幂等建表 + tenant 索引 + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_DDL)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_dms_change_requests_tenant_status "
            "ON dms_change_requests (tenant_id, status)"
        )
        apply_tenant_rls(cur, _TABLE)


def _with_heal(fn):
    """表不存在(新库/prod 未跑迁移)→ 建表重试一次;其余异常向上抛。"""
    try:
        return fn()
    except Exception as e:
        if _TABLE not in str(e):
            raise
        ensure_tables()
        return fn()


def _dal(name: str, default):
    def run(fn):
        try:
            return _with_heal(fn)
        except Exception as e:
            logger.error(f"[dms_approval] {name} failed: {e}")
            return default

    return run


# claim/读取共用的「有效 pending」判据:pending 或 processing 租约过期(执行方崩溃自愈)。
_CLAIMABLE = (
    "(status = 'pending' OR (status = 'processing' "
    f"AND processing_at < now() - interval '{PROCESSING_LEASE_MINUTES} minutes'))"
)


def create_request(
    tenant_id: str,
    operator_user_id: str,
    *,
    endpoint_id: str,
    customer_id: str,
    customer_name: str,
    field_diffs: List[dict],
    draft: Dict[str, Any],
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> Optional[str]:
    """落一张待审申请,返回 id。draft/diffs 快照存 JSON,执行时不再依赖会话。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO dms_change_requests "
                "(tenant_id, operator_user_id, endpoint_id, customer_id, customer_name, "
                " field_diffs, draft, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, now() + make_interval(hours => %s)) "
                "RETURNING id",
                (
                    str(tenant_id),
                    str(operator_user_id),
                    str(endpoint_id or ""),
                    str(customer_id),
                    str(customer_name or ""),
                    json.dumps(field_diffs, ensure_ascii=False),
                    json.dumps(draft, ensure_ascii=False),
                    int(ttl_hours),
                ),
            )
            return str(cur.fetchone()["id"])

    return _dal("create_request", None)(_run)


def get_request(tenant_id: str, request_id: str) -> Optional[dict]:
    """读单张申请(惰性过期:pending 已过 expires_at → 先落 expired 再返回)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "UPDATE dms_change_requests SET status = 'expired' "
                "WHERE id = %s AND tenant_id = %s AND " + _CLAIMABLE + " AND expires_at < now()",
                (str(request_id), str(tenant_id)),
            )
            cur.execute(
                "SELECT * FROM dms_change_requests WHERE id = %s AND tenant_id = %s",
                (str(request_id), str(tenant_id)),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    return _dal("get_request", None)(_run)


def set_target(tenant_id: str, request_id: str, target_user_id: Optional[str]) -> bool:
    """定审批人(None=广播全部管理员)。只许对未过期 pending 改派。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "UPDATE dms_change_requests SET target_user_id = %s "
                "WHERE id = %s AND tenant_id = %s AND status = 'pending' "
                "AND expires_at >= now()",
                (
                    str(target_user_id) if target_user_id else None,
                    str(request_id),
                    str(tenant_id),
                ),
            )
            return cur.rowcount == 1

    return bool(_dal("set_target", False)(_run))


def claim(tenant_id: str, request_id: str, decided_by: str) -> Optional[dict]:
    """管理员点批的原子认领(first-wins):有效 pending → processing 并回整行快照。

    抢不到(已被他人处理/已拒/已过期)→ None,调用方读回现状按 status 回话。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "UPDATE dms_change_requests "
                "SET status = 'processing', processing_at = now(), decided_by = %s "
                "WHERE id = %s AND tenant_id = %s AND " + _CLAIMABLE + " AND expires_at >= now() "
                "RETURNING *",
                (str(decided_by), str(request_id), str(tenant_id)),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    return _dal("claim", None)(_run)


def finish(tenant_id: str, request_id: str, status: str) -> bool:
    """执行收尾:processing → approved(写成功)/ rejected(拒)/ pending(写失败回炉可重试)。"""
    if status not in ("approved", "rejected", "pending"):
        return False
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            if status == "pending":  # 回炉:清租约与认领人,任何管理员可再批
                cur.execute(
                    "UPDATE dms_change_requests SET status = 'pending', "
                    "processing_at = NULL, decided_by = NULL "
                    "WHERE id = %s AND tenant_id = %s AND status = 'processing'",
                    (str(request_id), str(tenant_id)),
                )
            else:
                cur.execute(
                    "UPDATE dms_change_requests SET status = %s, decided_at = now() "
                    "WHERE id = %s AND tenant_id = %s AND status = 'processing'",
                    (status, str(request_id), str(tenant_id)),
                )
            return cur.rowcount == 1

    return bool(_dal("finish", False)(_run))
