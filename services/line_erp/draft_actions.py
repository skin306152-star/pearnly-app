"""ERP LINE staged-draft confirmation and discard actions."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from core import db
from services.erp import team_access
from services.intake_bridge import convert as convert_svc
from services.line_erp import push as line_push, store, target_preflight
from services.line_platform import client as line_client

CHANNEL = "erp"


class BatchIncomplete(Exception):
    def __init__(self, result):
        self.result = result


async def act_draft(
    binding: dict,
    line_user_id: str,
    reply_token: str | None,
    history_id: str,
    action: str,
    *,
    confirm_action: Callable[..., Awaitable[dict[str, Any]]],
    discard_action: Callable[..., Awaitable[dict[str, Any]]],
    feature_enabled: Callable[[Any, Any], bool],
) -> dict[str, Any]:
    if not history_id:
        return {"ok": False, "status": 409, "detail": "line_erp.draft_empty"}
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    payload = session.get("payload") or {}
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    if not history_ids and payload.get("history_id"):
        history_ids = [str(payload["history_id"])]
    if not history_ids:
        return {"ok": False, "status": 409, "detail": "line_erp.draft_empty"}
    if session.get("state") not in ("draft", "editing") or history_id not in history_ids:
        if reply_token:
            line_client.reply_text(
                reply_token, "รายการหมดอายุ กรุณาเปิดรายการใหม่", channel=CHANNEL
            )
        return {"ok": False, "status": 409, "detail": "line_erp.draft_expired"}
    mode = str(payload.get("mode") or "")
    if not team_access.mode_allowed(str(binding["tenant_id"]), str(binding["user_id"]), mode):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = db.find_user_by_id(binding["user_id"])
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding["tenant_id"])
        or not feature_enabled(binding.get("tenant_id"), binding.get("user_id"))
    ):
        return {"ok": False, "status": 403, "detail": "line_erp.draft_forbidden"}
    user = dict(user)
    user["entry"] = "erp"
    if action == "discard":
        result = await discard_action(binding, history_ids)
        if not result["ok"]:
            if reply_token:
                line_client.reply_text(
                    reply_token,
                    "ทิ้งเอกสารไม่สำเร็จ กรุณาลองใหม่",
                    channel=CHANNEL,
                )
            return result
        text = "ทิ้งเอกสารเรียบร้อยแล้ว"
    else:
        result = await confirm_action(
            binding,
            user,
            history_id,
            history_ids,
            reply_token,
            mode,
            str(payload.get("endpoint_id") or ""),
        )
        if not result["ok"]:
            return result
        text = (
            "บันทึกเอกสารและส่งคำสั่งไป ERP แล้ว"
            if result.get("push_ok")
            else "บันทึกเอกสารแล้ว แต่ส่ง ERP ไม่สำเร็จ กรุณาตรวจสอบประวัติการส่ง"
        )
    store.clear_session(binding["tenant_id"], line_user_id)
    if reply_token:
        line_client.reply_text(reply_token, text, channel=CHANNEL)
    response = {"ok": True, "action": action, "history_ids": history_ids}
    if action != "discard":
        response.update(
            {
                "push_ok": bool(result.get("push_ok")),
                "push_results": list(result.get("push_results") or []),
            }
        )
    return response


async def discard(binding: dict, history_ids: list[str]) -> dict[str, Any]:
    from core.db import get_cursor_rls
    from services.ocr import pdf_storage
    from services.ocr_history.staged import discard_staged_ocr_history_with_pdf_paths

    deleted, pdf_paths = await asyncio.to_thread(
        discard_staged_ocr_history_with_pdf_paths,
        str(binding["user_id"]),
        history_ids,
        tenant_id=binding["tenant_id"],
    )
    if deleted != len(history_ids):
        return {"ok": False, "status": 409, "detail": "line_erp.discard_incomplete"}
    for path in set(pdf_paths or []):
        with get_cursor_rls(bypass=True) as cur:
            cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (path,))
            still_used = cur.fetchone() is not None
        if not still_used:
            pdf_storage.delete_pdf(path)
    return {"ok": True}


async def confirm(
    binding: dict,
    user: dict,
    draft_id: str,
    history_ids: list[str],
    reply_token: str | None,
    mode: str,
    endpoint_id: str,
    *,
    records_loader: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    records = records_loader(
        str(binding["user_id"]), str(binding["tenant_id"]), draft_id, history_ids
    )
    from services.line_platform.draft_validation import batch_issues

    if batch_issues(records, mode, require_posting_kind=True):
        text = "กรุณาแก้ไขและเลือกประเภทสินค้า stock หรือบริการ service ให้ครบก่อนยืนยัน"
        if reply_token:
            line_client.reply_text(reply_token, text, channel=CHANNEL)
        return {"ok": False, "status": 409, "detail": "line_erp.posting_kind_required"}
    try:
        readiness = await asyncio.to_thread(
            target_preflight.require_ready,
            binding,
            refresh=True,
            expected_endpoint_id=endpoint_id or None,
        )
    except target_preflight.TargetNotReady as exc:
        if reply_token:
            line_client.reply_text(
                reply_token,
                target_preflight.status_text(exc.result),
                channel=CHANNEL,
            )
        return {"ok": False, "status": 409, "detail": "line_erp.target_not_ready"}
    try:
        with db.get_cursor_rls(
            binding["tenant_id"], user_id=str(binding["user_id"]), commit=True
        ) as cur:
            result = convert_svc.convert_histories(
                cur,
                tenant_id=binding["tenant_id"],
                user_id=str(binding["user_id"]),
                history_ids=history_ids,
            )
            converted_ids = {str(row.get("history_id")) for row in result.get("converted") or []}
            already_ids = {
                str(row.get("history_id"))
                for row in result.get("skipped") or []
                if row.get("reason") == "already_converted"
            }
            if set(history_ids) - (converted_ids | already_ids):
                raise BatchIncomplete(result)
            cur.execute(
                "UPDATE ocr_history SET staged = FALSE, updated_at = NOW() "
                "WHERE id = ANY(%s::uuid[]) AND tenant_id = %s::uuid "
                "AND user_id = %s::uuid AND staged = TRUE",
                (history_ids, str(binding["tenant_id"]), str(binding["user_id"])),
            )
            cur.execute(
                "SELECT count(*) AS n FROM ocr_history WHERE id = ANY(%s::uuid[]) "
                "AND tenant_id = %s::uuid AND user_id = %s::uuid AND staged = FALSE",
                (history_ids, str(binding["tenant_id"]), str(binding["user_id"])),
            )
            if int((cur.fetchone() or {}).get("n") or 0) != len(set(history_ids)):
                raise BatchIncomplete(result)
    except BatchIncomplete as exc:
        if reply_token:
            line_client.reply_text(
                reply_token,
                "ยืนยันไม่สำเร็จ เอกสารยังไม่ถูกบันทึก กรุณาตรวจสอบรายการ",
                channel=CHANNEL,
            )
        return {
            "ok": False,
            "status": 409,
            "detail": "line_erp.confirm_incomplete",
            "result": exc.result,
        }
    return await line_push.dispatch_confirmed(
        user=user,
        binding=binding,
        history_ids=history_ids,
        endpoint_id=str(readiness["endpoint_id"]),
    )


__all__ = ["BatchIncomplete", "act_draft", "confirm", "discard"]
