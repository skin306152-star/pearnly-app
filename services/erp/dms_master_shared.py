# -*- coding: utf-8 -*-
"""Fast, bounded-fresh DMS master snapshots shared by one tenant/account set.

The DMS has no revision endpoint.  Pearnly therefore keeps a tenant-safe shadow
snapshot: one caller refreshes it, concurrent callers reuse that result, and a
booking still performs the existing authoritative preflight immediately before
the write.  Empty/incomplete/failed reads never replace the last good snapshot.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SESSION_MAX_AGE_SECONDS = int(os.environ.get("DMS_MASTER_SESSION_MAX_AGE_SECONDS", "90"))
BACKGROUND_MAX_AGE_SECONDS = int(os.environ.get("DMS_MASTER_BACKGROUND_MAX_AGE_SECONDS", "45"))
PAINT_MAX_AGE_SECONDS = int(os.environ.get("DMS_PAINT_SESSION_MAX_AGE_SECONDS", "90"))
REFRESH_WAIT_SECONDS = int(os.environ.get("DMS_MASTER_REFRESH_WAIT_SECONDS", "45"))
REFRESH_LEASE_SECONDS = int(os.environ.get("DMS_MASTER_REFRESH_LEASE_SECONDS", "150"))
PAINT_WARM_LIMIT = int(os.environ.get("DMS_PAINT_WARM_LIMIT", "8"))

_LOCK_TABLE = "dms_master_refresh_locks"
_LOCK_DDL = f"""
CREATE TABLE IF NOT EXISTS {_LOCK_TABLE} (
    scope_key text PRIMARY KEY,
    owner uuid NOT NULL,
    lease_until timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
)
"""


def migrate_lock_table() -> None:
    """Create the refresh lease table from the serialized Cloud Run schema job."""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_LOCK_DDL)
        cur.execute(f"ALTER TABLE {_LOCK_TABLE} ENABLE ROW LEVEL SECURITY")
        cur.execute(f"REVOKE ALL ON {_LOCK_TABLE} FROM PUBLIC")


def _tenant_key(endpoint: Dict[str, Any]) -> str:
    tenant = str(endpoint.get("_dms_cache_tenant_id") or "").strip()
    if tenant:
        return tenant
    user_id = str(endpoint.get("user_id") or "").strip()
    if not user_id:
        return ""
    try:
        from core import db

        user = db.find_user_by_id(user_id) or {}
        return str(user.get("tenant_id") or "").strip()
    except Exception:
        logger.warning("[dms masters] tenant scope lookup failed", exc_info=True)
        return ""


def _admin_marker(config: Dict[str, Any]) -> str:
    from services.erp.erp_dms_push import _dms_resolve_admin_creds

    plain_user, plain_password, enc_user, enc_password = _dms_resolve_admin_creds(config)
    if plain_user and plain_password:
        return "plain:" + plain_user.casefold()
    if enc_user and enc_password:
        return "enc:" + enc_user
    return ""


def cache_scope_id(endpoint: Dict[str, Any]) -> str:
    """Return a shared key only when tenant and authoritative admin are known.

    Tenant is part of the digest even if two customers happen to configure the
    same DMS username.  Without an admin identity we retain the endpoint id so a
    salesperson's permission-trimmed view can never leak into another account.
    """
    endpoint_id = str(endpoint.get("id") or "")
    config = endpoint.get("config") or {}
    admin = _admin_marker(config)
    tenant = _tenant_key(endpoint)
    if not endpoint_id or not admin or not tenant:
        return endpoint_id
    system_url = (
        str(config.get("system_url") or "https://www.mrerp4sme.com/dms/index.php")
        .strip()
        .rstrip("/")
        .casefold()
    )
    raw = "\x1f".join((tenant, system_url, admin))
    return "shared-v1:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_shared_scope(endpoint: Dict[str, Any]) -> bool:
    return cache_scope_id(endpoint).startswith("shared-v1:")


def _complete(cached: Optional[dict], require_complete: bool) -> bool:
    if not cached or not isinstance(cached.get("masters"), dict):
        return False
    if not require_complete:
        return True
    from services.erp import dms_masters_cache as cache

    masters = cached["masters"]
    return all(isinstance(masters.get(key), list) for key in cache._COMPLETE_KEYS)


def _fresh(cached: Optional[dict], max_age_seconds: float, require_complete: bool) -> bool:
    return _complete(cached, require_complete) and float(cached.get("age_seconds") or 0) <= float(
        max_age_seconds
    )


def needs_refresh(endpoint: Dict[str, Any], max_age_seconds: float) -> bool:
    from services.erp import dms_masters_cache as cache

    return not _fresh(cache._read(cache_scope_id(endpoint)), max_age_seconds, True)


def _acquire(scope_key: str, lease_seconds: int = REFRESH_LEASE_SECONDS) -> Optional[str]:
    from core import db

    owner = str(uuid.uuid4())
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            f"INSERT INTO {_LOCK_TABLE}(scope_key, owner, lease_until) "
            "VALUES (%s, %s::uuid, now() + (%s * interval '1 second')) "
            "ON CONFLICT(scope_key) DO UPDATE SET owner=EXCLUDED.owner, "
            "lease_until=EXCLUDED.lease_until, updated_at=now() "
            f"WHERE {_LOCK_TABLE}.lease_until < now() RETURNING owner",
            (scope_key, owner, int(lease_seconds)),
        )
        return owner if cur.fetchone() else None


def _release(scope_key: str, owner: str) -> None:
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            f"DELETE FROM {_LOCK_TABLE} WHERE scope_key=%s AND owner=%s::uuid",
            (scope_key, owner),
        )


def _wait_for_fresh(scope_key: str, max_age_seconds: float, require_complete: bool) -> dict:
    from services.erp import dms_masters_cache as cache

    deadline = time.monotonic() + REFRESH_WAIT_SECONDS
    while time.monotonic() < deadline:
        cached = cache._read(scope_key)
        if _fresh(cached, max_age_seconds, require_complete):
            return cached["masters"]
        time.sleep(0.25)
    return {}


def _preserve_paints(fresh: dict, cached: Optional[dict]) -> dict:
    old = (cached or {}).get("masters") or {}
    old_paints = old.get("paints_by_car") or {}
    old_times = old.get("paints_refreshed_at") or {}
    valid_cars = {str(row[0]) for row in fresh.get("cars") or [] if row}
    paints = {str(key): value for key, value in old_paints.items() if str(key) in valid_cars}
    paint_times = {str(key): value for key, value in old_times.items() if str(key) in paints}
    if paints:
        fresh = {**fresh, "paints_by_car": paints, "paints_refreshed_at": paint_times}
    return fresh


def get_session_masters(
    endpoint: Dict[str, Any],
    *,
    max_age_seconds: float = SESSION_MAX_AGE_SECONDS,
    require_complete: bool = True,
) -> Dict[str, Any]:
    """Return a bounded-fresh complete bundle, coalescing concurrent refreshes."""
    from services.erp import dms_masters_cache as cache

    scope_key = cache_scope_id(endpoint)
    cached = cache._read(scope_key)
    if _fresh(cached, max_age_seconds, require_complete):
        return cached["masters"]
    owner = _acquire(scope_key)
    if not owner:
        return _wait_for_fresh(scope_key, max_age_seconds, require_complete)
    try:
        # A previous waiter may have completed between the first read and our lease.
        cached = cache._read(scope_key)
        if _fresh(cached, max_age_seconds, require_complete):
            return cached["masters"]
        fresh = cache._fetch_masters_via_login(endpoint, require_complete=require_complete)
        candidate = {"masters": fresh, "age_seconds": 0}
        if not _complete(candidate, require_complete):
            logger.warning("[dms masters] refresh returned an incomplete bundle; cache unchanged")
            return {}
        fresh = _preserve_paints(dict(fresh), cached)
        cache._write_full_preserving_paints(scope_key, fresh)
        return fresh
    finally:
        _release(scope_key, owner)


def _paint_fresh(masters: dict, car_id: str, max_age_seconds: float) -> bool:
    paints = masters.get("paints_by_car") or {}
    stamp = (masters.get("paints_refreshed_at") or {}).get(car_id)
    try:
        age = time.time() - float(stamp)
    except (TypeError, ValueError):
        return False
    return car_id in paints and age <= float(max_age_seconds)


def _paint_result(scope_key: str, car_id: str, max_age_seconds: float) -> Optional[list]:
    from services.erp import dms_masters_cache as cache

    cached = cache._read(scope_key)
    masters = (cached or {}).get("masters") or {}
    if _paint_fresh(masters, car_id, max_age_seconds):
        return list((masters.get("paints_by_car") or {})[car_id])
    return None


def get_session_paints(
    endpoint: Dict[str, Any],
    car_id: str,
    *,
    max_age_seconds: float = PAINT_MAX_AGE_SECONDS,
    require_complete: bool = True,
) -> list:
    """Return one car's bounded-fresh colors, shared across concurrent users."""
    from services.erp import dms_masters_cache as cache
    from services.erp.mrerp_dms_client_base import DMSClientError

    car_id = str(car_id or "")
    if not car_id:
        return []
    scope_key = cache_scope_id(endpoint)
    existing = _paint_result(scope_key, car_id, max_age_seconds)
    if existing is not None:
        return existing
    lock_key = scope_key + ":paint:" + car_id
    owner = _acquire(lock_key)
    if not owner:
        # A scheduled warmer or another operator is already refreshing this car.
        # Reuse the last complete list instead of making the LINE reply wait for
        # the DMS session. Final booking preflight still performs a live read.
        cached = cache._read(scope_key)
        stale = (((cached or {}).get("masters") or {}).get("paints_by_car") or {}).get(car_id)
        if isinstance(stale, list):
            return list(stale)
        deadline = time.monotonic() + REFRESH_WAIT_SECONDS
        while time.monotonic() < deadline:
            existing = _paint_result(scope_key, car_id, max_age_seconds)
            if existing is not None:
                return existing
            time.sleep(0.25)
        if require_complete:
            raise DMSClientError("DMS paint refresh timed out", "ERR_DMS_MASTER_UNAVAILABLE")
        return []
    try:
        existing = _paint_result(scope_key, car_id, max_age_seconds)
        if existing is not None:
            return existing
        rows = cache._fetch_paints_via_login(endpoint, car_id)
        if rows is None:
            if require_complete:
                raise DMSClientError(
                    f"DMS paint master unavailable for car {car_id!r}",
                    "ERR_DMS_MASTER_UNAVAILABLE",
                )
            return []
        cached = cache._read(scope_key)
        masters = dict((cached or {}).get("masters") or {})
        paints = dict(masters.get("paints_by_car") or {})
        paint_times = dict(masters.get("paints_refreshed_at") or {})
        paints[car_id] = list(rows)
        paint_times[car_id] = time.time()
        masters.update(paints_by_car=paints, paints_refreshed_at=paint_times)
        cache._write(scope_key, masters, touch_refreshed_at=False)
        return list(rows)
    finally:
        _release(lock_key, owner)


