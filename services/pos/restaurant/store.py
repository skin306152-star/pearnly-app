# -*- coding: utf-8 -*-
"""餐厅 POS DAL · 区域/桌台/开台 session/总览(POS 项目 · PO-R1 · docs/pos/restaurant/01)。

参数化叶子:每条语句 WHERE tenant_id(+ workspace_client_id),应用层硬隔离(RLS 仅兜底 · 见
[[pos-rls-bypass-app-layer-isolation]])。点单行 + 厨房单 DAL 在 order_store.py;编排在
tables/sessions/kitchen/checkout。钱 numeric(14,2)、量 numeric(14,3);SQL 内插只许模块常量列名 + 占位符。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# 行金额口径(SQL 内联 · 仅常量算式,无外部输入):份数×单价−行折扣。
_LINE_TOTAL = "(l.qty * l.unit_price - l.line_discount)"
# 已下单未结(总览金额 + 埋单候选):送厨房锁定、未结、未退。
_UNSETTLED_SENT = (
    "l.kot_id IS NOT NULL AND l.settled_sale_id IS NULL AND l.kitchen_status <> 'void'"
)
_ACTIVE_KITCHEN = "l.kot_id IS NOT NULL AND l.kitchen_status IN ('pending','cooking')"


def _d(v) -> Optional[Decimal]:
    return Decimal(str(v)) if v is not None else None


# ── 区域 ──────────────────────────────────────────────────────────────
def list_areas(cur, *, tenant_id: str, workspace_client_id: int, include_inactive=False) -> list:
    sql = (
        "SELECT a.id, a.name, a.sort, a.is_active, "
        "(SELECT COUNT(*) FROM pos_tables t "
        " WHERE t.tenant_id = a.tenant_id AND t.area_id = a.id AND t.is_active) AS table_count "
        "FROM pos_areas a WHERE a.tenant_id = %s AND a.workspace_client_id = %s"
    )
    params = [tenant_id, workspace_client_id]
    if not include_inactive:
        sql += " AND a.is_active = TRUE"
    sql += " ORDER BY a.sort, a.id"
    cur.execute(sql, params)
    return cur.fetchall()


def create_area(cur, *, tenant_id: str, workspace_client_id: int, name: str, sort: int = 0) -> dict:
    cur.execute(
        "INSERT INTO pos_areas (tenant_id, workspace_client_id, name, sort) "
        "VALUES (%s, %s, %s, %s) RETURNING id, name, sort, is_active",
        (tenant_id, workspace_client_id, name, sort),
    )
    return cur.fetchone()


def update_area(cur, *, tenant_id: str, workspace_client_id: int, area_id: int, fields: dict):
    sets, vals = _build_sets(fields, ("name", "sort", "is_active"))
    if not sets:
        return get_area(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, area_id=area_id
        )
    sets.append("updated_at = now()")
    cur.execute(
        f"UPDATE pos_areas SET {', '.join(sets)} "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING id, name, sort, is_active",
        (*vals, tenant_id, workspace_client_id, area_id),
    )
    return cur.fetchone()


def get_area(cur, *, tenant_id: str, workspace_client_id: int, area_id: int):
    cur.execute(
        "SELECT id, name, sort, is_active FROM pos_areas "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, area_id),
    )
    return cur.fetchone()


def area_has_tables(cur, *, tenant_id: str, workspace_client_id: int, area_id: int) -> bool:
    """区域下是否还有桌台(含停用)。有则不能删区域(先移走/删桌台)。"""
    cur.execute(
        "SELECT 1 FROM pos_tables "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND area_id = %s LIMIT 1",
        (tenant_id, workspace_client_id, area_id),
    )
    return cur.fetchone() is not None


def delete_area(cur, *, tenant_id: str, workspace_client_id: int, area_id: int) -> None:
    """硬删区域(仅 0 桌台 · 调用方先校验)。按 tenant+workspace 隔离。"""
    cur.execute(
        "DELETE FROM pos_areas WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, area_id),
    )


# ── 桌台 ──────────────────────────────────────────────────────────────
def list_tables(
    cur, *, tenant_id: str, workspace_client_id: int, area_id=None, include_inactive=False
) -> list:
    sql = (
        "SELECT t.id, t.name, t.area_id, a.name AS area_name, t.seats, t.sort, t.is_active "
        "FROM pos_tables t LEFT JOIN pos_areas a ON a.id = t.area_id "
        "WHERE t.tenant_id = %s AND t.workspace_client_id = %s"
    )
    params = [tenant_id, workspace_client_id]
    if area_id is not None:
        sql += " AND t.area_id = %s"
        params.append(area_id)
    if not include_inactive:
        sql += " AND t.is_active = TRUE"
    sql += " ORDER BY t.sort, t.id"
    cur.execute(sql, params)
    return cur.fetchall()


def get_table(cur, *, tenant_id: str, workspace_client_id: int, table_id: int):
    cur.execute(
        "SELECT id, name, area_id, seats, sort, is_active FROM pos_tables "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, table_id),
    )
    return cur.fetchone()


def table_name_exists(
    cur, *, tenant_id: str, workspace_client_id: int, name: str, exclude_id=None
) -> bool:
    sql = "SELECT 1 FROM pos_tables WHERE tenant_id = %s AND workspace_client_id = %s AND name = %s"
    params = [tenant_id, workspace_client_id, name]
    if exclude_id is not None:
        sql += " AND id <> %s"
        params.append(exclude_id)
    cur.execute(sql + " LIMIT 1", params)
    return cur.fetchone() is not None


def create_table(
    cur, *, tenant_id: str, workspace_client_id: int, name: str, area_id=None, seats=4, sort=0
) -> dict:
    cur.execute(
        "INSERT INTO pos_tables (tenant_id, workspace_client_id, area_id, name, seats, sort) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "RETURNING id, name, area_id, seats, sort, is_active",
        (tenant_id, workspace_client_id, area_id, name, seats, sort),
    )
    return cur.fetchone()


def update_table(cur, *, tenant_id: str, workspace_client_id: int, table_id: int, fields: dict):
    sets, vals = _build_sets(fields, ("name", "area_id", "seats", "sort", "is_active"))
    if not sets:
        return get_table(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, table_id=table_id
        )
    sets.append("updated_at = now()")
    cur.execute(
        f"UPDATE pos_tables SET {', '.join(sets)} "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING id, name, area_id, seats, sort, is_active",
        (*vals, tenant_id, workspace_client_id, table_id),
    )
    return cur.fetchone()


def tables_with_session(cur, *, tenant_id: str, workspace_client_id: int, area_id=None) -> list:
    """总览:活动桌台 LEFT JOIN 其活动 session(一桌至多一活动 → 无笛卡尔)。"""
    sql = (
        "SELECT t.id, t.name, t.area_id, t.seats, "
        "s.id AS session_id, s.status AS session_status, s.party_size, s.opened_at "
        "FROM pos_tables t "
        "LEFT JOIN pos_table_sessions s "
        "  ON s.tenant_id = t.tenant_id AND s.table_id = t.id AND s.status <> 'closed' "
        "WHERE t.tenant_id = %s AND t.workspace_client_id = %s AND t.is_active = TRUE"
    )
    params = [tenant_id, workspace_client_id]
    if area_id is not None:
        sql += " AND t.area_id = %s"
        params.append(area_id)
    sql += " ORDER BY t.sort, t.id"
    cur.execute(sql, params)
    return cur.fetchall()


def session_aggregates(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """每活动 session 的已下单未结金额 + 是否在制(总览 cook/seat 派生)。

    仅聚合 pos_session_lines(不 join payments)→ 无笛卡尔积。返回 {session_id: {amount, cooking}}。
    """
    cur.execute(
        "SELECT l.session_id, "
        f"COALESCE(SUM({_LINE_TOTAL}) FILTER (WHERE {_UNSETTLED_SENT}), 0) AS amount, "
        f"BOOL_OR({_ACTIVE_KITCHEN}) AS cooking "
        "FROM pos_session_lines l "
        "JOIN pos_table_sessions s ON s.id = l.session_id "
        "WHERE l.tenant_id = %s AND s.workspace_client_id = %s AND s.status <> 'closed' "
        "GROUP BY l.session_id",
        (tenant_id, workspace_client_id),
    )
    return {
        str(r["session_id"]): {"amount": _d(r["amount"]), "cooking": bool(r["cooking"])}
        for r in cur.fetchall()
    }


# ── 开台 session ──────────────────────────────────────────────────────
def table_has_session_history(cur, *, tenant_id: str, table_id: int) -> bool:
    """该桌是否开过台(含已结账历史)。有历史 → 只能停用不能硬删(留账)。"""
    cur.execute(
        "SELECT 1 FROM pos_table_sessions WHERE tenant_id = %s AND table_id = %s LIMIT 1",
        (tenant_id, table_id),
    )
    return cur.fetchone() is not None


def delete_table(cur, *, tenant_id: str, workspace_client_id: int, table_id: int) -> None:
    """硬删桌台(仅从没开过台的 · 调用方先校验)。按 tenant+workspace 隔离。"""
    cur.execute(
        "DELETE FROM pos_tables WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, table_id),
    )


def get_active_session_for_table(cur, *, tenant_id: str, table_id: int):
    cur.execute(
        "SELECT id, table_id, service_type, party_size, status, opened_at "
        "FROM pos_table_sessions "
        "WHERE tenant_id = %s AND table_id = %s AND status <> 'closed' LIMIT 1",
        (tenant_id, table_id),
    )
    return cur.fetchone()


def get_session(cur, *, tenant_id: str, session_id: str):
    cur.execute(
        "SELECT s.id, s.table_id, t.name AS table_name, s.workspace_client_id, s.service_type, "
        "s.party_size, s.status, s.opened_at, s.closed_at, s.cashier_id, s.note "
        "FROM pos_table_sessions s JOIN pos_tables t ON t.id = s.table_id "
        "WHERE s.tenant_id = %s AND s.id = %s",
        (tenant_id, session_id),
    )
    return cur.fetchone()


def create_session(
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
    cur.execute(
        "INSERT INTO pos_table_sessions "
        "(tenant_id, workspace_client_id, table_id, service_type, party_size, cashier_id, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "RETURNING id, table_id, service_type, party_size, status, opened_at",
        (
            tenant_id,
            workspace_client_id,
            table_id,
            service_type,
            party_size,
            cashier_id,
            created_by,
        ),
    )
    return cur.fetchone()


def set_session_status(cur, *, tenant_id: str, session_id: str, status: str, closed=False) -> None:
    closed_sql = ", closed_at = now()" if closed else ""
    cur.execute(
        f"UPDATE pos_table_sessions SET status = %s{closed_sql} WHERE tenant_id = %s AND id = %s",
        (status, tenant_id, session_id),
    )


# ── 菜品快照(加菜时冻结价/单位/税)────────────────────────────────────
def get_menu_product(cur, *, tenant_id: str, product_id: str):
    cur.execute(
        "SELECT id, base_unit, vat_applicable, unit_price, name_th, name_en, name_zh "
        "FROM products WHERE tenant_id = %s AND id = %s AND is_active = TRUE",
        (tenant_id, product_id),
    )
    return cur.fetchone()


# ── 公共:动态 SET 构造(白名单列 · 防 SQL 注入)────────────────────────
def _build_sets(fields: dict, allowed: tuple) -> tuple[list, list]:
    sets, vals = [], []
    for col in allowed:
        if col in fields and fields[col] is not None:
            sets.append(f"{col} = %s")
            vals.append(fields[col])
    return sets, vals
