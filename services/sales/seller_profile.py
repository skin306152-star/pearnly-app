# -*- coding: utf-8 -*-
"""开票方(卖方=账套主体)资料读写 + 买方读取(PO-6 · docs/sales-module/docs/13)。

卖方 = workspace_clients(账套主体):name/tax_id 已有,这里补的开票字段(address/
branch/phone/vat_registered)由 0008 迁移加。开票时按所选账套带出卖方块;买方取自
clients。纯参数化叶子,租户隔离靠 get_cursor_rls + WHERE tenant_id。
"""

from __future__ import annotations

from typing import Any, Optional

_SELLER_COLS = "id, name, tax_id, address, branch, phone, vat_registered, promptpay_id"
_SELLER_WRITABLE = (
    "name",
    "tax_id",
    "address",
    "branch",
    "phone",
    "vat_registered",
    "promptpay_id",
)


def list_sellers(cur, *, tenant_id: str) -> list:
    cur.execute(
        f"SELECT {_SELLER_COLS} FROM workspace_clients "
        "WHERE tenant_id=%s AND is_active=TRUE ORDER BY name",
        (tenant_id,),
    )
    return cur.fetchall()


def get_seller(cur, *, tenant_id: str, workspace_client_id: int) -> Optional[dict]:
    cur.execute(
        f"SELECT {_SELLER_COLS} FROM workspace_clients WHERE tenant_id=%s AND id=%s",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchone()


def set_seller(cur, *, tenant_id: str, workspace_client_id: int, fields: dict) -> Optional[dict]:
    updates = {k: fields[k] for k in _SELLER_WRITABLE if k in fields and fields[k] is not None}
    if not updates:
        return get_seller(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    sets = ", ".join(f"{k}=%s" for k in updates) + ", updated_at=now()"
    params: list[Any] = list(updates.values()) + [tenant_id, workspace_client_id]
    cur.execute(
        f"UPDATE workspace_clients SET {sets} WHERE tenant_id=%s AND id=%s "
        f"RETURNING {_SELLER_COLS}",
        params,
    )
    return cur.fetchone()


def get_buyer(cur, *, tenant_id: str, client_id: int) -> Optional[dict]:
    """买方(clients)展示信息。clients.tenant_id 可空,故按 (id) 取后校 tenant 归属。"""
    cur.execute(
        "SELECT id, name, tax_id, address FROM clients "
        "WHERE id=%s AND (tenant_id=%s OR tenant_id IS NULL)",
        (client_id, tenant_id),
    )
    return cur.fetchone()
