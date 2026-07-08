# -*- coding: utf-8 -*-
"""Google 外流凭据 / OAuth state / 归档幂等台账 DAL(按套账隔离 · 契约 05 §2.2)。

每句 WHERE tenant_id + workspace_client_id(凭据绝不跨套账串)。token base64 编解码
(token_version=1·P1 升 AES,同 erp_oauth_store)。调用方管事务(传 cur),便于单测。
"""

from __future__ import annotations

import base64


def _b64e(s: str) -> str:
    return base64.b64encode((s or "").encode("utf-8")).decode("ascii")


def _b64d(s: str) -> str:
    try:
        return base64.b64decode((s or "").encode("ascii")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return ""


# ── 凭据 ───────────────────────────────────────────────────────────────────
def upsert_credential(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    google_email,
    access_token,
    refresh_token,
    expires_at,
    scope,
    created_by=None,
) -> None:
    """存/覆盖该套账的 Google 凭据(同 tenant+ws 唯一)。token base64 落库。"""
    cur.execute(
        """
        INSERT INTO export_google_credentials
            (tenant_id, workspace_client_id, google_email, access_token, refresh_token,
             expires_at, scope, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET
            google_email = EXCLUDED.google_email,
            access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            expires_at = EXCLUDED.expires_at,
            scope = EXCLUDED.scope,
            token_version = export_google_credentials.token_version + 1,
            updated_at = now()
        """,
        (
            tenant_id,
            workspace_client_id,
            (google_email or "")[:320] or None,
            _b64e(access_token),
            _b64e(refresh_token),
            expires_at,
            (scope or "")[:1000] or None,
            created_by,
        ),
    )


def get_credential(cur, *, tenant_id, workspace_client_id):
    """取该套账凭据(token 解码为明文)。无 → None。"""
    cur.execute(
        "SELECT id, google_email, access_token, refresh_token, expires_at, scope, "
        "token_version, updated_at FROM export_google_credentials "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    out = dict(row)
    out["access_token"] = _b64d(out["access_token"])
    out["refresh_token"] = _b64d(out["refresh_token"])
    return out


def update_access_token(cur, *, tenant_id, workspace_client_id, access_token, expires_at) -> bool:
    """刷新后写回新 access_token + 过期(refresh_token 不变)。"""
    cur.execute(
        "UPDATE export_google_credentials SET access_token = %s, expires_at = %s, "
        "updated_at = now() WHERE tenant_id = %s AND workspace_client_id = %s",
        (_b64e(access_token), expires_at, tenant_id, workspace_client_id),
    )
    return cur.rowcount > 0


def delete_credential(cur, *, tenant_id, workspace_client_id) -> bool:
    """断开:删该套账凭据。"""
    cur.execute(
        "DELETE FROM export_google_credentials "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    return cur.rowcount > 0


# ── OAuth state(防 CSRF · 单次消费 · 5 分钟过期)─────────────────────────────
def save_state(
    cur, *, state, tenant_id, workspace_client_id, user_id, return_to="purchase-export"
) -> None:
    cur.execute("DELETE FROM export_oauth_states WHERE created_at < now() - interval '5 minutes'")
    cur.execute(
        "INSERT INTO export_oauth_states "
        "(state, tenant_id, workspace_client_id, user_id, return_to) "
        "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (state) DO UPDATE SET "
        "tenant_id = EXCLUDED.tenant_id, workspace_client_id = EXCLUDED.workspace_client_id, "
        "user_id = EXCLUDED.user_id, return_to = EXCLUDED.return_to, created_at = now()",
        (state, tenant_id, workspace_client_id, user_id, return_to),
    )


def consume_state(cur, *, state):
    """验证 + 单次消费(callback 用)。返回 {tenant_id,workspace_client_id,user_id,return_to} 或 None。"""
    cur.execute(
        "DELETE FROM export_oauth_states "
        "WHERE state = %s AND created_at >= now() - interval '5 minutes' "
        "RETURNING tenant_id, workspace_client_id, user_id, return_to",
        (state,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "tenant_id": str(row["tenant_id"]),
        "workspace_client_id": row["workspace_client_id"],
        "user_id": str(row["user_id"]),
        "return_to": row["return_to"] or "purchase-export",
    }


# ── 归档幂等台账(重跑只补未成功)──────────────────────────────────────────
def already_archived_ids(cur, *, tenant_id, workspace_client_id, doc_ids) -> set:
    """这批 doc_id 里已成功归档的集合(重跑跳过)。空入参 → 空集。"""
    if not doc_ids:
        return set()
    cur.execute(
        "SELECT doc_id FROM export_archived_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND doc_id = ANY(%s::uuid[])",
        (tenant_id, workspace_client_id, [str(d) for d in doc_ids]),
    )
    return {str(r["doc_id"]) for r in cur.fetchall()}


def mark_archived(
    cur, *, tenant_id, workspace_client_id, doc_id, drive_folder_id, drive_url, sheet_synced=True
) -> None:
    """登记某单已归档(幂等台账)。"""
    cur.execute(
        """
        INSERT INTO export_archived_docs
            (tenant_id, workspace_client_id, doc_id, drive_folder_id, drive_url, sheet_synced)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id, doc_id) DO UPDATE SET
            drive_folder_id = EXCLUDED.drive_folder_id,
            drive_url = EXCLUDED.drive_url,
            sheet_synced = EXCLUDED.sheet_synced,
            archived_at = now()
        """,
        (tenant_id, workspace_client_id, doc_id, drive_folder_id, drive_url, sheet_synced),
    )
