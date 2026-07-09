# -*- coding: utf-8 -*-
"""账套/租户管理 · 租户查询/创建/配额/状态/用量 + 用户多公司切换(数据访问层 · REFACTOR-WA)

从 services/tenant/store.py 按域拆出租户核心半边(纯搬家 · 0 逻辑改)。
覆盖:get_tenant/get_user_tenant/list_all_tenants/create_tenant/update_tenant_quota/
update_tenant_status/get_tenant_monthly_usage/increment_tenant_monthly_usage/
list_tenant_members/get_tenant_usage_summary/list_user_companies/set_user_active_tenant。
所有游标走 db.get_cursor(...) · 跨域 db 函数走 db.* · store.py 文件头 re-export 回
services.tenant.store 命名空间(db.xxx() 调用点不变)。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """根据 tenant_id 查租户信息"""
    if not tenant_id:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM tenants WHERE id = %s LIMIT 1",
                (str(tenant_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_tenant failed (id={tenant_id}): {e}")
        return None


def get_user_tenant(user_id: str) -> Optional[Dict[str, Any]]:
    """根据 user_id 查他所属的租户信息"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT t.*
                FROM tenants t
                JOIN users u ON u.tenant_id = t.id
                WHERE u.id = %s
                LIMIT 1
            """,
                (str(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_user_tenant failed (user_id={user_id}): {e}")
        return None


def list_all_tenants(limit: int = 200) -> List[Dict[str, Any]]:
    """
    超级管理员用 · 列出所有租户 + 每家当前用户数 + 用量概况
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.*,
                    (SELECT COUNT(*) FROM users WHERE tenant_id = t.id) AS actual_member_count,
                    (SELECT COUNT(*) FROM ocr_history oh
                      JOIN users u ON u.id = oh.user_id
                     WHERE u.tenant_id = t.id
                       AND oh.created_at >= DATE_TRUNC('month', NOW())
                    ) AS ocr_this_month
                FROM tenants t
                ORDER BY t.created_at DESC
                LIMIT %s
            """,
                (int(limit),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_all_tenants failed: {e}")
        return []


def create_tenant(
    name: str,
    owner_user_id: Optional[str] = None,
    tenant_type: str = "shared_api",
    monthly_quota: int = 100,
    notes: Optional[str] = None,
) -> Optional[str]:
    """
    超级管理员用 · 创建一个新租户
    tenant_type:
        'shared_api' = 月付 · 共用系统 Gemini key
        'byo_api'    = 买断 · 用户自带 Gemini key
        'admin'      = 超级管理员租户
    返回新建 tenant 的 id · 失败返回 None
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO tenants (
                    name, owner_user_id, tenant_type,
                    monthly_quota, used_this_month, status,
                    notes, member_count
                ) VALUES (
                    %s, %s, %s,
                    %s, 0, 'active',
                    %s, 0
                )
                RETURNING id
            """,
                (
                    name,
                    str(owner_user_id) if owner_user_id else None,
                    tenant_type,
                    int(monthly_quota) if monthly_quota else 0,
                    notes,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"create_tenant failed (name={name}): {e}")
        return None


def update_tenant_quota(tenant_id: str, monthly_quota: int) -> bool:
    """
    超级管理员用 · 改租户月度限额
    传 0 = 不限额(买断类 tenant 用)
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tenants SET monthly_quota = %s, updated_at = NOW() WHERE id = %s",
                (int(monthly_quota), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_tenant_quota failed: {e}")
        return False


def update_tenant_status(tenant_id: str, status: str) -> bool:
    """
    超级管理员用 · 改租户状态
    可选:active / warning / suspended / frozen
    """
    if status not in ("active", "warning", "suspended", "frozen"):
        logger.warning(f"update_tenant_status 无效状态: {status}")
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tenants SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_tenant_status failed: {e}")
        return False


def get_tenant_monthly_usage(tenant_id: str) -> Dict[str, Any]:
    """
    查租户当月用量(跨月显示层重置)
    返回 { used, quota, remaining, percent }
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT monthly_quota, used_this_month, quota_reset_at
                FROM tenants WHERE id = %s LIMIT 1
            """,
                (str(tenant_id),),
            )
            row = cur.fetchone()
            if not row:
                return {"used": 0, "quota": 0, "remaining": 0, "percent": 0}

            quota = int(row["monthly_quota"] or 0)
            used = int(row["used_this_month"] or 0)

            # 跨月显示层检查
            reset_at = row.get("quota_reset_at")
            from datetime import date

            today = date.today()
            if reset_at and hasattr(reset_at, "year"):
                if reset_at.year != today.year or reset_at.month != today.month:
                    used = 0

            remaining = max(quota - used, 0) if quota > 0 else -1  # -1 = 不限
            percent = round(used / quota * 100, 1) if quota > 0 else 0
            return {
                "used": used,
                "quota": quota,
                "remaining": remaining,
                "percent": percent,
            }
    except Exception as e:
        logger.error(f"get_tenant_monthly_usage failed: {e}")
        return {"used": 0, "quota": 0, "remaining": 0, "percent": 0}


