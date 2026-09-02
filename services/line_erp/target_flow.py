"""Interactive LINE steps for selecting one exact ERP destination."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.feature_flags import erp_target_projection_enabled_for
from services.erp import target_refresh, team_access
from services.line_erp import flow, selection_messages, store, target_preflight, target_selection
from services.line_platform import client as line_client

CHANNEL = "erp"
logger = logging.getLogger(__name__)


def _notify(line_user_id: str, reply_token: str | None, text: str) -> None:
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    else:
        line_client.push_text(line_user_id, text, channel=CHANNEL)


def _send_message(line_user_id: str, reply_token: str | None, message: dict) -> None:
    if reply_token:
        line_client.reply_messages(reply_token, [message], channel=CHANNEL)
    else:
        line_client.push_messages(line_user_id, [message], channel=CHANNEL)


def _locked(session: dict[str, Any]) -> bool:
    return session.get("state") in {"draft", "editing"}


async def _run_mrerp_refresh(request_id: str) -> None:
    try:
        await asyncio.to_thread(target_refresh.process_mrerp_request, request_id)
    except Exception:
        logger.exception("MR.ERP background refresh failed: %s", request_id[:8])


async def _request_master_refresh(
    binding: dict[str, Any], target: dict[str, Any], *, account_set_key: str | None = None
) -> dict[str, Any] | None:
    adapter = str(target.get("adapter") or "").lower()
    selected_key = str(account_set_key or target.get("selected_account_key") or "").strip()
    try:
        request = await asyncio.to_thread(
            target_refresh.request_refresh,
            tenant_id=str(binding["tenant_id"]),
            user_id=str(binding["user_id"]),
            endpoint_id=str(target["endpoint_id"]),
            account_set_key=selected_key,
            adapter=adapter,
        )
    except Exception:
        logger.exception(
            "ERP target refresh request failed: %s", str(target.get("endpoint_id"))[:8]
        )
        return None
    if adapter == "mrerp":
        asyncio.create_task(_run_mrerp_refresh(str(request["request_id"])))
    return request


async def _account_catalog_state(binding: dict[str, Any], refreshes: list[dict[str, Any]]) -> str:
    statuses = []
    for refresh in refreshes:
        state = await asyncio.to_thread(
            target_refresh.refresh_status,
            refresh.get("request_id"),
            tenant_id=str(binding["tenant_id"]),
            endpoint_id=str(refresh.get("endpoint_id") or ""),
        )
        statuses.append(str((state or {}).get("status") or "failed"))
    if statuses and all(status == "succeeded" for status in statuses):
        return "succeeded"
    if any(status == "failed" for status in statuses):
        return "failed"
    return "pending"


async def _start_account_catalog_refresh(
    binding: dict[str, Any], targets: list[dict[str, Any]], adapter: str
) -> list[dict[str, Any]] | None:
    refreshes = []
    seen: set[str] = set()
    for target in targets:
        endpoint_id = str(target.get("endpoint_id") or "")
        if (
            str(target.get("adapter") or "").lower() != adapter
            or not target.get("selectable")
            or not target.get("supports_master_refresh")
            or not endpoint_id
            or endpoint_id in seen
        ):
            continue
        seen.add(endpoint_id)
        request = await _request_master_refresh(
            binding,
            target,
            account_set_key=target_refresh.ENDPOINT_SCOPE_KEY,
        )
        if request is None:
            return None
        refreshes.append(
            {
                "request_id": request["request_id"],
                "endpoint_id": endpoint_id,
                "adapter": adapter,
            }
        )
    return refreshes


async def _inspect_targets(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    *,
    refresh: bool = True,
) -> dict[str, Any] | None:
    try:
        return await asyncio.to_thread(target_preflight.inspect_targets, binding, refresh=refresh)
    except target_preflight.TargetNotReady as exc:
        _notify(line_user_id, reply_token, target_preflight.status_text(exc.result))
    except Exception:
        _notify(line_user_id, reply_token, "ไม่สามารถตรวจสอบ ERP ได้ กรุณาลองใหม่")
    return None


async def show_target_picker(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    mode: str,
) -> None:
    allowed = team_access.binding_line_modes(binding)
    if mode not in flow.MODES or mode not in allowed:
        _notify(line_user_id, reply_token, "บัญชีนี้ไม่มีสิทธิ์สำหรับรายการนี้")
        return
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing" or _locked(session):
        _notify(line_user_id, reply_token, "รายการปัจจุบันยังไม่เสร็จ กรุณาดำเนินการให้เรียบร้อย")
        return
    result = await _inspect_targets(binding, line_user_id, reply_token, refresh=False)
    if result is None:
        return
    store.set_session(binding["tenant_id"], line_user_id, "target", {"mode": mode})
    _send_message(
        line_user_id,
        reply_token,
        selection_messages.erp_picker_message(result.get("targets") or [], mode),
    )


async def show_account_picker(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    mode: str,
    adapter: str,
    *,
    page: int = 0,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    payload = dict(session.get("payload") or {})
    session_mode = str(payload.get("mode") or "")
    adapter = str(adapter or "").lower()
    if (
        session.get("state") != "target"
        or mode != session_mode
        or mode not in team_access.binding_line_modes(binding)
        or adapter not in {"mrerp", "express"}
    ):
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือกประเภทเอกสารใหม่")
        return
    result = await _inspect_targets(binding, line_user_id, reply_token, refresh=False)
    if result is None:
        return
    targets = result.get("targets") or []
    if not any(str(target.get("adapter") or "").lower() == adapter for target in targets):
        _notify(line_user_id, reply_token, "ERP ปลายทางมีการเปลี่ยนแปลง กรุณาเลือกใหม่")
        return
    refreshes = payload.get("account_catalog_refreshes")
    projection_enabled = await asyncio.to_thread(
        erp_target_projection_enabled_for,
        str(binding["tenant_id"]),
        str(binding["user_id"]),
    )
    projection_enabled = projection_enabled and any(
        str(target.get("adapter") or "").lower() == adapter
        and target.get("selectable")
        and target.get("supports_master_refresh")
        for target in targets
    )
    if projection_enabled and isinstance(refreshes, list) and refreshes:
        refresh_state = await _account_catalog_state(binding, refreshes)
        if refresh_state != "succeeded":
            failed = refresh_state == "failed"
            if failed:
                store.set_session(
                    binding["tenant_id"],
                    line_user_id,
                    "target",
                    {"mode": mode, "adapter": adapter},
                )
            _send_message(
                line_user_id,
                reply_token,
                selection_messages.account_refresh_message(adapter, mode, failed=failed),
            )
            return
    elif projection_enabled:
        refreshes = await _start_account_catalog_refresh(binding, targets, adapter)
        if refreshes is None or not refreshes:
            _notify(line_user_id, reply_token, "ไม่สามารถอัปเดตรายการบัญชี ERP ได้ กรุณาลองใหม่")
            return
        store.set_session(
            binding["tenant_id"],
            line_user_id,
            "target",
            {"mode": mode, "adapter": adapter, "account_catalog_refreshes": refreshes},
        )
        _send_message(
            line_user_id,
            reply_token,
            selection_messages.account_refresh_message(adapter, mode),
        )
        return
    next_payload = {"mode": mode, "adapter": adapter}
    if refreshes:
        next_payload["account_catalog_refreshes"] = refreshes
    store.set_session(binding["tenant_id"], line_user_id, "target", next_payload)
    _send_message(
        line_user_id,
        reply_token,
        selection_messages.account_picker_message(targets, adapter, mode, page=page),
    )


async def begin_mode(
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
    mode: str,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") == "ocr_processing":
        _notify(line_user_id, reply_token, "กำลังอ่านเอกสารอยู่ กรุณารอผลการตรวจสอบสักครู่")
        return
    if _locked(session):
        _notify(
            line_user_id,
            reply_token,
            "กรุณายืนยัน แก้ไข หรือทิ้งเอกสารปัจจุบันก่อนเริ่มรายการใหม่",
        )
        return
    try:
        await show_target_picker(binding, line_user_id, reply_token, mode)
    except target_preflight.TargetNotReady as exc:
        _notify(line_user_id, reply_token, target_preflight.status_text(exc.result))
    except Exception:
        _notify(line_user_id, reply_token, "ไม่สามารถตรวจสอบ ERP ได้ กรุณาลองใหม่")


async def choose_target(
    params: dict[str, list[str]],
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    session_payload = dict(session.get("payload") or {})
    session_mode = str(session_payload.get("mode") or "")
    session_adapter = str(session_payload.get("adapter") or "").lower()
    mode = str((params.get("mode") or [session_mode])[0])
    if (
        session.get("state") != "target"
        or mode != session_mode
        or mode not in team_access.binding_line_modes(binding)
    ):
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือกประเภทเอกสารใหม่")
        return
    endpoint_id = str((params.get("endpoint") or [""])[0]).strip()
    raw_workspace = str((params.get("workspace") or [""])[0]).strip()
    try:
        workspace_id = int(raw_workspace) if raw_workspace else None
    except ValueError:
        _notify(line_user_id, reply_token, "กรุณาเลือกบัญชีและ ERP ใหม่")
        return
    try:
        readiness = await asyncio.to_thread(
            target_preflight.require_ready,
            binding,
            endpoint_id=endpoint_id,
            workspace_client_id=workspace_id,
            refresh=False,
        )
    except target_preflight.TargetNotReady as exc:
        _notify(line_user_id, reply_token, target_preflight.status_text(exc.result))
        return
    target = readiness["target"]
    target_adapter = str(target.get("adapter") or "").lower()
    if session_adapter and target_adapter != session_adapter:
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือก ERP ใหม่")
        return
    account_ref = str((params.get("account") or [""])[0]).strip()
    account_choices = [
        account
        for account in target.get("account_choices") or []
        if isinstance(account, dict) and account.get("writable") is not False
    ]
    if account_ref:
        account = next(
            (
                choice
                for choice in account_choices
                if selection_messages.account_reference(choice.get("key")) == account_ref
            ),
            None,
        )
    else:
        selected_key = str(target.get("selected_account_key") or "")
        account = next(
            (choice for choice in account_choices if str(choice.get("key") or "") == selected_key),
            None,
        )
    if account is None:
        _notify(line_user_id, reply_token, "ชุดบัญชีมีการเปลี่ยนแปลง กรุณาเลือกใหม่")
        return
    account_key = str(account["key"])
    account_label = str(account.get("label") or account_key)
    selected_target = {
        **target,
        "selected_account_key": account_key,
        "account_set_label": account_label,
        "label": " · ".join(
            value
            for value in (
                str(target.get("connection_label") or "").strip(),
                account_label,
            )
            if value
        ),
    }
    projection_enabled = await asyncio.to_thread(
        erp_target_projection_enabled_for,
        str(binding["tenant_id"]),
        str(binding["user_id"]),
    )
    refresh_required = projection_enabled and bool(selected_target.get("supports_master_refresh"))
    refresh_request = (
        await _request_master_refresh(binding, selected_target) if refresh_required else None
    )
    if refresh_required and refresh_request is None:
        _notify(
            line_user_id,
            reply_token,
            "ไม่สามารถเตรียมข้อมูล ERP ล่าสุดได้ กรุณาลองเลือกใหม่",
        )
        return
    payload = {
        "mode": mode,
        "direction": mode,
        "endpoint_id": str(target["endpoint_id"]),
        "workspace_client_id": target.get("workspace_client_id"),
        "adapter": target_adapter,
        "target_label": str(selected_target.get("label") or "")[:200],
        "account_root": str(account.get("root_key") or "").strip() or None,
        "account_set": account_key,
        "account_set_label": account_label[:200],
    }
    if refresh_request:
        payload["master_refresh_request_id"] = refresh_request["request_id"]
        payload["master_refresh_status"] = refresh_request["status"]
    store.set_session(binding["tenant_id"], line_user_id, "posting", payload)
    _send_message(
        line_user_id,
        reply_token,
        selection_messages.posting_mode_message(mode, selected_target),
    )


async def choose_posting_mode(
    value: str,
    binding: dict[str, Any],
    line_user_id: str,
    reply_token: str | None,
) -> None:
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") != "posting":
        _notify(line_user_id, reply_token, "รายการหมดอายุ กรุณาเลือกประเภทเอกสารใหม่")
        return
    requested = dict(session.get("payload") or {})
    field = "posting_kind" if requested.get("adapter") == "express" else "payment"
    requested[field] = value
    try:
        _, selection = await asyncio.to_thread(
            target_selection.normalize,
            binding,
            requested,
            refresh=False,
        )
    except target_selection.SelectionError as exc:
        text = (
            target_preflight.status_text(exc.readiness)
            if exc.readiness
            else "รูปแบบการบันทึกไม่ถูกต้อง กรุณาเลือกใหม่"
        )
        _notify(line_user_id, reply_token, text)
        return
    store.set_session(binding["tenant_id"], line_user_id, "receiving", selection)
    _notify(line_user_id, reply_token, "กรุณาส่งรูปภาพหรือ PDF")


__all__ = [
    "begin_mode",
    "choose_posting_mode",
    "choose_target",
    "show_account_picker",
    "show_target_picker",
]
