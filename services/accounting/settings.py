# -*- coding: utf-8 -*-
"""做账设置 DAL(一套账一行 · docs/accounting/01)。

安全带③(粒度 opt-in):auto_post 全局默认 FALSE=建议模式;auto_post_rules 按 rule_key
覆盖全局(如 {"R1": true} 只放行进货自动过账)。closed_through 由月末结账写(Phase books)。
"""

from __future__ import annotations

import json

DEFAULTS = {
    "auto_post": False,
    "auto_post_threshold": 90,
    "auto_post_rules": {},
    "accounting_standard": "TFRS_NPAE",
    "inventory_method": "periodic",
    "base_currency": "THB",
    "start_period": None,
    "closed_through": None,
}

_EDITABLE = (
    "auto_post",
    "auto_post_threshold",
    "auto_post_rules",
    "accounting_standard",
    "inventory_method",
    "base_currency",
    "start_period",
)


def get_settings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT auto_post, auto_post_threshold, auto_post_rules, accounting_standard, "
        "inventory_method, base_currency, start_period, closed_through "
        "FROM accounting_settings WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        return dict(DEFAULTS)
    out = dict(row)
    rules = out.get("auto_post_rules")
    out["auto_post_rules"] = rules if isinstance(rules, dict) else json.loads(rules or "{}")
    return out


def update_settings(cur, *, tenant_id: str, workspace_client_id: int, data: dict) -> dict:
    current = get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    merged = {k: data.get(k, current.get(k)) for k in _EDITABLE}
    cur.execute(
        "INSERT INTO accounting_settings "
        "(tenant_id, workspace_client_id, auto_post, auto_post_threshold, auto_post_rules, "
        " accounting_standard, inventory_method, base_currency, start_period) "
        "VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET "
        "auto_post = EXCLUDED.auto_post, "
        "auto_post_threshold = EXCLUDED.auto_post_threshold, "
        "auto_post_rules = EXCLUDED.auto_post_rules, "
        "accounting_standard = EXCLUDED.accounting_standard, "
        "inventory_method = EXCLUDED.inventory_method, "
        "base_currency = EXCLUDED.base_currency, "
        "start_period = EXCLUDED.start_period, "
        "updated_at = now()",
        (
            tenant_id,
            workspace_client_id,
            bool(merged["auto_post"]),
            merged["auto_post_threshold"],
            json.dumps(merged["auto_post_rules"] or {}),
            merged["accounting_standard"],
            merged["inventory_method"],
            merged["base_currency"],
            merged["start_period"],
        ),
    )
    return get_settings(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)


def is_period_closed(settings: dict, period: str) -> bool:
    """period('YYYY-MM') 是否已结账锁定。closed_through 之前(含)都锁。"""
    closed = settings.get("closed_through")
    return bool(closed) and period <= closed


def auto_post_allowed(settings: dict, rule_key: str) -> bool:
    """安全带③:rule_key 粒度覆盖优先,否则看全局 auto_post。"""
    rules = settings.get("auto_post_rules") or {}
    if rule_key in rules:
        return bool(rules[rule_key])
    return bool(settings.get("auto_post"))
