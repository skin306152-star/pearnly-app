# -*- coding: utf-8 -*-
"""餐厅 POS 编排 · 区域/桌台 CRUD + 总览状态机(POS 项目 · PO-R1 · docs/pos/restaurant/02 §1/§2)。

CRUD 为 owner 管理动作(路由层 require_owner);总览前台可读。桌台总览状态 free/seat/cook/bill 实时从
session.status + 行 kitchen_status 派生(单一真理 · docs/restaurant/01 §6),不存冗余态。
"""

from __future__ import annotations

from core.pos_api import PosError
from services.pos.restaurant import store
from services.pos.restaurant.view import minutes_since, money


# ── 区域 CRUD ─────────────────────────────────────────────────────────
def list_areas(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    rows = store.list_areas(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    return {"areas": [_area_view(r) for r in rows]}


def create_area(cur, *, tenant_id: str, workspace_client_id: int, name: str, sort: int) -> dict:
    if not (name or "").strip():
        raise PosError("pos.line_invalid", 422, detail="empty_name")
    row = store.create_area(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        name=name.strip(),
        sort=sort,
    )
    return {"area": _area_view(row)}


def update_area(
    cur, *, tenant_id: str, workspace_client_id: int, area_id: int, fields: dict
) -> dict:
    if (
        store.get_area(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
        )
        is None
    ):
        raise PosError("pos.product_not_found", 404)
    row = store.update_area(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        area_id=area_id,
        fields=fields,
    )
    return {"area": _area_view(row)}


def delete_area(cur, *, tenant_id: str, workspace_client_id: int, area_id: int) -> dict:
    """删区域 · 仅空区域(0 桌台);还有桌台 → 409(先移走/删桌台)。"""
    if (
        store.get_area(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
        )
        is None
    ):
        raise PosError("pos.product_not_found", 404)
    if store.area_has_tables(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
    ):
        raise PosError("pos.void_not_allowed", 409, detail="area_has_tables")
    store.delete_area(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
    )
    return {"deleted": area_id}


# ── 桌台 CRUD ─────────────────────────────────────────────────────────
def list_tables(cur, *, tenant_id: str, workspace_client_id: int, area_id=None) -> dict:
    # 老板后台管理:含停用桌台(显 off 卡可启用/删除);收银端总览另走 tables_with_session。
    rows = store.list_tables(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        area_id=area_id,
        include_inactive=True,
    )
    return {"tables": [_table_view(r) for r in rows]}


def create_table(
    cur, *, tenant_id: str, workspace_client_id: int, name: str, area_id=None, seats=4, sort=0
) -> dict:
    if not (name or "").strip():
        raise PosError("pos.line_invalid", 422, detail="empty_name")
    name = name.strip()
    if store.table_name_exists(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, name=name
    ):
        raise PosError("pos.line_invalid", 422, detail="duplicate_table")
    row = store.create_table(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        name=name,
        area_id=area_id,
        seats=seats,
        sort=sort,
    )
    return {"table": _table_view(row)}


def update_table(
    cur, *, tenant_id: str, workspace_client_id: int, table_id: int, fields: dict
) -> dict:
    if (
        store.get_table(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, table_id=table_id
        )
        is None
    ):
        raise PosError("pos.product_not_found", 404)
    name = fields.get("name")
    if name is not None:
        name = name.strip()
        if not name:
            raise PosError("pos.line_invalid", 422, detail="empty_name")
        if store.table_name_exists(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            name=name,
            exclude_id=table_id,
        ):
            raise PosError("pos.line_invalid", 422, detail="duplicate_table")
        fields["name"] = name
    # 停用占用中的桌:挡掉(在台未结账会丢账)。
    if fields.get("is_active") is False and store.get_active_session_for_table(
        cur, tenant_id=tenant_id, table_id=table_id
    ):
        raise PosError("pos.void_not_allowed", 409, detail="table_busy")
    row = store.update_table(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        table_id=table_id,
        fields=fields,
    )
    return {"table": _table_view(row)}


def delete_table(cur, *, tenant_id: str, workspace_client_id: int, table_id: int) -> dict:
    """硬删桌台 · 仅限从没开过台的;开过台(有 session 历史)的留账只能停用 → 409。"""
    if (
        store.get_table(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, table_id=table_id
        )
        is None
    ):
        raise PosError("pos.product_not_found", 404)
    if store.table_has_session_history(cur, tenant_id=tenant_id, table_id=table_id):
        raise PosError("pos.void_not_allowed", 409, detail="table_has_history")
    store.delete_table(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, table_id=table_id
    )
    return {"deleted": table_id}


# ── 总览(状态机派生)─────────────────────────────────────────────────
def overview(cur, *, tenant_id: str, workspace_client_id: int, area_id=None) -> dict:
    areas = store.list_areas(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    tables = store.tables_with_session(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
    )
    agg = store.session_aggregates(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return {
        "areas": [{"id": a["id"], "name": a["name"]} for a in areas],
        "tables": [_overview_table(t, agg) for t in tables],
    }


def _overview_table(t: dict, agg: dict) -> dict:
    session_id = str(t["session_id"]) if t.get("session_id") else None
    if session_id is None:
        return {
            "id": t["id"],
            "name": t["name"],
            "area_id": t["area_id"],
            "seats": t["seats"],
            "status": "free",
            "session_id": None,
            "party_size": None,
            "amount": "0.00",
            "minutes": 0,
        }
    a = agg.get(session_id, {"amount": 0, "cooking": False})
    status = "bill" if t["session_status"] == "billing" else "cook" if a.get("cooking") else "seat"
    return {
        "id": t["id"],
        "name": t["name"],
        "area_id": t["area_id"],
        "seats": t["seats"],
        "status": status,
        "session_id": session_id,
        "party_size": t["party_size"],
        "amount": money(a.get("amount")),
        "minutes": minutes_since(t["opened_at"]),
    }


def _area_view(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "sort": r["sort"],
        "is_active": r["is_active"],
        "table_count": int(r["table_count"]) if "table_count" in r else None,
    }


def _table_view(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "area_id": r["area_id"],
        "area_name": r.get("area_name"),
        "seats": r["seats"],
        "sort": r["sort"],
        "is_active": r["is_active"],
    }
