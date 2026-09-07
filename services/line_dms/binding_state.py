"""Transaction helpers shared by binding changes and conversation state writes."""

from services.line_dms import binding_guard


def lock_line(cur, line_user_id: str) -> None:
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        ("dms-binding:" + str(line_user_id),),
    )


def lock_scope(cur, line_user_id: str) -> None:
    """Serialize state writes with rebind, checking the epoch under the same lock."""
    lock_line(cur, line_user_id)
    binding = binding_guard.snapshot()
    if binding is None:
        return
    cur.execute(
        "SELECT id FROM line_dms_bindings WHERE line_user_id=%s AND id=%s "
        "AND user_id=%s AND tenant_id=%s",
        (line_user_id, str(binding["id"]), binding["user_id"], binding["tenant_id"]),
    )
    if not cur.fetchone():
        raise binding_guard.BindingChanged("dms_binding_changed")


def invalidate(cur, line_user_id: str, user_id: str) -> None:
    cur.execute("DELETE FROM dms_line_sessions WHERE line_user_id=%s", (line_user_id,))
    cur.execute("DELETE FROM line_dms_login_tickets WHERE user_id=%s", (str(user_id),))
