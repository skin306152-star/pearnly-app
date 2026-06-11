# -*- coding: utf-8 -*-
"""
services/auth/user_lookup.py · 用户查找 + OAuth 关联(REFACTOR-B2)

从 db.py 抽出的「auth · 用户查询/链接」域,纯 SELECT/UPDATE,
覆盖入口(spec E2E):
    find_user_by_username  → spec 01 登录
    find_user_by_id        → 所有 authed 路径(auth.get_current_user_from_request 间接)
    find_user_by_google_sub / link_google_sub_to_user → Google OAuth(handler 调用)
    find_user_by_line_uid  / link_line_uid_to_user    → LINE Login(spec 14 LINE binding 间接)
    update_user_avatar     → Google OAuth picture 写入

范式(ADR-007):import db + 运行时 `db.get_cursor()` —— 让单测 mock `db.get_cursor` 仍生效,
db.py 文件尾 `from services.auth.user_lookup import X as X` 显式 re-export,
所有 `db.find_user_by_*` / `from db import ...` 调用点零改动。
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Dict, Any

from core import db

logger = logging.getLogger(__name__)

# 鉴权热路径专用 TTL 缓存。首屏一次性打 ~22 个请求,每个鉴权依赖各跑 1 条同一
# find_user_by_id(同一行)→ 跨区 ~69ms ×22。缓存后每 worker 仅首条查 DB,后续命中。
# 仅 get_current_user_from_request 用;其他读路径仍走实时 find_user_by_id(避免 read-after-write 陈旧)。
# 代价:封禁/改密/权限变更 ≤TTL 秒延迟生效(可接受)。jti 轮换(登录/换设备)由鉴权侧
# "jti 不匹配则强制 fresh 重取" 收口——新令牌绝不被旧缓存误拒;create_access_token 另主动 evict 本进程。
_USER_CACHE: Dict[str, tuple] = {}
_USER_CACHE_TTL = 8.0


def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
            row = cur.fetchone()
            if not row and "@" in username:
                # 邮箱登录回退:用户名不含 @(注册校验保证),故 @ 必为邮箱 → 零歧义按 email 查
                cur.execute(
                    "SELECT * FROM users WHERE lower(email) = lower(%s) LIMIT 1", (username,)
                )
                row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 ({username}): {e}")
        return None


def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (id={user_id}): {e}")
        return None


def find_user_by_id_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """鉴权热路径专用:TTL 缓存的 find_user_by_id(降首屏重复同一查)。

    返回**副本**——调用方(get_current_user_from_request)会改写 tenant_id 等键,不可污染缓存。
    """
    key = str(user_id)
    ent = _USER_CACHE.get(key)
    now = time.monotonic()
    if ent and ent[0] > now:
        return dict(ent[1])
    # 经 db.* 调(re-export 同一函数),保持既有 mock 口径(测试 patch core.db.find_user_by_id)。
    row = db.find_user_by_id(user_id)
    if row is not None:
        _USER_CACHE[key] = (now + _USER_CACHE_TTL, dict(row))
    return row


def evict_user_cache(user_id) -> None:
    """清掉某用户的鉴权缓存(令牌轮换/改密/封禁后调,使变更即时生效本进程)。"""
    _USER_CACHE.pop(str(user_id), None)


# ============================================================
# v118.27.5 · Google OAuth 关联(google_sub = Google 用户唯一 ID)
# ============================================================
def find_user_by_google_sub(google_sub: str) -> Optional[Dict[str, Any]]:
    if not google_sub:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE google_sub = %s LIMIT 1", (google_sub,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (google_sub={google_sub}): {e}")
        return None


def link_google_sub_to_user(user_id: str, google_sub: str) -> bool:
    if not user_id or not google_sub:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET google_sub = %s WHERE id = %s", (google_sub, user_id))
        return True
    except Exception as e:
        logger.error(f"绑定 google_sub 失败 (user_id={user_id}): {e}")
        return False


def update_user_avatar(user_id: str, avatar_url: str) -> bool:
    if not user_id or not avatar_url:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
        return True
    except Exception as e:
        logger.error(f"更新 avatar_url 失败 (user_id={user_id}): {e}")
        return False


# ============================================================
# v118.28.4 · LINE Login OAuth 关联(line_uid = LINE user ID · sub claim)
# ============================================================
def find_user_by_line_uid(line_uid: str) -> Optional[Dict[str, Any]]:
    if not line_uid:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE line_uid = %s LIMIT 1", (line_uid,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询用户失败 (line_uid={line_uid}): {e}")
        return None


def link_line_uid_to_user(user_id: str, line_uid: str) -> bool:
    if not user_id or not line_uid:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET line_uid = %s WHERE id = %s", (line_uid, user_id))
        return True
    except Exception as e:
        logger.error(f"绑定 line_uid 失败 (user_id={user_id}): {e}")
        return False
