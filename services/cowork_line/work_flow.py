"""Owner-only LINE work conversation, independent of ERP draft state."""

from __future__ import annotations

import asyncio
import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import parse_qs

from fastapi import HTTPException

from services.cowork_line import work_actions as actions, work_store, work_views as views
from services.cowork_line.work_cards import STATES, button, card, t
from services.line_platform import client as line
from services.work_bridge import line_owner as remote

logger = logging.getLogger(__name__)


from services.cowork_line.work_views import _buttons, _prompt, _choices


def _data(identity, state):
    data = remote.snapshot(identity, state.get("board", ""))
    if state.get("board"):
        shared = work_store.board_mapping(identity, state["board"])
        if shared:
            state.setdefault("mappings", {})[state["board"]] = shared
    if len(data.get("cards", [])) > 2000 or len(data.get("boards", [])) > 200:
        raise HTTPException(422, "work.limit")
    return data


def _home(identity, lang, state):
    state.pop("input", None)
    state["editing_draft"] = False
    data = _data(identity, state)
    if not state.get("board"):
        return views.no_board(lang, state, data)
    return views.home(lang, state, data)


def _command(identity, lang, state, command, params, event):
    if command == "language":
        return card(
            "th",
            t("th", "language"),
            [],
            [
                button(label, "edit_lang", state["nonce"], l=code)
                for code, label in (
                    ("th", "ไทย"),
                    ("zh", "中文"),
                    ("en", "English"),
                    ("ja", "日本語"),
                )
            ],
        )
    if command == "edit_lang":
        if params.get("l") not in {"th", "zh", "en", "ja"}:
            raise HTTPException(422, "work.invalid")
        state["editor_lang"] = params["l"]
        return views.draft(params["l"], state, _data(identity, state))
    if command == "editor":
        return views.draft(state.get("editor_lang", "th"), state, _data(identity, state))
    if command in {"home", "back"}:
        return _home(identity, lang, state)
    if command == "open":
        data = remote.snapshot(identity, params["b"])
        item = actions.task(data, params["id"])
        state.update(board=params["b"], task=params["id"])
        state.pop("input", None)
        return views.detail(lang, state, _data(identity, state), item)
    if command == "boards":
        state["list_mode"] = "boards"
        return _choices(lang, state, remote.snapshot(identity))
    if command == "board":
        remote.snapshot(identity, params["id"])
        state["board"] = params["id"]
        state.pop("task", None)
        return _home(identity, lang, state)
    if command == "create_board":
        state["input"] = "board_name"
        return _prompt(lang, state, "board_name", t(lang, "new_board_hint"))
    if command == "confirm_board":
        board, mapped = actions.create_board(
            identity, state["board_draft"]["title"], lang, state["board_draft"]["operation"]
        )
        state["board"] = board
        state.setdefault("mappings", {})[board] = mapped
        work_store.publish_mapping(identity, board, mapped)
        state.pop("board_draft", None)
        return _home(identity, lang, state)
    if command == "page":
        data = (
            {"team": remote.team(identity)}
            if state.get("list_mode") == "team"
            else (
                remote.snapshot(identity)
                if state.get("list_mode") == "boards"
                else _data(identity, state)
            )
        )
        return _choices(lang, state, data, int(params.get("p", 0)))
    if command in {"cancel", "discard"}:
        state.pop("input", None)
        state.pop("pending", None)
        if command == "discard":
            state.pop("draft", None)
        return _home(identity, lang, state)
    data = _data(identity, state)
    if not state.get("board"):
        state["list_mode"] = "boards"
        return _choices(lang, state, data)
    if command == "team":
        state["list_mode"] = "team"
        return _choices(lang, state, {"team": remote.team(identity)})
    if command == "member":
        person = next((x for x in remote.team(identity) if x["user_id"] == params["id"]), None)
        if not person:
            raise HTTPException(403, "work.person")
        state["member"] = {"id": params["id"], "operation": secrets.token_urlsafe(18)}
        return card(
            lang,
            t(lang, "team"),
            [data["board"]["title"], person["display_name"]],
            _buttons(lang, state, "add_member", "cancel"),
        )
    if command == "add_member":
        person = next(
            (x for x in remote.team(identity) if x["user_id"] == state["member"]["id"]), None
        )
        if not person:
            raise HTTPException(403, "work.person")
        remote.request(
            identity,
            "POST",
            f'/_pearnly/line/member/{state["board"]}',
            {"member": person},
            operation=state["member"]["operation"],
        )
        state.pop("member", None)
        return _home(identity, lang, state)
    if command == "setup":
        state.update(setup={}, list_mode="setup")
        return _choices(lang, state, data)
    if command == "map":
        if (
            params["id"] not in {x["_id"] for x in data["lists"]}
            or params["id"] in state["setup"].values()
        ):
            raise HTTPException(422, "work.invalid")
        state["setup"][STATES[len(state["setup"])]] = params["id"]
        if len(state["setup"]) == len(STATES):
            state.setdefault("mappings", {})[state["board"]] = state.pop("setup")
            work_store.publish_mapping(identity, state["board"], views.mapping(state))
            return _home(identity, lang, state)
        return _choices(lang, state, data)
    if command in {"new", "resume"}:
        if command == "new" and not state.get("draft"):
            if not views.mapping(state) or not data["lanes"]:
                state.update(setup={}, list_mode="setup")
                return _choices(lang, state, data)
            state["draft"] = {"boardId": state["board"], "operation": secrets.token_urlsafe(18)}
            state["editing_draft"] = True
            state["input"] = "title"
            return _prompt(lang, state, "title")
        if not state.get("draft"):
            return _home(identity, lang, state)
        state["board"] = state["draft"]["boardId"]
        return views.draft(lang, state, _data(identity, state))
    if command in {"all", "attention"} or command in STATES or command == "overdue":
        state.update(filter=command, person="", search="", list_mode="tasks")
        if command == "all":
            return card(
                lang,
                t(lang, "all"),
                [],
                _buttons(
                    lang,
                    state,
                    "pending",
                    "doing",
                    "blocked",
                    "review",
                    "done",
                    *(("cancelled",) if state.get("work_role") != "employee" else ()),
                    "overdue",
                )
                + [button(t(lang, "all"), "list", state["nonce"])]
                + _buttons(lang, state, "back"),
            )
        return _choices(lang, state, data)
    if command == "list":
        state.update(list_mode="tasks", filter="all")
        return _choices(lang, state, data)
    if command in {"people", "assignee"}:
        state["list_mode"] = command
        return _choices(lang, state, data)
    if command == "person":
        if params["id"] not in views.people(data):
            raise HTTPException(403, "work.person")
        if state["list_mode"] == "assignee":
            state["draft"]["assignees"] = [params["id"]]
            return views.draft(lang, state, data)
        state.update(person=params["id"], list_mode="tasks")
        return _choices(lang, state, data)
    if command == "search":
        state["input"] = "search"
        return _prompt(lang, state, "search")
    if command in {"task", "detail"}:
        state["task"] = params["id"]
        state.pop("input", None)
        return views.detail(lang, state, data, actions.task(data, state["task"]))
    if command == "edit":
        if state.get("draft"):
            state["board"] = state["draft"]["boardId"]
            return views.draft(lang, state, _data(identity, state))
        original = actions.task(data, state["task"])
        state["draft"] = {**original, "operation": secrets.token_urlsafe(18)}
        return views.draft(lang, state, data)
    if command == "field":
        field = params["f"]
        if field not in {"title", "description", "due"}:
            raise HTTPException(422, "work.invalid")
        if field == "due":
            raw = event.get("postback", {}).get("params", {}).get("datetime", "")
            value = datetime.strptime(raw, "%Y-%m-%dT%H:%M").replace(tzinfo=views.ZONE)
            state["draft"]["dueAt"] = (
                value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            return views.draft(lang, state, data)
        state["input"] = field
        return _prompt(lang, state, field)
    if command == "save":
        if not state.get("draft", {}).get("title") or not state["draft"].get("assignees"):
            return card(lang, t(lang, "required"), [], _buttons(lang, state, "resume", "back"))
        ident = actions.save(identity, state, data)
        state.pop("draft", None)
        state["task"] = ident
        data = _data(identity, state)
        item = actions.task(data, ident)
        notice = actions.notify(identity, item, data, lang)
        result = views.detail(lang, state, data, item)
        result["text"] = (
            result["text"][:4800] + "\n" + t(lang, "saved" if notice else "notification_failed")
        )
        return result
    if command == "attachment":
        state["input"] = "attachment_draft" if state.get("editing_draft") else "attachment_task"
        return _prompt(lang, state, "attachment", t(lang, "upload"))
    item = actions.task(data, state["task"])
    if command in {"history", "files"}:
        page = max(0, min(99999, int(params.get("p", 0))))
        records = remote.request(
            identity,
            "GET",
            f'/_pearnly/line/records/{state["board"]}/{item["_id"]}/{command}/{page}',
        )
        buttons = []
        if command == "files":
            buttons = [
                {
                    "type": "button",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": x["name"][:40],
                        "uri": remote.file_url(identity, state["board"], item["_id"], x["_id"]),
                    },
                }
                for x in records["items"]
            ]
        if page:
            buttons.append(button(t(lang, "previous"), command, state["nonce"], p=page - 1))
        if records["more"]:
            buttons.append(button(t(lang, "next"), command, state["nonce"], p=page + 1))
        buttons.append(button(t(lang, "back"), "detail", state["nonce"], id=item["_id"]))
        lines = [x.get("text", "") for x in records["items"]] if command == "history" else []
        return card(
            lang,
            t(lang, command),
            lines or ([t(lang, "empty")] if not records["items"] else []),
            buttons,
        )
    if command == "status":
        return card(
            lang,
            item["title"],
            [],
            [
                button(t(lang, key), "set_status", state["nonce"], s=key)
                for key in ("pending", "doing", "blocked", "review")
            ]
            + _buttons(lang, state, "back"),
        )
    if command in {"comment", "return", "stop", "accept", "set_status"}:
        if command == "accept" and views.state_of(item, views.mapping(state)) != "review":
            raise HTTPException(409, "work.task_changed")
        target = {"accept": "done", "return": "doing", "stop": "cancelled"}.get(
            command, params.get("s", "")
        )
        if target and target not in STATES:
            raise HTTPException(422, "work.invalid")
        state["pending"] = {
            "command": command,
            "target": target,
            "task": item["_id"],
            "modifiedAt": item.get("modifiedAt"),
            "operation": secrets.token_urlsafe(18),
        }
        if command in {"comment", "return", "stop"}:
            state["input"] = "reason"
            return _prompt(lang, state, "reason")
        return card(
            lang,
            item["title"],
            [t(lang, target)],
            [button(t(lang, "confirm"), "apply", state["nonce"])] + _buttons(lang, state, "cancel"),
        )
    if command == "apply":
        pending = state["pending"]
        item = actions.task(data, pending["task"])
        if item.get("modifiedAt") != pending["modifiedAt"]:
            raise HTTPException(409, "work.task_changed")
        operation = pending["operation"]
        if pending.get("reason"):
            remote.mutate(
                identity,
                "POST",
                f'/api/boards/{state["board"]}/cards/{item["_id"]}/comments',
                {"comment": pending["reason"]},
                operation + "-comment",
            )
        if pending["target"]:
            remote.mutate(
                identity,
                "PUT",
                actions.path(item),
                {"listId": views.mapping(state)[pending["target"]]},
                operation + "-move",
            )
        fresh = _data(identity, state)
        confirmed = actions.task(fresh, item["_id"])
        if pending["target"] and confirmed["listId"] != views.mapping(state)[pending["target"]]:
            raise HTTPException(409, "work.readback_mismatch")
        state.pop("pending", None)
        notice = actions.notify(identity, confirmed, fresh, "th")
        result = views.detail("th", state, fresh, confirmed)
        if not notice:
            result["text"] = result["text"][:4800] + "\n" + t("th", "notification_failed")
        return result
    raise HTTPException(422, "work.invalid")


