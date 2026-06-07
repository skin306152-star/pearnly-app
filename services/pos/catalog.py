# -*- coding: utf-8 -*-
"""POS 选品 + 前台启动包(POS 项目 · PO-B2 · docs/pos/04 §1/§3)。

复用 products + product_units + 实时库存(默认仓总在库)。选品/扫码/bootstrap 都只读;每条语句
WHERE tenant_id。库存数随快照下发支撑离线选品(08 ADR-1)。near_expiry = 该商品任一批
expiry_date <= 今天 + near_expiry_days。
"""

from __future__ import annotations

from typing import Optional

from services.inventory import store as inv_store
from services.modules import store as modules_store
from services.pos import cashier as cashier_dal

_DEFAULT_NEAR_EXPIRY_DAYS = 30


def _name(r) -> dict:
    return {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]}


def _units_by_product(cur, *, tenant_id: str, product_ids: list) -> dict:
    if not product_ids:
        return {}
    cur.execute(
        "SELECT product_id, unit_name, factor_to_base, barcode, price, is_default_sell "
        "FROM product_units WHERE tenant_id = %s AND product_id = ANY(%s) "
        "ORDER BY factor_to_base",
        (tenant_id, product_ids),
    )
    out: dict = {}
    for r in cur.fetchall():
        out.setdefault(str(r["product_id"]), []).append(
            {
                "unit_name": r["unit_name"],
                "factor": f"{r['factor_to_base']:.3f}",
                "barcode": r["barcode"],
                "price": f"{r['price']:.2f}" if r["price"] is not None else None,
                "default_sell": bool(r["is_default_sell"]),
            }
        )
    return out


def _stock_by_product(cur, *, tenant_id: str, workspace_client_id: int, near_days: int) -> dict:
    """每商品默认仓总在库 + 近效期标记(预聚合 · 防 stock×batches 笛卡尔积翻倍)。"""
    cur.execute(
        "SELECT product_id, COALESCE(SUM(qty_on_hand), 0) AS qty FROM inventory_stock "
        "WHERE tenant_id = %s AND workspace_client_id = %s GROUP BY product_id",
        (tenant_id, workspace_client_id),
    )
    qty = {str(r["product_id"]): r["qty"] for r in cur.fetchall()}
    cur.execute(
        "SELECT DISTINCT s.product_id FROM inventory_stock s "
        "JOIN inventory_batches b ON b.id = s.batch_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.qty_on_hand > 0 "
        "AND b.expiry_date IS NOT NULL AND b.expiry_date <= CURRENT_DATE + %s",
        (tenant_id, workspace_client_id, near_days),
    )
    near = {str(r["product_id"]) for r in cur.fetchall()}
    return {"qty": qty, "near": near}


def _row_to_item(r, units: dict, stock: dict) -> dict:
    pid = str(r["id"])
    base_units = units.get(pid)
    if not base_units:
        base_units = [
            {
                "unit_name": r["base_unit"],
                "factor": "1.000",
                "barcode": r["barcode"],
                "price": f"{r['unit_price']:.2f}" if r["unit_price"] is not None else None,
                "default_sell": True,
            }
        ]
    q = stock["qty"].get(pid)
    return {
        "id": pid,
        "name": _name(r),
        "category_id": r["category_id"],
        "base_unit": r["base_unit"],
        "image_url": r["image_url"],
        "vat_applicable": bool(r["vat_applicable"]),
        "units": base_units,
        "track_batch": bool(r["track_batch"]),
        "is_weighed": bool(r["is_weighed"]),
        "stock": {
            "qty_base": f"{q:.3f}" if q is not None else "0.000",
            "near_expiry": pid in stock["near"],
        },
    }


_PROD_COLS = (
    "id, name_th, name_en, name_zh, category_id, barcode, base_unit, image_url, "
    "vat_applicable, track_batch, is_weighed, unit_price"
)


def list_products(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    q: Optional[str] = None,
    category: Optional[str] = None,
    near_days: int = _DEFAULT_NEAR_EXPIRY_DAYS,
) -> dict:
    sql = f"SELECT {_PROD_COLS} FROM products " f"WHERE tenant_id = %s AND is_active = TRUE"
    params: list = [tenant_id]
    if q:
        sql += " AND (name_th ILIKE %s OR name_en ILIKE %s OR barcode ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    if category:
        sql += " AND category_id = %s"
        params.append(category)
    sql += " ORDER BY name_th LIMIT 500"
    cur.execute(sql, params)
    rows = cur.fetchall()
    pids = [str(r["id"]) for r in rows]
    units = _units_by_product(cur, tenant_id=tenant_id, product_ids=pids)
    stock = _stock_by_product(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, near_days=near_days
    )
    return {"items": [_row_to_item(r, units, stock) for r in rows]}


def product_by_barcode(cur, *, tenant_id: str, workspace_client_id: int, code: str) -> dict:
    """扫码取单品。先配单位码(箱码≠瓶码),再配商品主码;命中单位回 matched_unit。"""
    cur.execute(
        "SELECT product_id, unit_name FROM product_units "
        "WHERE tenant_id = %s AND barcode = %s LIMIT 1",
        (tenant_id, code),
    )
    u = cur.fetchone()
    matched_unit = None
    if u:
        product_id = str(u["product_id"])
        matched_unit = u["unit_name"]
        cur.execute(
            f"SELECT {_PROD_COLS} FROM products WHERE tenant_id = %s AND id = %s AND is_active = TRUE",
            (tenant_id, product_id),
        )
    else:
        cur.execute(
            f"SELECT {_PROD_COLS} FROM products "
            f"WHERE tenant_id = %s AND barcode = %s AND is_active = TRUE LIMIT 1",
            (tenant_id, code),
        )
    row = cur.fetchone()
    if not row:
        from core.pos_api import PosError

        raise PosError("pos.product_not_found", 404)
    units = _units_by_product(cur, tenant_id=tenant_id, product_ids=[str(row["id"])])
    stock = _stock_by_product(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        near_days=_DEFAULT_NEAR_EXPIRY_DAYS,
    )
    item = _row_to_item(row, units, stock)
    item["matched_unit"] = matched_unit or row["base_unit"]
    return item


def bootstrap(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """前台启动包(登录后一次拉全 · 支撑离线)。"""
    modules = modules_store.get_modules(cur, tenant_id=tenant_id)
    pos_cfg = modules.get("pos", {}).get("config", {}) or {}
    near_days = int(pos_cfg.get("near_expiry_days", _DEFAULT_NEAR_EXPIRY_DAYS))
    cur.execute(
        "SELECT id, name, address, tax_id, phone, promptpay_id FROM workspace_clients "
        "WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    store_row = cur.fetchone()
    terminals = cashier_dal.list_terminals(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    products = list_products(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, near_days=near_days
    )["items"]
    inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    return {
        "store": dict(store_row) | {"id": store_row["id"]} if store_row else None,
        "modules": modules,
        "products": products,
        "terminals": [dict(t) for t in terminals],
        "settings": {
            "allow_price_edit": bool(pos_cfg.get("allow_price_edit", False)),
            "allow_discount": bool(pos_cfg.get("allow_discount", True)),
            "near_expiry_days": near_days,
        },
    }
