# -*- coding: utf-8 -*-
"""凭证 DAL(头+借贷行 · 连号 · 借贷平断言 · docs/accounting/01)。

借贷恒平是入库前的硬断言(acct.unbalanced 拒绝,绝不落不平凭证)。凭证号复用
document_number_sequences 按主体按期连号(doc_type='voucher' · FOR UPDATE 防跳号)。
调用方管事务。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.accounting import store as acct_store
from services.sales import numbering

_HEAD_COLS = (
    "id, voucher_no, voucher_date, period, source_type, source_id, source_ref, description, "
    "human_note, rule_key, confidence, source_tier, method, status, review_reason, "
    "total_debit, total_credit, created_by, reviewed_by, reviewed_at, created_at"
)

ZERO = Decimal("0")


def assert_balanced(lines: list) -> tuple[Decimal, Decimal]:
    """Σ借=Σ贷且>0,否则 acct.unbalanced(422)。返回 (total_debit, total_credit)。"""
    debit = sum((Decimal(str(ln["amount"])) for ln in lines if ln["dr_cr"] == "debit"), ZERO)
    credit = sum((Decimal(str(ln["amount"])) for ln in lines if ln["dr_cr"] == "credit"), ZERO)
    if debit != credit or debit <= ZERO:
        raise PosError("acct.unbalanced", 422, detail=f"debit={debit} credit={credit}")
    if any(Decimal(str(ln["amount"])) <= ZERO for ln in lines):
        raise PosError("acct.unbalanced", 422, detail="non_positive_line")
    return debit, credit


def find_active_by_source(cur, *, tenant_id, workspace_client_id, source_type, source_id):
    """防重复:同 source 已有非 void 凭证 → 返回它(幂等早退)。"""
    cur.execute(
        f"SELECT {_HEAD_COLS} FROM journal_vouchers "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND source_type = %s AND source_id = %s AND status != 'void'",
        (tenant_id, workspace_client_id, source_type, source_id),
    )
    return cur.fetchone()


def insert_voucher(
    cur, *, tenant_id: str, workspace_client_id: int, header: dict, lines: list
) -> dict:
    """落凭证头+借贷行。lines 可空(缺映射的待审壳,review_reason 必填);非空必先断言平。"""
    if lines:
        total_debit, total_credit = assert_balanced(lines)
    else:
        if not header.get("review_reason"):
            raise PosError("acct.unbalanced", 422, detail="empty_lines")
        total_debit = total_credit = Decimal(str(header.get("total_amount") or 0))

    voucher_date = header["voucher_date"]
    period = voucher_date.strftime("%Y-%m")
    voucher_no, _n = numbering.allocate(
        cur,
        tenant_id=tenant_id,
        doc_type="voucher",
        prefix="JV",
        reset="monthly",
        on=voucher_date,
        workspace_client_id=workspace_client_id,
    )
    cur.execute(
        "INSERT INTO journal_vouchers "
        "(tenant_id, workspace_client_id, voucher_no, voucher_date, period, source_type, "
        " source_id, source_ref, description, human_note, rule_key, confidence, source_tier, "
        " method, status, review_reason, total_debit, total_credit, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        f"RETURNING {_HEAD_COLS}",
        (
            tenant_id,
            workspace_client_id,
            voucher_no,
            voucher_date,
            period,
            header["source_type"],
            header.get("source_id"),
            header.get("source_ref"),
            header.get("description"),
            header.get("human_note"),
            header.get("rule_key"),
            header.get("confidence") or 0,
            header.get("source_tier") or "manual",
            header.get("method") or "suggested",
            header.get("status") or "pending_review",
            header.get("review_reason"),
            total_debit,
            total_credit,
            header.get("created_by"),
        ),
    )
    voucher = cur.fetchone()
    for i, ln in enumerate(lines):
        cur.execute(
            "INSERT INTO journal_lines "
            "(tenant_id, voucher_id, account_id, dr_cr, amount, memo, sort) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                tenant_id,
                voucher["id"],
                ln["account_id"],
                ln["dr_cr"],
                ln["amount"],
                ln.get("memo"),
                i,
            ),
        )
    return dict(voucher)


def get_voucher(cur, *, tenant_id: str, workspace_client_id: int, voucher_id) -> Optional[dict]:
    cur.execute(
        f"SELECT {_HEAD_COLS} FROM journal_vouchers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, voucher_id),
    )
    head = cur.fetchone()
    if head is None:
        return None
    out = dict(head)
    out["lines"] = get_lines(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    return out


def get_lines(cur, *, tenant_id: str, workspace_client_id: int, voucher_id) -> list:
    cur.execute(
        "SELECT id, account_id, dr_cr, amount, memo, sort FROM journal_lines "
        "WHERE tenant_id = %s AND voucher_id = %s ORDER BY sort",
        (tenant_id, voucher_id),
    )
    rows = [dict(r) for r in cur.fetchall()]
    names = acct_store.account_names(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        account_ids=[r["account_id"] for r in rows],
    )
    for r in rows:
        acct = names.get(str(r["account_id"])) or {}
        r["account_code"] = acct.get("code")
        r["account_name"] = acct.get("name_zh")
    return rows


def list_vouchers(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    period=None,
    source_type=None,
    status=None,
    method=None,
    q=None,
    limit: int = 200,
) -> list:
    sql = (
        f"SELECT {_HEAD_COLS} FROM journal_vouchers "
        "WHERE tenant_id = %s AND workspace_client_id = %s"
    )
    params: list = [tenant_id, workspace_client_id]
    for col, val in (
        ("period", period),
        ("source_type", source_type),
        ("status", status),
        ("method", method),
    ):
        if val:
            sql += f" AND {col} = %s"
            params.append(val)
    if q:
        sql += " AND (voucher_no ILIKE %s OR description ILIKE %s OR source_ref ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += " ORDER BY voucher_date DESC, created_at DESC LIMIT %s"
    params.append(min(int(limit), 500))
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def summary(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """主屏北极星:本月自动做账 / 已过账 / 待审计数。"""
    cur.execute(
        "SELECT "
        "count(*) FILTER (WHERE method = 'auto' AND status = 'auto_posted') AS auto_count, "
        "count(*) FILTER (WHERE status IN ('auto_posted','posted')) AS posted_count, "
        "count(*) FILTER (WHERE status = 'pending_review') AS pending_count "
        "FROM journal_vouchers "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s AND status != 'void'",
        (tenant_id, workspace_client_id, period),
    )
    row = cur.fetchone()
    return {
        "auto_count": int(row["auto_count"]),
        "posted_count": int(row["posted_count"]),
        "pending_count": int(row["pending_count"]),
    }


def apply_account_overrides(
    cur, *, tenant_id: str, workspace_client_id: int, voucher_id, account_overrides
) -> Optional[str]:
    """逐行改科目(金额不动 → 平衡不变)。科目必须属本套账且在用。返回最后改的科目 id。

    逐笔审与 PATCH 共用(改科目规则只此一处)。
    """
    last = None
    for line_id, account_id in (account_overrides or {}).items():
        cur.execute(
            "SELECT 1 FROM chart_of_accounts "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND is_active",
            (tenant_id, workspace_client_id, account_id),
        )
        if not cur.fetchone():
            raise PosError("acct.mapping_missing", 422, detail="override_account_not_found")
        cur.execute(
            "UPDATE journal_lines SET account_id = %s "
            "WHERE tenant_id = %s AND id = %s AND voucher_id = %s",
            (account_id, tenant_id, line_id, voucher_id),
        )
        last = account_id
    return last


def set_status(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    voucher_id,
    status: str,
    method=None,
    reviewed_by=None,
) -> None:
    set_clause = ["status = %s", "updated_at = now()"]
    params: list = [status]
    if method:
        set_clause.append("method = %s")
        params.append(method)
    if reviewed_by:
        set_clause += ["reviewed_by = %s", "reviewed_at = now()", "review_reason = NULL"]
        params.append(reviewed_by)
    cur.execute(
        f"UPDATE journal_vouchers SET {', '.join(set_clause)} "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        params + [tenant_id, workspace_client_id, voucher_id],
    )
