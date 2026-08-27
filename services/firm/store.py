# -*- coding: utf-8 -*-
"""会计事务所 profile DAL。

薄壳 · 每函数收调用方传入 cursor(与 entrance_store/daily 同款)。隔离=应用层
WHERE tenant_id(第一道防线 · RLS policy 第二道)· 参数化不拼串。单租户读写一律带 tenant_id。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_COLUMNS = "tenant_id::text, firm_code, display_name, tax_id, status"
_PROFILE_COLUMNS = "p.tenant_id::text, p.firm_code, p.display_name, p.tax_id, p.status"


def create_profile(
    cur,
    *,
    tenant_id: str,
    display_name: str,
    tax_id: Optional[str] = None,
) -> Optional[dict]:
    """建/幂等 upsert 本租户 firm profile · 不覆盖既有 firm_code。

    ON CONFLICT(tenant_id)仅随传参刷新 display_name + updated_at,不动 firm_code/tax_id。
    返回落库行或 None(RLS 拦/约束失败)。firm_code 走库内 sequence 默认,不经此处。
    """
    cur.execute(
        f"""
        INSERT INTO accounting_firm_profiles (tenant_id, display_name, tax_id, status)
        SELECT t.id, %s, %s,
               CASE WHEN t.status = 'active' THEN 'active' ELSE 'suspended' END
        FROM tenants t
        WHERE t.id = %s::uuid AND t.tenant_type_v2 = 'f_firm'
        ON CONFLICT (tenant_id)
        DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = now()
        RETURNING {_COLUMNS}, created_at, updated_at
        """,
        (display_name, tax_id, str(tenant_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_profile(cur, *, tenant_id: str) -> Optional[dict]:
    """取本租户 firm profile(单租户 · 无行返 None)。"""
    cur.execute(
        f"""
        SELECT {_COLUMNS}, created_at, updated_at
        FROM accounting_firm_profiles
        WHERE tenant_id = %s::uuid
        """,
        (str(tenant_id),),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_active_profiles(
    cur,
    *,
    tenant_id: str,
) -> list[dict]:
    """列本租户 active profile。平台跨租户列表须另走显式超管接口。"""
    cur.execute(
        f"""
        SELECT {_PROFILE_COLUMNS}, p.created_at, p.updated_at
        FROM accounting_firm_profiles p
        JOIN tenants t ON t.id = p.tenant_id
        WHERE p.tenant_id = %s::uuid
          AND p.status = 'active'
          AND t.status = 'active'
        ORDER BY p.firm_code
        """,
        (str(tenant_id),),
    )
    return [dict(r) for r in cur.fetchall()]
