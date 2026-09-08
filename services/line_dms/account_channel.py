# -*- coding: utf-8 -*-
"""Which DMS LINE OA a DMS account (tenant-first subject) is bound to.

The Earn invite page picks one of the registered OAs per DMS account. That choice is stored here
keyed by the same ``subject_id`` the invite allowlist uses (``tenant_id`` for team accounts,
``user_id`` for personal ones), so old rows / callers that never set one resolve to the legacy
``dms`` OA.

Changing the OA is a deliberate, auditable operation: pending bind codes are voided and every
existing LINE binding under the account is dropped, so a stale code or an old binding can never
keep replying through the previous OA. The new OA requires a fresh bind code.

Reads fail closed: a missing row is the legacy default, but a database error or an unknown stored
key raises :class:`AccountChannelError` instead of silently falling back to the legacy OA. The
change itself is one transaction under a per-account advisory lock shared with bind-code issuance
and binding writes, so a code minted before the change can never restore the previous OA.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from services.line_dms.schema import _with_heal
from services.line_platform import channels

logger = logging.getLogger(__name__)


class AccountChannelError(RuntimeError):
    """Account OA assignment could not be read safely; callers must fail closed."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def subject_for(tenant_id: Optional[str], user_id: Optional[str]) -> str:
    """Tenant-first subject, identical to the invite allowlist判据 (tenant → user fallback)."""
    return str(tenant_id) if tenant_id else str(user_id or "")


def _lock_key(subject_id: str) -> str:
    return "dms-account-channel:" + str(subject_id)


def lock_account(cur, subject_id: str) -> None:
    """Serialize code issuance / binding writes / OA changes for one account.

    Callers must take this lock before any per-user or per-LINE lock so lock order stays
    account → user → line and cannot deadlock against another writer.
    """
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        (_lock_key(str(subject_id)),),
    )


def read_channel(cur, subject_id: Optional[str]) -> str:
    """Read the assignment on an existing cursor.

    Missing subject / missing row → legacy default. Unknown non-empty stored value raises so a
    corrupted assignment can never silently send an account back to the legacy OA.
    """
    sid = str(subject_id or "").strip()
    if not sid:
        return channels.DEFAULT_DMS_CHANNEL
    cur.execute(
        "SELECT channel_key FROM dms_account_line_channels WHERE subject_id = %s",
        (sid,),
    )
    row = cur.fetchone()
    if not row:
        return channels.DEFAULT_DMS_CHANNEL
    value = (row.get("channel_key") or "").strip()
    if not value:
        return channels.DEFAULT_DMS_CHANNEL
    if not channels.is_valid(value):
        raise AccountChannelError("dms_channel.unknown_channel")
    return value


def get_channel(subject_id: Optional[str]) -> str:
    """Assigned OA key for an account; unset → legacy default ``dms``.

    DB errors and unknown stored values raise :class:`AccountChannelError` (fail closed).
    """
    sid = str(subject_id or "").strip()
    if not sid:
        return channels.DEFAULT_DMS_CHANNEL

    def _run():
        from core import db

        with db.get_cursor() as cur:
            return read_channel(cur, sid)

    try:
        return _with_heal(_run)
    except AccountChannelError:
        raise
    except Exception as e:
        logger.error(f"[dms_account_channel] get failed: {e}")
        raise AccountChannelError("dms_channel.unavailable") from e


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
    except AccountChannelError:
        raise
    except Exception as e:
        logger.error(f"[dms_account_channel] get_channels failed: {e}")
        raise AccountChannelError("dms_channel.unavailable") from e
    out: Dict[str, str] = {}
    for row in rows:
        value = (row.get("channel_key") or "").strip()
        if not value:
            out[row["subject_id"]] = channels.DEFAULT_DMS_CHANNEL
            continue
        if not channels.is_valid(value):
            raise AccountChannelError("dms_channel.unknown_channel")
        out[row["subject_id"]] = value
    return out


def _affected_user_ids_on(cur, subject_id: str) -> List[str]:
    """Users that belong to the account: all tenant members, or the single user itself."""
    cur.execute(
        "SELECT owner_user_id::text AS owner_user_id FROM tenants WHERE id::text = %s",
        (subject_id,),
    )
    row = cur.fetchone()
    if row and row.get("owner_user_id"):
        cur.execute("SELECT id::text AS id FROM users WHERE tenant_id::text = %s", (subject_id,))
        return [r["id"] for r in cur.fetchall()]
    return [subject_id]


