"""ERP target catalogue and selection checks for the dedicated LINE channel."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from core import db
from services.authz.resolver import resolve
from services.erp import line_target_catalog, team_access
from services.erp.legacy_generation import lock_endpoint_binding


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


def _project_targets(
    binding: dict[str, Any], *, refresh: bool = False, lock_endpoint_id: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    user = _active_user(binding)
    tenant_id = str(binding.get("tenant_id") or "")
    user_id = str(binding.get("user_id") or "")
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        if lock_endpoint_id:
            lock_endpoint_binding(cur, lock_endpoint_id)
        authz = resolve(user, cur=cur)
        if not authz.has("erp.endpoint.view") or not authz.has("erp.push.operate"):
            raise TargetNotReady({"ready": False, "block_reason": "erp_user_inactive"})
        targets, legacy_specs = line_target_catalog.collect_target_specs(cur, user, authz)
    targets = line_target_catalog.project_legacy_targets(
        targets,
        legacy_specs,
        refresh_probes=refresh,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    endpoints = {str(endpoint.get("id") or ""): endpoint for endpoint, *_ in legacy_specs}
    return user, targets, endpoints


def inspect_targets(
    binding: dict[str, Any],
    *,
    refresh: bool = False,
    endpoint_id: str | None = None,
    workspace_client_id: int | None = None,
    expected_endpoint_id: str | None = None,
    expected_workspace_client_id: int | None = None,
) -> dict[str, Any]:
    selected_endpoint = str(endpoint_id or expected_endpoint_id or "").strip()
    selected_workspace = (
        workspace_client_id if workspace_client_id is not None else expected_workspace_client_id
    )
    user, targets, endpoints = _project_targets(
        binding,
        refresh=refresh,
        lock_endpoint_id=selected_endpoint or None,
    )
    matches = [target for target in targets if target["endpoint_id"] == selected_endpoint]
    if selected_workspace is not None:
        matches = [
            target
            for target in matches
            if target.get("workspace_client_id") == int(selected_workspace)
        ]
    selected = matches[0] if len(matches) == 1 else None
    for target in targets:
        target["selected"] = target is selected
    if selected_endpoint and not matches:
        block_reason = "erp_target_changed"
    elif selected_endpoint and len(matches) != 1:
        block_reason = "erp_target_ambiguous"
    elif selected and not selected.get("selectable"):
        block_reason = str(selected.get("block_reason") or "erp_target_not_ready")
    elif selected is None:
        block_reason = "erp_target_required"
    else:
        block_reason = None
    return {
        "ready": block_reason is None,
        "any_ready": any(target.get("selectable") for target in targets),
        "block_reason": block_reason,
        "endpoint_id": selected_endpoint or None,
        "workspace_client_id": selected.get("workspace_client_id") if selected else None,
        "endpoint": endpoints.get(selected_endpoint) if selected else None,
        "target": selected,
        "user": user,
        "targets": targets,
    }


def require_ready(
    binding: dict[str, Any],
    *,
    endpoint_id: str | None = None,
    workspace_client_id: int | None = None,
    refresh: bool = False,
    expected_endpoint_id: str | None = None,
    expected_workspace_client_id: int | None = None,
) -> dict[str, Any]:
    result = inspect_targets(
        binding,
        refresh=refresh,
        endpoint_id=endpoint_id,
        workspace_client_id=workspace_client_id,
        expected_endpoint_id=expected_endpoint_id,
        expected_workspace_client_id=expected_workspace_client_id,
    )
    if not result["ready"]:
        raise TargetNotReady(result)
    return result


_THAI_REASONS = {
    "erp_target_required": "กรุณาเลือกบัญชีและ ERP ปลายทาง",
    "erp_target_ambiguous": "ERP ปลายทางนี้ผูกกับหลายบัญชี กรุณาเลือกบัญชีให้ชัดเจน",
    "endpoint_disabled": "ERP ปลายทางถูกปิดใช้งาน",
    "credentials_missing": "ยังไม่ได้ตั้งค่าบัญชี MR.ERP",
    "erp_connection_failed": "เชื่อมต่อ MR.ERP ไม่สำเร็จ",
    "companion_offline": "โปรแกรมผู้ช่วย Express ออฟไลน์",
    "companion_not_ready": "โปรแกรมผู้ช่วย Express ยังไม่พร้อม",
    "profile_unconfirmed": "ยังไม่ได้ยืนยันชุดบัญชี Express",
    "profile_mismatch": "ชุดบัญชี Express ไม่ตรงกับที่ตั้งค่า",
    "account_set_unavailable": "ไม่พบชุดบัญชี MR.ERP ที่ตั้งค่าไว้",
    "workspace_unbound": "ยังไม่ได้ผูกบัญชี Pearnly กับ ERP นี้",
    "workspace_binding_conflict": "ERP นี้ถูกผูกกับหลายบัญชี",
    "account_set_locked": "ชุดบัญชี Express กำลังถูกใช้งาน",
    "endpoint_revoked": "การเชื่อมต่อ ERP ถูกยกเลิก",
    "erp_target_changed": "ERP ปลายทางมีการเปลี่ยนแปลง",
    "erp_user_inactive": "บัญชี ERP นี้ไม่สามารถใช้งานได้",
}


def status_text(result: dict[str, Any]) -> str:
    lines = []
    targets = result.get("targets") or []
    visible_targets = targets[:6]
    for target in visible_targets:
        marker = "✓" if target.get("selectable") else "•"
        reason = (
            "พร้อมใช้งาน"
            if target.get("selectable")
            else _THAI_REASONS.get(str(target.get("block_reason") or ""), "ยังไม่พร้อมใช้งาน")
        )
        selected = " · ปลายทางที่เลือก" if target.get("selected") else ""
        workspace = str(target.get("workspace_name") or "").strip()
        label = str(target.get("label") or target.get("adapter") or "ERP")
        lines.append(
            f"{marker} {workspace + ' · ' if workspace else ''}{label}: {reason}{selected}"
        )
    remaining = len(targets) - len(visible_targets)
    if remaining > 0:
        lines.append(f"• มีอีก {remaining} ปลายทาง กรุณาเลือกในหน้าถัดไป")
    if not lines:
        reason = str(result.get("block_reason") or "erp_target_required")
        lines.append(f"• {_THAI_REASONS.get(reason, 'ยังไม่พร้อมใช้งาน')}")
    return "สถานะการเชื่อมต่อ ERP\n" + "\n".join(lines)


__all__ = ["TargetNotReady", "inspect_targets", "require_ready", "status_text"]
