# -*- coding: utf-8 -*-
"""LINE Bot 绑定 / 绑定码 CRUD(line_bindings · line_binding_codes 表)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
覆盖:生成/消费绑定码 · 绑定/换绑(冲突拒绝)· 查绑定 · LINE→user 反查(更新活跃时间)· 解绑。
游标走 db.get_cursor(...)·确保测试 mock.patch("core.db.get_cursor") 仍生效。
db.py 文件尾 re-export 回本命名空间(所有 db.xxx() 调用点不变 · app/line_binding_routes/
notification_routes/exception_checks 均走 db.*)。
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from core import db

logger = logging.getLogger(__name__)


def generate_line_binding_code(user_id: str, ttl_minutes: int = 10) -> Optional[Dict[str, Any]]:
    """
    为用户生成 6 位数字绑定码 · 10 分钟有效 · 重复生成会覆盖旧码。
    返回 {"code": "123456", "expires_at": "..."} 或 None
    """
    try:
        # 6 位随机数字码(避免 0 开头在 LINE 里看起来像字母)
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

        with db.get_cursor(commit=True) as cur:
            # 先把该用户之前未使用的码作废(只保留最新一个)
            cur.execute(
                """
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE user_id = %s
                   AND used_at IS NULL
            """,
                (str(user_id),),
            )

            # 插入新码
            cur.execute(
                """
                INSERT INTO line_binding_codes (code, user_id, expires_at)
                VALUES (%s, %s, %s)
                RETURNING code, expires_at
            """,
                (code, str(user_id), expires_at),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "code": row["code"],
                "expires_at": row["expires_at"].isoformat(),
            }
    except Exception as e:
        logger.error(f"generate_line_binding_code failed: {e}")
        return None


def consume_line_binding_code(code: str) -> Optional[str]:
    """
    验证绑定码 · 合法则标记为已用 · 返回对应 user_id。
    不合法(不存在 / 已用 / 已过期)返回 None。
    T1 轮 2 webhook 收到 LINE 文字消息时调用。
    """
    try:
        code = (code or "").strip()
        if not code or len(code) != 6 or not code.isdigit():
            return None
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE line_binding_codes
                   SET used_at = NOW()
                 WHERE code = %s
                   AND used_at IS NULL
                   AND expires_at > NOW()
                RETURNING user_id
            """,
                (code,),
            )
            row = cur.fetchone()
            return str(row["user_id"]) if row else None
    except Exception as e:
        logger.error(f"consume_line_binding_code failed: {e}")
        return None


def create_or_update_line_binding(
    user_id: str,
    line_user_id: str,
    display_name: Optional[str] = None,
    picture_url: Optional[str] = None,
) -> bool:
    """
    绑定 mrpilot user ↔ LINE user。
    一个 mrpilot user 只能绑一个 LINE 账号(UNIQUE user_id)
    一个 LINE 账号只能绑一个 mrpilot user(UNIQUE line_user_id)
    重复绑同一对会更新昵称/头像。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            # 检查冲突:该 LINE 账号是否已绑到别的 mrpilot user
            cur.execute(
                """
                SELECT user_id FROM line_bindings
                 WHERE line_user_id = %s
                 LIMIT 1
            """,
                (line_user_id,),
            )
            row = cur.fetchone()
            if row and str(row["user_id"]) != str(user_id):
                logger.warning(
                    f"LINE {line_user_id} 已绑到 user {row['user_id']} · "
                    f"拒绝绑到 user {user_id}"
                )
                return False

            # 先清空该 mrpilot user 已有的其他 LINE 绑定(换绑场景)
            cur.execute(
                """
                DELETE FROM line_bindings
                 WHERE user_id = %s
                   AND line_user_id != %s
            """,
                (str(user_id), line_user_id),
            )

            # upsert
            cur.execute(
                """
                INSERT INTO line_bindings
                    (user_id, line_user_id, line_display_name, line_picture_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (line_user_id) DO UPDATE SET
                    user_id            = EXCLUDED.user_id,
                    line_display_name  = EXCLUDED.line_display_name,
                    line_picture_url   = EXCLUDED.line_picture_url,
                    last_active_at     = NOW()
            """,
                (str(user_id), line_user_id, display_name, picture_url),
            )
            return True
    except Exception as e:
        logger.error(f"create_or_update_line_binding failed: {e}")
        return False


def get_line_binding_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    """查某 mrpilot 用户当前的 LINE 绑定信息"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT line_user_id, line_display_name, line_picture_url,
                       bound_at, last_active_at
                  FROM line_bindings
                 WHERE user_id = %s
                 LIMIT 1
            """,
                (str(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_line_binding_by_user failed: {e}")
        return None


def get_user_by_line_user_id(line_user_id: str) -> Optional[Dict[str, Any]]:
    """
    给定 LINE user_id · 查对应的 mrpilot 用户(含权限字段)。
    T1 轮 2 webhook 收到 LINE 消息 · 用这个反查。
    同时更新 last_active_at。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            # 更新活跃时间
            cur.execute(
                """
                UPDATE line_bindings SET last_active_at = NOW()
                 WHERE line_user_id = %s
                RETURNING user_id
            """,
                (line_user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            user_id = str(row["user_id"])

            # 查 mrpilot 用户(带上 line_user_id·users 表本身无此列·postback 处理器要用它)
            cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
            urow = cur.fetchone()
            if not urow:
                return None
            user = dict(urow)
            user["line_user_id"] = line_user_id
            return user
    except Exception as e:
        logger.error(f"get_user_by_line_user_id failed: {e}")
        return None


def unbind_line_by_user(user_id: str) -> bool:
    """用户主动解绑 LINE"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM line_bindings WHERE user_id = %s
            """,
                (str(user_id),),
            )
            return True
    except Exception as e:
        logger.error(f"unbind_line_by_user failed: {e}")
        return False


def unbind_line_by_line_user_id(line_user_id: str) -> bool:
    """删 Bot 好友(unfollow)时清理绑定。返回是否真的删到一行。"""
    if not line_user_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM line_bindings WHERE line_user_id = %s",
                (line_user_id,),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"unbind_line_by_line_user_id failed: {e}")
        return False


def ensure_line_binding_rls() -> None:
    """B8 RLS:给 line_bindings/line_binding_codes 上 policy(幂等 · 独立事务防牵连别的 ensure)。

    两表只有 user_id 列(无 tenant_id·INCIDENT §2 误归 tenant_or_user)→ 纯 user 隔离。
    legacy 表无 CREATE 钩子,故独立 ensure_*_rls(对齐 ensure_email_ingest_rls 范式)。
    force=False:本表全部访问是 owner(LINE webhook 无登录态·靠 line_user_id 反查·穿不进 user 上下文)
    → owner 绕过,store 全裸 get_cursor 不破;policy 仅作第二道防线。逐表先验存在防部分库整块失败。
    """
    from core.rls import apply_user_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_user_rls(cur, *existing_tables(cur, ("line_bindings", "line_binding_codes")))
    except Exception as e:
        logger.warning(f"ensure_line_binding_rls skipped: {e}")


def ensure_line_binding_columns() -> None:
    """LINE 会话态「当前套账」列(幂等 · IF NOT EXISTS)。legacy 表无 CREATE 钩子,启动时补。"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "ALTER TABLE line_bindings "
                "ADD COLUMN IF NOT EXISTS current_workspace_client_id BIGINT"
            )
    except Exception as e:
        logger.warning(f"ensure_line_binding_columns skipped: {e}")
