"""ERP LINE uses internal workspaces and the same records service as the web."""

from __future__ import annotations

import asyncio
import secrets
from services.sales.dates import bangkok_today
from uuid import uuid4

from fastapi import HTTPException

from core import db
from services.erp import internal_records, team_access
from services.authz.deps import check_workspace_scope
from services.line_erp import cards, store
from services.line_platform import client


def actor(binding):
    user = db.find_user_by_id(str(binding["user_id"]))
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding["tenant_id"])
    ):
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    user = {**user, "entry": "erp"}
    team_access.require_active_erp_user(user)
    return user


def selection(binding, payload):
    user = actor(binding)
    workspace_id = payload.get("workspace_client_id") or binding.get("workspace_client_id")
    direction = payload.get("mode") or payload.get("direction")
    if not workspace_id:
        raise HTTPException(409, detail="line_erp.workspace_required")
    internal_records.authorize(user, int(workspace_id), direction)
    with db.get_cursor_rls(str(binding["tenant_id"]), user_id=str(binding["user_id"])) as cur:
        subject = internal_records.workspace(cur, user, int(workspace_id))
    return user, {
        "mode": direction,
        "direction": direction,
        "workspace_client_id": int(workspace_id),
        "target_label": subject["name"],
        "internal_only": True,
    }


def notify(line_user_id, reply_token, messages):
    if reply_token:
        client.reply_messages(reply_token, messages, channel="erp")
    else:
        client.push_messages(line_user_id, messages, channel="erp")


async def begin_mode(binding, line_user_id, reply_token, mode):
    current = store.get_session(binding["tenant_id"], line_user_id) or {}
    if current.get("state") in {"draft", "editing"}:
        await remind_draft(binding, line_user_id, reply_token, current)
        return
    if current.get("state") == "ocr_processing":
        notify(
            line_user_id,
            reply_token,
            [{"type": "text", "text": "กำลังอ่านเอกสารอยู่ กรุณารอสักครู่"}],
        )
        return
    try:
        _, payload = await asyncio.to_thread(selection, binding, {"mode": mode})
    except HTTPException:
        user = await asyncio.to_thread(actor, binding)
        with db.get_cursor_rls(str(binding["tenant_id"]), user_id=str(binding["user_id"])) as cur:
            cur.execute(
                "SELECT id, name FROM workspace_clients WHERE tenant_id=%s::uuid AND is_active=TRUE ORDER BY name",
                (str(binding["tenant_id"]),),
            )
            rows = cur.fetchall()
        choices = []
        for row in rows:
            try:
                check_workspace_scope(None, user, row["id"])
            except HTTPException:
                continue
            choices.append(
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": str(row["name"])[:20],
                        "data": f"a=internal-workspace&mode={mode}&workspace={row['id']}",
                    },
                }
            )
        store.set_session(binding["tenant_id"], line_user_id, "workspace", {"mode": mode})
        text = "เลือกบริษัทที่ต้องการบันทึกครับ" if choices else "กรุณาสร้างบริษัทใน Pearnly ก่อนครับ"
        message = {"type": "text", "text": text}
        if choices:
            message["quickReply"] = {"items": choices[:13]}
        notify(line_user_id, reply_token, [message])
        return
    await offer_methods(binding, line_user_id, reply_token, payload)


async def offer_methods(binding, line_user_id, reply_token, payload):
    _, payload = await asyncio.to_thread(selection, binding, payload)
    payload = {**payload, "manual_history_id": str(uuid4())}
    store.set_session(binding["tenant_id"], line_user_id, "receiving", payload)
    notify(
        line_user_id,
        reply_token,
        [
            {
                "type": "text",
                "text": f"{payload['target_label']} · เลือกวิธีบันทึกครับ",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "uri",
                                "label": "กรอกเอง",
                                "uri": cards.edit_uri(payload["manual_history_id"]),
                            },
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "อัปโหลดเอกสาร",
                                "data": "a=internal-upload",
                            },
                        },
                    ]
                },
            }
        ],
    )


