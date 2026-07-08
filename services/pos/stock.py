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
        return _deduct_non_batch(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            need=need,
            sale_id=sale_id,
            created_by=created_by,
        )
    # 批次品:FEFO 先效先出选批;批次不足则从散装(无批次)行兜底——批次品若混有散装货
    # (进货没填批号 → 货进散装桶),否则同样"看得见卖不出"。总量不足才 out_of_stock。
    alloc = fefo.select_batches_for_outflow(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        qty_needed=need,
    )
    moves = [(a["batch_id"], Decimal(str(a["qty"]))) for a in alloc["allocations"]]
    shortfall = alloc["shortfall"]
    if shortfall > 0:
        take_loose = min(
            shortfall,
            _loose_on_hand(
                cur, tenant_id=tenant_id, product_id=product_id, warehouse_id=warehouse_id
            ),
        )
        if shortfall - take_loose > 0:
            raise PosError("pos.out_of_stock", 409, detail=str(product_id))
        if take_loose > 0:
            moves.append((None, take_loose))
    return _apply_sale_moves(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        moves=moves,
        sale_id=sale_id,
        created_by=created_by,
    )


def _loose_on_hand(cur, *, tenant_id: str, product_id: str, warehouse_id: int) -> Decimal:
    """散装行(batch NULL)当前库存;无行=0。已 FOR UPDATE 锁行(get_stock_for_update)。"""
    row = inv_store.get_stock_for_update(
        cur, tenant_id=tenant_id, product_id=product_id, warehouse_id=warehouse_id, batch_id=None
    )
    return Decimal(str(row["qty_on_hand"])) if row else Decimal("0")


def _apply_sale_moves(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    moves: list,
    sale_id: str,
    created_by=None,
) -> Optional[str]:
    """按 moves [(batch_id, qty>0)] 逐笔扣库存(sale_out),返回记到销售行的首个批次 id(全散装=None)。"""
    first = None
    for batch_id, qty in moves:
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
        first = first or batch_id
    return first


def _deduct_non_batch(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    warehouse_id: int,
    product_id: str,
    need: Decimal,
    sale_id: str,
    created_by=None,
) -> None:
    """非批次品出库:散装行(batch NULL)+ 批次行合成一个库存池,散装优先、再 FEFO 补。

    非批次品被「带批号进货」时货会落进批次行、散装行留 0——只查散装行会误判 out_of_stock,
    而库存页按所有行加总却显示有货("看得见卖不出")。两处当同一池扣,消除口径分裂;总量不足才拒。
    """
    take_loose = min(
        need,
        _loose_on_hand(cur, tenant_id=tenant_id, product_id=product_id, warehouse_id=warehouse_id),
    )
    remainder = need - take_loose
    # 散装已够整行时不必再查批次(省热路径一次 DB 往返 · 非批次品的常态)。
    alloc = (
        fefo.select_batches_for_outflow(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            qty_needed=remainder,
        )
        if remainder > 0
        else {"allocations": [], "shortfall": Decimal("0")}
    )
    if alloc["shortfall"] > 0:
        raise PosError("pos.out_of_stock", 409, detail=str(product_id))
    moves = [(None, take_loose)] if take_loose > 0 else []
    moves.extend((a["batch_id"], Decimal(str(a["qty"]))) for a in alloc["allocations"])
    _apply_sale_moves(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        moves=moves,
        sale_id=sale_id,
        created_by=created_by,
    )
    return None


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
