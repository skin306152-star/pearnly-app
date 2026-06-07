# -*- coding: utf-8 -*-
"""库存移动编排(POS 项目 · PO-A3 · docs/pos/04 §4)。

apply_movement = 一次原子库存变动:写 immutable 流水 + 同事务物化 inventory_stock(由调用方
的 get_cursor_rls(commit=True) 包成单事务)。离线幂等:带 client_uuid 的请求重复补传 → 命中
原流水即跳过(不重复扣)。receive/adjust/count 是面向接口的高层操作。

单位换算:入库行的 (unit_name, qty) 经 product_units.factor_to_base 折算成 base_unit 落账;
unit_name 缺省或等于 base_unit → factor 1。所有操作先校验商品属本租户(防挂他人商品)。
框架无关:坏输入抛 InventoryError(code),由路由翻成 PosError 信封。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from services.inventory import store


class InventoryError(Exception):
    """库存业务错误 · 携带 06 错误码;路由捕获后转 PosError 信封。"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def assert_product_owned(cur, *, tenant_id: str, product_id: str) -> str:
    """校验商品属本租户且在售;返回其 base_unit。不属/已删 → InventoryError。"""
    cur.execute(
        "SELECT base_unit FROM products WHERE tenant_id = %s AND id = %s AND is_active = TRUE",
        (tenant_id, product_id),
    )
    p = cur.fetchone()
    if not p:
        raise InventoryError("pos.product_not_found")
    return p["base_unit"]


def resolve_factor(cur, *, tenant_id: str, product_id: str, unit_name: Optional[str]) -> Decimal:
    """返回售卖/入库单位换算成 base_unit 的系数;顺带校验商品属本租户。"""
    base_unit = assert_product_owned(cur, tenant_id=tenant_id, product_id=product_id)
    if not unit_name or unit_name == base_unit:
        return Decimal("1")
    cur.execute(
        "SELECT factor_to_base FROM product_units "
        "WHERE tenant_id = %s AND product_id = %s AND unit_name = %s",
        (tenant_id, product_id, unit_name),
    )
    r = cur.fetchone()
    if not r:
        raise InventoryError("pos.line_invalid")
    return Decimal(str(r["factor_to_base"]))


def apply_movement(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    batch_id: Optional[str],
    txn_type: str,
    qty_delta,
    unit_cost=None,
    ref_type=None,
    ref_id=None,
    client_uuid=None,
    reason=None,
    created_by=None,
) -> dict:
    """写一笔流水 + 物化库存。返回 {"txn", "qty_on_hand", "deduped"}。"""
    if client_uuid:
        existing = store.find_txn_by_client_uuid(cur, tenant_id=tenant_id, client_uuid=client_uuid)
        if existing:
            return {"txn": existing, "qty_on_hand": None, "deduped": True}
    txn = store.insert_txn(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        batch_id=batch_id,
        txn_type=txn_type,
        qty_delta=qty_delta,
        unit_cost=unit_cost,
        ref_type=ref_type,
        ref_id=ref_id,
        client_uuid=client_uuid,
        reason=reason,
        created_by=created_by,
    )
    new_qty = store.apply_stock_delta(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        batch_id=batch_id,
        qty_delta=qty_delta,
    )
    return {"txn": txn, "qty_on_hand": new_qty, "deduped": False}


def receive(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    lines: list,
    ref_type: str = "purchase",
    ref_id=None,
    client_uuid=None,
    created_by=None,
) -> dict:
    """入库(进货):逐行换算 base_unit + 建批次 + 加库存。返回 {txn_ids, updated_stock, deduped}。

    请求级幂等锚在首行流水的 client_uuid:重复补传整请求 → 命中即跳过(receive 整体原子)。
    """
    if client_uuid and store.find_txn_by_client_uuid(
        cur, tenant_id=tenant_id, client_uuid=client_uuid
    ):
        return {"txn_ids": [], "updated_stock": [], "deduped": True}

    txn_ids = []
    updated = []
    for i, line in enumerate(lines):
        product_id = line["product_id"]
        factor = resolve_factor(
            cur, tenant_id=tenant_id, product_id=product_id, unit_name=line.get("unit_name")
        )
        qty_base = Decimal(str(line["qty"])) * factor
        if qty_base <= 0:
            raise InventoryError("pos.line_invalid")
        batch_id = None
        if line.get("batch_no"):
            batch = store.get_or_create_batch(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                product_id=product_id,
                batch_no=line["batch_no"],
                expiry_date=line.get("expiry_date"),
                unit_cost=line.get("unit_cost"),
            )
            batch_id = batch["id"]
        mv = apply_movement(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=batch_id,
            txn_type="purchase_in",
            qty_delta=qty_base,
            unit_cost=line.get("unit_cost"),
            ref_type=ref_type,
            ref_id=ref_id,
            client_uuid=client_uuid if i == 0 else None,
            created_by=created_by,
        )
        txn_ids.append(str(mv["txn"]["id"]))
        updated.append({"product_id": str(product_id), "qty_on_hand": float(mv["qty_on_hand"])})
    return {"txn_ids": txn_ids, "updated_stock": updated, "deduped": False}


def adjust(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    batch_id: Optional[str],
    qty_delta,
    reason=None,
    client_uuid=None,
    created_by=None,
) -> dict:
    """手动调整/报损(qty_delta 带符号)。"""
    assert_product_owned(cur, tenant_id=tenant_id, product_id=product_id)
    mv = apply_movement(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_id=batch_id,
        txn_type="adjust",
        qty_delta=qty_delta,
        ref_type="manual",
        client_uuid=client_uuid,
        reason=reason,
        created_by=created_by,
    )
    return {
        "txn_id": str(mv["txn"]["id"]) if not mv["deduped"] else None,
        "qty_on_hand": float(mv["qty_on_hand"]) if mv["qty_on_hand"] is not None else None,
        "deduped": mv["deduped"],
    }


def count(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    lines: list,
    created_by=None,
) -> dict:
    """盘点:实际数对系统数,差异生成 count 调整流水。返回 {adjustments}。"""
    adjustments = []
    for line in lines:
        product_id = line["product_id"]
        batch_id = line.get("batch_id")
        assert_product_owned(cur, tenant_id=tenant_id, product_id=product_id)
        row = store.get_stock_for_update(
            cur,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            batch_id=batch_id,
        )
        system_qty = Decimal(str(row["qty_on_hand"])) if row else Decimal("0")
        counted = Decimal(str(line["counted_qty"]))
        delta = counted - system_qty
        if delta != 0:
            apply_movement(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                warehouse_id=warehouse_id,
                product_id=product_id,
                batch_id=batch_id,
                txn_type="count",
                qty_delta=delta,
                ref_type="count",
                reason="stocktake",
                created_by=created_by,
            )
        adjustments.append(
            {
                "product_id": str(product_id),
                "system_qty": float(system_qty),
                "counted_qty": float(counted),
                "delta": float(delta),
            }
        )
    return {"adjustments": adjustments}
