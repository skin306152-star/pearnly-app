# -*- coding: utf-8 -*-
"""餐厅 POS DAL · 点单行 + 厨房单 KOT(POS 项目 · PO-R2/R3 · docs/pos/restaurant/01)。

承 store.py(区域/桌台/session)。点单行 pos_session_lines 兼作 KOT 明细:草稿(kot_id NULL)→ 送厨房
落 kot_id + kitchen_status;埋单结 settled_sale_id。每条语句 WHERE tenant_id;SQL 内插只许常量列名 + 占位符。
"""

from __future__ import annotations

from services.pos.restaurant.store import _LINE_TOTAL, _d

_LINE_VIEW = (
    "l.id, l.product_id, l.kot_id, l.sell_unit, l.unit_factor, l.qty, l.unit_price, "
    "l.line_discount, l.vat_applicable, l.note, l.kitchen_status, l.settled_sale_id, "
    "p.name_th, p.name_en, p.name_zh"
)


def _line_rows(cur, *, tenant_id: str, where: str, params: tuple) -> list:
    cur.execute(
        f"SELECT {_LINE_VIEW}, {_LINE_TOTAL} AS line_total "
        f"FROM pos_session_lines l JOIN products p ON p.id = l.product_id "
        f"WHERE l.tenant_id = %s AND {where} ORDER BY l.created_at, l.id",
        (tenant_id, *params),
    )
    return cur.fetchall()


# ── 点单行 ────────────────────────────────────────────────────────────
def list_lines(cur, *, tenant_id: str, session_id: str) -> list:
    return _line_rows(cur, tenant_id=tenant_id, where="l.session_id = %s", params=(session_id,))


def list_draft_lines(cur, *, tenant_id: str, session_id: str) -> list:
    return _line_rows(
        cur,
        tenant_id=tenant_id,
        where="l.session_id = %s AND l.kot_id IS NULL",
        params=(session_id,),
    )


def get_line(cur, *, tenant_id: str, line_id: str):
    cur.execute(
        "SELECT id, session_id, kot_id, qty, settled_sale_id, kitchen_status "
        "FROM pos_session_lines WHERE tenant_id = %s AND id = %s",
        (tenant_id, line_id),
    )
    return cur.fetchone()


def insert_line(cur, *, tenant_id: str, session_id: str, fields: dict, created_by=None) -> dict:
    cur.execute(
        "INSERT INTO pos_session_lines "
        "(tenant_id, session_id, product_id, sell_unit, unit_factor, qty, unit_price, "
        " line_discount, vat_applicable, note, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (
            tenant_id,
            session_id,
            fields["product_id"],
            fields.get("sell_unit"),
            _d(fields.get("unit_factor", 1)),
            _d(fields["qty"]),
            _d(fields["unit_price"]),
            _d(fields.get("line_discount", 0)),
            bool(fields.get("vat_applicable", True)),
            fields.get("note"),
            created_by,
        ),
    )
    return cur.fetchone()


def update_draft_line(cur, *, tenant_id: str, line_id: str, qty=None, note=None) -> None:
    sets, vals = [], []
    if qty is not None:
        sets.append("qty = %s")
        vals.append(_d(qty))
    if note is not None:
        sets.append("note = %s")
        vals.append(note)
    if not sets:
        return
    cur.execute(
        f"UPDATE pos_session_lines SET {', '.join(sets)} "
        f"WHERE tenant_id = %s AND id = %s AND kot_id IS NULL",
        (*vals, tenant_id, line_id),
    )


def delete_draft_line(cur, *, tenant_id: str, line_id: str) -> int:
    cur.execute(
        "DELETE FROM pos_session_lines WHERE tenant_id = %s AND id = %s AND kot_id IS NULL",
        (tenant_id, line_id),
    )
    return cur.rowcount


def assign_lines_to_kot(cur, *, tenant_id: str, session_id: str, kot_id: str, line_ids=None) -> int:
    """草稿行 → KOT(kot_id + kitchen_status='pending')。line_ids=None 时送本桌全部草稿。"""
    sql = (
        "UPDATE pos_session_lines SET kot_id = %s, kitchen_status = 'pending' "
        "WHERE tenant_id = %s AND session_id = %s AND kot_id IS NULL"
    )
    params = [kot_id, tenant_id, session_id]
    if line_ids:
        sql += " AND id = ANY(%s::uuid[])"
        params.append(list(line_ids))
    cur.execute(sql, params)
    return cur.rowcount


def list_billable_lines(cur, *, tenant_id: str, session_id: str, line_ids=None) -> list:
    """埋单候选:未结、未退行。line_ids 给定则交集(按项分单)。"""
    where = "l.session_id = %s AND l.settled_sale_id IS NULL AND l.kitchen_status <> 'void'"
    params = (session_id,)
    if line_ids:
        where += " AND l.id = ANY(%s::uuid[])"
        params = (session_id, list(line_ids))
    return _line_rows(cur, tenant_id=tenant_id, where=where, params=params)


def settle_lines(cur, *, tenant_id: str, line_ids: list, sale_id: str) -> int:
    cur.execute(
        "UPDATE pos_session_lines SET settled_sale_id = %s "
        "WHERE tenant_id = %s AND id = ANY(%s::uuid[]) AND settled_sale_id IS NULL",
        (sale_id, tenant_id, list(line_ids)),
    )
    return cur.rowcount


def count_unsettled(cur, *, tenant_id: str, session_id: str) -> int:
    cur.execute(
        "SELECT COUNT(*) AS n FROM pos_session_lines "
        "WHERE tenant_id = %s AND session_id = %s AND settled_sale_id IS NULL "
        "AND kitchen_status <> 'void'",
        (tenant_id, session_id),
    )
    return int(cur.fetchone()["n"])


