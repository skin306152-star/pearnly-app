"""Shared, credential-safe ERP readiness and cached MR.ERP connection probes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.erp._master_data_cache import TTLCache
from services.erp.shared_express_store import safe_endpoint_dto

_probe_cache = TTLCache(max_size=512, ttl_seconds=60.0)


def _credentials_configured(config: Any) -> bool:
    if not isinstance(config, dict):
        return False
    encrypted = bool(config.get("username_enc") and config.get("password_enc"))
    plaintext = bool(config.get("username") and config.get("password"))
    return encrypted or plaintext


def probe_endpoint(endpoint: dict[str, Any], *, refresh: bool = False) -> dict[str, Any]:
    """Return a safe runtime probe. MR.ERP network checks are cached for 60 seconds."""
    endpoint_id = str(endpoint.get("id") or "")
    actor_id = str(endpoint.get("user_id") or "")
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    cache_key = (actor_id, endpoint_id, adapter)
    cacheable = adapter in {"mrerp", "mrerp_dms"}
    if cacheable and not refresh:
        cached = _probe_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    if endpoint.get("enabled") is not True:
        result = {"ok": False, "error_code": "ENDPOINT_DISABLED", "elapsed_ms": 0}
    elif adapter == "mrerp":
        from services.erp import erp_push

        result = erp_push.test_mrerp_endpoint(dict(endpoint.get("config") or {}))
    elif adapter == "mrerp_dms":
        from services.erp import erp_push

        result = erp_push.test_mrerp_dms_endpoint(dict(endpoint.get("config") or {}))
    elif adapter == "express":
        dto = safe_endpoint_dto(
            endpoint,
            endpoint.get("server_now") or datetime.now(timezone.utc),
        )
        state = str(dto.get("connection_state") or "needs_attention")
        result = {
            "ok": state == "online",
            "error_code": None if state == "online" else state.upper(),
            "elapsed_ms": 0,
            "connection_state": state,
        }
    else:
        from services.erp import erp_push

        legacy = erp_push.test_endpoint_connection(adapter, dict(endpoint.get("config") or {}))
        result = {
            "ok": bool(legacy.get("success")),
            "elapsed_ms": legacy.get("elapsed_ms", 0),
            "http_status": legacy.get("http_status"),
            "raw_error": legacy.get("error_msg"),
            "companies": [],
            "error_code": None if legacy.get("success") else "ERR_TECHNICAL",
            "error_friendly": None,
        }

    projected = {
        **result,
        "ok": bool(result.get("ok")),
        "elapsed_ms": int(result.get("elapsed_ms") or 0),
        "last_tested_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }
    if cacheable:
        _probe_cache.set(cache_key, projected)
    return projected


def endpoint_status(
    endpoint: dict[str, Any],
    *,
    probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project one endpoint without credentials, tokens, or profile keys."""
    adapter = str(endpoint.get("adapter") or "").strip().lower()
    enabled = endpoint.get("enabled") is True
    configured = True
    missing: list[str] = []
    if not enabled:
        missing.append("endpoint_disabled")

    if adapter == "mrerp":
        configured = _credentials_configured(endpoint.get("config"))
        if not configured:
            missing.append("credentials_missing")
        state = "disabled" if not enabled else "configured" if configured else "unconfigured"
        if enabled and configured and probe is not None:
            if probe.get("ok"):
                state = "online"
            else:
                state = "offline"
                missing.append("erp_connection_failed")
    elif adapter == "express":
        dto = safe_endpoint_dto(
            endpoint,
            endpoint.get("server_now") or datetime.now(timezone.utc),
        )
        state = str(dto.get("connection_state") or "needs_attention")
        configured = state not in {"unpaired", "pairing", "needs_attention"}
        reason_by_state = {
            "disabled": "endpoint_disabled",
            "revoked": "endpoint_revoked",
            "offline": "companion_offline",
            "unpaired": "companion_not_ready",
            "pairing": "companion_not_ready",
            "unbound": "profile_unconfirmed",
            "mismatch": "profile_mismatch",
            "needs_attention": "companion_not_ready",
        }
        reason = reason_by_state.get(state)
        if reason and reason not in missing:
            missing.append(reason)
    else:
        state = "online" if enabled else "disabled"

    return {
        "adapter": adapter,
        "configured": configured,
        "connection_state": state,
        "ready": not missing,
        "missing": missing,
        "block_reason": missing[0] if missing else None,
        "last_tested_at": probe.get("last_tested_at") if probe else None,
        "cached": bool(probe and probe.get("cached")),
    }


def clear_probe_cache() -> None:
    _probe_cache.clear()


__all__ = ["_probe_cache", "clear_probe_cache", "endpoint_status", "probe_endpoint"]
