# -*- coding: utf-8 -*-
"""POS 库存联动 — 卖出扣减(FEFO)+ 退货/作废回补(POS 项目 · PO-B2 · docs/pos/03 §3)。

复用库存域:批次品按 fefo 先效先出选批扣;非批次品扣 batch NULL 行。每笔写 immutable
inventory_transactions(ref_type=pos_sale/pos_refund/pos_void · ref_id=单据)+ 同事务物化
inventory_stock(由调用方单事务包)。在线建单:库存不足直接 pos.out_of_stock(离线乐观扣+
允许负库存是 PWA 层的事 · 见 08 ADR-5)。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.inventory import fefo, ledger
from services.inventory import store as inv_store


def deduct_for_sale(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    qty_base,
    track_batch: bool,
    explicit_batch_id: Optional[str],
    sale_id: str,
    created_by=None,
) -> Optional[str]:
    """卖出扣库存,返回记到行上的 batch_id(非批次=None;多批 FEFO=首批)。不足 → out_of_stock。"""
    need = Decimal(str(qty_base))
    if explicit_batch_id:
        _check_and_move(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=explicit_batch_id,
            qty=need,
            sale_id=sale_id,
            created_by=created_by,
        )
        return explicit_batch_id
    if not track_batch:
        _check_and_move(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=None,
            qty=need,
            sale_id=sale_id,
            created_by=created_by,
        )
        return None
    alloc = fefo.select_batches_for_outflow(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        qty_needed=need,
    )
    if alloc["shortfall"] > 0:
        raise PosError("pos.out_of_stock", 409, detail=str(product_id))
    first = None
    for a in alloc["allocations"]:
        ledger.apply_movement(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            batch_id=a["batch_id"],
            txn_type="sale_out",
            qty_delta=-Decimal(str(a["qty"])),
            ref_type="pos_sale",
            ref_id=sale_id,
            created_by=created_by,
        )
        first = first or a["batch_id"]
    return first


def _check_and_move(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    batch_id: Optional[str],
    qty: Decimal,
    sale_id: str,
    created_by=None,
) -> None:
    row = inv_store.get_stock_for_update(
        cur,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        batch_id=batch_id,
    )
    avail = Decimal(str(row["qty_on_hand"])) if row else Decimal("0")
    if avail < qty:
        raise PosError("pos.out_of_stock", 409, detail=str(product_id))
    ledger.apply_movement(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_id=batch_id,
        txn_type="sale_out",
        qty_delta=-qty,
        ref_type="pos_sale",
        ref_id=sale_id,
        created_by=created_by,
    )


def restock(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    batch_id: Optional[str],
    qty_base,
    ref_type: str,
    ref_id: str,
    txn_type: str = "return_in",
    created_by=None,
) -> None:
    """退货/作废回补库存(原批次正向移动)。"""
    ledger.apply_movement(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        batch_id=batch_id,
        txn_type=txn_type,
        qty_delta=Decimal(str(qty_base)),
        ref_type=ref_type,
        ref_id=ref_id,
        created_by=created_by,
    )
