"""Periodic tenant-safe DMS master refresh orchestration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from services.erp.dms_master_shared import (
    BACKGROUND_MAX_AGE_SECONDS,
    cache_scope_id,
    get_session_masters,
    is_shared_scope,
    needs_refresh,
)

logger = logging.getLogger(__name__)

_ADMIN_KEYS = (
    "admin_username",
    "admin_password",
    "admin_username_enc",
    "admin_password_enc",
)


def _rows() -> List[Dict[str, Any]]:
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT ep.id, ep.user_id, ep.name, ep.adapter, ep.config, ep.enabled, "
            "u.tenant_id AS _dms_cache_tenant_id, COALESCE(u.role, 'owner') AS _role "
            "FROM erp_endpoints ep JOIN users u ON u.id = ep.user_id "
            "WHERE lower(ep.adapter) = 'mrerp_dms' AND ep.enabled IS NOT FALSE "
            "AND ep.binding_generation = 0 "
            "ORDER BY u.tenant_id, CASE WHEN COALESCE(u.role, 'owner') = 'owner' THEN 0 ELSE 1 END, "
            "ep.created_at"
        )
        return [dict(row) for row in cur.fetchall()]


def _has_admin(config: dict) -> bool:
    from services.erp.dms_id_ocr import _cfg_has_admin

    return _cfg_has_admin(config)


def shared_endpoints() -> List[Dict[str, Any]]:
    """Return one representative per tenant/system/admin credential scope."""
    rows = _rows()
    owners: Dict[str, dict] = {}
    for row in rows:
        tenant = str(row.get("_dms_cache_tenant_id") or "")
        config = row.get("config") or {}
        if row.get("_role") == "owner" and tenant and _has_admin(config):
            owners.setdefault(tenant, config)

    found: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        endpoint = dict(raw)
        tenant = str(endpoint.get("_dms_cache_tenant_id") or "")
        config = dict(endpoint.get("config") or {})
        if not _has_admin(config):
            owner_config = owners.get(tenant) or {}
            for key in _ADMIN_KEYS:
                if owner_config.get(key):
                    config[key] = owner_config[key]
        endpoint["config"] = config
        if not is_shared_scope(endpoint):
            continue
        found.setdefault(cache_scope_id(endpoint), endpoint)
    return list(found.values())


def sweep() -> dict:
    """Enqueue only stale shared scopes; request threads never perform this scan."""
    from services.cloud_tasks import dispatch

    checked = queued = 0
    for endpoint in shared_endpoints():
        checked += 1
        if not needs_refresh(endpoint, BACKGROUND_MAX_AGE_SECONDS):
            continue
        dispatch.enqueue("dms.masters_refresh", str(endpoint["id"]))
        queued += 1
    logger.info("dms_master_sweep checked=%s queued=%s", checked, queued)
    return {"checked": checked, "queued": queued}


def refresh_endpoint(endpoint_id: str) -> dict:
    """Refresh the current representative after re-reading configuration."""
    endpoint = next(
        (row for row in shared_endpoints() if str(row.get("id") or "") == str(endpoint_id)),
        None,
    )
    if endpoint is None:
        return {"status": "skipped", "reason": "endpoint_unavailable"}
    masters = get_session_masters(
        endpoint,
        max_age_seconds=BACKGROUND_MAX_AGE_SECONDS,
        require_complete=True,
    )
    if not masters:
        raise RuntimeError("dms_master_refresh_failed")
    return {"status": "fresh", "scope": cache_scope_id(endpoint)[:20]}
