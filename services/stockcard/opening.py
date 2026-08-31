# -*- coding: utf-8 -*-
"""期初结存 CRUD(一次性填表 · 幂等 upsert)。

商户上线本报表那天,过去的进销存不重放(没有更早的原始票也无从重放),而是由会计
直接填一笔「期初结存」当滚存起点。同一商品/名称在同一账套只留一行 —— 改期初是覆盖
不是累加(表上两条 partial unique 索引保证,upsert 用 ON CONFLICT 命中即更新)。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from core.pos_api import PosError
from services.stockcard import grouping


def _dec(v, *, field: str) -> Decimal:
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise PosError("stockcard.opening_invalid", 422, detail=field) from e


def parse_iso_date(raw, *, code: str, field: str) -> date:
    """ISO 日期字符串(或已是 date 对象)→ date。烂字符串在这里挡下,不留到 SQL 层才炸
    (那会是诚实的 422 变成不诚实的 500)。错误码/字段名由调用方传(期初层
    stockcard.opening_invalid、报表层 routes/stock_card_routes.py 的 stockcard.bad_date
    各自的错误码不同),解析逻辑单一来源(此前 routes/stock_card_routes.py 另有一份同款
    _parse_date)。"""
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw).strip())
    except (ValueError, TypeError) as e:
        raise PosError(code, 422, detail=field) from e


def _normalize(row: dict) -> tuple[Optional[str], Optional[str], Decimal, Decimal, date]:
    """一行期初入参 → (product_id, name_key, qty, unit_cost, as_of_date)。恰一身份非空。"""
    product_id = row.get("product_id") or None
    name_key = None if product_id else grouping.name_key(row.get("name") or "")
    if not product_id and not name_key:
        raise PosError("stockcard.opening_invalid", 422, detail="missing_identity")
    raw_date = row.get("as_of_date")
    if not raw_date:
        raise PosError("stockcard.opening_invalid", 422, detail="missing_as_of_date")
    as_of_date = parse_iso_date(raw_date, code="stockcard.opening_invalid", field="as_of_date")
    qty = _dec(row.get("qty", 0), field="qty")
    unit_cost = _dec(row.get("unit_cost", 0), field="unit_cost")
    return product_id, name_key, qty, unit_cost, as_of_date


_COLS = "id, product_id, name_key, qty, unit_cost, as_of_date, created_at, updated_at"

_UPSERT_ID_COLS = frozenset({"product_id", "name_key"})


def _upsert_sql(id_col: str) -> str:
    """product_id/name_key 两条 upsert 语句共用同一模板,只身份列名不同(WHERE 子句挡的是
    两条 partial unique 索引各自的一半:product_id 行不撞 name_key 索引,反之亦然)。id_col
    白名单断言 —— 当前调用点都是硬编码常量,断言是防以后改成外部可控值时悄悄开一个
    SQL 拼接注入面,不是当前就有洞。"""
    if id_col not in _UPSERT_ID_COLS:
        raise ValueError(f"unsupported id_col: {id_col!r}")
    return (
        f"INSERT INTO stock_card_openings (tenant_id, workspace_client_id, {id_col}, "
        f"qty, unit_cost, as_of_date, created_by) VALUES (%s,%s,%s,%s,%s,%s,%s) "
        f"ON CONFLICT (tenant_id, workspace_client_id, {id_col}) WHERE {id_col} IS NOT NULL "
        f"DO UPDATE SET qty = EXCLUDED.qty, unit_cost = EXCLUDED.unit_cost, "
        f"as_of_date = EXCLUDED.as_of_date, updated_at = now() "
        f"RETURNING {_COLS}"
    )


_UPSERT_PRODUCT = _upsert_sql("product_id")
_UPSERT_NAME = _upsert_sql("name_key")


def upsert_openings(
    cur, *, tenant_id: str, workspace_client_id: int, rows: list[dict], created_by: Optional[str]
) -> list[dict]:
    """批量幂等写期初(逐行 upsert,单条错误即整批 422 —— 期初是一次性动作,不做部分成功)。"""
    out = []
    for raw in rows:
        product_id, name_key, qty, unit_cost, as_of_date = _normalize(raw)
        if product_id:
            cur.execute(
                _UPSERT_PRODUCT,
                (
                    tenant_id,
                    workspace_client_id,
                    product_id,
                    qty,
                    unit_cost,
                    as_of_date,
                    created_by,
                ),
            )
        else:
            cur.execute(
                _UPSERT_NAME,
                (tenant_id, workspace_client_id, name_key, qty, unit_cost, as_of_date, created_by),
            )
        out.append(cur.fetchone())
    return out


def list_openings(
    cur, *, tenant_id: str, workspace_client_id: int, created_by: Optional[str] = None
) -> list[dict]:
    sql = (
        f"SELECT {_COLS} FROM stock_card_openings "
        "WHERE tenant_id = %s AND workspace_client_id = %s"
    )
    params: list = [tenant_id, workspace_client_id]
    if created_by is not None:
        sql += " AND created_by = %s"
        params.append(created_by)
    sql += " ORDER BY as_of_date, created_at"
    cur.execute(sql, tuple(params))
    return cur.fetchall()


def load_by_key(
    cur, *, tenant_id: str, workspace_client_id: int, created_by: Optional[str] = None
) -> dict:
    """取本账套全部期初,按 grouping key(p:<id> / n:<name>)映射,供 report.py 装配用。"""
    rows = list_openings(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        created_by=created_by,
    )
    out: dict = {}
    for r in rows:
        key = (
            f"{grouping.PRODUCT_PREFIX}{r['product_id']}"
            if r.get("product_id")
            else f"{grouping.NAME_PREFIX}{r['name_key']}"
        )
        out[key] = r
    return out
