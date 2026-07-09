# -*- coding: utf-8 -*-
"""供应商过账档案 DAL(F4 · L2 · 商户采购 · 套账隔离)。

档案锚是卖方税号(seller_tax_id),记这个供应商的现/赊、货/费"通常怎么记"——喂进
`payment_verdict` 的第四级判据(profile,见 services/erp/express_push/common.py)。
default_item_type 只存不自动消费:主站不拿它压过票面法定证据(有完整税票=可抵进项,
自动判据/档案习惯都不许覆盖),留给工单线预填。

隔离=每句 WHERE tenant_id + workspace_client_id;值一律 %s 参数化。调用方负责事务
(与 services/purchase/suppliers.py 同风格:cur 注入 + keyword-only)。
"""

from __future__ import annotations

from typing import Dict, List, Optional

_SELECT = (
    "seller_tax_id, default_payment, default_item_type, "
    "default_category_id, default_erp_account, source, updated_at"
)


def get_profiles(
    cur, *, tenant_id: str, workspace_client_id: int, tax_ids: List[str]
) -> Dict[str, dict]:
    """按税号批量取过账档案(一次 IN 查询)。返回 {seller_tax_id: profile_dict}。"""
    ids = [str(t).strip() for t in (tax_ids or []) if str(t or "").strip()]
    if not ids:
        return {}
    cur.execute(
        f"SELECT {_SELECT} FROM supplier_posting_profiles "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND seller_tax_id = ANY(%s)",
        (tenant_id, workspace_client_id, ids),
    )
    return {row["seller_tax_id"]: dict(row) for row in cur.fetchall()}


def upsert_profile(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    seller_tax_id: str,
    default_payment: Optional[str] = None,
    default_item_type: Optional[str] = None,
    source: str = "correction",
) -> None:
    """UPSERT 过账默认。default_payment/default_item_type 传 None = 不改该字段
    (首次建档落空串 '' · 已有档案保留原值,COALESCE 语义)。

    冲突时:correction(纠错自学)不许覆盖已有 user_rule 行(用户在设置页显式挂过的优先,
    与 services/expense/conversation.py::learn 同规则);user_rule 可覆盖任意来源。
    """
    tax = str(seller_tax_id or "").strip()
    if not tax:
        return
    payment_val = default_payment if default_payment is not None else ""
    item_type_val = default_item_type if default_item_type is not None else ""
    cur.execute(
        "INSERT INTO supplier_posting_profiles "
        "(tenant_id, workspace_client_id, seller_tax_id, default_payment, default_item_type, "
        "source, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, now()) "
        "ON CONFLICT (tenant_id, workspace_client_id, seller_tax_id) DO UPDATE SET "
        "default_payment = CASE WHEN %s IS NULL THEN supplier_posting_profiles.default_payment "
        "ELSE EXCLUDED.default_payment END, "
        "default_item_type = CASE WHEN %s IS NULL THEN supplier_posting_profiles.default_item_type "
        "ELSE EXCLUDED.default_item_type END, "
        "source = EXCLUDED.source, updated_at = now() "
        "WHERE supplier_posting_profiles.source <> 'user_rule' OR EXCLUDED.source = 'user_rule'",
        (
            tenant_id,
            workspace_client_id,
            tax,
            payment_val,
            item_type_val,
            source,
            default_payment,
            default_item_type,
        ),
    )
