# -*- coding: utf-8 -*-
"""租户级开票设置(M7 · docs/16 §M7 / §N)。

一行/租户,存连号默认(前缀/重置/起始号)、审批模式、以及开票表单默认(价内外/WHT/模板/
语言/纸张/省纸)。开票时读默认,单据可覆盖;`approval_mode` 在此存,issue 路由据此激活 §F
审批工作流。`number_start` 用于接旧账本(设 = 旧末号+1,新序列从该号起)。纯参数化叶子,
租户隔离靠 get_cursor_rls + WHERE tenant_id。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

# 列 → 默认值。get 读不到行时回这套(行为=保持现状:无审批/价外/yearly 连号)。
DEFAULTS: dict[str, Any] = {
    "number_prefix": None,
    "number_reset": "yearly",
    "number_start": 1,
    "approval_mode": "none",
    "price_includes_vat_default": False,
    "default_wht_rate": Decimal("0"),
    "default_template_id": "classic",
    "default_doc_lang": "th",
    "default_paper": "A4",
    "default_copies_layout": "separate",
}
_COLS = tuple(DEFAULTS.keys())
APPROVAL_MODES = ("none", "single")


def get_settings(cur, *, tenant_id: str) -> dict:
    """读租户设置;无行回 DEFAULTS 副本(新租户零配置即可开票)。"""
    cur.execute(
        f"SELECT {', '.join(_COLS)} FROM sales_settings WHERE tenant_id=%s",
        (tenant_id,),
    )
    row = cur.fetchone()
    if not row:
        return dict(DEFAULTS)
    return {k: (row[k] if row.get(k) is not None else DEFAULTS[k]) for k in _COLS}


def set_settings(cur, *, tenant_id: str, fields: dict) -> dict:
    """upsert 设置(只写给定且非 None 的列)。审批模式非法回落 none。返回合并后的设置。"""
    updates = {k: fields[k] for k in _COLS if k in fields and fields[k] is not None}
    if "approval_mode" in updates and updates["approval_mode"] not in APPROVAL_MODES:
        updates["approval_mode"] = "none"
    cols = ["tenant_id"] + list(updates.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    set_clause = ", ".join(f"{k}=EXCLUDED.{k}" for k in updates) or "tenant_id=EXCLUDED.tenant_id"
    cur.execute(
        f"INSERT INTO sales_settings ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (tenant_id) DO UPDATE SET {set_clause}, updated_at=now()",
        [tenant_id] + list(updates.values()),
    )
    return get_settings(cur, tenant_id=tenant_id)
