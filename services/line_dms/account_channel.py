# -*- coding: utf-8 -*-
"""Which DMS LINE OA a DMS account (tenant-first subject) is bound to.

The Earn invite page picks one of the registered OAs per DMS account. That choice is stored here
keyed by the same ``subject_id`` the invite allowlist uses (``tenant_id`` for team accounts,
``user_id`` for personal ones), so old rows / callers that never set one resolve to the legacy
``dms`` OA.

Changing the OA is a deliberate, auditable operation: pending bind codes are voided and every
existing LINE binding under the account is dropped, so a stale code or an old binding can never
keep replying through the previous OA. The new OA requires a fresh bind code.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from services.line_dms.schema import _with_heal
from services.line_platform import channels

logger = logging.getLogger(__name__)


def subject_for(tenant_id: Optional[str], user_id: Optional[str]) -> str:
    """Tenant-first subject, identical to the invite allowlist判据 (tenant → user fallback)."""
    return str(tenant_id) if tenant_id else str(user_id or "")


def get_channel(subject_id: Optional[str]) -> str:
    """Assigned OA key for an account; unknown / unset → legacy default ``dms``."""
    sid = str(subject_id or "").strip()
    if not sid:
        return channels.DEFAULT_DMS_CHANNEL

    def _run():
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                "SELECT channel_key FROM dms_account_line_channels WHERE subject_id = %s",
                (sid,),
            )
            return cur.fetchone()

    try:
        row = _with_heal(_run)
    except Exception as e:
        logger.error(f"[dms_account_channel] get failed: {e}")
        return channels.DEFAULT_DMS_CHANNEL
    if not row:
        return channels.DEFAULT_DMS_CHANNEL
    return channels.normalize(row.get("channel_key"))


def get_channels(subject_ids: Iterable[str]) -> Dict[str, str]:
    """Bulk lookup for list views; missing subjects are simply absent from the map."""
    ids = [str(s) for s in subject_ids if s]
    if not ids:
        return {}

    def _run():
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                "SELECT subject_id, channel_key FROM dms_account_line_channels "
                "WHERE subject_id = ANY(%s)",
                (ids,),
            )
            return [dict(r) for r in cur.fetchall()]

    try:
        rows = _with_heal(_run)
    except Exception as e:
        logger.error(f"[dms_account_channel] get_channels failed: {e}")
        return {}
    return {r["subject_id"]: channels.normalize(r["channel_key"]) for r in rows}


def _affected_user_ids(subject_id: str) -> List[str]:
    """Users that belong to the account: all tenant members, or the single user itself."""
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT owner_user_id::text AS owner_user_id FROM tenants WHERE id::text = %s",
            (subject_id,),
        )
        row = cur.fetchone()
        if row and row.get("owner_user_id"):
            cur.execute(
                "SELECT id::text AS id FROM users WHERE tenant_id::text = %s", (subject_id,)
            )
            return [r["id"] for r in cur.fetchall()]
    return [subject_id]


def set_channel(subject_id: str, channel_key: str, *, actor_id: Optional[str] = None) -> dict:
    """Assign an OA to an account. Returns ``{"error": code}`` or a result dict.

    When the key actually changes, existing bindings and pending codes for every user under the
    account are revoked first (``unbound`` / ``codes_voided``), so no old binding keeps answering
    on the previous OA. Re-setting the same key is a no-op and never unbinds anyone.
    """
    from services.line_dms import store as line_dms_store

    sid = str(subject_id or "").strip()
    key = (channel_key or "").strip()
    if not sid:
        return {"error": "dms_channel.missing_subject"}
    if not channels.is_valid(key):
        return {"error": "dms_channel.invalid_channel"}

    previous = get_channel(sid)
    if previous == key:
        return {"ok": True, "channel_key": key, "changed": False, "unbound": 0, "codes_voided": 0}

    user_ids = _affected_user_ids(sid)
    unbound = 0
    codes_voided = 0
    for user_id in user_ids:
        if line_dms_store.unbind_by_user(user_id):
            unbound += 1
        if line_dms_store.void_bind_codes_for_user(user_id):
            codes_voided += 1

    def _run():
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO dms_account_line_channels (subject_id, channel_key, updated_at, updated_by) "
                "VALUES (%s, %s, now(), %s) "
                "ON CONFLICT (subject_id) DO UPDATE SET "
                "  channel_key = EXCLUDED.channel_key, updated_at = now(), "
                "  updated_by = EXCLUDED.updated_by",
                (sid, key, str(actor_id) if actor_id else None),
            )

    try:
        _with_heal(_run)
    except Exception as e:
        logger.error(f"[dms_account_channel] set failed: {e}")
        return {"error": "dms_channel.save_failed"}

    logger.info(
        "[dms_account_channel] subject=%s %s→%s unbound=%d codes_voided=%d",
        sid,
        previous,
        key,
        unbound,
        codes_voided,
    )
    return {
        "ok": True,
        "channel_key": key,
        "changed": True,
        "unbound": unbound,
        "codes_voided": codes_voided,
    }
