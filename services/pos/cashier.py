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

from psycopg2.extras import Json

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_CASHIER_COLS = (
    "id, tenant_id, workspace_client_id, user_id, display_name, pin_hash, "
    "color, is_active, caps, created_at, updated_at"
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
            # 与 alembic 0068 同源:纯收银员按人权限载体(绑主账号者按 RBAC 换算,不读本列)。
            cur.execute(
                "ALTER TABLE pos_cashiers "
                "ADD COLUMN IF NOT EXISTS caps jsonb NOT NULL DEFAULT '{}'::jsonb"
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
            # 与 alembic 0069 同源:每 (tenant,ws) 连号 tamper-evidence,唯一约束兜并发撞号。
            # prod 不自动跑迁移(靠本双跑建 schema)→ 回填必须也在此,否则存量班次 shift_seq 恒 NULL,
            # 新开班 _next_seq=MAX+1=1 会与日后手动回填的 1 撞唯一约束。ADD→回填(仅补 NULL·幂等)→建索引。
            cur.execute("ALTER TABLE pos_shifts ADD COLUMN IF NOT EXISTS shift_seq integer")
            cur.execute(
                "WITH numbered AS ("
                "  SELECT id, row_number() OVER ("
                "    PARTITION BY tenant_id, workspace_client_id"
                "    ORDER BY opened_at, created_at, id"
                "  ) AS rn FROM pos_shifts"
                ") "
                "UPDATE pos_shifts s SET shift_seq = n.rn "
                "FROM numbered n WHERE s.id = n.id AND s.shift_seq IS NULL"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_seq "
                "ON pos_shifts (tenant_id, workspace_client_id, shift_seq)"
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


# ── 收银员后台管理(owner · 含停用项)─────────────────────────────────
def list_cashiers_admin(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """后台管理列表:含停用项 + is_active + 最近开班时间 + 是否开过班(决定可否删)。不含 pin_hash。"""
    cur.execute(
        "SELECT c.id, c.display_name, c.color, c.is_active, c.user_id, c.caps, "
        "  (SELECT MAX(s.opened_at) FROM pos_shifts s "
        "   WHERE s.tenant_id = c.tenant_id AND s.cashier_id = c.id) AS last_opened_at, "
        "  EXISTS(SELECT 1 FROM pos_shifts s "
        "   WHERE s.tenant_id = c.tenant_id AND s.cashier_id = c.id) AS has_shifts "
        "FROM pos_cashiers c "
        "WHERE c.tenant_id = %s AND c.workspace_client_id = %s "
        "ORDER BY c.is_active DESC, c.display_name",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def delete_cashier_if_unused(cur, *, tenant_id: str, workspace_client_id: int, cashier_id: str):
    """删除从未开过班的收银员。返回 True=已删 / False=有开班记录不可删 / None=不存在。"""
    cur.execute(
        "SELECT 1 FROM pos_cashiers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, cashier_id),
    )
    if not cur.fetchone():
        return None
    cur.execute(
        "SELECT 1 FROM pos_shifts WHERE tenant_id = %s AND cashier_id = %s LIMIT 1",
        (tenant_id, cashier_id),
    )
    if cur.fetchone():
        return False
    cur.execute(
        "DELETE FROM pos_cashiers " "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, cashier_id),
    )
    return True


def is_active_member(cur, *, tenant_id: str, user_id: str) -> bool:
    """该 user 是否本租户的在职成员(店长授权人绑定前置校验 · 防绑跨租户/离职账号)。"""
    cur.execute(
        "SELECT 1 FROM memberships "
        "WHERE tenant_id = %s AND user_id = %s AND status = 'active' LIMIT 1",
        (str(tenant_id), str(user_id)),
    )
    return cur.fetchone() is not None


# _UNSET 让 user_id 能被显式改成 None(解绑)而不与「本次不改」混淆(None 是有效目标值)。
_UNSET = object()


_RETURN_COLS = "id, display_name, color, is_active, caps"


def update_cashier(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    cashier_id: str,
    display_name: Optional[str] = None,
    color: Optional[str] = None,
    is_active: Optional[bool] = None,
    pin_hash: Optional[str] = None,
    user_id=_UNSET,
    caps=_UNSET,
):
    """改名/换色/启停/重设 PIN/绑解主账号/改 caps(只更传入字段)。找不到返 None。

    user_id 绑定 = 把该收银员标为「店长授权人」的载体:绑到一个持 pos.refund.approve 的
    主账号后,其 PIN 才能在退货授权窗覆盖放行(校验走关联主账号的 RBAC · services/pos/approval)。
    caps = 纯收银员按人权限(折扣上限/退作废/改价/成本可见);调用方须先 caps.sanitize_caps 白名单。
    """
    sets, vals = [], []
    if display_name is not None:
        sets.append("display_name = %s")
        vals.append(display_name)
    if color is not None:
        sets.append("color = %s")
        vals.append(color)
    if is_active is not None:
        sets.append("is_active = %s")
        vals.append(is_active)
    if pin_hash is not None:
        sets.append("pin_hash = %s")
        vals.append(pin_hash)
    if user_id is not _UNSET:
        sets.append("user_id = %s")
        vals.append(str(user_id) if user_id else None)
    if caps is not _UNSET:
        sets.append("caps = %s")
        vals.append(Json(caps or {}))
    if not sets:
        cur.execute(
            f"SELECT {_RETURN_COLS} FROM pos_cashiers "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
            (tenant_id, workspace_client_id, cashier_id),
        )
        return cur.fetchone()
    sets.append("updated_at = now()")
    set_clause = ", ".join(sets)  # 全为 "<列名> = %s" 常量片段(值走 %s 参数化)
    cur.execute(
        f"UPDATE pos_cashiers SET {set_clause} "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s "
        f"RETURNING {_RETURN_COLS}",
        vals + [tenant_id, workspace_client_id, cashier_id],
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


def get_open_shift_for_workspace(cur, *, tenant_id: str, workspace_client_id: int):
    """套账(收银台)当前的未结班次 —— 按终端唯一,与开班人无关。
    收银台=共享钱箱:任何收银员登录都接续这一班、都能交班(避免第二人被锁死/重复开班)。"""
    cur.execute(
        "SELECT id, terminal_id, opened_at, opening_float, shift_seq FROM pos_shifts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'open' "
        "ORDER BY opened_at DESC LIMIT 1",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchone()