def _affected_user_ids(subject_id: str) -> List[str]:
    """Own-connection wrapper kept for callers/tests that only need the user list."""
    from core import db

    with db.get_cursor() as cur:
        return _affected_user_ids_on(cur, str(subject_id))


def set_channel(subject_id: str, channel_key: str, *, actor_id: Optional[str] = None) -> dict:
    """Assign an OA to an account. Returns ``{"error": code}`` or a result dict.

    When the key actually changes, existing bindings and pending codes for every user under the
    account are revoked first (``unbound`` / ``codes_voided``), so no old binding keeps answering
    on the previous OA. Re-setting the same key is a no-op and never unbinds anyone.

    The read, revoke and write happen in one transaction under the account lock shared with
    bind-code issuance and binding creation; menu reconciliation runs only after commit.
    """
    sid = str(subject_id or "").strip()
    key = (channel_key or "").strip()
    if not sid:
        return {"error": "dms_channel.missing_subject"}
    if not channels.is_valid(key):
        return {"error": "dms_channel.invalid_channel"}

    removed: List[tuple] = []
    result: dict = {}

    def _run():
        from core import db

        removed.clear()
        result.clear()
        with db.get_cursor(commit=True) as cur:
            lock_account(cur, sid)
            previous = read_channel(cur, sid)
            result["previous"] = previous
            if previous == key:
                result["changed"] = False
                return
            user_ids = _affected_user_ids_on(cur, sid)
            unbound = 0
            codes_voided = 0
            for user_id in user_ids:
                cur.execute(
                    "SELECT line_user_id, channel_key, tenant_id::text AS tenant_id "
                    "FROM line_dms_bindings WHERE user_id = %s",
                    (str(user_id),),
                )
                for row in cur.fetchall():
                    removed.append(
                        (
                            row["line_user_id"],
                            channels.normalize(row.get("channel_key")),
                            str(row["tenant_id"]),
                            str(user_id),
                        )
                    )
                cur.execute(
                    "UPDATE line_dms_binding_codes SET used_at = now() "
                    "WHERE user_id = %s AND used_at IS NULL",
                    (str(user_id),),
                )
                codes_voided += max(0, int(cur.rowcount or 0))
                cur.execute("DELETE FROM line_dms_bindings WHERE user_id = %s", (str(user_id),))
                unbound += max(0, int(cur.rowcount or 0))
            for line_id, line_channel, tenant_id, user_id in removed:
                cur.execute(
                    "DELETE FROM dms_line_sessions "
                    "WHERE tenant_id = %s AND channel_key = %s AND line_user_id = %s",
                    (tenant_id, line_channel, line_id),
                )
                cur.execute(
                    "DELETE FROM line_dms_login_tickets "
                    "WHERE tenant_id = %s AND user_id = %s AND channel_key = %s",
                    (tenant_id, user_id, line_channel),
                )
            cur.execute(
                "INSERT INTO dms_account_line_channels (subject_id, channel_key, updated_at, updated_by) "
                "VALUES (%s, %s, now(), %s) "
                "ON CONFLICT (subject_id) DO UPDATE SET "
                "  channel_key = EXCLUDED.channel_key, updated_at = now(), "
                "  updated_by = EXCLUDED.updated_by",
                (sid, key, str(actor_id) if actor_id else None),
            )
            result.update({"changed": True, "unbound": unbound, "codes_voided": codes_voided})

    try:
        _with_heal(_run)
    except AccountChannelError as e:
        logger.error(f"[dms_account_channel] set rejected: {e}")
        return {"error": e.code}
    except Exception as e:
        logger.error(f"[dms_account_channel] set failed: {e}")
        return {"error": "dms_channel.save_failed"}

    if not result.get("changed"):
        return {
            "ok": True,
            "channel_key": key,
            "changed": False,
            "unbound": 0,
            "codes_voided": 0,
        }

    # Network reconciliation must never run inside the transaction that moved the account.
    from services.line_dms import menu_sync

    for line_id, line_channel, _tenant_id, _user_id in removed:
        try:
            menu_sync.request_sync(line_id, line_channel)
        except Exception:
            logger.exception("[dms_account_channel] menu reconciliation pending")

    logger.info(
        "[dms_account_channel] subject=%s %s→%s unbound=%d codes_voided=%d",
        sid,
        result.get("previous"),
        key,
        result.get("unbound", 0),
        result.get("codes_voided", 0),
    )
    return {
        "ok": True,
        "channel_key": key,
        "changed": True,
        "unbound": result.get("unbound", 0),
        "codes_voided": result.get("codes_voided", 0),
    }
