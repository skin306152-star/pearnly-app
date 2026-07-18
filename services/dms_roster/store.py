# -*- coding: utf-8 -*-
"""操作员花名册档案表 dms_operator_profiles 的 DAL(波3 · DL-8)。

范式照 services/line_dms/store.py:prod 无 alembic 钩子 → 首用 ensure 幂等自愈 + _with_heal
重试一次;tenant_id NOT NULL → apply_tenant_rls 隔离。档案行只存「显示名 + 角色 + 启停」这层
老板可见元数据 —— 凭据落各操作员 erp_endpoints(走 db 现有 DAL),LINE 绑定落 line_dms_bindings。

建操作员用户 + 档案行在同一事务(create_operator_records):用户与档案要么一起有、要么一起无;
erp_endpoint 因走独立 DAL(自管事务、需用户已提交才能过 RLS)是可补偿的尾步,失败由 service 层
调 delete_operator_records 清理,不留半成品。RLS 表走 owner 连接(同 line_dms · 显式 WHERE
tenant_id 兜租户隔离,不依赖会话 RLS 上下文)。
"""

from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

TABLE = "dms_operator_profiles"

_PROFILES = """
CREATE TABLE IF NOT EXISTS dms_operator_profiles (
    user_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    display_name text NOT NULL,
    dms_role text NOT NULL CHECK (dms_role IN ('sales', 'admin')),
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz DEFAULT now()
)
"""


def ensure_tables() -> None:
    """幂等建表 + apply_tenant_rls(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_PROFILES)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_dms_operator_profiles_tenant "
            "ON dms_operator_profiles (tenant_id)"
        )
        apply_tenant_rls(cur, TABLE)


def _with_heal(fn):
    """表不存在(新库/prod 未跑迁移)→ 建表重试一次;其余异常上抛由调用方兜底。"""
    try:
        return fn()
    except Exception as e:
        if TABLE not in str(e):
            raise
        ensure_tables()
        return fn()


def create_operator_records(
    *,
    tenant_id: str,
    username: str,
    password: str,
    company_name: Optional[str],
    display_name: str,
    dms_role: str,
) -> str:
    """同一事务建 member 用户 + 档案行 · 返回新 user_id(异常上抛,由 service 层回滚兜底)。"""
    from core import db
    from services.tenant import owner_users

    def _run() -> str:
        with db.get_cursor(commit=True) as cur:
            uid = owner_users.create_member_user(
                cur,
                tenant_id=tenant_id,
                username=username,
                password=password,
                company_name=company_name,
            )
            cur.execute(
                "INSERT INTO dms_operator_profiles "
                "(user_id, tenant_id, display_name, dms_role) VALUES (%s, %s, %s, %s)",
                (uid, str(tenant_id), display_name, dms_role),
            )
            return uid

    return _with_heal(_run)


def delete_operator_records(*, tenant_id: str, user_id: str) -> None:
    """补偿清理(endpoint 建失败时):删档案行 + 该 member 用户(严格限本租户 · member)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM dms_operator_profiles WHERE tenant_id = %s AND user_id = %s",
            (str(tenant_id), str(user_id)),
        )
        cur.execute(
            "DELETE FROM users WHERE id = %s AND tenant_id = %s AND role = 'member'",
            (str(user_id), str(tenant_id)),
        )


def get_profile(tenant_id: str, user_id: str) -> Optional[dict]:
    """取本租户内某档案行(路由校验 {user_id} 属本租户且有档案 · 防跨租户/防对 owner 自身操作)。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, tenant_id, display_name, dms_role, status "
                "FROM dms_operator_profiles WHERE tenant_id = %s AND user_id = %s",
                (str(tenant_id), str(user_id)),
            )
            return cur.fetchone()

    try:
        row = _with_heal(_run)
    except Exception as e:
        logger.error(f"[dms_roster] get_profile failed: {e}")
        return None
    return dict(row) if row else None


def list_profiles(tenant_id: str) -> List[dict]:
    """列本租户全部操作员档案 + 用户名 + LINE 绑定态 + endpoint 配置态(一次 JOIN,无 N+1)。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT p.user_id, p.display_name, p.dms_role, p.status, p.created_at,
                       u.username,
                       b.display_name AS line_name, b.bound_at,
                       e.enabled AS ep_enabled
                FROM dms_operator_profiles p
                JOIN users u ON u.id = p.user_id
                LEFT JOIN line_dms_bindings b ON b.user_id = p.user_id
                LEFT JOIN LATERAL (
                    SELECT enabled FROM erp_endpoints
                    WHERE user_id = p.user_id AND LOWER(adapter) = 'mrerp_dms'
                    ORDER BY is_default DESC, created_at LIMIT 1
                ) e ON TRUE
                WHERE p.tenant_id = %s
                ORDER BY p.created_at DESC
                """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    try:
        return _with_heal(_run)
    except Exception as e:
        logger.error(f"[dms_roster] list_profiles failed: {e}")
        return []


def update_profile(
    tenant_id: str,
    user_id: str,
    *,
    display_name: Optional[str] = None,
    dms_role: Optional[str] = None,
) -> bool:
    """改显示名/角色(只在给定字段上更新;两者皆空则无操作返 False)。"""
    from core import db

    sets, vals = [], []
    if display_name is not None:
        sets.append("display_name = %s")
        vals.append(display_name)
    if dms_role is not None:
        sets.append("dms_role = %s")
        vals.append(dms_role)
    if not sets:
        return False
    vals.extend([str(tenant_id), str(user_id)])

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                f"UPDATE dms_operator_profiles SET {', '.join(sets)} "
                "WHERE tenant_id = %s AND user_id = %s",
                tuple(vals),
            )
            return cur.rowcount > 0

    try:
        return bool(_with_heal(_run))
    except Exception as e:
        logger.error(f"[dms_roster] update_profile failed: {e}")
        return False


def set_profile_status(tenant_id: str, user_id: str, status: str) -> bool:
    """置启停(active|inactive)。"""
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE dms_operator_profiles SET status = %s "
                "WHERE tenant_id = %s AND user_id = %s",
                (status, str(tenant_id), str(user_id)),
            )
            return cur.rowcount > 0

    try:
        return bool(_with_heal(_run))
    except Exception as e:
        logger.error(f"[dms_roster] set_profile_status failed: {e}")
        return False
