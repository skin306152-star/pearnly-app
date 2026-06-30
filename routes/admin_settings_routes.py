# -*- coding: utf-8 -*-
"""平台全局设置(钥匙闸)超管路由(WP2)。

超管在平台后台「全局设置」开 / 关对话 Agent 总闸 + 维护灰度名单。全部 _require_super_admin
守门(平台层 · 非超管 403)。设置读写经 services/platform_settings/store · 安全阀默认关。

覆盖:
  GET  /api/admin/platform-settings                   · 读 agent_enabled 总闸 + 灰度名单(附用户名)
  POST /api/admin/platform-settings                   · 设总闸 enabled + rollout(allowlist/all)
  POST /api/admin/platform-settings/allowlist/add     · 加灰度用户
  POST /api/admin/platform-settings/allowlist/remove  · 移除灰度用户
"""

from __future__ import annotations

import logging
import uuid as _uuid

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.feature_flags import AGENT_ENABLED_KEY
from core.route_helpers import _require_super_admin
from services.platform_settings import store

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_ROLLOUTS = ("allowlist", "all")


def _resolve_user_id(raw: str) -> str:
    """把超管输入解析成真实 user_id:支持填邮箱(没人记 UUID)→ 查 users 表换 id。
    空 / 查不到 / 非法 UUID → 400/404 友好报错,绝不让坏值插进 UUID 列触发 500。"""
    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(400, detail="platform_settings.missing_user_id")
    if "@" in raw:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id::text AS id FROM users WHERE lower(email) = lower(%s) LIMIT 1",
                (raw,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail="platform_settings.user_email_not_found")
        return row["id"]
    try:
        return str(_uuid.UUID(raw))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(400, detail="platform_settings.bad_user_id")


def _enrich_users(user_ids: list[str]) -> list[dict]:
    """把 allowlist 的 user_id 配上用户名/邮箱(展示用 · 删号也不报错)。"""
    if not user_ids:
        return []
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id::text AS id, username, email FROM users WHERE id::text = ANY(%s)",
                (list(user_ids),),
            )
            by_id = {r["id"]: r for r in cur.fetchall()}
    except Exception as e:
        logger.warning(f"_enrich_users skip: {e}")
        by_id = {}
    out = []
    for uid in user_ids:
        r = by_id.get(uid) or {}
        out.append(
            {"user_id": uid, "username": r.get("username") or "", "email": r.get("email") or ""}
        )
    return out


@router.get("/api/admin/platform-settings")
async def get_platform_settings(request: Request):
    """读 agent_enabled 总闸 + 灰度策略 + 名单。无记录 → 默认关 / allowlist。"""
    _require_super_admin(request)
    row = store.get_setting(AGENT_ENABLED_KEY)
    value = (row or {}).get("value") or {}
    rollout = value.get("rollout") if isinstance(value, dict) else None
    return {
        "agent_enabled": {
            "enabled": bool(row and row.get("enabled")),
            "rollout": rollout or "allowlist",
            "updated_at": row["updated_at"].isoformat() if row and row.get("updated_at") else None,
        },
        "allowlist": _enrich_users(store.list_allowlist(AGENT_ENABLED_KEY)),
    }


@router.post("/api/admin/platform-settings")
async def set_platform_settings(request: Request):
    """设总闸 + 灰度策略。body: {enabled: bool, rollout: 'allowlist'|'all'}。"""
    user = _require_super_admin(request)
    body = await request.json()
    enabled = bool(body.get("enabled"))
    rollout = body.get("rollout") or "allowlist"
    if rollout not in _ROLLOUTS:
        raise HTTPException(400, detail="platform_settings.bad_rollout")
    store.set_setting(AGENT_ENABLED_KEY, {"rollout": rollout}, enabled, by=str(user["id"]))
    return {"ok": True}


@router.post("/api/admin/platform-settings/allowlist/add")
async def add_allowlist_user(request: Request):
    """加灰度用户。body: {user_id}(可填邮箱或 UUID)。"""
    _require_super_admin(request)
    body = await request.json()
    user_id = _resolve_user_id(body.get("user_id") or "")
    store.add_to_allowlist(AGENT_ENABLED_KEY, user_id)
    return {"ok": True, "allowlist": _enrich_users(store.list_allowlist(AGENT_ENABLED_KEY))}


@router.post("/api/admin/platform-settings/allowlist/remove")
async def remove_allowlist_user(request: Request):
    """移除灰度用户。body: {user_id}(可填邮箱或 UUID)。"""
    _require_super_admin(request)
    body = await request.json()
    user_id = _resolve_user_id(body.get("user_id") or "")
    store.remove_from_allowlist(AGENT_ENABLED_KEY, user_id)
    return {"ok": True, "allowlist": _enrich_users(store.list_allowlist(AGENT_ENABLED_KEY))}
