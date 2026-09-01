"""ERP target catalogue and selection checks for the dedicated LINE channel."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from core import db
from services.erp import line_target_projection, target_readiness, team_access
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


def _workspace_rows(
    cur, tenant_id: str, allowed_workspace_id: int | None = None
) -> list[dict[str, Any]]:
    params: list[Any] = [tenant_id]
    where = "tenant_id = %s AND is_active = TRUE"
    if allowed_workspace_id is not None:
        where += " AND id = %s"
        params.append(int(allowed_workspace_id))
    cur.execute(
        f"SELECT id, name, erp_endpoint_id FROM workspace_clients WHERE {where} ORDER BY name, id",
        tuple(params),
    )
    return [dict(row) for row in (cur.fetchall() or [])]


def _owner_endpoint_rows(cur, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, name, adapter, config, is_default, auto_push, enabled,
               user_id, tenant_id, workspace_client_id, shared_scope,
               binding_generation, bound_account_set, bound_profile_key,
               live_account_set, live_profile_key, agent_last_seen_at,
               agent_version, revoked_at, clock_timestamp() AS server_now
        FROM erp_endpoints
        WHERE (
                user_id = %s AND binding_generation = 0
                AND adapter IN ('mrerp', 'express')
                AND (tenant_id IS NULL OR tenant_id = %s)
              )
           OR (
                tenant_id = %s AND binding_generation > 0
                AND shared_scope = TRUE AND adapter = 'express'
              )
        ORDER BY adapter, is_default DESC, created_at, id
        """,
        (user_id, tenant_id, tenant_id),
    )
    return [dict(row) for row in (cur.fetchall() or [])]


def _project_member_target(
    endpoint: dict[str, Any],
    workspace: dict[str, Any] | None,
    *,
    refresh: bool,
    managed_state: tuple[bool, bool] = (False, False),
) -> list[dict[str, Any]]:
    if workspace is None:
        return []
    adapter = str(endpoint.get("adapter") or "").lower()
    if adapter == "express" and int(endpoint.get("binding_generation") or 0) > 0:
        cloud_in_flight, waiting_lock = managed_state
        return [
            line_target_projection.managed_target(
                endpoint,
                workspace,
                cloud_in_flight=cloud_in_flight,
                waiting_lock=waiting_lock,
            )
        ]
    probe = target_readiness.probe_endpoint(endpoint, refresh=refresh)
    return [
        line_target_projection.legacy_target(
            endpoint,
            workspace,
            binding_count=1,
            probe=probe,
        )
    ]


def _project_owner_targets(
    endpoints: list[dict[str, Any]],
    workspaces: list[dict[str, Any]],
    *,
    refresh: bool,
    managed_states: dict[str, tuple[bool, bool]],
) -> list[dict[str, Any]]:
    by_endpoint: dict[str, list[dict[str, Any]]] = {}
    for workspace in workspaces:
        endpoint_id = str(workspace.get("erp_endpoint_id") or "")
        if endpoint_id:
            by_endpoint.setdefault(endpoint_id, []).append(workspace)
    targets: list[dict[str, Any]] = []
    for endpoint in endpoints:
        endpoint_id = str(endpoint.get("id") or "")
        adapter = str(endpoint.get("adapter") or "").lower()
        bindings = by_endpoint.get(endpoint_id, [])
        managed = adapter == "express" and int(endpoint.get("binding_generation") or 0) > 0
        if managed:
            workspace = next(
                (
                    row
                    for row in bindings
                    if int(row["id"]) == int(endpoint.get("workspace_client_id") or 0)
                ),
                None,
            )
            if workspace is not None:
                in_flight, waiting_lock = managed_states.get(endpoint_id, (False, False))
                targets.append(
                    line_target_projection.managed_target(
                        endpoint,
                        workspace,
                        duplicate=len(bindings) != 1,
                        cloud_in_flight=in_flight,
                        waiting_lock=waiting_lock,
                    )
                )
            continue
        probe = target_readiness.probe_endpoint(endpoint, refresh=refresh)
        if bindings:
            targets.extend(
                line_target_projection.legacy_target(
                    endpoint,
                    workspace,
                    binding_count=len(bindings),
                    probe=probe,
                )
                for workspace in bindings
            )
        else:
            targets.append(
                line_target_projection.legacy_target(
                    endpoint,
                    None,
                    binding_count=0,
                    probe=probe,
                )
            )
    return targets


def _project_targets(
    binding: dict[str, Any], *, refresh: bool = False, lock_endpoint_id: str | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    user = _active_user(binding)
    assigned = team_access.assigned_push_endpoint(user)
    tenant_id = str(binding.get("tenant_id") or "")
    user_id = str(binding.get("user_id") or "")
    access = team_access.access_for_user(tenant_id, user_id) or {}
    is_owner = bool(
        user.get("is_super_admin")
        or str(user.get("role") or "").lower() == "owner"
        or access.get("is_owner")
    )
    allowed_workspace = None if is_owner else access.get("workspace_client_id")
    assigned_target: tuple[dict[str, Any], dict[str, Any] | None] | None = None
    endpoint_rows: list[dict[str, Any]] = []
    managed_states: dict[str, tuple[bool, bool]] = {}
    with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
        if lock_endpoint_id:
            lock_endpoint_binding(cur, lock_endpoint_id)
        workspaces = _workspace_rows(cur, tenant_id, allowed_workspace)
        if assigned is not None:
            workspace_id = assigned.get("assigned_workspace_client_id") or allowed_workspace
            workspace = next(
                (row for row in workspaces if int(row["id"]) == int(workspace_id or 0)), None
            )
            assigned_target = (assigned, workspace)
            endpoints = {str(assigned.get("id") or ""): assigned}
            if (
                str(assigned.get("adapter") or "").lower() == "express"
                and int(assigned.get("binding_generation") or 0) > 0
            ):
                endpoint_id = str(assigned.get("id") or "")
                managed_states[endpoint_id] = line_target_projection.active_push_state(
                    cur, endpoint_id
                )
        else:
            endpoint_rows = _owner_endpoint_rows(cur, user_id, tenant_id)
            for endpoint in endpoint_rows:
                endpoint_id = str(endpoint.get("id") or "")
                if (
                    str(endpoint.get("adapter") or "").lower() == "express"
                    and int(endpoint.get("binding_generation") or 0) > 0
                ):
                    managed_states[endpoint_id] = line_target_projection.active_push_state(
                        cur, endpoint_id
                    )
            endpoints = {str(row.get("id") or ""): row for row in endpoint_rows}
    if assigned_target is not None:
        assigned_endpoint_id = str(assigned_target[0].get("id") or "")
        targets = _project_member_target(
            *assigned_target,
            refresh=refresh,
            managed_state=managed_states.get(assigned_endpoint_id, (False, False)),
        )
    else:
        targets = _project_owner_targets(
            endpoint_rows,
            workspaces,
            refresh=refresh,
            managed_states=managed_states,
        )
    targets.sort(
        key=lambda row: (
            str(row.get("workspace_name") or "").casefold(),
            str(row.get("adapter") or ""),
            str(row.get("label") or "").casefold(),
        )
    )
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
