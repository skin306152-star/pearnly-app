# -*- coding: utf-8 -*-
"""Permission-gated, compact LINE flow for fresh DMS sales queries."""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from services.cloud_tasks import dispatch as cloud_dispatch
from services.erp import mrerp_dms_sales_readback as sales_readback
from services.line_dms import _out, cards, query_access, query_cards, store
from services.line_dms._out import _CHANNEL, _push, _reply, _send, _thr
from services.line_platform import client as line_client

QUERY_ACTIONS = frozenset(
    {
        cards.ACT_MENU_QUERY,
        query_cards.ACT_QUERY_TYPE,
        query_cards.ACT_QUERY_DIMENSION,
        query_cards.ACT_QUERY_STATUS,
        query_cards.ACT_QUERY_TOP_GROUP,
        query_cards.ACT_QUERY_TOP_METRIC,
        query_cards.ACT_QUERY_TOP_PERIOD,
        query_cards.ACT_QUERY_PAGE,
    }
)

_TEXT_FIELDS = frozenset(
    {
        "advisor",
        "vehicle",
        "customer",
        "color",
        "booking_date",
        "delivery_date",
        "sales_doc_no",
        "engine_no",
    }
)
_DATE_RE = re.compile(r"^(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})\s+(\d{1,2})$")
_spawn = _out.make_spawn("line_dms.query_flow")


async def _can_query(binding: dict) -> bool:
    return bool(await _thr(query_access.can_query, binding))


async def open_query(
    binding: dict,
    line_user_id: str,
    reply_token: str,
) -> None:
    if not await _can_query(binding):
        _reply(reply_token, query_cards.TXT_DENIED)
        return
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "query_menu", {})
    _send(line_user_id, query_cards.query_type_message(), reply_token)


async def handle_postback(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    action: str,
    values: dict,
    sess: Optional[dict],
) -> None:
    if action == cards.ACT_MENU_QUERY:
        await open_query(binding, line_user_id, reply_token)
        return
    if not await _can_query(binding):
        _reply(reply_token, query_cards.TXT_DENIED)
        return
    if action == query_cards.ACT_QUERY_TYPE:
        await _pick_type(binding, line_user_id, reply_token, values.get("kind") or "")
    elif action == query_cards.ACT_QUERY_DIMENSION:
        await _pick_dimension(binding, line_user_id, reply_token, values.get("dimension") or "")
    elif action == query_cards.ACT_QUERY_STATUS:
        await _begin_records(
            binding,
            line_user_id,
            status=values.get("status") or "active",
            reply_token=reply_token,
        )
    elif action == query_cards.ACT_QUERY_TOP_GROUP:
        await _pick_top_group(binding, line_user_id, reply_token, values.get("group") or "model")
    elif action == query_cards.ACT_QUERY_TOP_METRIC:
        await _pick_top_metric(
            binding, line_user_id, reply_token, sess, values.get("metric") or "quantity"
        )
    elif action == query_cards.ACT_QUERY_TOP_PERIOD:
        await _pick_top_period(binding, line_user_id, reply_token, sess, values)
    elif action == query_cards.ACT_QUERY_PAGE:
        await _paginate(binding, line_user_id, reply_token, sess, values)


async def handle_text(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    text: str,
) -> bool:
    state = (sess or {}).get("state")
    if state not in {"query_sales_input", "query_top_custom"}:
        return False
    if not await _can_query(binding):
        _reply(reply_token, query_cards.TXT_DENIED)
        return True
    value = (text or "").strip()
    if state == "query_sales_input":
        field = str(((sess or {}).get("payload") or {}).get("field") or "")
        if not value or field not in _TEXT_FIELDS:
            _send(line_user_id, query_cards.input_prompt(field), reply_token)
            return True
        await _begin_records(
            binding,
            line_user_id,
            field=field,
            query=value,
            status="active",
            reply_token=reply_token,
        )
        return True

    match = _DATE_RE.match(value)
    if not match or not 1 <= int(match.group(3)) <= 30:
        _send(line_user_id, query_cards.top_custom_prompt(), reply_token)
        return True
    payload = (sess or {}).get("payload") or {}
    await _begin_top(
        binding,
        line_user_id,
        group=str(payload.get("group") or "model"),
        metric=str(payload.get("metric") or "quantity"),
        date_from=match.group(1),
        date_to=match.group(2),
        limit=int(match.group(3)),
        reply_token=reply_token,
    )
    return True


