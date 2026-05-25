# -*- coding: utf-8 -*-
"""员工管理(老板自助 · users 表 role=member)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
老板给自家公司增删/启停员工 · 全部按 tenant_id 隔离 + role='member' 安全校验 ·
remove_employee 级联清理员工相关数据(ocr_history/erp_push_logs/line_*/user_settings)。
add_employee 复用 db.find_user_by_username(留在 db.py 的用户/认证 DAL)做用户名唯一校验。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import bcrypt as _bcrypt

import db

logger = logging.getLogger(__name__)


def list_employees(tenant_id: str) -> List[Dict[str, Any]]:
    """列某 tenant 下的员工(role=member)"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, role, is_active, last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s AND role = 'member'
                ORDER BY created_at ASC
            """,
                (str(tenant_id),),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_employees failed: {e}")
        return []


def add_employee(
    tenant_id: str,
    username: str,
    password: str,
    invited_by: Optional[str] = None,
) -> Optional[str]:
    """
    老板给自家公司加员工
    - 用户名全局唯一
    - tenant_id 必填
    - role 固定 = 'member'
    返回新员工 user_id · 失败返回 None
    """
    try:
        existing = db.find_user_by_username(username)
        if existing:
            return None

        pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

        # 取 tenant 的 company_name
        with db.get_cursor(commit=True) as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s", (str(tenant_id),))
            row = cur.fetchone()
            company_name = row["name"] if row else None

            cur.execute(
                """
                INSERT INTO users (
                    username, password_hash, plan, is_active, is_super_admin,
                    tenant_id, role, invited_by, company_name
                ) VALUES (%s, %s, 'credits', TRUE, FALSE, %s, 'member', %s, %s)
                RETURNING id
            """,
                (
                    username,
                    pw_hash,
                    str(tenant_id),
                    str(invited_by) if invited_by else None,
                    company_name,
                ),
            )
            return str(cur.fetchone()["id"])
    except Exception as e:
        logger.error(f"add_employee failed: {e}")
        return None


def remove_employee(tenant_id: str, employee_user_id: str) -> bool:
    """
    老板删员工
    安全校验:只删 tenant_id 匹配 + role=member 的 user
    """
    try:
        with db.get_cursor(commit=True) as cur:
            # 先看员工是否存在且属于该 tenant
            cur.execute(
                """
                SELECT id FROM users
                WHERE id = %s AND tenant_id = %s AND role = 'member'
                LIMIT 1
            """,
                (str(employee_user_id), str(tenant_id)),
            )
            if not cur.fetchone():
                return False

            # 级联删员工相关数据
            for sql in [
                "DELETE FROM ocr_history WHERE user_id = %s",
                "DELETE FROM erp_push_logs WHERE user_id = %s",
                "DELETE FROM line_bindings WHERE user_id = %s",
                "DELETE FROM line_binding_codes WHERE user_id = %s",
                "DELETE FROM user_settings WHERE user_id = %s",
            ]:
                try:
                    cur.execute(sql, (str(employee_user_id),))
                except Exception:
                    pass  # 表可能不存在 · 安全跳过

            cur.execute("DELETE FROM users WHERE id = %s", (str(employee_user_id),))
            return True
    except Exception as e:
        logger.error(f"remove_employee failed: {e}")
        return False


def toggle_employee_active(
    tenant_id: str,
    employee_user_id: str,
    is_active: bool,
) -> bool:
    """老板启用/停用员工"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET is_active = %s
                WHERE id = %s AND tenant_id = %s AND role = 'member'
            """,
                (bool(is_active), str(employee_user_id), str(tenant_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"toggle_employee_active failed: {e}")
        return False
