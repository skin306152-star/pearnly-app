# -*- coding: utf-8 -*-
"""FEFO 先效先出 — 批次品出库的批次分配(POS 项目 · PO-A3 · docs/pos/03 §3)。

按 expiry_date 升序(NULL 最后)、再 received_at 升序,从有库存的批次依次扣减,直到满足
需求量。不足时分配到现有批次为止,返回缺口(由上层按 08 ADR 决定允许负库存+告警还是拒卖)。
POS 卖批次品收款时调(PO-B2);A3 先建 + 单测,库存读侧近效期排序同此规则。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def _num(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def select_batches_for_outflow(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    product_id: str,
    warehouse_id: int,
    qty_needed,
) -> dict:
    """返回 {"allocations": [{"batch_id", "qty"}], "shortfall": Decimal}。

    allocations 按 FEFO 顺序;shortfall>0 表示现有批次不够(缺这么多 base_unit)。
    """
    need = _num(qty_needed)
    cur.execute(
        "SELECT s.batch_id, s.qty_on_hand, b.expiry_date "
        "FROM inventory_stock s JOIN inventory_batches b ON b.id = s.batch_id "
        "WHERE s.tenant_id = %s AND s.workspace_client_id = %s AND s.product_id = %s "
        "AND s.warehouse_id = %s AND s.batch_id IS NOT NULL AND s.qty_on_hand > 0 "
        "ORDER BY b.expiry_date ASC NULLS LAST, b.received_at ASC, s.batch_id ASC "
        "FOR UPDATE OF s",
        (tenant_id, workspace_client_id, product_id, warehouse_id),
    )
    allocations = []
    for row in cur.fetchall():
        if need <= 0:
            break
        avail = _num(row["qty_on_hand"])
        take = avail if avail < need else need
        allocations.append({"batch_id": row["batch_id"], "qty": take})
        need -= take
    return {"allocations": allocations, "shortfall": need if need > 0 else Decimal("0")}
