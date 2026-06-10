# -*- coding: utf-8 -*-
"""所有权转移流(docs/permissions/01 · QBO+Square 杂交最严做法)。

仅现任 owner 发起;接收方必须已是本租户 admin;24h 确认 token(只存哈希);
完成 = 同事务旧 owner 降 admin + 新 owner 升 owner + users.role 双写。不可逆。
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any, Dict

from core import db
from services.authz.resolver import set_membership_role

logger = logging.getLogger("mr-pilot")

TRANSFER_TTL_HOURS = 24


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def initiate(*, tenant_id: str, from_user_id: str, to_user_id: str) -> Dict[str, Any]:
    """发起转移。返回 {ok, token, expires_at} 或 {error}。"""
    if str(from_user_id) == str(to_user_id):
        return {"error": "transfer.self"}
    from services.team.console_store import get_member

    target = get_member(tenant_id, to_user_id)
    if target is None:
        return {"error": "team.member_not_found"}
    if target["role_key"] != "admin":
        return {"error": "transfer.target_not_admin"}
    token = secrets.token_urlsafe(32)
    with db.get_cursor(commit=True) as cur:
        # 同租户旧 pending 作废(一次只跑一单转移)
        cur.execute(
            "UPDATE ownership_transfers SET cancelled_at = NOW() "
            "WHERE tenant_id = %s AND completed_at IS NULL AND cancelled_at IS NULL",
            (str(tenant_id),),
        )
        cur.execute(
            """
            INSERT INTO ownership_transfers (tenant_id, from_user_id, to_user_id, token_hash,
                                             expires_at)
            VALUES (%s, %s, %s, %s, NOW() + %s * INTERVAL '1 hour')
            RETURNING id, expires_at
            """,
            (str(tenant_id), str(from_user_id), str(to_user_id), _hash(token), TRANSFER_TTL_HOURS),
        )
        row = cur.fetchone()
    return {
        "ok": True,
        "id": str(row["id"]),
        "token": token,
        "to_username": target.get("username"),
        "expires_at": row["expires_at"].isoformat(),
    }


def accept(*, token: str, acting_user_id: str) -> Dict[str, Any]:
    """接收方确认:同事务换角色。返回 {ok, tenant_id, from_user_id} 或 {error}。"""
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            SELECT * FROM ownership_transfers
            WHERE token_hash = %s AND completed_at IS NULL AND cancelled_at IS NULL
            """,
            (_hash(token),),
        )
        row = cur.fetchone()
        if row is None:
            return {"error": "transfer.invalid"}
        cur.execute("SELECT NOW() > %s AS expired", (row["expires_at"],))
        if bool(cur.fetchone()["expired"]):
            return {"error": "transfer.expired"}
        if str(row["to_user_id"]) != str(acting_user_id):
            return {"error": "transfer.wrong_user"}
        tenant_id = str(row["tenant_id"])
        ok_new = set_membership_role(
            cur,
            user_id=str(row["to_user_id"]),
            tenant_id=tenant_id,
            role_key="owner",
            granted_by=str(row["from_user_id"]),
        )
        ok_old = set_membership_role(
            cur,
            user_id=str(row["from_user_id"]),
            tenant_id=tenant_id,
            role_key="admin",
            granted_by=str(row["to_user_id"]),
        )
        if not (ok_new and ok_old):
            raise RuntimeError("ownership transfer membership update failed")
        cur.execute(
            "UPDATE ownership_transfers SET completed_at = NOW() WHERE id = %s",
            (str(row["id"]),),
        )
    return {"ok": True, "tenant_id": tenant_id, "from_user_id": str(row["from_user_id"])}