async def manual(binding, line_user_id, reply_token):
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    if session.get("state") in {"draft", "editing"}:
        await remind_draft(binding, line_user_id, reply_token, session)
        return
    if session.get("state") != "receiving":
        raise HTTPException(409, detail="line_erp.draft_expired")
    user, payload = await asyncio.to_thread(selection, binding, session.get("payload") or {})
    history_id = (session.get("payload") or {}).get("manual_history_id") or str(uuid4())
    store.set_session(
        binding["tenant_id"],
        line_user_id,
        "receiving",
        {**payload, "manual_history_id": history_id},
    )
    await create_manual(binding, line_user_id, history_id)
    notify(
        line_user_id,
        reply_token,
        [
            {
                "type": "text",
                "text": "กรอกข้อมูลแล้วกดบันทึกครับ",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "uri",
                                "label": "กรอกเอง",
                                "uri": cards.edit_uri(history_id),
                            },
                        }
                    ]
                },
            }
        ],
    )


async def create_manual(binding, line_user_id, history_id):
    """Materialize a reserved manual draft only after authenticated editor entry."""
    session = store.get_session(binding["tenant_id"], line_user_id) or {}
    current = session.get("payload") or {}
    if session.get("state") in {"draft", "editing"} and history_id in current.get(
        "history_ids", []
    ):
        return
    if session.get("state") != "receiving" or current.get("manual_history_id") != history_id:
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    user, payload = await asyncio.to_thread(selection, binding, current)
    await asyncio.to_thread(
        internal_records.save_draft,
        user,
        history_id=history_id,
        workspace_id=payload["workspace_client_id"],
        direction=payload["direction"],
        fields={
            "date": bangkok_today().isoformat(),
            "invoice_number": "",
            "seller_name": "",
            "buyer_name": "",
            "seller_tax": "",
            "buyer_tax": "",
            "notes": "",
            "items": [],
        },
        source="line_erp",
    )
    store.set_session(
        binding["tenant_id"],
        line_user_id,
        "draft",
        {
            **payload,
            "history_ids": [history_id],
            "nonce": secrets.token_urlsafe(24),
        },
    )


async def remind_draft(binding, line_user_id, reply_token, session=None):
    from services.line_erp import draft_view

    session = session or store.get_session(binding["tenant_id"], line_user_id) or {}
    session = await asyncio.to_thread(refresh_draft_selection, binding, line_user_id, session)
    payload = session.get("payload") or {}
    ids = [str(value) for value in payload.get("history_ids") or []]
    if not ids:
        return
    records = await asyncio.to_thread(
        draft_view.records, str(binding["user_id"]), str(binding["tenant_id"]), ids[0], ids
    )
    fields = (records[0].get("pages") or [{}])[0].get("fields") or {}
    card = cards.preview_card(
        ids[0],
        payload.get("mode"),
        fields,
        target={"label": payload.get("target_label")},
        posting_mode="",
        record_count=len(ids),
        item_count=sum(
            len((record.get("pages") or [{}])[0].get("fields", {}).get("items") or [])
            for record in records
        ),
    )
    if records[0].get("filename") == "manual" and not fields.get("items"):
        card["contents"]["footer"]["contents"].pop(0)
    notify(line_user_id, reply_token, [card])


def recognized_selection(binding, payload, history_ids):
    """Use OCR's persisted subject assignment, never the pre-upload workspace."""
    from services.ocr_history.queries import get_ocr_history_detail

    workspace_ids = set()
    for history_id in history_ids:
        record = get_ocr_history_detail(
            str(binding["user_id"]), str(history_id), tenant_id=str(binding["tenant_id"])
        )
        if not record or not record.get("workspace_client_id"):
            raise HTTPException(409, detail="line_erp.workspace_required")
        workspace_ids.add(int(record["workspace_client_id"]))
    if len(workspace_ids) != 1:
        raise HTTPException(409, detail="line_erp.multiple_workspaces")
    _, resolved = selection(binding, {**payload, "workspace_client_id": workspace_ids.pop()})
    return resolved


def refresh_draft_selection(binding, line_user_id, session):
    """Repair pending sessions created before OCR workspace handoff was fixed."""
    payload = session.get("payload") or {}
    ids = payload.get("history_ids") or []
    if session.get("state") not in {"draft", "editing"} or not ids:
        return session
    resolved = recognized_selection(binding, payload, ids)
    if resolved["workspace_client_id"] != payload.get("workspace_client_id"):
        payload = {**payload, **resolved}
        store.set_session(binding["tenant_id"], line_user_id, session["state"], payload)
        return {**session, "payload": payload}
    return session
