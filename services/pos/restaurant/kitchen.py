# -*- coding: utf-8 -*-
"""餐厅 POS 编排 · 后厨板 + KOT 状态机(POS 项目 · PO-R2 · docs/pos/restaurant/02 §4)。

整单态从行 kitchen_status 派生(单一真理,不存冗余列):全 done→done、有 cooking→cooking、否则 new、
全 void→void。整单按钮(开始制作/全部完成)= 逐项流转的批量糖衣;另留逐项接口(单菜先出/退菜)。
在已开事务的 cursor 上调用。
"""

from __future__ import annotations

from core.pos_api import PosError
from services.pos.restaurant import order_store
from services.pos.restaurant.view import iso, minutes_since, name_obj, qty

_ITEM_STATUSES = ("cooking", "done", "void")


def derive_status(counts: dict) -> str:
    """{kitchen_status: n} → 整单派生态 new/cooking/done/void。"""
    non_void = counts.get("pending", 0) + counts.get("cooking", 0) + counts.get("done", 0)
    if non_void == 0:
        return "void"
    if counts.get("done", 0) == non_void:
        return "done"
    if counts.get("cooking", 0) > 0:
        return "cooking"
    return "new"


def board(cur, *, tenant_id: str, workspace_client_id: int, late_minutes: int = 15) -> dict:
    kots = order_store.list_active_kots(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    kot_ids = [str(k["id"]) for k in kots]
    items = order_store.list_kot_items(cur, tenant_id=tenant_id, kot_ids=kot_ids)
    by_kot: dict[str, list] = {}
    for it in items:
        by_kot.setdefault(str(it["kot_id"]), []).append(it)

    tickets, stat = [], {"pending": 0, "cooking": 0, "late": 0}
    for k in kots:
        kid = str(k["id"])
        rows = by_kot.get(kid, [])
        counts = _counts(rows)
        status = derive_status(counts)
        minutes = minutes_since(k["sent_at"])
        late = minutes >= late_minutes
        if status == "cooking":
            stat["cooking"] += 1
        elif status == "new":
            stat["pending"] += 1
        if late:
            stat["late"] += 1
        tickets.append(
            {
                "id": kid,
                "ticket_no": k["ticket_no"],
                "table_name": k["table_name"],
                "sent_at": iso(k["sent_at"]),
                "minutes": minutes,
                "late": late,
                "status": status,
                "items": [_item_view(it) for it in rows],
            }
        )
    return {"stat": stat, "tickets": tickets}


def set_kot_status(
    cur, *, tenant_id: str, workspace_client_id: int, kot_id: str, status: str
) -> dict:
    kot = order_store.get_kot(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, kot_id=kot_id
    )
    if not kot:
        raise PosError("pos.product_not_found", 404)
    if status == "cooking":
        order_store.bulk_set_kitchen_status(
            cur, tenant_id=tenant_id, kot_id=kot_id, from_statuses=["pending"], to_status="cooking"
        )
        order_store.touch_kot_started(cur, tenant_id=tenant_id, kot_id=kot_id)
    elif status == "done":
        order_store.bulk_set_kitchen_status(
            cur,
            tenant_id=tenant_id,
            kot_id=kot_id,
            from_statuses=["pending", "cooking"],
            to_status="done",
        )
        order_store.touch_kot_done(cur, tenant_id=tenant_id, kot_id=kot_id)
    else:
        raise PosError("pos.line_invalid", 422, detail="bad_status")
    return _kot_status_view(cur, tenant_id=tenant_id, kot=kot)


def set_item_status(cur, *, tenant_id: str, line_id: str, status: str) -> dict:
    if status not in _ITEM_STATUSES:
        raise PosError("pos.line_invalid", 422, detail="bad_status")
    line = order_store.get_line(cur, tenant_id=tenant_id, line_id=line_id)
    if not line:
        raise PosError("pos.product_not_found", 404)
    if line["kot_id"] is None:
        raise PosError("pos.line_invalid", 422, detail="not_sent")
    order_store.set_line_kitchen_status(cur, tenant_id=tenant_id, line_id=line_id, status=status)
    kot_id = str(line["kot_id"])
    if status == "cooking":
        order_store.touch_kot_started(cur, tenant_id=tenant_id, kot_id=kot_id)
    counts = order_store.kot_item_status_counts(cur, tenant_id=tenant_id, kot_id=kot_id)
    if derive_status(counts) == "done":
        order_store.touch_kot_done(cur, tenant_id=tenant_id, kot_id=kot_id)
    return {"line_id": line_id, "kitchen_status": status, "kot_status": derive_status(counts)}


# ── 内部 ──────────────────────────────────────────────────────────────
def _counts(rows: list) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["kitchen_status"]] = counts.get(r["kitchen_status"], 0) + 1
    return counts


def _kot_status_view(cur, *, tenant_id: str, kot: dict) -> dict:
    kid = str(kot["id"])
    items = order_store.list_kot_items(cur, tenant_id=tenant_id, kot_ids=[kid])
    counts = order_store.kot_item_status_counts(cur, tenant_id=tenant_id, kot_id=kid)
    return {
        "kot": {
            "id": kid,
            "ticket_no": kot["ticket_no"],
            "status": derive_status(counts),
            "items": [_item_view(it) for it in items],
        }
    }


def _item_view(it: dict) -> dict:
    return {
        "line_id": str(it["id"]),
        "name": name_obj(it),
        "qty": qty(it["qty"]),
        "note": it.get("note"),
        "kitchen_status": it["kitchen_status"],
    }