async def _pick_type(binding: dict, line_user_id: str, reply_token: str, kind: str) -> None:
    if kind != "sales":
        _reply(reply_token, query_cards.TXT_COMING_SOON)
        return
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "query_sales", {})
    _send(line_user_id, query_cards.sales_dimension_message(), reply_token)


async def _pick_dimension(
    binding: dict, line_user_id: str, reply_token: str, dimension: str
) -> None:
    if dimension == "latest":
        await _begin_records(
            binding,
            line_user_id,
            field="booking_date",
            status="active",
            reply_token=reply_token,
        )
        return
    if dimension in _TEXT_FIELDS:
        await _thr(
            store.set_session,
            binding["tenant_id"],
            line_user_id,
            "query_sales_input",
            {"field": dimension},
        )
        _send(line_user_id, query_cards.input_prompt(dimension), reply_token)
        return
    if dimension in {"finance", "allocation", "contract"}:
        _send(line_user_id, query_cards.status_message(dimension), reply_token)
        return
    if dimension == "top":
        await _thr(store.set_session, binding["tenant_id"], line_user_id, "query_top_group", {})
        _send(line_user_id, query_cards.top_group_message(), reply_token)


async def _pick_top_group(binding: dict, line_user_id: str, reply_token: str, group: str) -> None:
    if group not in sales_readback.TOP_GROUPS:
        group = "model"
    await _thr(
        store.set_session,
        binding["tenant_id"],
        line_user_id,
        "query_top_metric",
        {"group": group},
    )
    _send(line_user_id, query_cards.top_metric_message(), reply_token)


async def _pick_top_metric(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    metric: str,
) -> None:
    payload = (sess or {}).get("payload") or {}
    group = str(payload.get("group") or "model")
    if metric not in sales_readback.TOP_METRICS:
        metric = "quantity"
    await _thr(
        store.set_session,
        binding["tenant_id"],
        line_user_id,
        "query_top_period",
        {"group": group, "metric": metric},
    )
    _send(line_user_id, query_cards.top_period_message(), reply_token)


async def _pick_top_period(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    values: dict,
) -> None:
    payload = (sess or {}).get("payload") or {}
    group = str(payload.get("group") or "model")
    metric = str(payload.get("metric") or "quantity")
    period = values.get("period") or "month"
    if period == "custom":
        await _thr(
            store.set_session,
            binding["tenant_id"],
            line_user_id,
            "query_top_custom",
            {"group": group, "metric": metric},
        )
        _send(line_user_id, query_cards.top_custom_prompt(), reply_token)
        return
    today = date.today()
    year_be = today.year + 543
    date_from = f"01/{today.month:02d}/{year_be}" if period == "month" else f"01/01/{year_be}"
    date_to = f"{today.day:02d}/{today.month:02d}/{year_be}"
    await _begin_top(
        binding,
        line_user_id,
        group=group,
        metric=metric,
        date_from=date_from,
        date_to=date_to,
        limit=min(max(int(values.get("limit") or 10), 1), 30),
        reply_token=reply_token,
    )


async def _start_loading(line_user_id: str) -> None:
    await _thr(line_client.start_loading, line_user_id, 30, channel=_CHANNEL)


