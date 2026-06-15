# -*- coding: utf-8 -*-
"""采购设置 DAL · 一套账一行(商户采购 · docs/purchasing/01-02 §6)。

默认 VAT/进货入库/重复票拦/账期/付款审批/服务默认 WHT 率/本位币。无显式行回落默认
(老租户开 expense 即用默认,不强配)。隔离=每句 WHERE tenant_id + workspace_client_id;
率用 numeric(Decimal)不用 float。调用方负责事务。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

_DEFAULTS = {
    "default_vat_rate": "7",
    "auto_stock_in": False,
    "dedupe_block": True,
    "default_due_days": 0,
    "pay_needs_approval": False,
    "default_wht_service_rate": "3",
    "base_currency": "THB",
    "auto_book": False,
}


def _rate(value, fallback: str) -> Decimal:
    """率 → [0,100] Decimal(挡非法/越界)。"""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(fallback)
    if d < 0:
        return Decimal("0")
    return Decimal("100") if d > 100 else d


def _rate_str(value) -> str:
    """numeric → 干净字符串(10.00→'10' · 8.50→'8.5')。format('f') 避开科学计数法。"""
    try:
        d = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        d = Decimal("0")
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """返回本套账采购设置(无行回落默认)。"""
    cur.execute(
        "SELECT default_vat_rate, auto_stock_in, dedupe_block, default_due_days, "
        "pay_needs_approval, default_wht_service_rate, base_currency, auto_book "
        "FROM purchase_settings "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        return dict(_DEFAULTS)
    return {
        "default_vat_rate": _rate_str(row["default_vat_rate"]),
        "auto_stock_in": bool(row["auto_stock_in"]),
        "dedupe_block": bool(row["dedupe_block"]),
        "default_due_days": int(row["default_due_days"]),
        "pay_needs_approval": bool(row["pay_needs_approval"]),
        "default_wht_service_rate": _rate_str(row["default_wht_service_rate"]),
        "base_currency": (row["base_currency"] or "THB"),
        "auto_book": bool(row["auto_book"]),
    }


def save_settings(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    default_vat_rate,
    auto_stock_in: bool,
    dedupe_block: bool,
    default_due_days,
    pay_needs_approval: bool,
    default_wht_service_rate,
    base_currency: str,
    auto_book: bool = False,
) -> dict:
    """upsert 采购设置。返回回读视图。"""
    cur.execute(
        """
        INSERT INTO purchase_settings
            (tenant_id, workspace_client_id, default_vat_rate, auto_stock_in,
             dedupe_block, default_due_days, pay_needs_approval,
             default_wht_service_rate, base_currency, auto_book)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id)
        DO UPDATE SET default_vat_rate = EXCLUDED.default_vat_rate,
                      auto_stock_in = EXCLUDED.auto_stock_in,
                      dedupe_block = EXCLUDED.dedupe_block,
                      default_due_days = EXCLUDED.default_due_days,
                      pay_needs_approval = EXCLUDED.pay_needs_approval,
                      default_wht_service_rate = EXCLUDED.default_wht_service_rate,
                      base_currency = EXCLUDED.base_currency,
                      auto_book = EXCLUDED.auto_book,
                      updated_at = now()
        """,
        (
            tenant_id,
            workspace_client_id,
            _rate(default_vat_rate, "7"),
            bool(auto_stock_in),
            bool(dedupe_block),
            max(0, int(default_due_days or 0)),
            bool(pay_needs_approval),
            _rate(default_wht_service_rate, "3"),
            (base_currency or "THB").strip()[:8] or "THB",
            bool(auto_book),
        ),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
