# -*- coding: utf-8 -*-
"""平台全局设置读写(钥匙闸)· 超管开关 + allowlist 灰度(WP2)。

策略(单一来源):
- platform_settings.enabled  = 总闸:关 → 任何人都关。
- value.rollout              = "all"(全开)/ "allowlist"(默认 · 仅名单内开)。
- is_enabled_for_user        = 总闸关→False;rollout=all→True;否则查 allowlist。

钥匙闸是安全阀:所有读默认收口到「关」—— 无记录 / value 坏 / 查询异常一律返 False,
绝不因为基建抖动误把 Agent 放出来。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from core import db

logger = logging.getLogger(__name__)


# 闸设置在 LINE webhook 热路径上每消息读 2-4 次;闸只由超管手动翻,秒级陈旧无害 →
# 进程内 30s TTL 缓存把每消息 SELECT 清零。set_setting 失效本进程;多 worker 最迟 30s 收敛。
_CACHE_TTL_S = 30
_cache: dict[str, tuple[float, Optional[dict]]] = {}


def get_setting(key: str) -> Optional[dict]:
    """读一条设置;不存在返 None(30s 进程缓存)。value 为 psycopg2 已解析的 dict(jsonb)。"""
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_TTL_S:
        return hit[1]
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT key, value, enabled, updated_at, updated_by "
            "FROM platform_settings WHERE key = %s",
            (key,),
        )
        row = cur.fetchone()
    out = dict(row) if row else None
    _cache[key] = (time.monotonic(), out)
    return out


def set_setting(key: str, value: Any, enabled: bool, by: Optional[str] = None) -> None:
    """upsert 一条设置(总闸 + 灰度策略)。by = 操作超管 user_id(审计)。"""
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO platform_settings (key, value, enabled, updated_at, updated_by)
               VALUES (%s, %s::jsonb, %s, NOW(), %s)
               ON CONFLICT (key) DO UPDATE
                 SET value = EXCLUDED.value,
                     enabled = EXCLUDED.enabled,
                     updated_at = NOW(),
                     updated_by = EXCLUDED.updated_by""",
            (key, json.dumps(value or {}), bool(enabled), str(by) if by else None),
        )
    _cache.pop(key, None)


def list_allowlist(key: str) -> list[str]:
    """返回某设置 allowlist 内的 user_id(str)列表。"""
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT user_id::text AS user_id FROM platform_setting_allowlist "
            "WHERE setting_key = %s ORDER BY created_at",
            (key,),
        )
        return [r["user_id"] for r in cur.fetchall()]


def is_allowlisted(key: str, subject_id: str) -> bool:
    """单主体名单点查(索引级)。跟 is_enabled_for_user 不同:不折总闸/rollout,
    纯问「在不在名单」——发放侧(邀请管理)要的是名单事实,不是灰度判定结果。"""
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM platform_setting_allowlist "
            "WHERE setting_key = %s AND user_id = %s LIMIT 1",
            (key, str(subject_id)),
        )
        return cur.fetchone() is not None


def add_to_allowlist(key: str, user_id: str) -> None:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO platform_setting_allowlist (setting_key, user_id) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (key, str(user_id)),
        )


def remove_from_allowlist(key: str, user_id: str) -> None:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM platform_setting_allowlist WHERE setting_key = %s AND user_id = %s",
            (key, str(user_id)),
        )


def _rollout(value: Any) -> str:
    """从 value(dict 或 json 串)取灰度策略 · 缺省 allowlist。"""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return "allowlist"
    if isinstance(value, dict):
        return value.get("rollout") or "allowlist"
    return "allowlist"


def is_enabled_for_user(key: str, user_id: Optional[str]) -> bool:
    """钥匙闸判定(fail-closed):总闸关→False;rollout=all→True;否则名单内才 True。"""
    try:
        row = get_setting(key)
        if not row or not row.get("enabled"):
            return False
        if _rollout(row.get("value")) == "all":
            return True
        if not user_id:
            return False
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM platform_setting_allowlist "
                "WHERE setting_key = %s AND user_id = %s",
                (key, str(user_id)),
            )
            return cur.fetchone() is not None
    except Exception as e:
        logger.warning(f"is_enabled_for_user({key}) fail-closed: {e}")
        return False