def _input(identity, lang, state, event):
    message = event.get("message", {})
    field = state.get("input")
    if field in {"attachment_draft", "attachment_task"} and message.get("type") in {
        "image",
        "file",
    }:
        if int(message.get("fileSize") or 0) > 10 * 1024 * 1024:
            raise HTTPException(422, "work.invalid")
        attachment = {"message_id": message["id"], "name": message.get("fileName") or "image.jpg"}
        if field == "attachment_draft":
            files = state["draft"].setdefault("attachments", [])
            if len(files) >= 5:
                raise HTTPException(422, "work.invalid")
            if attachment not in files:
                files.append(attachment)
            state.pop("input", None)
            return views.draft(lang, state, _data(identity, state))
        item = actions.task(_data(identity, state), state["task"])
        actions.attach(identity, item, attachment, "attachment-" + message["id"])
        state.pop("input", None)
        return views.detail(lang, state, _data(identity, state), item)
    text = str(message.get("text") or "").strip()
    if (
        message.get("type") != "text"
        or not text
        or len(text) > (1000 if field in {"title", "board_name"} else 4000)
    ):
        raise HTTPException(422, "work.invalid")
    if field == "board_name":
        state["board_draft"] = {"title": text, "operation": secrets.token_urlsafe(18)}
        state.pop("input", None)
        return card(
            lang,
            text,
            [t(lang, "new_board_hint")],
            [button(t(lang, "confirm"), "confirm_board", state["nonce"])]
            + _buttons(lang, state, "cancel"),
        )
    if field in {"title", "description"}:
        state["draft"][field] = text
        state.pop("input", None)
        return views.draft(lang, state, _data(identity, state))
    if field == "search":
        state.update(search=text, person="", filter="all", list_mode="tasks")
        state.pop("input", None)
        return _choices(lang, state, _data(identity, state))
    if field == "reason":
        state["pending"]["reason"] = text
        state.pop("input", None)
        return card(
            lang,
            t(lang, "reason"),
            [text],
            [button(t(lang, "confirm"), "apply", state["nonce"])] + _buttons(lang, state, "cancel"),
        )
    return _home(identity, lang, state)


