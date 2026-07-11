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
_SELECT_WITH_SUPPLIER_NAME = (
    "p.seller_tax_id, p.default_payment, p.default_item_type, "
    "p.default_category_id, p.default_erp_account, p.source, p.updated_at, "
    "s.name AS supplier_name"
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


def list_profiles(
    cur, *, tenant_id: str, workspace_client_id: int, limit: Optional[int] = None
) -> List[dict]:
    """套账下全部过账档案,按 updated_at 倒序(管理页用途 · 量小照惯例不分页,limit 供路由层收口)。"""
    sql = (
        f"SELECT {_SELECT} FROM supplier_posting_profiles "
        "WHERE tenant_id = %s AND workspace_client_id = %s ORDER BY updated_at DESC"
    )
    params: list = [tenant_id, workspace_client_id]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)
    cur.execute(sql, tuple(params))
    return [dict(row) for row in cur.fetchall()]


def list_profiles_with_supplier_names(
    cur, *, tenant_id: str, workspace_client_id: int, limit: Optional[int] = None
) -> List[dict]:
    """管理页列表读侧富化(Z3-b):LEFT JOIN 供应商主档按清洗税号取名,查不到 → supplier_name=None
    (前端显示「—」)。独立新读 helper——不改 list_profiles 签名,批量预取
    (preflight.build_batch_prefetch)与单票消费两条路仍读 get_profiles/list_profiles,零影响。

    suppliers.tax_id 建档路径不保证已是纯数字(手录/OCR 落库格式不一),JOIN 前用
    regexp_replace 剥非数字字符再比 —— 与 field_clean.clean_tax_id 同一清洗口径。
    """
    sql = (
        f"SELECT {_SELECT_WITH_SUPPLIER_NAME} "
        "FROM supplier_posting_profiles p "
        "LEFT JOIN suppliers s ON s.tenant_id = p.tenant_id "
        "AND s.workspace_client_id = p.workspace_client_id "
        "AND regexp_replace(COALESCE(s.tax_id, ''), '\\D', '', 'g') = p.seller_tax_id "
        "WHERE p.tenant_id = %s AND p.workspace_client_id = %s "
        "ORDER BY p.updated_at DESC"
    )
    params: list = [tenant_id, workspace_client_id]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)
    cur.execute(sql, tuple(params))
    return [dict(row) for row in cur.fetchall()]


def delete_profile(cur, *, tenant_id: str, workspace_client_id: int, seller_tax_id: str) -> bool:
    """删一条过账档案。幂等:不存在也不报错,返回值告知调用方是否真删到行(路由层自定 404/no-op)。"""
    tax = str(seller_tax_id or "").strip()
    if not tax:
        return False
    cur.execute(
        "DELETE FROM supplier_posting_profiles "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND seller_tax_id = %s",
        (tenant_id, workspace_client_id, tax),
    )
    return cur.rowcount > 0


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
