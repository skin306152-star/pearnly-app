"""Employee LINE actions; the native service independently enforces assignment."""

from fastapi import HTTPException

from services.cowork_line import work_views as views

READ_COMMANDS = {
    "home",
    "back",
    "boards",
    "board",
    "page",
    "cancel",
    "open",
    "all",
    "list",
    "pending",
    "doing",
    "blocked",
    "review",
    "done",
    "overdue",
    "search",
    "task",
    "detail",
    "history",
    "files",
}
WRITE_COMMANDS = {"comment", "attachment", "set_status", "apply"}


def process(identity, state, params, event, actor):
    from services.cowork_line import work_flow

    state["work_role"] = "employee"
    state["readonly"] = actor.get("work_readonly", False)
    state.pop("draft", None)
    state["editing_draft"] = False
    if params is None:
        if state.get("input") not in {"search", "reason", "attachment_task", None}:
            state.pop("input", None)
        if state["readonly"] and state.get("input") in {"reason", "attachment_task"}:
            raise HTTPException(403, "work.employee_readonly")
        return work_flow._input(identity, "th", state, event)
    command = params.get("c", "home")
    if command not in READ_COMMANDS | WRITE_COMMANDS:
        raise HTTPException(403, "work.employee_action")
    if command in WRITE_COMMANDS:
        if state["readonly"]:
            raise HTTPException(403, "work.employee_readonly")
        data = work_flow._data(identity, state)
        item = work_flow.actions.task(data, state.get("task"))
        if views.state_of(item, views.mapping(state)) in {"done", "cancelled"}:
            raise HTTPException(409, "work.task_closed")
        target = (
            params.get("s") if command == "set_status" else state.get("pending", {}).get("target")
        )
        if target and target not in {"doing", "blocked", "review"}:
            raise HTTPException(403, "work.employee_action")
    return work_flow._command(identity, "th", state, command, params, event)
