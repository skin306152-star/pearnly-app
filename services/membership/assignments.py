# -*- coding: utf-8 -*-
"""成员访问范围与 tenant 归属查询。

保留只读的历史客户范围约束,避免旧成员在权限管理功能下线后扩大数据可见面。
get_user_tenant_id 供 ERP 推送链定位租户使用。
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
