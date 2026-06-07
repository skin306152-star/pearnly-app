# -*- coding: utf-8 -*-
"""开通收银(POS 项目 · PO-B1 · docs/pos/04 §2)。

选业态 → 一键就绪:开 inventory+pos 模块(pos.config 写业态预设能力块)+ 建账套默认仓 +
建默认终端 + 建首位收银员(PIN)。业态预设 = 一组能力块开关(01-requirements 的通用内核 +
业态预设)。一个事务内完成(调用方 get_cursor_rls(commit=True))。
"""

from __future__ import annotations

from typing import Optional

from services.inventory import store as inventory_store
from services.modules import store as modules_store
from services.pos import auth as pos_auth
from services.pos import cashier as cashier_dal

# 业态预设:能力块清单(写进 tenant_modules.pos.config,前端按块显隐;后端按块裁行为)。
# 通用内核之上叠加,未列业态回落 retail。能力块语义见 docs/pos/01 + 03 §5。
BUSINESS_PRESETS: dict[str, list[str]] = {
    "retail": ["multi_unit"],
    "grocery": ["multi_unit", "track_batch", "track_expiry"],
    "pharmacy": ["multi_unit", "track_batch", "track_expiry", "prescription"],
    "restaurant": ["tables", "kitchen"],
    "service": [],
}


def onboard(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    business_type: str,
    warehouse_name: str | None = None,
    first_cashier: dict | None = None,
) -> dict:
    """返回 {enabled_modules, capabilities, cashier_id}。first_cashier 缺省时不建收银员。"""
    capabilities = BUSINESS_PRESETS.get(business_type, BUSINESS_PRESETS["retail"])

    modules_store.set_module(cur, tenant_id=tenant_id, module_key="inventory", enabled=True)
    pos_config = {"business_type": business_type}
    for cap in capabilities:
        pos_config[cap] = True
    modules_store.set_module(
        cur, tenant_id=tenant_id, module_key="pos", enabled=True, config=pos_config
    )

    inventory_store.get_or_create_default_warehouse(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, name=warehouse_name
    )
    cashier_dal.get_or_create_default_terminal(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )

    cashier_id = None
    if first_cashier and first_cashier.get("display_name") and first_cashier.get("pin"):
        created = cashier_dal.create_cashier(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            display_name=first_cashier["display_name"],
            pin_hash=pos_auth.hash_pin(first_cashier["pin"]),
            color=first_cashier.get("color"),
        )
        cashier_id = str(created["id"])

    return {
        "enabled_modules": ["inventory", "pos"],
        "capabilities": capabilities,
        "cashier_id": cashier_id,
    }


def get_state(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """开通状态(给屏8 判断是否已开通、当前业态,避免重复开通)。

    onboarded = pos 模块已开 且 该账套已建仓+至少一名收银员。business_type / capabilities 从
    pos 模块 config 读出。每条语句 WHERE tenant_id(+ 账套)· 参数化。
    """
    modules = modules_store.get_modules(cur, tenant_id=tenant_id)
    pos_cfg = modules.get("pos", {}).get("config", {}) or {}
    business_type: Optional[str] = pos_cfg.get("business_type")

    cur.execute(
        "SELECT COUNT(*) AS n FROM pos_cashiers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE",
        (tenant_id, workspace_client_id),
    )
    cashier_count = int(cur.fetchone()["n"])
    cur.execute(
        "SELECT 1 FROM warehouses WHERE tenant_id = %s AND workspace_client_id = %s LIMIT 1",
        (tenant_id, workspace_client_id),
    )
    has_warehouse = cur.fetchone() is not None

    pos_on = bool(modules.get("pos", {}).get("enabled"))
    return {
        "onboarded": pos_on and has_warehouse and cashier_count > 0,
        "business_type": business_type,
        "capabilities": [
            k for k in BUSINESS_PRESETS.get(business_type or "", []) if pos_cfg.get(k)
        ],
        "pos_enabled": pos_on,
        "inventory_enabled": bool(modules.get("inventory", {}).get("enabled")),
        "has_warehouse": has_warehouse,
        "cashier_count": cashier_count,
    }
