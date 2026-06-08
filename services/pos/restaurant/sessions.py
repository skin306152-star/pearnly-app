# -*- coding: utf-8 -*-
"""餐厅 POS 编排 · 开台/点单 append/送厨房 KOT(POS 项目 · PO-R2 · docs/pos/restaurant/02 §3/§4)。

开台 = 一桌一活动 session(DB partial unique 兜底,这里先查给友好码)。点单 = append 草稿行(kot_id NULL,
可加减删);送厨房 = 草稿行打包成一张 KOT(锁定不可改,要改走退菜重下)。加菜 = 同桌再 append + 再送一张 KOT。
菜品价/单位/税在加菜时按 product 快照冻结(不信前端价)。每条语句 WHERE tenant_id;在已开事务的 cursor 上调用。
"""

from __future__ import annotations

from decimal import Decimal

from core.pos_api import PosError
from services.pos.restaurant import order_store, store
from services.pos.restaurant.view import iso, line_view, minutes_since, money


def open_session(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    table_id: int,
    party_size: int,
    service_type: str = "dine_in",
    cashier_id=None,
    created_by=None,
) -> dict:
    table = store.get_table(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, table_id=table_id
    )
    if not table or not table["is_active"]:
        raise PosError("pos.product_not_found", 404)
    if store.get_active_session_for_table(cur, tenant_id=tenant_id, table_id=table_id):
        raise PosError("pos.line_invalid", 422, detail="table_occupied")
    row = store.create_session(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        table_id=table_id,
        party_size=max(1, int(party_size or 1)),
        service_type=service_type or "dine_in",
        cashier_id=cashier_id,
        created_by=created_by,
    )
    return {
        "session": {
            "id": str(row["id"]),
            "table_id": table_id,
            "table_name": table["name"],
            "party_size": row["party_size"],
            "service_type": row["service_type"],
            "status": row["status"],
            "opened_at": iso(row["opened_at"]),
        }
    }


def session_detail(cur, *, tenant_id: str, session_id: str) -> dict:
    session = _require_session(cur, tenant_id=tenant_id, session_id=session_id)
    rows = order_store.list_lines(cur, tenant_id=tenant_id, session_id=session_id)
    tickets = order_store.kot_tickets_for_session(cur, tenant_id=tenant_id, session_id=session_id)
    draft, sent = [], []
    ordered_sub = draft_sub = Decimal("0")
    for r in rows:
        v = line_view(r)
        if r["kot_id"] is None:
            draft.append(v)
            draft_sub += Decimal(str(r["line_total"]))
        else:
            v["ticket_no"] = tickets.get(str(r["kot_id"]))
            sent.append(v)
            if r["settled_sale_id"] is None and r["kitchen_status"] != "void":
                ordered_sub += Decimal(str(r["line_total"]))
    return {
        "session": _session_head(session),
        "draft_lines": draft,
        "sent_lines": sent,
        "totals": {
            "ordered_subtotal": money(ordered_sub),
            "draft_subtotal": money(draft_sub),
            "unsettled_subtotal": money(ordered_sub + draft_sub),
        },
    }


def add_lines(
    cur, *, tenant_id: str, workspace_client_id: int, session_id: str, lines: list, created_by=None
) -> dict:
    session = _require_session(cur, tenant_id=tenant_id, session_id=session_id)
    if session["status"] == "closed":
        raise PosError("pos.void_not_allowed", 409, detail="session_not_open")
    if not lines:
        raise PosError("pos.line_invalid", 422, detail="empty_lines")
    for ln in lines:
        prod = store.get_menu_product(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=ln.get("product_id"),
        )
        if not prod:
            raise PosError("pos.line_invalid", 422, detail=str(ln.get("product_id")))
        qty = Decimal(str(ln.get("qty", 0)))
        if qty <= 0:
            raise PosError("pos.line_invalid", 422, detail="bad_qty")
        order_store.insert_line(
            cur,
            tenant_id=tenant_id,
            session_id=session_id,
            fields={
                "product_id": str(prod["id"]),
                "sell_unit": ln.get("sell_unit") or prod["base_unit"],
                "unit_factor": 1,
                "qty": qty,
                "unit_price": prod["unit_price"] if prod["unit_price"] is not None else 0,
                "line_discount": ln.get("line_discount", 0),
                "vat_applicable": bool(prod["vat_applicable"]),
                "note": (ln.get("note") or None),
            },
            created_by=created_by,
        )
    return {"draft_lines": _draft_view(cur, tenant_id=tenant_id, session_id=session_id)}