def has_sent_lines(cur, *, tenant_id: str, session_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM pos_session_lines "
        "WHERE tenant_id = %s AND session_id = %s AND kot_id IS NOT NULL LIMIT 1",
        (tenant_id, session_id),
    )
    return cur.fetchone() is not None


# ── 厨房单 KOT ────────────────────────────────────────────────────────
def next_ticket_no(cur, *, tenant_id: str, workspace_client_id: int) -> int:
    """当日(UTC)当门店递增叫号(展示用,非强一致;同事务串行调用)。"""
    cur.execute(
        "SELECT COALESCE(MAX(ticket_no), 0) + 1 AS n FROM pos_kot "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND sent_at::date = (now() AT TIME ZONE 'UTC')::date",
        (tenant_id, workspace_client_id),
    )
    return int(cur.fetchone()["n"])


def create_kot(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    session_id: str,
    ticket_no: int,
    created_by=None,
) -> dict:
    cur.execute(
        "INSERT INTO pos_kot (tenant_id, workspace_client_id, session_id, ticket_no, created_by) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id, ticket_no, sent_at",
        (tenant_id, workspace_client_id, session_id, ticket_no, created_by),
    )
    return cur.fetchone()


def kot_tickets_for_session(cur, *, tenant_id: str, session_id: str) -> dict:
    """{kot_id: ticket_no} · 本桌已送 KOT 叫号(本单视图给已下单行标号)。"""
    cur.execute(
        "SELECT id, ticket_no FROM pos_kot WHERE tenant_id = %s AND session_id = %s",
        (tenant_id, session_id),
    )
    return {str(r["id"]): r["ticket_no"] for r in cur.fetchall()}


def get_kot(cur, *, tenant_id: str, workspace_client_id: int, kot_id: str):
    cur.execute(
        "SELECT id, session_id, ticket_no, sent_at, started_at, done_at FROM pos_kot "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, kot_id),
    )
    return cur.fetchone()


def list_active_kots(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """未完成 KOT(≥1 行 pending/cooking)+ 桌号 + 出单时间。不 join 明细(明细另查防笛卡尔)。"""
    cur.execute(
        "SELECT k.id, k.ticket_no, k.sent_at, t.name AS table_name "
        "FROM pos_kot k "
        "JOIN pos_table_sessions s ON s.id = k.session_id "
        "JOIN pos_tables t ON t.id = s.table_id "
        "WHERE k.tenant_id = %s AND k.workspace_client_id = %s AND EXISTS ("
        "  SELECT 1 FROM pos_session_lines l "
        "  WHERE l.tenant_id = k.tenant_id AND l.kot_id = k.id "
        "  AND l.kitchen_status IN ('pending','cooking')) "
        "ORDER BY k.sent_at",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def list_kot_items(cur, *, tenant_id: str, kot_ids: list) -> list:
    """一批 KOT 的明细(后厨板:按 kot_id 分组在编排层)。"""
    if not kot_ids:
        return []
    cur.execute(
        "SELECT l.id, l.kot_id, l.qty, l.note, l.kitchen_status, p.name_th, p.name_en, p.name_zh "
        "FROM pos_session_lines l JOIN products p ON p.id = l.product_id "
        "WHERE l.tenant_id = %s AND l.kot_id = ANY(%s::uuid[]) ORDER BY l.created_at, l.id",
        (tenant_id, list(kot_ids)),
    )
    return cur.fetchall()


def kot_item_status_counts(cur, *, tenant_id: str, kot_id: str) -> dict:
    """派生整单态用:各 kitchen_status 计数。"""
    cur.execute(
        "SELECT kitchen_status, COUNT(*) AS n FROM pos_session_lines "
        "WHERE tenant_id = %s AND kot_id = %s GROUP BY kitchen_status",
        (tenant_id, kot_id),
    )
    return {r["kitchen_status"]: int(r["n"]) for r in cur.fetchall()}


def bulk_set_kitchen_status(
    cur, *, tenant_id: str, kot_id: str, from_statuses: list, to_status: str
) -> int:
    cur.execute(
        "UPDATE pos_session_lines SET kitchen_status = %s "
        "WHERE tenant_id = %s AND kot_id = %s AND kitchen_status = ANY(%s)",
        (to_status, tenant_id, kot_id, list(from_statuses)),
    )
    return cur.rowcount


def set_line_kitchen_status(cur, *, tenant_id: str, line_id: str, status: str) -> int:
    cur.execute(
        "UPDATE pos_session_lines SET kitchen_status = %s "
        "WHERE tenant_id = %s AND id = %s AND kot_id IS NOT NULL",
        (status, tenant_id, line_id),
    )
    return cur.rowcount


def touch_kot_started(cur, *, tenant_id: str, kot_id: str) -> None:
    cur.execute(
        "UPDATE pos_kot SET started_at = COALESCE(started_at, now()) "
        "WHERE tenant_id = %s AND id = %s",
        (tenant_id, kot_id),
    )


def touch_kot_done(cur, *, tenant_id: str, kot_id: str) -> None:
    cur.execute(
        "UPDATE pos_kot SET done_at = now() WHERE tenant_id = %s AND id = %s",
        (tenant_id, kot_id),
    )


def set_sale_service_charge(cur, *, tenant_id: str, sale_id: str, service_charge) -> None:
    """埋单后回写服务费(pos_sales 加列 · 不动 sales_store._SALE_COLS)。"""
    cur.execute(
        "UPDATE pos_sales SET service_charge = %s WHERE tenant_id = %s AND id = %s",
        (_d(service_charge), tenant_id, sale_id),
    )
