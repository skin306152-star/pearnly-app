# -*- coding: utf-8 -*-
"""
services/auth/password.py · 用户密码 verify / reset(REFACTOR-B2)

从 db.py 抽出的「auth · 密码」域,bcrypt 直跑(_bcrypt 私有 · 不外露)。
E2E 覆盖(spec 13 password-change · auth.py:139 token.iat<password_changed_at→401):
    verify_user_password — 二次验证用 · 改密 / 危险操作前需重新输密码场景
    reset_user_password  — 超管用 · 给指定用户重置密码 + 同步 password_changed_at=NOW()
                            → 已签发的旧 JWT 全部失效(铁律 v118.28.9)。

范式(ADR-007):import db + 运行时 `db.get_cursor()`,db.py 文件尾 re-export,
所有 `db.verify_user_password / db.reset_user_password` 调用点零改动。
"""

from __future__ import annotations

import logging

import bcrypt as _bcrypt

from core import db

logger = logging.getLogger(__name__)


def verify_user_password(user_id: str, password: str) -> bool:
    """二次验证用 · 返回密码是否匹配"""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return False
            return _bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
    except Exception as e:
        logger.error(f"verify_user_password failed: {e}")
        return False


def reset_user_password(user_id: str, new_password: str) -> bool:
    """超管用 · 给指定用户重置密码(同步刷新 password_changed_at · 旧 JWT 全失效)"""
    try:
        pw_hash = _bcrypt.hashpw(new_password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (pw_hash, str(user_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"reset_user_password failed: {e}")
        return False
