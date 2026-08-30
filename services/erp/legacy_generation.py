"""Locks shared by the pre-enrollment ERP writers."""

from __future__ import annotations

from typing import Optional

_BINDING_LOCK_SEED = 0x50454152


def lock_endpoint_binding(cur, endpoint_id: Optional[str]) -> bool:
    """Serialize enrollment and every legacy writer for one endpoint."""
    if not endpoint_id:
        return True
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, %s))",
        (str(endpoint_id).strip(), _BINDING_LOCK_SEED),
    )
    return True


def lock_legacy_endpoint(cur, endpoint_id: Optional[str], user_id: Optional[str] = None) -> bool:
    """Hold a share lock while an old writer uses an endpoint.

    A missing endpoint id belongs to the legacy orphan-log path.  A supplied
    id must still be an active generation-zero endpoint for its creator.
    """
    if not endpoint_id:
        return True
    sql = "SELECT id FROM erp_endpoints WHERE id = %s " "AND binding_generation = 0"
    params: list[str] = [str(endpoint_id)]
    if user_id is not None:
        sql += " AND user_id = %s"
        params.append(str(user_id))
    sql += " FOR SHARE"
    cur.execute(sql, tuple(params))
    return cur.fetchone() is not None


def read_log_endpoint_id(cur, log_id: str) -> Optional[str]:
    """Read a log's endpoint pointer before locking the endpoint itself."""
    cur.execute("SELECT endpoint_id FROM erp_push_logs WHERE id = %s", (str(log_id),))
    row = cur.fetchone()
    if not row:
        return None
    value = row.get("endpoint_id") if hasattr(row, "get") else row[0]
    return str(value) if value is not None else None
