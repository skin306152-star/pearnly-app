"""Transaction helpers shared by binding changes and conversation state writes."""

from services.line_dms import binding_guard
from services.line_platform import channels


class UnknownChannel(ValueError):
    """A non-empty channel key that is not a registered OA.

    Scoping helpers raise instead of rewriting it to the legacy OA: locking or deleting under
    the wrong channel would let one OA's write race another OA's rebind.
    """

    code = "dms_channel.unknown_channel"

    def __init__(self, channel_key):
        super().__init__(self.code)
        self.channel_key = str(channel_key or "")


def _scoped_channel(channel_key) -> str:
    """Empty → legacy; registered key → itself; unknown non-empty → raise (fail closed)."""
    key = channels.resolve(channel_key)
    if key is None:
        raise UnknownChannel(channel_key)
    return key


def lock_line(cur, line_user_id: str, channel_key: str = "") -> None:
    key = _scoped_channel(channel_key)
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        ("dms-binding:" + key + ":" + str(line_user_id),),
    )


def lock_scope(cur, line_user_id: str, channel_key: str = "") -> None:
    """Serialize state writes with rebind, checking the epoch under the same lock."""
    key = _scoped_channel(channel_key)
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
    Unknown non-empty keys raise instead of deleting the legacy OA's rows.
    """
    key = _scoped_channel(channel_key)
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
