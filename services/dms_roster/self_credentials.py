# -*- coding: utf-8 -*-
"""LINE-bound DMS operators may replace only their own stored credentials."""

from __future__ import annotations

import logging
from typing import Optional

from services.dms_roster import store

logger = logging.getLogger("mr-pilot")


class SelfCredentialError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _operator_context(user: dict) -> tuple[str, str]:
    tenant_id = str(user.get("tenant_id") or "").strip()
    user_id = str(user.get("id") or "").strip()
    if not tenant_id or not user_id or (user.get("role") or "") != "member":
        raise SelfCredentialError("dms_credentials.operator_only")
    profile = store.get_profile(tenant_id, user_id)
    if not profile or (profile.get("status") or "active") != "active":
        raise SelfCredentialError("dms_credentials.operator_inactive")
    return tenant_id, user_id


def _endpoint(user_id: str) -> Optional[dict]:
    from core import db

    for endpoint in db.list_erp_endpoints(user_id) or []:
        if (endpoint.get("adapter") or "").strip().lower() == "mrerp_dms":
            return endpoint
    return None


def load(user: dict) -> dict:
    """Return the operator's current DMS username; passwords never leave the server."""
    _tenant_id, user_id = _operator_context(user)
    endpoint = _endpoint(user_id)
    if not endpoint or endpoint.get("enabled") is False:
        raise SelfCredentialError("dms_credentials.endpoint_missing")
    try:
        from services.erp.erp_dms_push import _dms_plain_creds

        username, _password = _dms_plain_creds(endpoint.get("config") or {})
    except Exception as exc:
        raise SelfCredentialError("dms_credentials.unavailable") from exc
    if not username:
        raise SelfCredentialError("dms_credentials.unavailable")
    return {"username": username}


def update(user: dict, *, username: str, password: str) -> dict:
    """Atomically replace this operator's encrypted DMS username/password pair."""
    tenant_id, user_id = _operator_context(user)
    username = str(username or "").strip()
    password = str(password or "")
    if not username or not password:
        raise SelfCredentialError("dms_credentials.required")
    if len(username) > 120 or len(password) > 256:
        raise SelfCredentialError("dms_credentials.too_long")

    endpoint = _endpoint(user_id)
    if not endpoint or endpoint.get("enabled") is False:
        raise SelfCredentialError("dms_credentials.endpoint_missing")

    from core import db
    from core.kms_helper import encrypt_str

    config = dict(endpoint.get("config") or {})
    config["username_enc"] = encrypt_str(username)
    config["password_enc"] = encrypt_str(password)
    config.pop("username", None)
    config.pop("password", None)
    if not db.update_erp_endpoint(user_id, str(endpoint["id"]), config=config):
        raise SelfCredentialError("dms_credentials.update_failed")

    logger.info(
        "DMS operator updated own credentials: tenant_id=%s user_id=%s endpoint_id=%s",
        tenant_id,
        user_id,
        endpoint["id"],
    )
    return {"updated": True}
