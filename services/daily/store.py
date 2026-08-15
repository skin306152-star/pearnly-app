# -*- coding: utf-8 -*-
"""Daily 周记账 DAL(每函数收调用方传入 cursor · 与 entrance_store 同款薄壳)。

隔离:全部 SQL 带 tenant_id 条件(应用层第一道防线 · RLS policy 第二道)·
参数化不拼串 · 金额 numeric(12,2) 走 Decimal,不碰 float(铁律)。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def list_entries(cur, tenant_id: str, month: str) -> list[dict]:
    """月内全部记录(month 形如 2026-09 · 路由层已校验格式)。"""
    cur.execute(
        """
        SELECT id::text, entry_date, kind, title, amount, created_at
        FROM daily_entries
        WHERE tenant_id = %s::uuid AND to_char(entry_date, 'YYYY-MM') = %s
        ORDER BY entry_date DESC, created_at DESC
        """,
        (str(tenant_id), month),
    )
    return [dict(r) for r in cur.fetchall()]


def list_all_entries(cur, tenant_id: str) -> list[dict]:
    """全量记录(JSON 备份导出用 · 与列表同款租户隔离)。"""
    cur.execute(
        """
        SELECT id::text, entry_date, kind, title, amount, created_at
        FROM daily_entries
        WHERE tenant_id = %s::uuid
        ORDER BY entry_date, created_at
        """,
        (str(tenant_id),),
    )
    return [dict(r) for r in cur.fetchall()]


def insert_entry(
    cur,
    tenant_id: str,
    entry_date: str,
    kind: str,
    title: str,
    amount: Decimal,
) -> Optional[dict]:
    """新建一条记录 · 返回落库行(含 id/created_at)或 None(RLS 拦/约束失败)。"""
    cur.execute(
        """
        INSERT INTO daily_entries (tenant_id, entry_date, kind, title, amount)
        VALUES (%s::uuid, %s, %s, %s, %s)
        RETURNING id::text, entry_date, kind, title, amount, created_at
        """,
        (str(tenant_id), entry_date, kind, title, amount),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def delete_entry(cur, tenant_id: str, entry_id: str) -> bool:
    """删除本租户的一条记录 · 返回是否真删到(0 行 = 不存在或非本租户)。"""
    cur.execute(
        "DELETE FROM daily_entries WHERE tenant_id = %s::uuid AND id = %s::uuid",
        (str(tenant_id), entry_id),
    )
    return bool(cur.rowcount)
