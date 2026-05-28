# -*- coding: utf-8 -*-
"""
services/auth/account_merge.py · LINE 临时账号补邮箱 / 合并老账号(REFACTOR-B2)

LINE OAuth 注册流程:首次扫码 → 给用户建 `line_xxx@line.local` 临时占位账号 → 后续
强制补邮箱(home.js line-email-modal)→ 这一刻:
  - 若新邮箱**未注册** → 直接 update username/email/email_normalized = 新邮箱
  - 若新邮箱**已绑定老账号** → 把 line_uid 从临时账号转移到老账号 + 删临时账号
                                  (临时账号刚建 · 0 业务数据 · 直接删干净)

E2E 覆盖(间接):spec 01 登录 + spec 14 LINE 绑定。
范式(ADR-007):import db + 运行时 db.get_cursor()。
"""

from __future__ import annotations

import logging

import db

logger = logging.getLogger(__name__)


def is_line_placeholder_username(username: str) -> bool:
    """判断是否是 line_xxx@line.local 临时占位"""
    return bool(username and username.startswith("line_") and username.endswith("@line.local"))


def update_user_email_and_username(user_id: str, new_email: str) -> bool:
    """LINE 临时账号填完真邮箱后 · 把 username/email/email_normalized 都更新成真邮箱"""
    if not user_id or not new_email:
        return False
    try:
        from auth_signup import normalize_email as _norm_email
    except Exception:
        _norm_email = lambda x: (x or "").strip().lower()
    new_email_clean = (new_email or "").strip().lower()
    new_email_norm = _norm_email(new_email_clean)
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET username = %s, email = %s, email_normalized = %s
                WHERE id = %s
            """,
                (new_email_clean, new_email_clean, new_email_norm, user_id),
            )
        return True
    except Exception as e:
        logger.error(f"更新 email/username 失败 (user_id={user_id}): {e}")
        return False


def merge_line_account_into_existing(temp_user_id: str, target_user_id: str, line_uid: str) -> bool:
    """LINE 补邮箱发现该 email 已绑定老账号 · 把 line_uid 转移到老账号 + 删临时账号
    注意:临时账号只是刚创建的 · 没有发票/客户/任何业务数据 · 直接删
    """
    if not temp_user_id or not target_user_id or not line_uid:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            # 1) 先从临时账号摘掉 line_uid(防 unique 冲突)
            cur.execute("UPDATE users SET line_uid = NULL WHERE id = %s", (temp_user_id,))
            # 2) 绑到老账号
            cur.execute("UPDATE users SET line_uid = %s WHERE id = %s", (line_uid, target_user_id))
            # 3) 删临时账号的示例 client(create_user_via_line_oauth 建的 1 个)
            cur.execute("DELETE FROM clients WHERE user_id = %s", (temp_user_id,))
            # 4) 删订阅日志
            try:
                cur.execute("DELETE FROM subscription_log WHERE user_id = %s", (temp_user_id,))
            except Exception:
                pass  # 表可能不存在 · 安全跳过
            # 5) 删临时账号
            cur.execute("DELETE FROM users WHERE id = %s", (temp_user_id,))
        logger.info(
            f"[v118.28.4.1] merged line_uid={line_uid} from temp={temp_user_id} → target={target_user_id}"
        )
        return True
    except Exception as e:
        logger.error(f"合并 LINE 账号失败 (temp={temp_user_id} → target={target_user_id}): {e}")
        return False
