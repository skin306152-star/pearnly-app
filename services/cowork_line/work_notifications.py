"""Native status changes notify subscribed owners with stable LINE retry keys."""

import json
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

import httpx
from fastapi import HTTPException

from core import db
from services.cowork_line import work_views as views
from services.cowork_line.work_cards import button, card, t
from services.line_platform import client as line
from services.work_bridge import line_owner as remote

TABLE = """
CREATE TABLE IF NOT EXISTS cowork_line_work_notifications (
    tenant_id uuid NOT NULL REFERENCES tenants(id),
    membership_id uuid NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
    event_id text NOT NULL,
    payload jsonb NOT NULL,
    first_at timestamptz NOT NULL DEFAULT now(),
    completed boolean NOT NULL DEFAULT false,
    PRIMARY KEY (tenant_id, membership_id, event_id)
)
"""


def push(recipient, message, retry_key):
    token = line._get_channel_token("cowork")
    if not token:
        raise HTTPException(503, "work.notification_unavailable")
    response = httpx.post(
        "https://api.line.me/v2/bot/message/push",
        timeout=10,
        headers={"Authorization": "Bearer " + token, "X-Line-Retry-Key": retry_key},
        json={"to": recipient, "messages": [message]},
    )
    if response.status_code == 409 and response.headers.get("x-line-accepted-request-id"):
        return
    if response.status_code >= 400:
        raise HTTPException(503, "work.notification_failed")


def deliver(board_id, card_id, event_id, list_id):
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT s.tenant_id::text, s.membership_id::text, s.payload, "
            "i.user_id::text, i.line_user_id FROM cowork_line_work_sessions s "
            "JOIN cowork_line_identities i ON i.membership_id=s.membership_id "
            "AND i.tenant_id=s.tenant_id WHERE i.revoked_at IS NULL "
            "AND s.payload->'mappings' ? %s",
            (board_id,),
        )
        recipients = cur.fetchall()
    for row in recipients:
        identity = {k: row[k] for k in ("tenant_id", "membership_id", "user_id", "line_user_id")}
        try:
            data = remote.snapshot(identity, board_id)
        except HTTPException as exc:
            if exc.status_code in {401, 403, 404}:
                continue
            raise
        task = next((x for x in data["cards"] if x["_id"] == card_id), None)
        state = {**row["payload"], "board": board_id}
        if (
            not task
            or task["listId"] != list_id
            or views.state_of(task, views.mapping(state)) not in {"review", "blocked"}
        ):
            continue
        lang = "th"
        message = card(
            lang,
            t(lang, "attention"),
            [
                data["board"]["title"],
                task["title"],
                t(lang, views.state_of(task, views.mapping(state))),
            ],
            [button(t(lang, "attention"), "open", b=board_id, id=card_id)],
        )
        key = (row["tenant_id"], row["membership_id"], event_id)
        with db.get_cursor_rls(row["tenant_id"], commit=True) as cur:
            cur.execute(
                "INSERT INTO cowork_line_work_notifications "
                "(tenant_id,membership_id,event_id,payload) VALUES (%s,%s,%s,%s::jsonb) "
                "ON CONFLICT DO NOTHING",
                (*key, json.dumps(message)),
            )
        with db.get_cursor_rls(row["tenant_id"], commit=True) as cur:
            cur.execute(
                "SELECT payload,first_at,completed FROM cowork_line_work_notifications "
                "WHERE tenant_id=%s AND membership_id=%s AND event_id=%s FOR UPDATE",
                key,
            )
            receipt = cur.fetchone()
            if receipt["completed"]:
                continue
            if receipt["first_at"] > datetime.now(timezone.utc) - timedelta(hours=23):
                remote.owner(identity)
                push(
                    row["line_user_id"],
                    receipt["payload"],
                    str(uuid5(NAMESPACE_URL, "pearnly-work:" + ":".join(key))),
                )
            cur.execute(
                "UPDATE cowork_line_work_notifications SET completed=true "
                "WHERE tenant_id=%s AND membership_id=%s AND event_id=%s",
                key,
            )
    return {"ok": True}
