# -*- coding: utf-8 -*-
"""收发存报表装配:summary(全商品期间汇总)/ card(单商品逐笔明细)/ excluded(未入账清单)。

期间口径(拍板):期初一次性填表 + date_from 之前的全部流水,先滚出一行「期初结转」合成
首行;期间内([date_from, date_to])逐笔展示。有期初记录时只重放 as_of_date 之后的流水
(期初已经把它之前的东西吸收掉了,重放会重复计 —— 这条边界对"as_of_date 之前/之后"
统一生效,不论落在 date_from 哪一侧,防止期初与期间流水在交界处重复计);没有期初记录
就从 0 滚起,可能诚实进入"成本未知"态直到第一笔真实购入。

数字字段一律输出字符串(Decimal 经 JSON 会被前端当 float 解析,精度会漂)。desc/kind
不夹带中文/泰文展示文案 —— i18n 由前端按 kind 挑语言,后端只吐语义。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from services.stockcard import grouping
from services.stockcard import movements as mv_svc
from services.stockcard import opening as opening_svc
from services.stockcard import rolling


def _str(v) -> Optional[str]:
    return None if v is None else str(v)


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _covered_by_opening(d, start_date) -> bool:
    """流水日期是否已被期初(as_of_date)吸收 —— 吸收掉的绝不重放,防与期初重复计。"""
    return start_date is not None and d <= start_date


def _split(movs: list, opening_row: Optional[dict], date_from, date_to) -> tuple[list, list]:
    """一个 key 的全部流水(已按时间排好序)→ (滚进期初的, 期间内逐笔展示的)。"""
    start_date = opening_row["as_of_date"] if opening_row else None
    remaining = [m for m in movs if not _covered_by_opening(m.date, start_date)]
    before = [m for m in remaining if m.date < date_from]
    period = [m for m in remaining if date_from <= m.date <= date_to]
    return before, period


def _base_balance(opening_row: Optional[dict]) -> rolling.Balance:
    if not opening_row:
        return rolling.ZERO_BALANCE
    return rolling.opening_balance(opening_row["qty"], opening_row["unit_cost"])


def _roll_key(movs: list, opening_row: Optional[dict], date_from, date_to):
    """→ (期初结转态, 期末结存态, 期间逐笔行)。"""
    before, period = _split(movs, opening_row, date_from, date_to)
    carried, _ = rolling.roll(_base_balance(opening_row), before)
    final, rows = rolling.roll(carried, period)
    return carried, final, rows


def _fmt_row(r: dict) -> dict:
    return {
        "date": _iso(r["date"]),
        "doc_no": r["doc_no"],
        "kind": r["kind"],
        "desc": r["desc"],
        "qty": str(r["qty"]),
        "unit_price": _str(r["unit_price"]),
        "amount": _str(r["amount"]),
        "bal_qty": str(r["bal_qty"]),
        "bal_unit_cost": _str(r["bal_unit_cost"]),
        "bal_value": _str(r["bal_value"]),
    }


def _sum_qty(rows: list, kind: str) -> Decimal:
    return sum((r["qty"] for r in rows if r["kind"] == kind), Decimal("0"))


def _sum_amount(rows: list, kind: str) -> Decimal:
    return sum(
        (r["amount"] for r in rows if r["kind"] == kind and r["amount"] is not None), Decimal("0")
    )


def summary(cur, *, tenant_id: str, workspace_client_id: int, date_from, date_to) -> dict:
    data = mv_svc.load(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )
    openings = opening_svc.load_by_key(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )

    keys = sorted(set(data.by_key) | set(openings))
    product_ids = [grouping.key_product_id(k) for k in keys if grouping.is_product_key(k)]
    products = mv_svc.product_names(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_ids=product_ids
    )
    name_units = mv_svc.purchase_units(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )

    out = []
    for key in keys:
        carried, final, period_rows = _roll_key(
            data.by_key.get(key, []), openings.get(key), date_from, date_to
        )
        name, unit = mv_svc.key_display_name(key, products, name_units)
        out.append(
            {
                "key": key,
                "product_id": grouping.key_product_id(key),
                "name": name,
                "unit": unit,
                "opening_qty": str(carried.qty),
                "in_qty": str(_sum_qty(period_rows, "in")),
                "out_qty": str(_sum_qty(period_rows, "out")),
                "bal_qty": str(final.qty),
                "bal_unit_cost": _str(final.unit),
                "bal_value": _str(final.value),
                "negative": final.qty < 0,
                "matched": grouping.is_product_key(key),
            }
        )
    excluded_count = len(mv_svc.filter_excluded_by_period(data.excluded, date_from, date_to))
    return {"products": out, "excluded_count": excluded_count}


def card(cur, *, tenant_id: str, workspace_client_id: int, key: str, date_from, date_to) -> Optional[dict]:
    data = mv_svc.load(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
    )
    opening_row = opening_svc.load_by_key(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    ).get(key)
    movs = data.by_key.get(key, [])
    if not movs and not opening_row:
        return None  # 路由层翻 404:这个 key 在本账套从未出现过

    products, name_units = {}, {}
    if grouping.is_product_key(key):
        products = mv_svc.product_names(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_ids=[grouping.key_product_id(key)],
        )
    else:
        name_units = mv_svc.purchase_units(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, date_to=date_to
        )
    name, unit = mv_svc.key_display_name(key, products, name_units)

    carried, final, period_rows = _roll_key(movs, opening_row, date_from, date_to)
    rows = [
        {
            "date": _iso(date_from),
            "doc_no": "",
            "kind": "open",
            "desc": "",
            "qty": str(carried.qty),
            "unit_price": None,
            "amount": None,
            "bal_qty": str(carried.qty),
            "bal_unit_cost": _str(carried.unit),
            "bal_value": _str(carried.value),
        }
    ]
    rows.extend(_fmt_row(r) for r in period_rows)

    return {
        "product": {
            "key": key,
            "product_id": grouping.key_product_id(key),
            "name": name,
            "unit": unit,
        },
        "rows": rows,
        "totals": {
            "in_qty": str(_sum_qty(period_rows, "in")),
            "in_amount": str(_sum_amount(period_rows, "in")),
            "out_qty": str(_sum_qty(period_rows, "out")),
            "out_amount": str(_sum_amount(period_rows, "out")),
            "bal_qty": str(final.qty),
            "bal_unit_cost": _str(final.unit),
            "bal_value": _str(final.value),
        },
    }


def excluded(cur, *, tenant_id: str, workspace_client_id: int, date_from, date_to) -> list:
    rows = mv_svc.excluded_only(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_from=date_from,
        date_to=date_to,
    )
    return [
        {
            "date": _iso(r["date"]),
            "doc_no": r["doc_no"],
            "desc": r["desc"],
            "amount": _str(r["amount"]),
            "reason": r["reason"],
            "side": r["side"],
        }
        for r in rows
    ]
