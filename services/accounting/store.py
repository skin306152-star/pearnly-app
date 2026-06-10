# -*- coding: utf-8 -*-
"""科目表 + 科目映射 DAL(docs/accounting/01 · 套账隔离每句 WHERE tenant+ws)。

预置科目不可删只可停;映射 role→account 唯一,引擎过账时经 resolve_mappings 解析。
调用方管事务。
"""

from __future__ import annotations


from core.pos_api import PosError

_ACCT_COLS = "id, code, name_zh, name_th, acct_type, parent_id, is_preset, is_active, sort"


def list_accounts(cur, *, tenant_id: str, workspace_client_id: int, acct_type=None, q=None):
    sql = (
        f"SELECT {_ACCT_COLS} FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s"
    )
    params: list = [tenant_id, workspace_client_id]
    if acct_type:
        sql += " AND acct_type = %s"
        params.append(acct_type)
    if q:
        sql += " AND (code ILIKE %s OR name_zh ILIKE %s OR name_th ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += " ORDER BY sort, code"
    cur.execute(sql, params)
    return cur.fetchall()


def get_account(cur, *, tenant_id: str, workspace_client_id: int, account_id: str):
    cur.execute(
        f"SELECT {_ACCT_COLS} FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, account_id),
    )
    return cur.fetchone()


def create_account(cur, *, tenant_id: str, workspace_client_id: int, data: dict) -> dict:
    code = (data.get("code") or "").strip()
    name_zh = (data.get("name_zh") or "").strip()
    acct_type = data.get("acct_type")
    if (
        not code
        or not name_zh
        or acct_type
        not in (
            "asset",
            "liability",
            "equity",
            "revenue",
            "expense",
        )
    ):
        raise PosError("acct.unexpected", 422, detail="account_fields_invalid")
    cur.execute(
        "SELECT 1 FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND code = %s",
        (tenant_id, workspace_client_id, code),
    )
    if cur.fetchone():
        raise PosError("acct.unexpected", 409, detail="code_exists")
    cur.execute(
        "INSERT INTO chart_of_accounts "
        "(tenant_id, workspace_client_id, code, name_zh, name_th, acct_type, parent_id, sort) "
        f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING {_ACCT_COLS}",
        (
            tenant_id,
            workspace_client_id,
            code,
            name_zh,
            (data.get("name_th") or None),
            acct_type,
            data.get("parent_id"),
            int(data.get("sort") or 0),
        ),
    )
    return cur.fetchone()


def update_account(
    cur, *, tenant_id: str, workspace_client_id: int, account_id: str, data: dict
) -> dict:
    """改名/停启用/排序。预置科目编号与类型不可改,只能停用(is_preset 保护)。"""
    row = get_account(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, account_id=account_id
    )
    if row is None:
        raise PosError("acct.unexpected", 404, detail="account_not_found")
    allowed = ("name_zh", "name_th", "is_active", "sort")
    if not row["is_preset"]:
        allowed += ("code", "acct_type", "parent_id")
    set_clause, params = [], []
    for col in allowed:
        if col in data:
            set_clause.append(f"{col} = %s")
            params.append(data[col])
    if not set_clause:
        return row
    set_clause.append("updated_at = now()")
    cur.execute(
        f"UPDATE chart_of_accounts SET {', '.join(set_clause)} "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        params + [tenant_id, workspace_client_id, account_id],
    )
    return get_account(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, account_id=account_id
    )


def resolve_mappings(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """role → account_id 全量映射(引擎过账用·一次取全免逐角色查)。"""
    cur.execute(
        "SELECT m.role, m.account_id FROM account_mappings m "
        "JOIN chart_of_accounts a ON a.id = m.account_id AND a.tenant_id = m.tenant_id "
        "WHERE m.tenant_id = %s AND m.workspace_client_id = %s AND a.is_active",
        (tenant_id, workspace_client_id),
    )
    return {r["role"]: r["account_id"] for r in cur.fetchall()}


def list_mappings(cur, *, tenant_id: str, workspace_client_id: int):
    cur.execute(
        "SELECT m.role, m.account_id, a.code, a.name_zh FROM account_mappings m "
        "JOIN chart_of_accounts a ON a.id = m.account_id AND a.tenant_id = m.tenant_id "
        "WHERE m.tenant_id = %s AND m.workspace_client_id = %s ORDER BY m.role",
        (tenant_id, workspace_client_id),
    )
    return cur.fetchall()


def set_mapping(
    cur, *, tenant_id: str, workspace_client_id: int, role: str, account_id: str
) -> None:
    """upsert 单角色映射;科目必须属本套账(防跨套账指针)。"""
    acct = get_account(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, account_id=account_id
    )
    if acct is None:
        raise PosError("acct.unexpected", 404, detail="account_not_found")
    cur.execute(
        "INSERT INTO account_mappings (tenant_id, workspace_client_id, role, account_id) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id, role) "
        "DO UPDATE SET account_id = EXCLUDED.account_id, updated_at = now()",
        (tenant_id, workspace_client_id, role, account_id),
    )


def account_names(cur, *, tenant_id: str, workspace_client_id: int, account_ids: list) -> dict:
    """id → {code,name_zh,name_th}(凭证详情借贷行显示用)。"""
    if not account_ids:
        return {}
    cur.execute(
        "SELECT id, code, name_zh, name_th FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = ANY(%s::uuid[])",
        (tenant_id, workspace_client_id, [str(a) for a in account_ids]),
    )
    return {str(r["id"]): r for r in cur.fetchall()}
