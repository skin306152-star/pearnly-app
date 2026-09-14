"""Read-only live LINE board, backed by fresh native task snapshots."""

import hashlib
import json
import time

import jwt
from fastapi import HTTPException

from services.cowork_line import identity_store, work_invites, work_store, work_views
from services.work_bridge import line_owner

AUDIENCE = "cowork-line-live"


def url(board=""):
    return work_invites.url("live", board)


def entry(board=""):
    return {"type": "button", "action": {"type": "uri", "label": "ภาพรวมงานสด", "uri": url(board)}}


def authenticate(token):
    profile = work_invites.claims(token)
    identity = identity_store.resolve_active_identity(profile["sub"])
    if not identity:
        raise HTTPException(403, "work.line_binding_required")
    line_owner.actor(identity)
    now = int(time.time())
    return {
        "token": jwt.encode(
            {"identity": identity, "aud": AUDIENCE, "iat": now, "exp": now + 1200},
            line_owner.service().secret,
            algorithm="HS256",
        ),
        "expires_in": 1200,
    }


def read(token, board=""):
    try:
        payload = jwt.decode(
            token,
            line_owner.service().secret,
            algorithms=["HS256"],
            audience=AUDIENCE,
            options={"require": ["exp", "iat", "aud", "identity"]},
        )
        identity = payload["identity"]
    except (jwt.PyJWTError, KeyError, TypeError):
        raise HTTPException(401, "work.live_session_expired") from None
    actor = line_owner.actor(identity)
    catalog = line_owner.snapshot(identity)
    boards = catalog.get("boards", [])
    if len(boards) > 200:
        raise HTTPException(422, "work.limit")
    if board and board not in {x["_id"] for x in boards}:
        raise HTTPException(403, "work.board_forbidden")
    selected = board or (boards[0]["_id"] if boards else "")
    tasks = []
    mapping = {}
    if selected:
        data = line_owner.snapshot(identity, selected)
        if len(data["cards"]) > 2000:
            raise HTTPException(422, "work.limit")
        mapping = work_store.board_mapping(identity, selected)
        names = work_views.people(data)
        lists = {x["_id"]: x["title"] for x in data["lists"]}
        for task in data["cards"]:
            status = work_views.state_of(task, mapping)
            tasks.append(
                {
                    "id": task["_id"],
                    "title": task["title"],
                    "description": task.get("description", ""),
                    "status": status or "other",
                    "status_label": (
                        work_views.t("th", status) if status else lists.get(task["listId"], "—")
                    ),
                    "assignees": [names.get(x, "—") for x in task.get("assignees", [])],
                    "due": work_views.due(task.get("dueAt")),
                    "overdue": work_views.overdue(task, mapping),
                    "updated_at": task.get("modifiedAt"),
                    "latest_comment": next(
                        (
                            x.get("text", "")
                            for x in data.get("comments", [])
                            if x.get("cardId") == task["_id"]
                        ),
                        "",
                    ),
                }
            )
    result = {
        "role": actor["work_role"],
        "boards": boards,
        "board": selected,
        "tasks": tasks,
        "mapping_ready": bool(mapping.get("done")),
    }
    result["version"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, default=str).encode()
    ).hexdigest()
    return result
