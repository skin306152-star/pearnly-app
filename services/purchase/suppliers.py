# -*- coding: utf-8 -*-
"""供应商主数据 DAL(商户采购 · 套账隔离 · docs/purchasing/01-02 §5)。

供应商归套账(workspace_client_id)不归租户。AI 拍票自动建为主(见过的按税号匹配),手录兜底。
隔离=每句 WHERE tenant_id + workspace_client_id;值一律 %s 参数化,列名走模块常量白名单。
tax_id 13 位可空;停用=is_active 不删;删除仅限零单据(防悬挂引用)。调用方负责事务。
"""

from __future__ import annotations

import re
from typing import Optional

# 写入列白名单(SQL 内插只允许这串模块常量,杜绝拼接用户输入 · 见 test_purchase_sql_isolation)。
_COLS = (
    "name",
    "tax_id",
    "branch_type",
    "branch_no",
    "address",
    "phone",
    "note",
)
_SELECT = (
    "id, name, tax_id, branch_type, branch_no, address, phone, note, "
    "is_active, created_at, updated_at"
)
_BRANCH_TYPES = ("none", "head_office", "branch")
_TAX_RE = re.compile(r"^\d{13}$")


def is_valid_tax_id(tax_id) -> bool:
    """泰国税号 = 13 位数字(空表示小供应商无税号,合法)。"""
    if tax_id in (None, ""):
        return True
    return bool(_TAX_RE.match(str(tax_id).strip()))


def _clean(fields: dict) -> dict:
    """规整入参:strip 文本、branch_type 落白名单、空串归 None。"""
    out: dict = {}
    for col in _COLS:
        v = fields.get(col)
        if isinstance(v, str):
            v = v.strip() or None
        out[col] = v
    if out.get("branch_type") not in _BRANCH_TYPES:
        out["branch_type"] = "none"
    return out


def find_by_tax_id(cur, *, tenant_id: str, workspace_client_id: int, tax_id: str) -> Optional[dict]:
    """按税号在本套账找供应商(AI 拍票去重/匹配用)。无税号返回 None。"""
    if not tax_id:
        return None
    cur.execute(
        f"SELECT {_SELECT} FROM suppliers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND tax_id = %s",
        (tenant_id, workspace_client_id, str(tax_id).strip()),
    )
    return cur.fetchone()


def list_suppliers(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    q: Optional[str] = None,
    include_inactive: bool = False,
) -> list:
    """列本套账供应商(名/税号搜 · 默认只活跃)。"""
    sql = f"SELECT {_SELECT} FROM suppliers " "WHERE tenant_id = %s AND workspace_client_id = %s"
    params: list = [tenant_id, workspace_client_id]
    if not include_inactive:
        sql += " AND is_active = TRUE"
    if q:
        sql += " AND (name ILIKE %s OR tax_id ILIKE %s)"
        like = f"%{q.strip()}%"
        params += [like, like]
    sql += " ORDER BY name"
    cur.execute(sql, tuple(params))
    return cur.fetchall()


def get_supplier(
    cur, *, tenant_id: str, workspace_client_id: int, supplier_id: str
) -> Optional[dict]:
    cur.execute(
        f"SELECT {_SELECT} FROM suppliers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, supplier_id),
    )
    return cur.fetchone()


def _find_by_canonical_brand(cur, *, tenant_id, workspace_client_id, brand) -> Optional[dict]:
    """已知大连锁:在本套账按归一品牌键找既有供应商。

    税号缺失时(便利店随手记账常无税号)也能并 7-Eleven/711 这类同一连锁的不同写法,
    避免各建一个供应商。仅 create_supplier 在 is_known_brand 命中时调用。
    """
    from services.expense import merchant

    cur.execute(
        f"SELECT {_SELECT} FROM suppliers " "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    for row in cur.fetchall():
        if merchant.canonical_merchant(row["name"], row.get("tax_id") or "") == brand:
            return row
    return None


def create_supplier(cur, *, tenant_id: str, workspace_client_id: int, **fields) -> dict:
    """建供应商。给了税号且本套账已存在 → 返回既有(AI 匹配语义,不重复建)。

    无税号但属已知大连锁 → 按归一品牌键复用既有(治 7-Eleven/711 各建一个供应商);
    通用小店名不并(防误并两个不同的同名小店)。
    """
    from services.expense import merchant

    data = _clean(fields)
    existing = find_by_tax_id(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, tax_id=data["tax_id"]
    )
    if existing is not None:
        return existing
    if data["name"] and merchant.is_known_brand(data["name"]):
        brand = merchant.canonical_merchant(data["name"], data["tax_id"] or "")
        if brand:
            hit = _find_by_canonical_brand(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, brand=brand
            )
            if hit is not None:
                return hit
    cur.execute(
        f"INSERT INTO suppliers (tenant_id, workspace_client_id, {', '.join(_COLS)}) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
        f"RETURNING {_SELECT}",
        (
            tenant_id,
            workspace_client_id,
            data["name"],
            data["tax_id"],
            data["branch_type"],
            data["branch_no"],
            data["address"],
            data["phone"],
            data["note"],
        ),
    )
    return cur.fetchone()


def update_supplier(
    cur, *, tenant_id: str, workspace_client_id: int, supplier_id: str, **fields
) -> Optional[dict]:
    """改供应商(仅传入列)。无可改列 → 返回当前。"""
    data = _clean(fields)
    sets, params = [], []
    for col in _COLS:
        if col in fields:
            sets.append(f"{col} = %s")
            params.append(data[col])
    if not sets:
        return get_supplier(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            supplier_id=supplier_id,
        )
    sets.append("updated_at = now()")
    set_clause = ", ".join(sets)
    params += [tenant_id, workspace_client_id, supplier_id]
    cur.execute(
        f"UPDATE suppliers SET {set_clause} "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING {_SELECT}",
        tuple(params),
    )
    return cur.fetchone()


def set_active(
    cur, *, tenant_id: str, workspace_client_id: int, supplier_id: str, is_active: bool
) -> Optional[dict]:
    """停用/启用(停用=隐藏不删)。"""
    cur.execute(
        "UPDATE suppliers SET is_active = %s, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING {_SELECT}",
        (bool(is_active), tenant_id, workspace_client_id, supplier_id),
    )
    return cur.fetchone()


def doc_count(cur, *, tenant_id: str, workspace_client_id: int, supplier_id: str) -> int:
    """该供应商关联单据数(删除前校验:仅零单据可删)。"""
    cur.execute(
        "SELECT count(*) AS n FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND supplier_id = %s",
        (tenant_id, workspace_client_id, supplier_id),
    )
    row = cur.fetchone()
    return int(row["n"]) if row else 0


def delete_supplier(cur, *, tenant_id: str, workspace_client_id: int, supplier_id: str) -> None:
    """硬删供应商(调用方已校验零单据)。"""
    cur.execute(
        "DELETE FROM suppliers " "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, supplier_id),
    )
