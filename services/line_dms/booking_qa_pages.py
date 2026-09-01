# -*- coding: utf-8 -*-
"""Live DMS master paging for the LINE booking question flow."""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.line_dms import qa_cards
from services.line_dms._out import _send
from services.line_dms.qa_util import car_label_of

PAGED_MASTER = {
    "place": "place_books",
    "term": "term_sales",
    "regis": "regis_behalfs",
    "bank": "company_banks",
    "paint": "paints",
}


def static_question(step, qa) -> Optional[Dict[str, Any]]:
    """Render a question that does not need a DMS master lookup."""
    from datetime import date

    channel = (qa.get("pending_channel") or {}).get("channel", "")
    return {
        "slip": qa_cards.ask_slip(),
        "car_search": qa_cards.ask_car(),
        "date": qa_cards.ask_date(date.today()),
        "regis_name": qa_cards.ask_regis_name(),
        "pay_channel": qa_cards.ask_pay_channel(),
        "pay_amount": qa_cards.ask_amount(qa_cards.PAY_LABELS.get(channel, "")),
        "pay_src": qa_cards.ask_pay_src(),
        "pay_ref": qa_cards.ask_pay_ref(channel),
        "pay_more": qa_cards.ask_more(),
        "slip_after": qa_cards.need_slip(),
        "slip_conflict": qa_cards.slip_conflict(),
    }.get(step)


async def question(line_user_id, qa, step, masters, paints) -> Optional[Dict[str, Any]]:
    """Read the current DMS master and render the requested page."""
    pages = qa.get("pages") or {}
    if step == "place":
        return qa_cards.ask_place(
            await masters(line_user_id, qa, "place_books"), pages.get("place_books", 0)
        )
    if step == "term":
        return qa_cards.ask_term(
            await masters(line_user_id, qa, "term_sales"), pages.get("term_sales", 0)
        )
    if step == "regis":
        return qa_cards.ask_regis(
            await masters(line_user_id, qa, "regis_behalfs"), pages.get("regis_behalfs", 0)
        )
    if step == "paint":
        return qa_cards.ask_paint(
            car_label_of(qa), await paints(line_user_id, qa), pages.get("paints", 0)
        )
    if step == "pay_dst":
        return qa_cards.ask_pay_dst(
            await masters(line_user_id, qa, "company_banks"), pages.get("company_banks", 0)
        )
    return None


def page_number(value: str) -> Optional[int]:
    """Parse a paging token without treating a DMS ID as navigation."""
    if not (value or "").startswith(qa_cards.PAGE_TOKEN):
        return None
    try:
        return int(value[len(qa_cards.PAGE_TOKEN) :])
    except ValueError:
        return None


async def flip_page(
    tenant_id,
    line_user_id,
    qa,
    action,
    page,
    reply_token,
    *,
    send_step,
    persist,
    reask,
):
    """Change only the visible page; selecting a DMS row remains separate."""
    if action == "car":
        search = qa.get("car_search") or {}
        hits = search.get("hits") or []
        if not hits:
            await reask(tenant_id, line_user_id, qa, "", reply_token)
            return
        last = (len(hits) - 1) // qa_cards.QR_PAGE_SIZE
        search["page"] = max(0, min(page, last))
        await persist(tenant_id, line_user_id, qa)
        _send(line_user_id, qa_cards.car_results(hits, len(hits), search["page"]), reply_token)
        return
    key = PAGED_MASTER.get(action)
    if not key:
        await reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa.setdefault("pages", {})[key] = page
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, qa.get("step") or "", reply_token)
