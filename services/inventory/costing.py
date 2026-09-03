# -*- coding: utf-8 -*-
"""库存实价缺失时的商品参考成本查询。"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


def product_reference_cost(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str
) -> Optional[Decimal]:
    cur.execute(
        "SELECT default_cost FROM products "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id),
    )
    row = cur.fetchone()
    value = row.get("default_cost") if row else None
    return Decimal(str(value)) if value is not None else None
