# -*- coding: utf-8 -*-
"""B3B3 database boundary for managed Express heartbeat and profile confirm."""

from __future__ import annotations

from core import db

from services.erp.shared_express_live_ddl import LIVE_DDL

HEARTBEAT_GATE = "app.erp_managed_live_heartbeat"
CONFIRM_GATE = "app.erp_managed_live_confirm"
LIVE_TENANT = "app.erp_managed_live_tenant_id"
LIVE_ACTOR = "app.erp_managed_live_actor_id"
LIVE_ENDPOINT = "app.erp_managed_live_endpoint_id"
LIVE_GENERATION = "app.erp_managed_live_generation"
CONFIRM_GENERATION = "app.erp_managed_live_expected_generation"

_READY = False


def live_schema_ready() -> bool:
    return _READY is True


def apply_shared_express_live_schema(cur) -> None:
    for statement in LIVE_DDL:
        cur.execute(statement)


def ensure_shared_express_live_schema() -> None:
    global _READY
    try:
        with db.get_cursor(commit=True) as cur:
            apply_shared_express_live_schema(cur)
    except Exception:
        _READY = False
        raise
    _READY = True


def _reset(cur) -> None:
    names = (
        HEARTBEAT_GATE,
        CONFIRM_GATE,
        LIVE_TENANT,
        LIVE_ACTOR,
        LIVE_ENDPOINT,
        LIVE_GENERATION,
        CONFIRM_GENERATION,
    )
    cur.execute("SELECT " + ", ".join("set_config(%s, '', true)" for _ in names), names)


def enable_managed_live_heartbeat(
    cur, *, tenant_id, actor_user_id, endpoint_id, generation
) -> bool:
    """Set the heartbeat gate only after the caller has locked and authenticated the row."""
    _reset(cur)
    values = [
        str(tenant_id or "").strip(),
        str(actor_user_id or "").strip(),
        str(endpoint_id or "").strip(),
        str(generation),
    ]
    if (
        not values[0]
        or not values[2]
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 1
    ):
        return False
    cur.execute(
        "SELECT set_config(%s, 'on', true), set_config(%s, %s, true), "
        "set_config(%s, %s, true), set_config(%s, %s, true), set_config(%s, %s, true)",
        (
            HEARTBEAT_GATE,
            LIVE_TENANT,
            values[0],
            LIVE_ACTOR,
            values[1],
            LIVE_ENDPOINT,
            values[2],
            LIVE_GENERATION,
            values[3],
        ),
    )
    return True


def enable_managed_live_confirm(
    cur, *, tenant_id, actor_user_id, endpoint_id, expected_generation
) -> bool:
    """Set the exact owner-confirm gate; policy and trigger enforce the post-state."""
    _reset(cur)
    if not tenant_id or not actor_user_id or not endpoint_id:
        return False
    if (
        not isinstance(expected_generation, int)
        or isinstance(expected_generation, bool)
        or expected_generation < 1
    ):
        return False
    cur.execute(
        "SELECT set_config(%s, 'on', true), set_config(%s, %s, true), set_config(%s, %s, true), "
        "set_config(%s, %s, true), set_config(%s, %s, true), set_config(%s, %s, true)",
        (
            CONFIRM_GATE,
            LIVE_TENANT,
            str(tenant_id),
            LIVE_ACTOR,
            str(actor_user_id),
            LIVE_ENDPOINT,
            str(endpoint_id),
            CONFIRM_GENERATION,
            str(expected_generation),
            LIVE_GENERATION,
            str(expected_generation),
        ),
    )
    return True


__all__ = [
    "CONFIRM_GATE",
    "CONFIRM_GENERATION",
    "HEARTBEAT_GATE",
    "LIVE_ACTOR",
    "LIVE_ENDPOINT",
    "LIVE_GENERATION",
    "LIVE_TENANT",
    "LIVE_DDL",
    "apply_shared_express_live_schema",
    "enable_managed_live_confirm",
    "enable_managed_live_heartbeat",
    "ensure_shared_express_live_schema",
    "live_schema_ready",
]