def increment_tenant_monthly_usage(tenant_id: str, n: int = 1) -> int:
    """
    租户级配额累加 · 跨月自动重置
    返回最新 used_this_month · 失败返回 -1
    """
    if not tenant_id:
        return -1
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE tenants SET
                    used_this_month = CASE
                        WHEN quota_reset_at IS NULL
                          OR quota_reset_at < DATE_TRUNC('month', NOW())::date
                        THEN %s
                        ELSE COALESCE(used_this_month, 0) + %s
                    END,
                    quota_reset_at = DATE_TRUNC('month', NOW())::date,
                    last_active_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING used_this_month
            """,
                (n, n, str(tenant_id)),
            )
            row = cur.fetchone()
            return int(row["used_this_month"]) if row else -1
    except Exception as e:
        logger.warning(f"increment_tenant_monthly_usage failed (id={tenant_id}): {e}")
        return -1


def list_tenant_members(tenant_id: str) -> List[Dict[str, Any]]:
    """
    列出某租户的所有用户(老板 + 员工)
    超管后台 / 租户管理页用
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email, role, is_active, is_super_admin,
                       last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s
                ORDER BY
                    CASE WHEN role = 'owner' THEN 0 ELSE 1 END,
                    created_at ASC
            """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_tenant_members failed (tenant_id={tenant_id}): {e}")
        return []


def get_tenant_usage_summary(tenant_id: str) -> Dict[str, Any]:
    """
    租户运营面板用 · 返回完整概况
    - 配额 / 用量 / 剩余 / 百分比
    - 本月识别数
    - 用户数
    - 最近活跃
    """
    try:
        quota = get_tenant_monthly_usage(tenant_id)

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users WHERE tenant_id = %s) AS user_count,
                    (SELECT COUNT(*) FROM ocr_history oh
                      JOIN users u ON u.id = oh.user_id
                     WHERE u.tenant_id = %s
                       AND oh.created_at >= DATE_TRUNC('month', NOW())
                    ) AS ocr_this_month,
                    (SELECT MAX(last_login_at) FROM users WHERE tenant_id = %s) AS last_login
            """,
                (str(tenant_id), str(tenant_id), str(tenant_id)),
            )
            stats = cur.fetchone()

        return {
            "quota": quota,
            "user_count": stats["user_count"] if stats else 0,
            "ocr_this_month": stats["ocr_this_month"] if stats else 0,
            "last_login": (
                stats["last_login"].isoformat() if stats and stats.get("last_login") else None
            ),
        }
    except Exception as e:
        logger.error(f"get_tenant_usage_summary failed: {e}")
        return {
            "quota": {"used": 0, "quota": 0, "remaining": 0, "percent": 0},
            "user_count": 0,
            "ocr_this_month": 0,
            "last_login": None,
        }


# ============================================================
# 多公司成员 / 当前账套切换(REFACTOR-B2 · 从 db.py 搬入 · 纯搬家 0 逻辑改)
# user_company_roles 表 · active_tenant_id · billing_routes 用
# ============================================================
def list_user_companies(user_id: str) -> list:
    """Return all companies a user belongs to.

    Each item: {tenant_id, name, role, balance_thb, pages_this_month, is_active}
    Uses Asia/Bangkok timezone for year_month.
    """
    try:
        year_month = db._bkk_year_month()
        with db.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    ucr.tenant_id::text AS tenant_id,
                    t.name AS name,
                    ucr.role AS role,
                    ucr.is_active AS is_active,
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month,
                    COALESCE(ts.pages_used_this_cycle, 0) AS sub_pages_used
                FROM user_company_roles ucr
                JOIN tenants t ON t.id = ucr.tenant_id
                LEFT JOIN tenant_credits tc ON tc.tenant_id = ucr.tenant_id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = ucr.tenant_id AND mpu.year_month = %s
                {db.active_sub_usage_join_sql("ts", "ucr.tenant_id")}
                WHERE ucr.user_id = %s::uuid AND ucr.is_active = TRUE
                ORDER BY t.name
            """,
                (year_month, str(user_id)),
            )
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            # 本月用量 = 按量表 + 活跃订阅本周期用量(两计数器互斥不重复计 · 见
            # services/billing/subscription.py active_sub_usage_join_sql)
            pages_this_month = int(r["pages_this_month"] or 0) + int(r.get("sub_pages_used") or 0)
            out.append(
                {
                    "tenant_id": r["tenant_id"],
                    "name": r["name"] or "",
                    "role": r["role"] or "member",
                    "balance_thb": float(r["balance_thb"] or 0),
                    "pages_this_month": pages_this_month,
                    "is_active": bool(r["is_active"]),
                }
            )
        return out
    except Exception as e:
        logger.error(f"list_user_companies failed: {e}")
        return []


def set_user_active_tenant(user_id: str, tenant_id: str) -> bool:
    """Validate user belongs to tenant; if yes set active_tenant_id."""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                SELECT 1 FROM user_company_roles
                WHERE user_id = %s::uuid AND tenant_id = %s::uuid AND is_active = TRUE
                LIMIT 1
            """,
                (str(user_id), str(tenant_id)),
            )
            if not cur.fetchone():
                return False
            cur.execute(
                """
                UPDATE users SET active_tenant_id = %s::uuid
                WHERE id = %s::uuid
            """,
                (str(tenant_id), str(user_id)),
            )
        return True
    except Exception as e:
        logger.error(f"set_user_active_tenant failed: {e}")
        return False
