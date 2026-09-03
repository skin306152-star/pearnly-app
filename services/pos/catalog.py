# -*- coding: utf-8 -*-
"""POS 选品 + 前台启动包(POS 项目 · PO-B2 · docs/pos/04 §1/§3)。

复用 products + product_units + 实时库存(默认仓总在库)。选品/扫码/bootstrap 都只读;每条语句
WHERE tenant_id。库存数随快照下发支撑离线选品(08 ADR-1)。near_expiry = 该商品任一批
expiry_date <= 今天 + near_expiry_days。
"""

from __future__ import annotations

from typing import Optional

from services.inventory import queries as inv_queries
from services.inventory import store as inv_store
from services.modules import store as modules_store
from services.pos import cashier as cashier_dal
from services.pos import caps as caps_svc

_DEFAULT_NEAR_EXPIRY_DAYS = 30


def _name(r) -> dict:
    return {"th": r["name_th"], "en": r["name_en"], "zh": r["name_zh"]}


def _units_by_product(cur, *, tenant_id: str, workspace_client_id: int, product_ids: list) -> dict:
    if not product_ids:
        return {}
    cur.execute(
        "SELECT product_id, unit_name, factor_to_base, barcode, price, is_default_sell "
        "FROM product_units WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND product_id = ANY(%s::uuid[]) ORDER BY factor_to_base",
        (tenant_id, workspace_client_id, product_ids),
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


def _stock_by_product(
    cur, *, tenant_id: str, workspace_client_id: int, near_days: int, product_ids: list
) -> dict:
    """这批商品的默认仓总在库 + 近效期标记。两条查询分开(SUM 不 join batches · 防笛卡尔积翻倍 ·
    见 [[pos-po-a1-shipped]])。只聚合本页 product_ids(大商品库时不全表扫)。空列表直接返回空。"""
    if not product_ids:
        return {"qty": {}, "near": set()}
    cur.execute(
        "SELECT product_id, COALESCE(SUM(qty_on_hand), 0) AS qty FROM inventory_stock "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = ANY(%s::uuid[]) "
        "GROUP BY product_id",
        (tenant_id, workspace_client_id, product_ids),
    )
    qty = {str(r["product_id"]): r["qty"] for r in cur.fetchall()}
    cur.execute(
        "SELECT DISTINCT s.product_id FROM inventory_stock s "
        "JOIN inventory_batches b ON b.id = s.batch_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.product_id = ANY(%s::uuid[]) "
        "AND s.qty_on_hand > 0 AND b.expiry_date IS NOT NULL "
        "AND b.expiry_date <= CURRENT_DATE + %s",
        (tenant_id, workspace_client_id, product_ids, near_days),
    )
    near = {str(r["product_id"]) for r in cur.fetchall()}
    return {"qty": qty, "near": near}


def _row_to_item(r, units: dict, stock: dict, *, avg_cost=None, cost_visible: bool = False) -> dict:
    pid = str(r["id"])
    base_price = f"{r['unit_price']:.2f}" if r["unit_price"] is not None else None
    base_units = units.get(pid)
    if not base_units:
        base_units = [
            {
                "unit_name": r["base_unit"],
                "factor": "1.000",
                "barcode": r["barcode"],
                "price": base_price,
                "default_sell": True,
            }
        ]
    q = stock["qty"].get(pid)
    return {
        "id": pid,
        "name": _name(r),
        "category_id": r["category_id"],
        "base_unit": r["base_unit"],
        # 建了命名单位行(箱/打)的商品,units 里就只有那几行,基本单位的挂牌价一个字都没下发。
        # 扫商品主码时后端把 matched_unit 填成基本单位(见 product_by_barcode)→ 前端在 units 里
        # 找不到它,只能一律拒收,这瓶货在收银台就卖不出去了。后端本来认基本单位
        # (services/pos/sale.py 的 _resolve_unit 走 products.unit_price),缺的只是这一行。
        "base_price": base_price,
        "avg_cost": f"{avg_cost:.2f}" if cost_visible and avg_cost is not None else None,
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


def _cost_projection(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    product_ids: list,
    operator: Optional[dict],
) -> tuple[bool, dict]:
    if not operator:
        return False, {}
    caps = caps_svc.operator_caps(
        cur,
        user=operator,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
    )
    if not caps.get("cost_visible"):
        return False, {}
    return True, inv_queries.average_costs_by_product(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_ids=product_ids,
    )


def list_products(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    q: Optional[str] = None,
    category: Optional[str] = None,
    near_days: int = _DEFAULT_NEAR_EXPIRY_DAYS,
    operator: Optional[dict] = None,
) -> dict:
    sql = (
        f"SELECT {_PROD_COLS} FROM products "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE"
    )
    params: list = [tenant_id, workspace_client_id]
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
    units = _units_by_product(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_ids=pids
    )
    stock = _stock_by_product(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        near_days=near_days,
        product_ids=pids,
    )
    cost_visible, costs = _cost_projection(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_ids=pids,
        operator=operator,
    )
    return {
        "items": [
            _row_to_item(
                r,
                units,
                stock,
                avg_cost=costs.get(str(r["id"])),
                cost_visible=cost_visible,
            )
            for r in rows
        ]
    }


def product_by_barcode(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    code: str,
    operator: Optional[dict] = None,
) -> dict:
    """扫码取单品。先配单位码(箱码≠瓶码),再配商品主码;命中单位回 matched_unit。

    单位码查询带 product_active:停用商品的单位行保留 barcode 值(靠谓词让位 · 见
    services/sales/products._set_unit_visibility),不筛就有多条同码行,`LIMIT 1` 无 ORDER BY
    挑中哪条全看运气 —— 那是钱路径。命中单位但商品已停用(老库里 product_active 回填前的
    残留行)时回落主码,跟主 SPA 的 find_by 同一套口径:两边分叉过一次,POS 认得的箱码在
    建品查重那边显示"没人用",绿字骗人还放行重码。不回落就是收银员对着列表里明明在的商品
    看 404「商品不存在」,台前没处可查。
    """
    cur.execute(
        "SELECT product_id, unit_name FROM product_units "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND barcode = %s "
        "AND product_active LIMIT 1",
        (tenant_id, workspace_client_id, code),
    )
    u = cur.fetchone()
    matched_unit = None
    row = None
    if u:
        cur.execute(
            f"SELECT {_PROD_COLS} FROM products "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND is_active = TRUE",
            (tenant_id, workspace_client_id, str(u["product_id"])),
        )
        row = cur.fetchone()
        if row:
            matched_unit = u["unit_name"]
    if not row:
        cur.execute(
            f"SELECT {_PROD_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s "
            "AND barcode = %s AND is_active = TRUE LIMIT 1",
            (tenant_id, workspace_client_id, code),
        )
        row = cur.fetchone()
    if not row:
        from core.pos_api import PosError

        raise PosError("pos.product_not_found", 404)
    units = _units_by_product(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_ids=[str(row["id"])],
    )
    stock = _stock_by_product(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        near_days=_DEFAULT_NEAR_EXPIRY_DAYS,
        product_ids=[str(row["id"])],
    )
    cost_visible, costs = _cost_projection(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_ids=[str(row["id"])],
        operator=operator,
    )
    item = _row_to_item(
        row,
        units,
        stock,
        avg_cost=costs.get(str(row["id"])),
        cost_visible=cost_visible,
    )
    item["matched_unit"] = matched_unit or row["base_unit"]
    return item


def bootstrap(
    cur, *, tenant_id: str, workspace_client_id: int, operator: Optional[dict] = None
) -> dict:
    """前台启动包(登录后一次拉全 · 支撑离线)。"""
    modules = modules_store.get_modules(cur, tenant_id=tenant_id)
    pos_cfg = modules.get("pos", {}).get("config", {}) or {}
    near_days = int(pos_cfg.get("near_expiry_days", _DEFAULT_NEAR_EXPIRY_DAYS))
    # 合规字段(G1)随店档下发:离线/兜底本地小票要与服务端 PDF 同轴(法定抬头按
    # vat_registered 切、Register No. 有号才印、footer_text 页脚)。
    cur.execute(
        "SELECT id, name, address, tax_id, phone, promptpay_id, "
        "vat_registered, pos_register_no, footer_text FROM workspace_clients "
        "WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    store_row = cur.fetchone()
    terminals = cashier_dal.list_terminals(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    products = list_products(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        near_days=near_days,
        operator=operator,
    )["items"]
    inv_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    from services.pos import payment_settings as pay_settings

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
        # 收款设置(老板配)→ 收银端按此显隐支付方式 / 出码用配的 PromptPay ID / 服务费·含VAT。
        # promptpay_id 复用上面 store_row 已查到的值,免 get_settings 再查一次 workspace_clients。
        "payment": pay_settings.get_settings(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            promptpay_id=(store_row["promptpay_id"] if store_row else ""),
            vat_registered=bool(store_row and store_row["vat_registered"]),
        ),
    }
