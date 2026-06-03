# -*- coding: utf-8 -*-
"""成员/权限分配域 · 客户分配(老板分客户给员工)+ tenant 归属查询(数据访问层 · REFACTOR-WA)

从 services/membership/store.py 按域拆出客户分配半边(纯搬家 · 0 逻辑改)。
覆盖:get_visible_client_ids_for_user / list_assignments_by_employees /
set_employee_assignments / auto_assign_client_to_creator(全部按 tenant_id 隔离防越权)/
get_user_tenant_id(memberships 优先回退 users.tenant_id)。
游标走 db.get_cursor(...) · store.py 文件头 re-export 回 services.membership.store 命名空间。
"""

import logging
from typing import Optional

from core import db

logger = logging.getLogger(__name__)


def get_visible_client_ids_for_user(user: dict):
    """返回用户能看到的 client_id 列表
    - super_admin / owner → None(不限制 · SQL 不加 client filter)
    - member → List[int]:从 client_assignments 拿(空列表 = 没分到任何客户)
    返回 None 时调用方不加 client filter · 返回 list 时加 WHERE client_id IN (list)
    """
    if not user:
        return []
    if user.get("is_super_admin"):
        return None
    role = user.get("role") or "owner"
    if role == "owner":
        return None
    user_id = str(user.get("id") or "")
    if not user_id:
        return []
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT client_id FROM client_assignments WHERE user_id = %s", (user_id,))
            rows = cur.fetchall() or []
            return [int(r["client_id"] if isinstance(r, dict) else r[0]) for r in rows]
    except Exception as e:
        logger.error(f"get_visible_client_ids_for_user failed (user={user_id}): {e}")
        return []  # 出错时拒绝访问 · 不暴露


def list_assignments_by_employees(tenant_id: str):
    """老板用 · 拿同 tenant 内每个 member 的 assignments
    返回 {employee_user_id: [client_id, ...]}
    """
    out = {}
    if not tenant_id:
        return out
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT ca.user_id, ca.client_id
                FROM client_assignments ca
                JOIN users u ON u.id = ca.user_id
                WHERE u.tenant_id = %s
            """,
                (str(tenant_id),),
            )
            for r in cur.fetchall() or []:
                uid = str(r["user_id"] if isinstance(r, dict) else r[0])
                cid = int(r["client_id"] if isinstance(r, dict) else r[1])
                out.setdefault(uid, []).append(cid)
    except Exception as e:
        logger.error(f"list_assignments_by_employees failed: {e}")
    return out


def set_employee_assignments(
    employee_user_id: str, client_ids, assigned_by: str, tenant_id: str
) -> bool:
    """覆盖式设置员工的客户列表
    安全:校验员工和所有 client_id 都在 tenant_id 内 · 防跨租户
    """
    if not employee_user_id or not assigned_by or not tenant_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            # 校验员工属于本租户
            cur.execute(
                "SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(employee_user_id),)
            )
            row = cur.fetchone()
            if not row:
                return False
            row_tid = row["tenant_id"] if isinstance(row, dict) else row[0]
            if str(row_tid) != str(tenant_id):
                return False

            # 删现有所有
            cur.execute(
                "DELETE FROM client_assignments WHERE user_id = %s", (str(employee_user_id),)
            )

            # 校验要分配的 client_ids 都在本租户(防越权写)
            valid_ids = []
            if client_ids:
                int_ids = [int(c) for c in client_ids if c is not None]
                if int_ids:
                    cur.execute(
                        """
                        SELECT id FROM clients
                        WHERE id = ANY(%s::bigint[])
                          AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    """,
                        (int_ids, str(tenant_id)),
                    )
                    valid_ids = [
                        int(r["id"] if isinstance(r, dict) else r[0])
                        for r in (cur.fetchall() or [])
                    ]

            # 批插
            for cid in valid_ids:
                cur.execute(
                    """
                    INSERT INTO client_assignments (user_id, client_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, client_id) DO NOTHING
                """,
                    (str(employee_user_id), cid, str(assigned_by)),
                )
            return True
    except Exception as e:
        logger.error(f"set_employee_assignments failed: {e}")
        return False


def auto_assign_client_to_creator(creator_user_id: str, client_id: int) -> bool:
    """创建客户时 · 给创建者一个 assignment(让员工身份创建的能看自己建的)
    老板/超管不需要(他们不受 assignment 限制)· 但调用方简单起见统一调用 · 这里幂等 OK"""
    if not creator_user_id or not client_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO client_assignments (user_id, client_id, assigned_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, client_id) DO NOTHING
            """,
                (str(creator_user_id), int(client_id), str(creator_user_id)),
            )
        return True
    except Exception as e:
        logger.error(f"auto_assign_client_to_creator failed: {e}")
        return False


def get_user_tenant_id(user_id: str) -> Optional[str]:
    """v118.27.7 兼容层 · 优先读 memberships · 回退 users.tenant_id
    迁移过渡期老代码继续用 user.tenant_id · 新代码可以用本函数无缝过渡
    """
    if not user_id:
        return None
    try:
        with db.get_cursor() as cur:
            # 优先读 memberships(新模型)
            cur.execute(
                """
                SELECT tenant_id FROM memberships
                WHERE user_id = %s AND status = 'active'
                LIMIT 1
            """,
                (str(user_id),),
            )
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            # 回退 users.tenant_id(老字段 · 过渡期共存)
            cur.execute("SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            return None
    except Exception as e:
        logger.warning(f"get_user_tenant_id failed (user_id={user_id}): {e}")
        return None
