"""Scoped account-catalog refresh operations for the ERP LINE editor."""

from __future__ import annotations

import asyncio
from typing import Any

from core.feature_flags import erp_target_projection_enabled_for
from services.cloud_tasks import dispatch as cloud_dispatch
from services.erp import target_catalog_evidence, target_refresh
from services.line_erp import target_preflight


class CatalogRefreshError(Exception):
    def __init__(self, code: str, status_code: int = 409):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _target(binding: dict[str, Any], endpoint_id: str, workspace_client_id: int | None) -> dict:
    try:
        readiness = target_preflight.require_ready(
            binding,
            endpoint_id=endpoint_id,
            workspace_client_id=workspace_client_id,
            refresh=False,
            include_account_catalog=False,
        )
    except target_preflight.TargetNotReady as exc:
        code = str(exc.result.get("block_reason") or "erp_target_not_ready")
        raise CatalogRefreshError(code) from None
    if not erp_target_projection_enabled_for(binding["tenant_id"], binding["user_id"]):
        raise CatalogRefreshError("target_refresh_unavailable")
    target = readiness["target"]
    if str(target.get("adapter") or "").lower() == "express" and not target.get(
        "supports_master_refresh"
    ):
        raise CatalogRefreshError("companion_update_required")
    return target


async def start(
    binding: dict[str, Any],
    user_id: str,
    endpoint_id: str,
    workspace_client_id: int | None,
) -> dict[str, Any]:
    target = await asyncio.to_thread(_target, binding, endpoint_id, workspace_client_id)
    adapter = str(target.get("adapter") or "").lower()
    try:
        refresh = await asyncio.to_thread(
            target_refresh.request_refresh,
            tenant_id=str(binding["tenant_id"]),
            user_id=str(user_id),
            endpoint_id=str(target["endpoint_id"]),
            account_set_key=target_refresh.ENDPOINT_SCOPE_KEY,
            adapter=adapter,
            reason="line_editor_account_catalog",
        )
    except ValueError as exc:
        raise CatalogRefreshError(str(exc)) from None
    if adapter == "mrerp":
        cloud_dispatch.spawn_sync(
            "erp.refresh", target_refresh.process_mrerp_request, refresh["request_id"]
        )
    return refresh


async def status(
    binding: dict[str, Any],
    endpoint_id: str,
    workspace_client_id: int | None,
    request_id: str,
) -> dict[str, Any]:
    compact_target = await asyncio.to_thread(_target, binding, endpoint_id, workspace_client_id)
    refresh = await asyncio.to_thread(
        target_refresh.refresh_status,
        request_id,
        tenant_id=str(binding["tenant_id"]),
        endpoint_id=endpoint_id,
    )
    if (
        not refresh
        or str(refresh.get("account_set_key") or "") != target_refresh.ENDPOINT_SCOPE_KEY
    ):
        raise CatalogRefreshError("target_refresh_missing", 404)
    result = {"refresh": refresh}
    if str(refresh.get("status") or "") == "succeeded":
        try:
            readiness = await asyncio.to_thread(
                target_preflight.require_ready,
                binding,
                endpoint_id=endpoint_id,
                workspace_client_id=workspace_client_id,
                refresh=False,
                include_account_catalog=True,
            )
        except target_preflight.TargetNotReady as exc:
            code = str(exc.result.get("block_reason") or "erp_target_not_ready")
            raise CatalogRefreshError(code) from None
        target = readiness["target"]
        receipt = await asyncio.to_thread(
            target_catalog_evidence.validate_refresh_receipt,
            tenant_id=str(binding["tenant_id"]),
            user_id=str(binding["user_id"]),
            endpoint_id=endpoint_id,
            adapter=str(compact_target.get("adapter") or ""),
            request_id=request_id,
            request_revision=refresh.get("result_revision"),
            catalog_revision=target.get("projection_revision"),
        )
        if not receipt["ok"]:
            raise CatalogRefreshError("target_refresh_superseded")
        result["target"] = target
    return result


__all__ = ["CatalogRefreshError", "start", "status"]