async def _begin_records(
    binding: dict,
    line_user_id: str,
    *,
    field: str = "booking_no",
    query: str = "",
    status: str = "active",
    limit: int = 10,
    page: int = 1,
    reply_token: str = "",
) -> None:
    params = {
        "query_kind": "records",
        "field": field,
        "query": query,
        "status": status,
        "limit": min(max(int(limit), 1), 10),
        "page": max(int(page), 1),
    }
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "query_results", params)
    await _start_loading(line_user_id)
    cloud_dispatch.spawn(
        "dms.records", _run_records, binding, line_user_id, params, _legacy_spawn=_spawn
    )


async def _run_records(binding: dict, line_user_id: str, params: dict) -> None:
    result = await _thr(
        sales_readback.fetch_sales_records,
        str(binding["user_id"]),
        field=params["field"],
        query=params["query"],
        status=params["status"],
        limit=params["limit"],
        page=params["page"],
    )
    if not await _can_query(binding):
        _push(line_user_id, query_cards.TXT_DENIED)
        return
    if not result.get("ok"):
        _push(
            line_user_id,
            (
                query_cards.TXT_NO_ENDPOINT
                if result.get("error_code") == "ERR_NO_CREDS"
                else query_cards.TXT_QUERY_FAILED
            ),
        )
        return
    _send(line_user_id, query_cards.sales_board(result))


async def _begin_top(
    binding: dict,
    line_user_id: str,
    *,
    group: str,
    metric: str,
    date_from: str,
    date_to: str,
    limit: int,
    page: int = 1,
    reply_token: str = "",
) -> None:
    params = {
        "query_kind": "top",
        "group": group,
        "metric": metric,
        "date_from": date_from,
        "date_to": date_to,
        "limit": min(max(int(limit), 1), 30),
        "page": max(int(page), 1),
    }
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "query_results", params)
    await _start_loading(line_user_id)
    cloud_dispatch.spawn("dms.top", _run_top, binding, line_user_id, params, _legacy_spawn=_spawn)


async def _run_top(binding: dict, line_user_id: str, params: dict) -> None:
    result = await _thr(
        sales_readback.fetch_top_sales,
        str(binding["user_id"]),
        group=params["group"],
        metric=params["metric"],
        date_from=params["date_from"],
        date_to=params["date_to"],
        limit=params["limit"],
        page=params["page"],
    )
    if not await _can_query(binding):
        _push(line_user_id, query_cards.TXT_DENIED)
        return
    if not result.get("ok"):
        _push(
            line_user_id,
            (
                query_cards.TXT_NO_ENDPOINT
                if result.get("error_code") == "ERR_NO_CREDS"
                else query_cards.TXT_QUERY_FAILED
            ),
        )
        return
    _send(line_user_id, query_cards.top_sales_board(result))


async def _paginate(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    values: dict,
) -> None:
    if (sess or {}).get("state") != "query_results":
        _reply(reply_token, "รายการนี้หมดอายุแล้ว พิมพ์ เมนู เพื่อค้นหาใหม่")
        return
    params = dict((sess or {}).get("payload") or {})
    if params.get("query_kind") != values.get("kind"):
        _reply(reply_token, "รายการนี้หมดอายุแล้ว พิมพ์ เมนู เพื่อค้นหาใหม่")
        return
    direction = values.get("direction")
    page = max(int(params.get("page") or 1), 1)
    params["page"] = page - 1 if direction == "prev" and page > 1 else page
    if direction == "next":
        params["page"] = page + 1
    if params["query_kind"] == "records":
        await _begin_records(
            binding,
            line_user_id,
            reply_token=reply_token,
            **{key: params[key] for key in ("field", "query", "status", "limit", "page")},
        )
    else:
        await _begin_top(
            binding,
            line_user_id,
            reply_token=reply_token,
            **{
                key: params[key]
                for key in ("group", "metric", "date_from", "date_to", "limit", "page")
            },
        )


__all__ = ["QUERY_ACTIONS", "handle_postback", "handle_text", "open_query"]
