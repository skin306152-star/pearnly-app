"""ERP target checks shared by LINE menu, OCR admission, and final posting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from core import db
from services.erp import target_readiness, team_access


class TargetNotReady(Exception):
    def __init__(self, result: dict[str, Any]):
        self.result = result
        super().__init__(str(result.get("block_reason") or "erp_target_not_ready"))


def _active_user(binding: dict[str, Any]) -> dict[str, Any]:
    user = db.find_user_by_id(str(binding.get("user_id") or ""))
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id") or "") != str(binding.get("tenant_id") or "")
    ):
        raise TargetNotReady({"ready": False, "block_reason": "erp_user_inactive"})
    projected = dict(user)
    projected["entry"] = "erp"
    try:
        team_access.require_active_erp_user(projected)
    except HTTPException:
        raise TargetNotReady({"ready": False, "block_reason": "erp_user_inactive"}) from None
    return projected


def _workspace_endpoint(binding: dict[str, Any]) -> dict[str, Any] | None:
    workspace_id = binding.get("workspace_client_id")
    if not workspace_id:
        return None
    with db.get_cursor_rls(
        tenant_id=str(binding.get("tenant_id") or ""),
        user_id=str(binding.get("user_id") or ""),
    ) as cur:
        cur.execute(
            """
            SELECT ep.id, ep.name, ep.adapter, ep.config, ep.is_default, ep.auto_push,
                   ep.enabled, ep.user_id, ep.tenant_id, ep.workspace_client_id,
                   ep.shared_scope, ep.binding_generation, ep.bound_account_set,
                   ep.bound_profile_key, ep.live_account_set, ep.live_profile_key,
                   ep.agent_last_seen_at, ep.agent_version, ep.revoked_at,
                   clock_timestamp() AS server_now
            FROM workspace_clients workspace
            JOIN erp_endpoints ep ON ep.id = workspace.erp_endpoint_id
            WHERE workspace.id = %s AND workspace.tenant_id = %s
              AND workspace.is_active = TRUE
            LIMIT 1
            """,
            (int(workspace_id), str(binding.get("tenant_id") or "")),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def _owner_endpoints(
    user: dict[str, Any],
    workspace_endpoint: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    endpoints = [dict(row) for row in db.list_erp_endpoints(str(user["id"])) or []]
    if workspace_endpoint and all(
        str(row.get("id")) != str(workspace_endpoint.get("id")) for row in endpoints
    ):
        endpoints.append(workspace_endpoint)
    now = datetime.now(timezone.utc)
    for endpoint in endpoints:
        endpoint.setdefault("server_now", now)
    return endpoints


def _selected_endpoint(
    user: dict[str, Any],
    endpoints: list[dict[str, Any]],
    workspace_endpoint: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if (
        user.get("entry") == "erp"
        and not user.get("is_super_admin")
        and str(user.get("role") or "").lower() != "owner"
    ):
        return endpoints[0] if endpoints else None
    if workspace_endpoint:
        return next(
            (row for row in endpoints if str(row.get("id")) == str(workspace_endpoint.get("id"))),
            workspace_endpoint,
        )
    return next(
        (row for row in endpoints if row.get("is_default")), endpoints[0] if endpoints else None
    )


def inspect_targets(
    binding: dict[str, Any],
    *,
    refresh: bool = False,
    expected_endpoint_id: str | None = None,
) -> dict[str, Any]:
    user = _active_user(binding)
    assigned = team_access.assigned_push_endpoint(user)
    workspace_endpoint = None if assigned is not None else _workspace_endpoint(binding)
    endpoints = [assigned] if assigned is not None else _owner_endpoints(user, workspace_endpoint)
    selected = _selected_endpoint(user, endpoints, workspace_endpoint)
    selected_id = str((selected or {}).get("id") or "")
    target_rows = []
    for endpoint in endpoints:
        probe = target_readiness.probe_endpoint(endpoint, refresh=refresh)
        status = target_readiness.endpoint_status(endpoint, probe=probe)
        target_rows.append(
            {
                "endpoint_id": str(endpoint.get("id") or ""),
                "label": str(endpoint.get("name") or endpoint.get("adapter") or "ERP")[:80],
                "adapter": str(endpoint.get("adapter") or "").lower(),
                "selected": str(endpoint.get("id") or "") == selected_id,
                **status,
            }
        )
    selected_status = next((row for row in target_rows if row["selected"]), None)
    block_reason = None
    if selected_status is None:
        block_reason = "no_default_endpoint"
    elif expected_endpoint_id and str(expected_endpoint_id) != selected_id:
        block_reason = "erp_target_changed"
    elif not selected_status.get("ready"):
        block_reason = str(selected_status.get("block_reason") or "erp_target_not_ready")
    return {
        "ready": block_reason is None,
        "block_reason": block_reason,
        "endpoint_id": selected_id or None,
        "endpoint": selected,
        "user": user,
        "targets": target_rows,
    }


def require_ready(
    binding: dict[str, Any],
    *,
    refresh: bool = False,
    expected_endpoint_id: str | None = None,
) -> dict[str, Any]:
    result = inspect_targets(
        binding,
        refresh=refresh,
        expected_endpoint_id=expected_endpoint_id,
    )
    if not result["ready"]:
        raise TargetNotReady(result)
    return result


_THAI_REASONS = {
    "no_default_endpoint": "ยังไม่ได้ตั้งค่า ERP ปลายทาง",
    "endpoint_disabled": "ERP ปลายทางถูกปิดใช้งาน",
    "credentials_missing": "ยังไม่ได้ตั้งค่าบัญชี MR.ERP",
    "erp_connection_failed": "เชื่อมต่อ MR.ERP ไม่สำเร็จ",
    "companion_offline": "โปรแกรมผู้ช่วย Express ออฟไลน์",
    "companion_not_ready": "โปรแกรมผู้ช่วย Express ยังไม่พร้อม",
    "profile_unconfirmed": "ยังไม่ได้ยืนยันชุดบัญชี Express",
    "profile_mismatch": "ชุดบัญชี Express ไม่ตรงกับที่ตั้งค่า",
    "endpoint_revoked": "การเชื่อมต่อ ERP ถูกยกเลิก",
    "erp_target_changed": "ERP ปลายทางมีการเปลี่ยนแปลง",
    "erp_user_inactive": "บัญชี ERP นี้ไม่สามารถใช้งานได้",
}


def status_text(result: dict[str, Any]) -> str:
    lines = []
    for target in result.get("targets") or []:
        marker = "✓" if target.get("ready") else "•"
        reason = (
            "พร้อมใช้งาน"
            if target.get("ready")
            else _THAI_REASONS.get(str(target.get("block_reason") or ""), "ยังไม่พร้อมใช้งาน")
        )
        selected = " · ปลายทาง" if target.get("selected") else ""
        lines.append(f"{marker} {target.get('label')}: {reason}{selected}")
    if not lines:
        reason = str(result.get("block_reason") or "no_default_endpoint")
        lines.append(f"• {_THAI_REASONS.get(reason, 'ยังไม่พร้อมใช้งาน')}")
    return "สถานะการเชื่อมต่อ ERP\n" + "\n".join(lines)


__all__ = ["TargetNotReady", "inspect_targets", "require_ready", "status_text"]