def update_draft(
    cur, *, tenant_id: str, session_id: str, line_id: str, qty=None, note=None
) -> dict:
    line = _require_draft(cur, tenant_id=tenant_id, session_id=session_id, line_id=line_id)
    if qty is not None and Decimal(str(qty)) <= 0:
        order_store.delete_draft_line(cur, tenant_id=tenant_id, line_id=line["id"])
    else:
        order_store.update_draft_line(
            cur, tenant_id=tenant_id, line_id=line["id"], qty=qty, note=note
        )
    return {"draft_lines": _draft_view(cur, tenant_id=tenant_id, session_id=session_id)}


def delete_draft(cur, *, tenant_id: str, session_id: str, line_id: str) -> dict:
    _require_draft(cur, tenant_id=tenant_id, session_id=session_id, line_id=line_id)
    order_store.delete_draft_line(cur, tenant_id=tenant_id, line_id=line_id)
    return {"draft_lines": _draft_view(cur, tenant_id=tenant_id, session_id=session_id)}


def send_kitchen(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    session_id: str,
    line_ids=None,
    created_by=None,
) -> dict:
    _require_session(cur, tenant_id=tenant_id, session_id=session_id)
    drafts = order_store.list_draft_lines(cur, tenant_id=tenant_id, session_id=session_id)
    draft_ids = {str(d["id"]) for d in drafts}
    if line_ids:
        line_ids = [i for i in line_ids if i in draft_ids]
    target = line_ids if line_ids is not None else list(draft_ids)
    if not target:
        raise PosError("pos.line_invalid", 422, detail="no_draft_lines")
    ticket_no = order_store.next_ticket_no(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    kot = order_store.create_kot(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        session_id=session_id,
        ticket_no=ticket_no,
        created_by=created_by,
    )
    order_store.assign_lines_to_kot(
        cur, tenant_id=tenant_id, session_id=session_id, kot_id=str(kot["id"]), line_ids=target
    )
    items = order_store.list_kot_items(cur, tenant_id=tenant_id, kot_ids=[str(kot["id"])])
    return {"kot": _kot_view(kot, items)}


def cancel_session(cur, *, tenant_id: str, session_id: str) -> dict:
    _require_session(cur, tenant_id=tenant_id, session_id=session_id)
    if order_store.has_sent_lines(cur, tenant_id=tenant_id, session_id=session_id):
        raise PosError("pos.void_not_allowed", 409, detail="session_has_orders")
    for d in order_store.list_draft_lines(cur, tenant_id=tenant_id, session_id=session_id):
        order_store.delete_draft_line(cur, tenant_id=tenant_id, line_id=str(d["id"]))
    store.set_session_status(
        cur, tenant_id=tenant_id, session_id=session_id, status="closed", closed=True
    )
    return {"session": {"id": session_id, "status": "closed"}}


# ── 内部 ──────────────────────────────────────────────────────────────
def _require_session(cur, *, tenant_id: str, session_id: str) -> dict:
    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id)
    if not session:
        raise PosError("pos.product_not_found", 404)
    return session


def _require_draft(cur, *, tenant_id: str, session_id: str, line_id: str) -> dict:
    line = order_store.get_line(cur, tenant_id=tenant_id, line_id=line_id)
    if not line or str(line["session_id"]) != str(session_id):
        raise PosError("pos.product_not_found", 404)
    if line["kot_id"] is not None:
        raise PosError("pos.line_invalid", 422, detail="line_locked")
    return line


def _draft_view(cur, *, tenant_id: str, session_id: str) -> list:
    return [
        line_view(r)
        for r in order_store.list_draft_lines(cur, tenant_id=tenant_id, session_id=session_id)
    ]


def _session_head(session: dict) -> dict:
    return {
        "id": str(session["id"]),
        "table_id": session["table_id"],
        "table_name": session["table_name"],
        "party_size": session["party_size"],
        "service_type": session["service_type"],
        "status": session["status"],
        "opened_at": iso(session["opened_at"]),
        "minutes": minutes_since(session["opened_at"]),
        "note": session.get("note"),
    }


def _kot_view(kot: dict, items: list) -> dict:
    from services.pos.restaurant.view import name_obj, qty

    return {
        "id": str(kot["id"]),
        "ticket_no": kot["ticket_no"],
        "sent_at": iso(kot["sent_at"]),
        "items": [
            {
                "line_id": str(it["id"]),
                "name": name_obj(it),
                "qty": qty(it["qty"]),
                "note": it.get("note"),
                "kitchen_status": it["kitchen_status"],
            }
            for it in items
        ],
    }
