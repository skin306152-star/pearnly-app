# -*- coding: utf-8 -*-
"""库存读侧聚合(POS 项目 · PO-A3 · docs/pos/04 §4)。

只读查询,与写侧 store.py 分离。每条语句 WHERE tenant_id + workspace_client_id(应用层隔离)。
GET /api/inventory/stock 的 items+summary、近效期清单都在此组装,路由保持薄层。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


def _f(v) -> Optional[float]:
    return float(v) if v is not None else None


def _status(qty: Decimal, min_stock) -> str:
    if qty <= 0:
        return "out"
    if min_stock is not None and qty < min_stock:
        return "low"
    return "ok"


def stock_overview(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    filter_: str = "all",
    q: Optional[str] = None,
    mask_cost: bool = False,
) -> dict:
    """返回 {"items": [...], "summary": {...}}(04 §4 GET /api/inventory/stock)。

    items:每个在售商品的总在库(跨批求和)+ 阈值 + 均价 + 状态 low/ok/out + 批次明细。
    filter_:low|out|all(在库总量筛选)。q:商品名/条码 ILIKE。
    mask_cost=True(无 field.cost.view 码):均价/库存货值列返 None(G4 成本遮蔽)。
    """
    # 批次均价用【预聚合子查询】join(每商品一行),不直接 join inventory_batches——
    # 否则 stock×batches 笛卡尔积会把 SUM(qty_on_hand) 按批次数重复计(实测 2 批 → 翻倍)。
    # PO-5:商品按套账隔离(对齐 PO-3 products)——此前只 p.tenant_id,会把别套账的商品
    # 也列出来(零库存)。批次均价子查询同步按套账,避免跨套账批次拉低/抬高本套账均价。
    sql = (
        "SELECT p.id AS product_id, p.name_th, p.name_en, p.name_zh, p.barcode, "
        "p.base_unit, p.min_stock, p.default_cost, "
        "COALESCE(SUM(s.qty_on_hand), 0) AS qty_on_hand, "
        "COALESCE(MAX(b.avg_cost), p.default_cost) AS avg_cost "
        "FROM products p "
        "LEFT JOIN inventory_stock s "
        "  ON s.product_id = p.id AND s.tenant_id = p.tenant_id "
        "  AND s.workspace_client_id = %s "
        "LEFT JOIN (SELECT product_id, AVG(unit_cost) AS avg_cost FROM inventory_batches "
        "           WHERE tenant_id = %s AND workspace_client_id = %s "
        "           GROUP BY product_id) b ON b.product_id = p.id "
        "WHERE p.tenant_id = %s AND p.workspace_client_id = %s AND p.is_active = TRUE"
    )
    params: list = [
        workspace_client_id,
        tenant_id,
        workspace_client_id,
        tenant_id,
        workspace_client_id,
    ]
    if q:
        sql += " AND (p.name_th ILIKE %s OR p.name_en ILIKE %s OR p.barcode ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += (
        " GROUP BY p.id, p.name_th, p.name_en, p.name_zh, p.barcode, p.base_unit, "
        "p.min_stock, p.default_cost ORDER BY p.name_th"
    )
    cur.execute(sql, params)
    rows = cur.fetchall()

    batches_by_product = _batches_by_product(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )

    items = []
    sku_count = low_count = out_count = 0
    stock_value = Decimal("0")
    for r in rows:
        qty = Decimal(str(r["qty_on_hand"]))
        status = _status(qty, r["min_stock"])
        if filter_ == "low" and status != "low":
            continue
        if filter_ == "out" and status != "out":
            continue
        if qty != 0:
            sku_count += 1
        if status == "low":
            low_count += 1
        if status == "out":
            out_count += 1
        if r["avg_cost"] is not None:
            stock_value += qty * Decimal(str(r["avg_cost"]))
        items.append(
            {
                "product_id": str(r["product_id"]),
                "name": {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]},
                "barcode": r["barcode"],
                "base_unit": r["base_unit"],
                "qty_on_hand": _f(qty),
                "min_stock": _f(r["min_stock"]),
                "avg_cost": None if mask_cost else _f(r["avg_cost"]),
                "status": status,
                "batches": batches_by_product.get(str(r["product_id"]), []),
            }
        )
    summary = {
        "sku_count": sku_count,
        "stock_value": None if mask_cost else _f(stock_value),
        "low_count": low_count,
        "out_count": out_count,
    }
    return {"items": items, "summary": summary}


def _batches_by_product(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT s.product_id, b.batch_no, b.expiry_date, SUM(s.qty_on_hand) AS qty "
        "FROM inventory_stock s JOIN inventory_batches b ON b.id = s.batch_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.batch_id IS NOT NULL "
        "AND s.qty_on_hand <> 0 "
        "GROUP BY s.product_id, b.batch_no, b.expiry_date "
        "ORDER BY b.expiry_date ASC NULLS LAST",
        (tenant_id, workspace_client_id),
    )
    out: dict = {}
    for r in cur.fetchall():
        out.setdefault(str(r["product_id"]), []).append(
            {
                "batch_no": r["batch_no"],
                "expiry_date": r["expiry_date"].isoformat() if r["expiry_date"] else None,
                "qty": _f(r["qty"]),
            }
        )
    return out


def near_expiry(cur, *, tenant_id: str, workspace_client_id: int, days: int = 30) -> list:
    """近效期清单(04 §4):有库存且 expiry_date <= 今天+days 的批次,按效期升序。"""
    cur.execute(
        "SELECT s.product_id, p.name_th, p.name_en, p.name_zh, b.batch_no, b.expiry_date, "
        "SUM(s.qty_on_hand) AS qty, (b.expiry_date - CURRENT_DATE) AS days_left "
        "FROM inventory_stock s "
        "JOIN inventory_batches b ON b.id = s.batch_id "
        "JOIN products p ON p.id = s.product_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.batch_id IS NOT NULL "
        "AND b.expiry_date IS NOT NULL AND b.expiry_date <= CURRENT_DATE + %s "
        "AND s.qty_on_hand > 0 "
        "GROUP BY s.product_id, p.name_th, p.name_en, p.name_zh, b.batch_no, b.expiry_date "
        "ORDER BY b.expiry_date ASC",
        (tenant_id, workspace_client_id, days),
    )
    out = []
    for r in cur.fetchall():
        out.append(
            {
                "product_id": str(r["product_id"]),
                "name": {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]},
                "batch_no": r["batch_no"],
                "expiry_date": r["expiry_date"].isoformat() if r["expiry_date"] else None,
                "qty": _f(r["qty"]),
                "days_left": int(r["days_left"]) if r["days_left"] is not None else None,
            }
        )
    return out