def process(event, identity, lang):
    lang = "th"
    parsed = parse_qs(event.get("postback", {}).get("data", ""))
    params = {k: v[0] for k, v in parsed.items()}
    work = params.get("a") == "work"
    menu = event.get("message", {}).get("text", "").strip().lower() in {
        "menu",
        "菜单",
        "菜單",
        "เมนู",
        "メニュー",
    }
    with work_store.conversation(identity) as state:
        if not work and (event.get("type") == "postback" or menu):
            state["active"] = False
            return None
        if not work and (not state.get("active") or event.get("type") != "message"):
            return None
        try:
            current = remote.actor(identity)
            if (
                work
                and params.get("c") not in {"home", "open"}
                and params.get("n") != state.get("nonce")
            ):
                return {"type": "text", "text": t(lang, "expired")}
            state["work_role"] = current["work_role"]
            state["active"] = True
            state["lang"] = lang
            state["nonce"] = secrets.token_urlsafe(12)
            if current["work_role"] == "employee":
                from services.cowork_line import work_employee

                return work_employee.process(
                    identity, state, params if work else None, event, current
                )
            if work:
                return _command(identity, lang, state, params.get("c", "home"), params, event)
            return _input(identity, lang, state, event)
        except Exception as exc:
            logger.warning("LINE work operation failed: %s", type(exc).__name__)
            status = getattr(exc, "status_code", None)
            key = (
                "forbidden"
                if status == 403
                else (
                    "limit"
                    if getattr(exc, "detail", "") == "work.limit"
                    else "invalid" if status == 422 or isinstance(exc, ValueError) else "failed"
                )
            )
            return card(
                lang,
                t(lang, "home"),
                [t(lang, key)],
                (
                    _buttons(lang, state, "back")
                    if state.get("work_role") == "employee"
                    else _buttons(lang, state, "back", "resume")
                ),
            )


async def handle(event, identity, lang):
    response = await asyncio.to_thread(process, event, identity, lang)
    if response is None:
        return False
    if event.get("replyToken"):
        await asyncio.to_thread(
            line.reply_messages, event["replyToken"], [response], channel="cowork"
        )
    return True
