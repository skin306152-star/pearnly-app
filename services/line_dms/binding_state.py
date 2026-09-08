"""Transaction helpers shared by binding changes and conversation state writes."""

from services.line_dms import binding_guard
from services.line_platform import channels


def lock_line(cur, line_user_id: str, channel_key: str = "") -> None:
    key = channels.normalize(channel_key)
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        ("dms-binding:" + key + ":" + str(line_user_id),),
    )


def lock_scope(cur, line_user_id: str, channel_key: str = "") -> None:
    """Serialize state writes with rebind, checking the epoch under the same lock."""
    key = channels.normalize(channel_key)
    lock_line(cur, line_user_id, key)
    binding = binding_guard.snapshot()
    if binding is None:
        return
    cur.execute(
        "SELECT id FROM line_dms_bindings WHERE line_user_id=%s AND channel_key=%s AND id=%s "
        "AND user_id=%s AND tenant_id=%s",
        (line_user_id, key, str(binding["id"]), binding["user_id"], binding["tenant_id"]),
    )
    if not cur.fetchone():
        raise binding_guard.BindingChanged("dms_binding_changed")


def invalidate(cur, line_user_id: str, user_id: str, channel_key: str, tenant_id: str) -> None:
    """Drop exactly this (tenant, OA, LINE user) conversation and its browser tickets.

    The old unscoped DELETE removed the same LINE id's sessions/tickets in other OAs and
    tenants. Both dimensions are required now so a rebind in one OA can never log out another.
    """
    key = channels.normalize(channel_key)
    cur.execute(
        "DELETE FROM dms_line_sessions "
        "WHERE tenant_id=%s AND channel_key=%s AND line_user_id=%s",
        (str(tenant_id), key, line_user_id),
    )
    cur.execute(
        "DELETE FROM line_dms_login_tickets "
        "WHERE tenant_id=%s AND user_id=%s AND channel_key=%s",
        (str(tenant_id), str(user_id), key),
    )
