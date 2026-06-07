# -*- coding: utf-8 -*-
"""tenant_modules DAL — 模块开关读写(POS 项目 · PO-A1 · docs/pos/03 §5 + 04 §2)。

每个函数收路由层传入的 cursor + tenant_id。隔离真正生效的是【应用层 WHERE tenant_id】:
每条语句都按 tenant_id 过滤。db.get_cursor_rls 设的 app.current_tenant_id + 表上的 RLS
policy 只是给未来最小权限角色的兜底——prod 现以 postgres(BYPASSRLS)连库,Postgres RLS
对本连接不强制(2026-06-07 真库验证),故 WHERE tenant_id 是唯一硬保证。module_key 取白名单,
值一律占位符。

默认值约定(get_modules / is_enabled):无显式行的模块回落 DEFAULT_ENABLED——既有租户保持
今天的导航(sales/expense/recon/knowledge 默认开),POS/inventory 默认关到 onboarding 才开。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger("mr-pilot")

# 可被开关的模块全集。未列入的 key 一律拒写(防任意键污染)。
KNOWN_MODULES = (
    "inventory",
    "pos",
    "sales",
    "expense",
    "recon",
    "knowledge",
)

# 无显式行时的回落:既有功能默认开;POS/库存默认关(onboarding 才开)。
DEFAULT_ENABLED = {
    "sales": True,
    "expense": True,
    "recon": True,
    "knowledge": True,
    "inventory": False,
    "pos": False,
}


def ensure_table() -> None:
    """幂等建表 + RLS policy(启动调 · 与 alembic 0021 双跑)。失败仅告警不 raise。"""
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tenant_modules (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    module_key text NOT NULL,
                    enabled boolean NOT NULL DEFAULT FALSE,
                    config jsonb NOT NULL DEFAULT '{}'::jsonb,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id, module_key)
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_tenant_modules_tenant "
                "ON tenant_modules (tenant_id)"
            )
            cur.execute("ALTER TABLE tenant_modules ENABLE ROW LEVEL SECURITY")
            cur.execute("DROP POLICY IF EXISTS tenant_isolation ON tenant_modules")
            cur.execute("""
                CREATE POLICY tenant_isolation ON tenant_modules
                FOR ALL
                USING (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                )
                WITH CHECK (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                )
                """)
        logger.info("✅ tenant_modules 表 + RLS policy 已就绪 (POS PO-A1)")
    except Exception as e:
        logger.warning(f"ensure_table tenant_modules 失败(跳过 · 等 alembic 0021): {e}")


def get_modules(cur, *, tenant_id: str) -> dict:
    """返回该租户全模块开关视图:DEFAULT_ENABLED 打底,显式行覆盖。

    形态:{module_key: {"enabled": bool, "config": {...}}}(覆盖 KNOWN_MODULES 全集)。
    """
    cur.execute(
        "SELECT module_key, enabled, config FROM tenant_modules WHERE tenant_id = %s",
        (tenant_id,),
    )
    rows = {r["module_key"]: r for r in cur.fetchall()}
    out: dict = {}
    for key in KNOWN_MODULES:
        row = rows.get(key)
        if row is not None:
            out[key] = {"enabled": bool(row["enabled"]), "config": _as_dict(row["config"])}
        else:
            out[key] = {"enabled": DEFAULT_ENABLED.get(key, False), "config": {}}
    return out


def is_enabled(cur, *, tenant_id: str, module_key: str) -> bool:
    """单模块是否开:显式行优先,否则回落默认,未知模块=关。"""
    if module_key not in KNOWN_MODULES:
        return False
    cur.execute(
        "SELECT enabled FROM tenant_modules WHERE tenant_id = %s AND module_key = %s",
        (tenant_id, module_key),
    )
    row = cur.fetchone()
    if row is not None:
        return bool(row["enabled"])
    return DEFAULT_ENABLED.get(module_key, False)


def set_module(
    cur,
    *,
    tenant_id: str,
    module_key: str,
    enabled: bool,
    config: Optional[dict] = None,
) -> dict:
    """upsert 单模块开关。未知 module_key 抛 ValueError(由路由翻 4xx)。

    config=None 时不动既有 config(只翻开关);传 dict 则整体覆盖。
    """
    if module_key not in KNOWN_MODULES:
        raise ValueError(f"unknown module_key: {module_key}")
    if config is None:
        cur.execute(
            """
            INSERT INTO tenant_modules (tenant_id, module_key, enabled)
            VALUES (%s, %s, %s)
            ON CONFLICT (tenant_id, module_key)
            DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = now()
            RETURNING module_key, enabled, config
            """,
            (tenant_id, module_key, enabled),
        )
    else:
        cur.execute(
            """
            INSERT INTO tenant_modules (tenant_id, module_key, enabled, config)
            VALUES (%s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, module_key)
            DO UPDATE SET enabled = EXCLUDED.enabled,
                          config = EXCLUDED.config,
                          updated_at = now()
            RETURNING module_key, enabled, config
            """,
            (tenant_id, module_key, enabled, json.dumps(config)),
        )
    row = cur.fetchone()
    return {
        "module_key": row["module_key"],
        "enabled": bool(row["enabled"]),
        "config": _as_dict(row["config"]),
    }


def _as_dict(config) -> dict:
    """jsonb 列回来可能是 dict(psycopg2 已解析)或 str;统一成 dict。"""
    if config is None:
        return {}
    if isinstance(config, dict):
        return config
    try:
        return json.loads(config)
    except (TypeError, ValueError):
        return {}
