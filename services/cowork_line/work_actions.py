"""Native task writes with explicit operation keys and readback."""

import base64
import mimetypes
from datetime import datetime

from fastapi import HTTPException

from core import db
from services.cowork_line.work_cards import STATES, t
from services.line_platform import client as line
from services.work_bridge import line_owner as remote


def task(data, ident):
    found = next((x for x in data["cards"] if x["_id"] == ident), None)
    if not found:
        raise HTTPException(404, "work.task_missing")
    return found


def path(item):
    return f'/api/boards/{item["boardId"]}/lists/{item["listId"]}/cards/{item["_id"]}'


def create_board(identity, name, lang, operation):
    result = remote.mutate(
        identity, "POST", "/api/boards", {"title": name, "permission": "private"}, operation
    )
    board = result["_id"]
    mapping = {}
    for key in STATES:
        created = remote.mutate(
            identity,
            "POST",
            f"/api/boards/{board}/lists",
            {"title": t(lang, key)},
            operation + "-" + key,
        )
        mapping[key] = created["_id"]
    return board, mapping


def attach(identity, item, attachment, operation):
    content = line.download_message_content(attachment["message_id"], channel="cowork")
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(422, "work.attachment_unavailable")
    return remote.request(
        identity,
        "POST",
        f'/_pearnly/line/attachments/{item["boardId"]}/{item["_id"]}',
        {
            "data": base64.b64encode(content).decode(),
            "name": attachment["name"],
            "type": mimetypes.guess_type(attachment["name"])[0] or "application/octet-stream",
        },
        operation=operation,
    )


def save(identity, state, data):
    draft = state["draft"]
    if draft["boardId"] != state["board"]:
        raise HTTPException(409, "work.board_changed")
    operation = draft["operation"]
    body = {
        "title": draft["title"],
        "description": draft.get("description") or " ",
        "assignees": draft["assignees"],
        "dueAt": draft.get("dueAt") or None,
    }
    if draft.get("written_id"):
        ident = draft["written_id"]
    elif draft.get("_id"):
        original = task(data, draft["_id"])
        if original.get("modifiedAt") != draft.get("modifiedAt"):
            raise HTTPException(409, "work.task_changed")
        remote.mutate(identity, "PUT", path(original), body, operation)
        ident = original["_id"]
    else:
        mapping = state["mappings"][state["board"]]
        body["swimlaneId"] = data["lanes"][0]["_id"]
        body["authorId"] = data["userId"]
        result = remote.mutate(
            identity,
            "POST",
            f'/api/boards/{state["board"]}/lists/{mapping["pending"]}/cards',
            body,
            operation,
        )
        ident = result["_id"]
    draft["written_id"] = ident
    fresh = remote.snapshot(identity, state["board"])
    item = task(fresh, ident)
    # Some native versions accept due dates only on PUT, so ensure the final value.
    if (
        item["title"] != body["title"]
        or (item.get("description") or "").strip() != body["description"].strip()
        or set(item.get("assignees", [])) != set(body["assignees"])
    ):
        raise HTTPException(409, "work.readback_mismatch")

    def date_value(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None

    if date_value(item.get("dueAt")) != date_value(body.get("dueAt")):
        if draft.get("due_done"):
            raise HTTPException(409, "work.task_changed")
        remote.mutate(identity, "PUT", path(item), {"dueAt": body["dueAt"]}, operation + "-due")
        item = task(remote.snapshot(identity, state["board"]), ident)
        if date_value(item.get("dueAt")) != date_value(body.get("dueAt")):
            raise HTTPException(409, "work.readback_mismatch")
    draft["due_done"] = True
    for index, attachment in enumerate(draft.get("attachments", [])):
        attach(identity, item, attachment, operation + "-file-" + str(index))
    return ident


def notify(identity, item, data, lang):
    users = [
        p["user_id"]
        for p in data["people"]
        if p["_id"] in item.get("assignees", []) and p.get("user_id")
    ]
    users = [user for user in users if user != identity["user_id"]]
    if not users:
        return not any(x != data["userId"] for x in item.get("assignees", []))
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT i.line_user_id FROM cowork_line_identities i "
            "JOIN memberships m ON m.id=i.membership_id JOIN users u ON u.id=m.user_id "
            "WHERE i.tenant_id=%s AND i.user_id::text=ANY(%s) AND i.revoked_at IS NULL "
            "AND m.status='active' AND u.is_active=TRUE",
            (identity["tenant_id"], users),
        )
        recipients = [r["line_user_id"] for r in cur.fetchall()]
    ok = len(recipients) == len(users)
    for recipient in recipients:
        ok = (
            line.push_messages(
                recipient,
                [
                    {
                        "type": "text",
                        "text": f'{t(lang, "notification")}\n{data["board"]["title"]}\n{item["title"]}\n{item.get("description") or ""}'[
                            :4900
                        ],
                    }
                ],
                channel="cowork",
            )
            and ok
        )
    return ok