def warm_cached_paints(
    endpoint: Dict[str, Any], *, max_age_seconds: float = BACKGROUND_MAX_AGE_SECONDS
) -> int:
    """Refresh recently used color lists off the LINE request path.

    Only cars already selected by users are eligible, capped per scope. Their
    individual leases avoid racing an interactive refresh, while one DMS login
    serves the whole batch.
    """
    from services.erp import dms_masters_cache as cache

    scope_key = cache_scope_id(endpoint)
    cached = cache._read(scope_key)
    masters = (cached or {}).get("masters") or {}
    paints = masters.get("paints_by_car") or {}
    stamps = masters.get("paints_refreshed_at") or {}
    candidates = []
    for car_id in paints:
        try:
            age = time.time() - float(stamps.get(car_id))
        except (TypeError, ValueError):
            age = float("inf")
        if age > float(max_age_seconds):
            candidates.append((float(stamps.get(car_id) or 0), str(car_id)))
    candidates.sort(reverse=True)

    leases = []
    for _stamp, car_id in candidates[: max(0, PAINT_WARM_LIMIT)]:
        owner = _acquire(scope_key + ":paint:" + car_id)
        if owner:
            leases.append((car_id, owner))
    if not leases:
        return 0
    try:
        rows_by_car = cache._fetch_paints_batch_via_login(
            endpoint, [car_id for car_id, _owner in leases]
        )
        if rows_by_car is None:
            return 0
        now = time.time()
        update = {
            "paints_by_car": {car_id: rows_by_car[car_id] for car_id, _owner in leases},
            "paints_refreshed_at": {car_id: now for car_id, _owner in leases},
        }
        cache._write(scope_key, update, touch_refreshed_at=False)
        return len(leases)
    finally:
        for car_id, owner in leases:
            _release(scope_key + ":paint:" + car_id, owner)
