# -*- coding: utf-8 -*-
"""POS 终端/收银员/班次 DAL + 双跑迁移(POS 项目 · PO-B1 · docs/pos/03 §4)。

参数化叶子:每个函数收 cursor + tenant_id,每条语句 WHERE tenant_id(应用层硬隔离 ·
prod 角色 BYPASSRLS,RLS 仅兜底 · 见 [[pos-rls-bypass-app-layer-isolation]])。pin_hash
由 services/pos/auth 生成(bcrypt),本层只存取不解释。班次开/交逻辑在 services/pos/shift(B2),
此处仅 pin 登录需要的只读 open-班次查询 + 终端/收银员 CRUD。
"""

from __future__ import annotations

import logging
from typing import Optional

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_CASHIER_COLS = (
    "id, tenant_id, workspace_client_id, user_id, display_name, pin_hash, "
    "color, is_active, created_at, updated_at"
)
_CASHIER_PUBLIC = ("id", "display_name", "color")


# ── schema 双跑(与 alembic 0024 同源幂等 DDL)─────────────────────────
def ensure_core_schema() -> None:
    from core import db

    rls_tables = ("pos_terminals", "pos_cashiers", "pos_shifts")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_terminals (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    name text NOT NULL DEFAULT 'แคชเชียร์ 1',
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_terminals_ws "
                "ON pos_terminals (tenant_id, workspace_client_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_cashiers (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    user_id uuid REFERENCES users(id) ON DELETE SET NULL,
                    display_name text NOT NULL,
                    pin_hash text NOT NULL,
                    color text,
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_cashiers_ws "
                "ON pos_cashiers (tenant_id, workspace_client_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_shifts (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    terminal_id bigint NOT NULL REFERENCES pos_terminals(id) ON DELETE CASCADE,
                    cashier_id uuid NOT NULL REFERENCES pos_cashiers(id) ON DELETE CASCADE,
                    opened_at timestamptz NOT NULL DEFAULT now(),
                    closed_at timestamptz,
                    opening_float numeric(14,2) NOT NULL DEFAULT 0,
                    expected_cash numeric(14,2),
                    counted_cash numeric(14,2),
                    cash_diff numeric(14,2),
                    status text NOT NULL DEFAULT 'open',
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_open "
                "ON pos_shifts (tenant_id, terminal_id) WHERE status = 'open'"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_shifts_cashier "
                "ON pos_shifts (tenant_id, cashier_id, status)"
            )
            apply_tenant_rls(cur, *rls_tables)
        logger.info("✅ POS 核心 3 表 + RLS 已就绪 (POS PO-B1)")
    except Exception as e:
        logger.warning(f"ensure_core_schema pos 失败(跳过 · 等 alembic 0024): {e}")


# ── 租户解析(PIN 登录前匿名拉名单 · 由 workspace_client_id 反查 tenant)──────
def resolve_tenant_for_workspace(cur, *, workspace_client_id: int) -> Optional[str]:
    """workspace_client_id 是全局 bigserial,反查其 tenant_id(供前台匿名 pin 登录定位租户)。"""
    cur.execute(
        "SELECT tenant_id FROM workspace_clients WHERE id = %s",
        (workspace_client_id,),
    )
    row = cur.fetchone()
    return str(row["tenant_id"]) if row and row.get("tenant_id") else None


# ── terminals ─────────────────────────────────────────────────────────
def list_terminals(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    cur.execute(
        "SELECT id, name, is_active FROM pos_terminals "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE ORDER BY id",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def get_terminal(cur, *, tenant_id: str, workspace_client_id: int, terminal_id: int):
    cur.execute(
        "SELECT id, name, is_active FROM pos_terminals "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, terminal_id),
    )
    return cur.fetchone()


def get_or_create_default_terminal(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    cur.execute(
        "SELECT id, name, is_active FROM pos_terminals "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE "
        "ORDER BY id LIMIT 1",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        "INSERT INTO pos_terminals (tenant_id, workspace_client_id) "
        "VALUES (%s, %s) RETURNING id, name, is_active",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchone()


# ── cashiers ──────────────────────────────────────────────────────────
def list_cashiers(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """开班选人列表:仅公开字段(名字/颜色),不含 pin_hash。"""
    cur.execute(
        "SELECT id, display_name, color FROM pos_cashiers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND is_active = TRUE "
        "ORDER BY display_name",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def get_cashier(cur, *, tenant_id: str, workspace_client_id: int, cashier_id: str):
    """完整收银员行(含 pin_hash/is_active)· PIN 登录校验用。"""
    cur.execute(
        f"SELECT {_CASHIER_COLS} FROM pos_cashiers "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, cashier_id),
    )
    return cur.fetchone()


def create_cashier(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    display_name: str,
    pin_hash: str,
    user_id: Optional[str] = None,
    color: Optional[str] = None,
) -> dict:
    cur.execute(
        "INSERT INTO pos_cashiers "
        "(tenant_id, workspace_client_id, user_id, display_name, pin_hash, color) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "RETURNING id, display_name, color, is_active",
        (tenant_id, workspace_client_id, user_id, display_name, pin_hash, color),
    )
    return cur.fetchone()


# ── 班次只读(PIN 登录返回当前 open 班次 · 开/交逻辑在 shift.py B2)────────
def get_open_shift_for_cashier(cur, *, tenant_id: str, cashier_id: str):
    cur.execute(
        "SELECT id, terminal_id, opened_at, opening_float FROM pos_shifts "
        "WHERE tenant_id = %s AND cashier_id = %s AND status = 'open' "
        "ORDER BY opened_at DESC LIMIT 1",
        (tenant_id, cashier_id),
    )
    return cur.fetchone()
