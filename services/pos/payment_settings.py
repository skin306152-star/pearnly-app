# -*- coding: utf-8 -*-
"""POS 收款设置 DAL(POS 项目 · 老板后台 · 按账套 workspace_client_id 隔离)。

存一行/账套:支付方式开关(现金恒开 · PromptPay/刷卡可关)+ 服务费率 + 价格含 VAT。
PromptPay 收款 ID 复用既有 workspace_clients.promptpay_id 列(账套主体级 · 不重复存)。
隔离=应用层 WHERE tenant_id;RLS policy 兜底。prod 无自动迁移 → ensure_payment_schema 双跑
幂等 DDL(与 alembic 0029 同源)。金额率用 numeric 不用 float。
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

# 默认值:现金恒开;PromptPay/刷卡默认开(老板可关);价格含 VAT(泰国零售惯例)。
# 服务费默认按业态智能给:餐厅 10%(泰国餐厅惯例·老板可改),其余 0。见 _default_service_rate。
_DEFAULTS = {
    "promptpay_enabled": True,
    "card_enabled": True,
    "price_includes_vat": True,
}
_RESTAURANT_DEFAULT_SERVICE_RATE = "10"


def _default_service_rate(cur, tenant_id: str) -> str:
    """无显式设置时的服务费默认:餐厅业态 10%,其余 0(智能默认·老板可改)。"""
    from services.modules import store as modules_store

    bt = modules_store.get_business_type(cur, tenant_id=tenant_id)
    return _RESTAURANT_DEFAULT_SERVICE_RATE if bt == "restaurant" else "0"


def ensure_payment_schema() -> None:
    """幂等建表 + RLS(startup 经 bootstrap_pos_schema 调 · 与 alembic 0029 同源)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pos_payment_settings (
                tenant_id uuid NOT NULL,
                workspace_client_id bigint NOT NULL,
                promptpay_enabled boolean NOT NULL DEFAULT TRUE,
                card_enabled boolean NOT NULL DEFAULT TRUE,
                service_charge_rate numeric(6,2) NOT NULL DEFAULT 0,
                price_includes_vat boolean NOT NULL DEFAULT TRUE,
                updated_at timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (tenant_id, workspace_client_id)
            )
            """)
        apply_tenant_rls(cur, "pos_payment_settings")


def _rate_str(value) -> str:
    """numeric → 干净字符串(整数去小数尾 · 10.00→'10' · 8.50→'8.5')。"""
    try:
        d = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        d = Decimal("0")
    d = d.normalize()
    return str(d if d == d.to_integral() else d).replace("E+1", "0")


def _clean_rate(value) -> Decimal:
    """入参服务费率 → [0,100] 的 Decimal(挡非法/越界)。"""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")
    if d < 0:
        return Decimal("0")
    return Decimal("100") if d > 100 else d


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """返回该账套收款设置(无行回落默认)+ 账套 promptpay_id。"""
    cur.execute(
        "SELECT promptpay_enabled, card_enabled, service_charge_rate, price_includes_vat "
        "FROM pos_payment_settings WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    cur.execute(
        "SELECT promptpay_id FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    pp = cur.fetchone()
    out = {
        "promptpay_enabled": _DEFAULTS["promptpay_enabled"],
        "card_enabled": _DEFAULTS["card_enabled"],
        "service_charge_rate": _default_service_rate(cur, tenant_id),
        "price_includes_vat": _DEFAULTS["price_includes_vat"],
        "promptpay_id": (pp["promptpay_id"] if pp else None) or "",
    }
    if row is not None:
        out["promptpay_enabled"] = bool(row["promptpay_enabled"])
        out["card_enabled"] = bool(row["card_enabled"])
        out["service_charge_rate"] = _rate_str(row["service_charge_rate"])
        out["price_includes_vat"] = bool(row["price_includes_vat"])
    return out


def save_settings(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    promptpay_enabled: bool,
    card_enabled: bool,
    service_charge_rate,
    price_includes_vat: bool,
    promptpay_id: str,
) -> dict:
    """upsert 收款设置 + 回写账套 promptpay_id(现金恒开不存)。返回回读视图。"""
    rate = _clean_rate(service_charge_rate)
    cur.execute(
        """
        INSERT INTO pos_payment_settings
            (tenant_id, workspace_client_id, promptpay_enabled, card_enabled,
             service_charge_rate, price_includes_vat)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id)
        DO UPDATE SET promptpay_enabled = EXCLUDED.promptpay_enabled,
                      card_enabled = EXCLUDED.card_enabled,
                      service_charge_rate = EXCLUDED.service_charge_rate,
                      price_includes_vat = EXCLUDED.price_includes_vat,
                      updated_at = now()
        """,
        (
            tenant_id,
            workspace_client_id,
            bool(promptpay_enabled),
            bool(card_enabled),
            rate,
            bool(price_includes_vat),
        ),
    )
    cur.execute(
        "UPDATE workspace_clients SET promptpay_id = %s WHERE id = %s AND tenant_id = %s",
        ((promptpay_id or "").strip()[:40] or None, workspace_client_id, tenant_id),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
