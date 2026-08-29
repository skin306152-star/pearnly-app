# -*- coding: utf-8 -*-
"""Tenant-scoped rollout gate for shared Express endpoints."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

ERP_SHARED_EXPRESS_ENDPOINT_KEY = "erp_shared_express_endpoint"


def erp_shared_express_endpoint_enabled_for(tenant_id: Optional[str]) -> bool:
    """Return False unless the tenant is explicitly enabled."""
    if not tenant_id:
        return False
    try:
        from services.platform_settings import store

        return bool(store.is_enabled_for_user(ERP_SHARED_EXPRESS_ENDPOINT_KEY, str(tenant_id)))
    except Exception as exc:
        logger.warning("shared Express endpoint flag fail-closed: %s", exc)
        return False
