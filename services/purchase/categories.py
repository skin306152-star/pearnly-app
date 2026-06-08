# -*- coding: utf-8 -*-
"""费用科目 DAL · 两级树(商户采购 · 套账隔离 · docs/purchasing/01-02 §6)。

parent_id NULL=大类,非空=子类(严格两级,不许三级)。AI 归类把费用映射到子类。预设按
(tenant,ws) 懒种子:首次读到空树时插入泰国标准科目(用户可增删改)。隔离=每句 WHERE
tenant_id + workspace_client_id;值一律 %s 参数化。调用方负责事务。
"""

from __future__ import annotations

from typing import Optional

_SELECT = "id, parent_id, name, is_active, sort"

# 预设(大类 → 子类)· 泰国小商户常用费用科目(默认市场语言 th · 用户可改)。
_PRESET: tuple = (
    ("ซื้อสินค้า", ()),
    ("ค่าเดินทาง", ("ค่าแท็กซี่", "ค่าน้ำมัน")),
    ("ค่าสาธารณูปโภค", ("ค่าน้ำ", "ค่าไฟ")),
    ("ค่าสำนักงาน", ("เครื่องเขียน", "อุปกรณ์")),
    ("ค่าทำความสะอาด", ()),
    ("ค่าเช่า", ()),
    ("ค่าโฆษณา", ()),
    ("ค่าซ่อมบำรุง", ()),
    ("ค่าจ้างบริการภายนอก", ()),
)


def _count(cur, *, tenant_id: str, workspace_client_id: int) -> int:
    cur.execute(
        "SELECT count(*) AS n FROM expense_categories "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return int(row["n"]) if row else 0


def _insert(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    name: str,
    parent_id: Optional[str],
    sort: int,
) -> dict:
    cur.execute(
        "INSERT INTO expense_categories "
        "(tenant_id, workspace_client_id, parent_id, name, sort) "
        "VALUES (%s, %s, %s, %s, %s) "
        f"RETURNING {_SELECT}",
        (tenant_id, workspace_client_id, parent_id, name, sort),
    )
    return cur.fetchone()


def seed_presets(cur, *, tenant_id: str, workspace_client_id: int) -> None:
    """空树时插入预设两级科目(幂等:仅当本套账零科目才种)。"""
    if _count(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id) > 0:
        return
    for i, (parent_name, children) in enumerate(_PRESET):
        parent = _insert(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            name=parent_name,
            parent_id=None,
            sort=i,
        )
        for j, child_name in enumerate(children):
            _insert(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                name=child_name,
                parent_id=parent["id"],
                sort=j,
            )


def get_tree(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """返回两级科目树:[{...大类, children:[...子类]}]。空树先种预设再读。"""
    if _count(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id) == 0:
        seed_presets(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    cur.execute(
        f"SELECT {_SELECT} FROM expense_categories "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "ORDER BY sort, name",
        (tenant_id, workspace_client_id),
    )
    rows = cur.fetchall()
    parents = [dict(r, children=[]) for r in rows if r["parent_id"] is None]
    by_id = {p["id"]: p for p in parents}
    for r in rows:
        if r["parent_id"] is not None and r["parent_id"] in by_id:
            by_id[r["parent_id"]]["children"].append(dict(r))
    return parents


def _is_top_level(cur, *, tenant_id: str, workspace_client_id: int, category_id: str) -> bool:
    """该科目是否大类(parent_id IS NULL)· 校验两级不超深用。"""
    cur.execute(
        "SELECT parent_id FROM expense_categories "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, category_id),
    )
    row = cur.fetchone()
    return row is not None and row["parent_id"] is None


def create_category(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    name: str,
    parent_id: Optional[str] = None,
    sort: int = 0,
) -> Optional[dict]:
    """建科目。带 parent_id 时父必须是本套账大类(拒绝三级 → 返回 None)。"""
    clean = (name or "").strip()
    if not clean:
        return None
    if parent_id is not None:
        if not _is_top_level(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            category_id=parent_id,
        ):
            return None
    return _insert(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        name=clean,
        parent_id=parent_id,
        sort=int(sort or 0),
    )


def update_category(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    category_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort: Optional[int] = None,
) -> Optional[dict]:
    sets, params = [], []
    if name is not None and name.strip():
        sets.append("name = %s")
        params.append(name.strip())
    if is_active is not None:
        sets.append("is_active = %s")
        params.append(bool(is_active))
    if sort is not None:
        sets.append("sort = %s")
        params.append(int(sort))
    if not sets:
        return None
    set_clause = ", ".join(sets)
    params += [tenant_id, workspace_client_id, category_id]
    cur.execute(
        f"UPDATE expense_categories SET {set_clause} "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING {_SELECT}",
        tuple(params),
    )
    return cur.fetchone()


def delete_category(cur, *, tenant_id: str, workspace_client_id: int, category_id: str) -> None:
    """删科目(子类随 FK ON DELETE CASCADE 一并删)。"""
    cur.execute(
        "DELETE FROM expense_categories "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, category_id),
    )
