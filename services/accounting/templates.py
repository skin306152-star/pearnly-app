# -*- coding: utf-8 -*-
"""凭证模板 DAL(docs/accounting/bank-recon-mj/04 · acct_voucher_templates)。

模板 = 手工凭证骨架(科目 + 借贷方向 + 摘要,无金额),录入时套用省键盘。一键存(from_voucher)、
用(use_count++)、删(不影响历史凭证)。调用方管事务;每句 WHERE tenant_id + workspace_client_id。
"""

from __future__ import annotations

import json
from typing import Optional

from core.pos_api import PosError
from services.accounting import store as acct_store

_COLS = "id, name, lines, use_count, created_by, created_at"

_VALID_DRCR = ("debit", "credit")


def _normalize_lines(cur, *, tenant_id, workspace_client_id, lines) -> list:
    """校验每行 account_id 属本套账 + dr_cr 合法;模板不存金额。"""
    out = []
    for ln in lines or []:
        account_id = ln.get("account_id")
        dr_cr = ln.get("dr_cr")
        if dr_cr not in _VALID_DRCR or not account_id:
            raise PosError("acct.unexpected", 422, detail="template_line_invalid")
        acct = acct_store.get_account(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            account_id=account_id,
        )
        if acct is None:
            raise PosError("acct.mapping_missing", 422, detail="account_not_found")
        out.append({"account_id": str(account_id), "dr_cr": dr_cr, "memo": ln.get("memo") or None})
    if not out:
        raise PosError("acct.unexpected", 422, detail="template_empty")
    return out


def list_templates(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    cur.execute(
        f"SELECT {_COLS} FROM acct_voucher_templates "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "ORDER BY use_count DESC, created_at DESC",
        (tenant_id, workspace_client_id),
    )
    out = []
    for r in cur.fetchall():
        row = dict(r)
        if isinstance(row["lines"], str):
            row["lines"] = json.loads(row["lines"] or "[]")
        out.append(row)
    return out


def create_template(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    name: str,
    lines: list,
    created_by=None,
) -> dict:
    name = (name or "").strip()
    if not name:
        raise PosError("acct.unexpected", 422, detail="template_name_required")
    norm = _normalize_lines(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, lines=lines
    )
    cur.execute(
        "SELECT 1 FROM acct_voucher_templates "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND name = %s",
        (tenant_id, workspace_client_id, name),
    )
    if cur.fetchone():
        raise PosError("acct.unexpected", 409, detail="template_name_exists")
    cur.execute(
        "INSERT INTO acct_voucher_templates "
        "(tenant_id, workspace_client_id, name, lines, created_by) "
        f"VALUES (%s, %s, %s, %s::jsonb, %s) RETURNING {_COLS}",
        (tenant_id, workspace_client_id, name, json.dumps(norm), created_by),
    )
    row = dict(cur.fetchone())
    if isinstance(row["lines"], str):
        row["lines"] = json.loads(row["lines"] or "[]")
    return row


def lines_from_voucher(cur, *, tenant_id, workspace_client_id, voucher_id) -> list:
    """一键存:从已有凭证取借贷骨架(去金额)做模板。"""
    from services.accounting import vouchers as jv

    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if voucher is None:
        raise PosError("acct.unexpected", 404, detail="voucher_not_found")
    return [
        {"account_id": str(ln["account_id"]), "dr_cr": ln["dr_cr"], "memo": ln.get("memo")}
        for ln in voucher["lines"]
    ]


def bump_use_count(cur, *, tenant_id: str, workspace_client_id: int, template_id) -> None:
    cur.execute(
        "UPDATE acct_voucher_templates SET use_count = use_count + 1 "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, template_id),
    )


def delete_template(cur, *, tenant_id: str, workspace_client_id: int, template_id) -> Optional[str]:
    """删模板(不影响历史凭证:模板与凭证无 FK)。"""
    cur.execute(
        "DELETE FROM acct_voucher_templates "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s RETURNING id",
        (tenant_id, workspace_client_id, template_id),
    )
    row = cur.fetchone()
    return str(row["id"]) if row else None
