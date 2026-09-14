"""Render owner task state into bounded native LINE cards."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.cowork_line.work_cards import STATES, button, card, edit_button, t

ZONE = ZoneInfo("Asia/Bangkok")


def due(value):
    if not value:
        return "—"
    try:
        return (
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(ZONE)
            .strftime("%Y-%m-%d %H:%M")
        )
    except (ValueError, AttributeError):
        return str(value)


def state_of(task, mapping):
    return next((key for key, value in mapping.items() if value == task.get("listId")), "")


def overdue(task, mapping):
    if state_of(task, mapping) in {"done", "cancelled"} or not task.get("dueAt"):
        return False
    return datetime.fromisoformat(task["dueAt"].replace("Z", "+00:00")) < datetime.now(timezone.utc)


def mapping(state):
    return state.get("mappings", {}).get(state.get("board"), {})


def people(data):
    return {p["_id"]: p["name"] for p in data.get("people", [])}


def task_lines(lang, task, data, state):
    names = people(data)
    status = state_of(task, mapping(state))
    list_name = next((x["title"] for x in data["lists"] if x["_id"] == task.get("listId")), "—")
    return [
        data["board"]["title"],
        t(lang, status) if status else list_name,
        t(lang, "assignee") + ": " + ", ".join(names.get(x, x) for x in task.get("assignees", [])),
        t(lang, "due") + ": " + due(task.get("dueAt")),
        task.get("description") or "—",
    ]


def paged(lang, state, title, items, command, *, page=0, extras=()):
    page = max(0, min(page, max(0, (len(items) - 1) // 6)))
    nonce = state["nonce"]
    buttons = [
        button(label, command, nonce, id=ident) for ident, label in items[page * 6 : page * 6 + 6]
    ]
    if page:
        buttons.append(button(t(lang, "previous"), "page", nonce, p=page - 1))
    if (page + 1) * 6 < len(items):
        buttons.append(button(t(lang, "next"), "page", nonce, p=page + 1))
    buttons.extend(extras)
    buttons.append(button(t(lang, "back"), "home", nonce))
    return card(
        lang,
        title,
        [f"{page + 1} / {max(1, (len(items) + 5) // 6)}" if items else t(lang, "empty")],
        buttons,
    )


def home(lang, state, data):
    nonce = state["nonce"]
    counts = {key: sum(state_of(x, mapping(state)) == key for x in data["cards"]) for key in STATES}
    lines = [
        data["board"]["title"],
        f'{t(lang, "review")}: {counts["review"]} · {t(lang, "blocked")}: {counts["blocked"]}',
        f'{t(lang, "overdue")}: {sum(overdue(x, mapping(state)) for x in data["cards"])}',
    ]
    buttons = [button(t(lang, key), key, nonce) for key in ("new", "attention", "all")]
    if state.get("draft"):
        buttons.append(button(t(lang, "resume"), "resume", nonce))
    buttons.extend(button(t(lang, key), key, nonce) for key in ("boards", "team", "setup"))
    return card(lang, t(lang, "home"), lines, buttons)


def draft(lang, state, data):
    lang = state.get("editor_lang", "th")
    state["editing_draft"] = True
    item = state["draft"]
    nonce = state["nonce"]
    task = {
        "title": item.get("title"),
        "description": item.get("description"),
        "assignees": item.get("assignees", []),
        "dueAt": item.get("dueAt"),
    }
    buttons = [edit_button(lang, key, nonce, item.get(key, "")) for key in ("title", "description")]
    buttons.extend(
        [
            button(t(lang, "assignee"), "assignee", nonce),
            edit_button(lang, "due", nonce),
            button(t(lang, "attachment"), "attachment", nonce),
            button(t(lang, "language"), "language", nonce),
            button(t(lang, "confirm" if item.get("_id") else "dispatch"), "save", nonce),
            button(t(lang, "edit"), "editor", nonce),
            button(t(lang, "cancel"), "discard", nonce),
            button(t(lang, "back"), "home", nonce),
        ]
    )
    return card(
        lang,
        task.get("title") or t("th", "new"),
        task_lines("th", task, data, state)[2:]
        + [f'{t("th", "attachment")}: {len(item.get("attachments", []))}'],
        buttons,
    )


def detail(lang, state, data, task):
    state["editing_draft"] = False
    nonce = state["nonce"]
    keys = ["edit", "comment", "history", "attachment", "files"]
    if state_of(task, mapping(state)) == "review":
        keys += ["accept", "return"]
    keys += ["status", "stop", "back"]
    return card(
        lang,
        task["title"],
        task_lines(lang, task, data, state),
        [button(t(lang, key), "home" if key == "back" else key, nonce) for key in keys],
    )


def _buttons(lang, state, *keys):
    return [button(t(lang, key), "home" if key == "back" else key, state["nonce"]) for key in keys]


def _prompt(lang, state, key, text=""):
    return card(
        lang, t(lang, key), [text or t(lang, "input")], _buttons(lang, state, "cancel", "back")
    )


def _choices(lang, state, data, page=0):
    mode = state.get("list_mode", "tasks")
    if mode == "team":
        return paged(
            lang,
            state,
            t(lang, "team"),
            [(x["user_id"], x["display_name"]) for x in data["team"]],
            "member",
            page=page,
        )
    if mode == "boards":
        return paged(
            lang,
            state,
            t(lang, "boards"),
            [(x["_id"], x["title"]) for x in data["boards"]],
            "board",
            page=page,
            extras=_buttons(lang, state, "create_board", "resume"),
        )
    if mode in {"assignee", "people"}:
        return paged(
            lang,
            state,
            t(lang, mode),
            [(x["_id"], x["name"]) for x in data["people"]],
            "person",
            page=page,
        )
    if mode == "setup":
        key = STATES[len(state.get("setup", {}))]
        return paged(
            lang,
            state,
            t(lang, key) + " · " + t(lang, "setup_hint"),
            [
                (x["_id"], x["title"])
                for x in data["lists"]
                if x["_id"] not in state.get("setup", {}).values()
            ],
            "map",
            page=page,
        )
    selected = []
    for item in data["cards"]:
        status = state_of(item, mapping(state))
        filter_key = state.get("filter", "all")
        if filter_key == "attention" and status not in {"review", "blocked"}:
            continue
        if filter_key == "overdue" and not overdue(item, mapping(state)):
            continue
        if filter_key in STATES and status != filter_key:
            continue
        if state.get("person") and state["person"] not in item.get("assignees", []):
            continue
        if state.get("search", "").casefold() not in item["title"].casefold():
            continue
        selected.append((item["_id"], item["title"]))
    return paged(
        lang,
        state,
        t(lang, "all"),
        selected,
        "task",
        page=page,
        extras=_buttons(lang, state, "search", "people"),
    )
