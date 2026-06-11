# -*- coding: utf-8 -*-
"""银行对账数据层(docs/accounting/bank-recon-mj/04):账户登记 + 流水池导入/列表 + 三余额。

复用最大化:解析栈在 routes 经 services/recon 跑(asyncio.to_thread),本层只落 lines;
账面余额取自 journal_lines(已过账)单一事实源,不另算;匹配/凭证生成在 bank_match.py。
调用方管事务;每句 WHERE tenant_id + workspace_client_id 双隔离。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.accounting import store as acct_store

ZERO = Decimal("0")

_ACCOUNT_COLS = (
    "id, bank_code, account_label, account_last4, coa_account_id, "
    "last_closing_balance, last_closing_date, is_active, created_at"
)
_LINE_COLS = (
    "id, bank_account_id, line_date, amount, direction, description, bank_ref, "
    "import_batch_id, status, matched_voucher_id, matched_at, created_at"
)


def _dec(v) -> Decimal:
    return Decimal(str(v if v is not None else 0))


# --------------------------------------------------------------------------- #
# 银行账户登记
# --------------------------------------------------------------------------- #
def list_bank_accounts(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    cur.execute(
        f"SELECT {_ACCOUNT_COLS} FROM acct_bank_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "ORDER BY is_active DESC, created_at",
        (tenant_id, workspace_client_id),
    )
    return [dict(r) for r in cur.fetchall()]


def get_bank_account(
    cur, *, tenant_id: str, workspace_client_id: int, account_id
) -> Optional[dict]:
    cur.execute(
        f"SELECT {_ACCOUNT_COLS} FROM acct_bank_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, account_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def create_bank_account(cur, *, tenant_id: str, workspace_client_id: int, data: dict) -> dict:
    """登记银行账户。coa_account_id 缺省回落 'bank' 角色映射(银行存款 1020)。"""
    bank_code = (data.get("bank_code") or "").strip().upper()
    if not bank_code:
        raise PosError("acct.unexpected", 422, detail="bank_code_required")
    coa_account_id = data.get("coa_account_id")
    if coa_account_id:
        acct = acct_store.get_account(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            account_id=coa_account_id,
        )
        if acct is None:
            raise PosError("acct.mapping_missing", 422, detail="coa_account_not_found")
    else:
        mappings = acct_store.resolve_mappings(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        coa_account_id = mappings.get("bank")
    cur.execute(
        "INSERT INTO acct_bank_accounts "
        "(tenant_id, workspace_client_id, bank_code, account_label, account_last4, coa_account_id) "
        f"VALUES (%s, %s, %s, %s, %s, %s) RETURNING {_ACCOUNT_COLS}",
        (
            tenant_id,
            workspace_client_id,
            bank_code,
            (data.get("account_label") or None),
            (data.get("account_last4") or None),
            coa_account_id,
        ),
    )
    return dict(cur.fetchone())


# --------------------------------------------------------------------------- #
# 流水导入(解析在 routes 跑完,本层落 lines + 更新统计余额)
# --------------------------------------------------------------------------- #
def insert_lines(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    bank_account_id,
    batch_id,
    sha256: str,
    transactions: list,
    closing_balance=None,
    closing_date=None,
) -> dict:
    """逐行落库(行级 uq 去重 → skipped);返回 {inserted, skipped}。

    direction 规范化 IN→in / OUT→out;amount 取绝对值(方向单列承载正负义)。
    """
    inserted, skipped = 0, 0
    for tx in transactions:
        line_date = tx.get("tx_date") or tx.get("line_date")
        amount = abs(_dec(tx.get("amount")))
        dir_raw = str(tx.get("direction", "")).upper()
        if not line_date or amount <= ZERO or dir_raw not in ("IN", "OUT"):
            # 缺日期/金额非正/方向未解析 → 跳过(诚实,不臆测)
            skipped += 1
            continue
        direction = "in" if dir_raw == "IN" else "out"
        cur.execute(
            "INSERT INTO acct_bank_lines "
            "(tenant_id, workspace_client_id, bank_account_id, line_date, amount, direction, "
            " description, bank_ref, import_batch_id, source_file_sha256) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (bank_account_id, line_date, amount, "
            "COALESCE(description, ''), COALESCE(bank_ref, '')) DO NOTHING RETURNING id",
            (
                tenant_id,
                workspace_client_id,
                bank_account_id,
                line_date,
                amount,
                direction,
                (tx.get("description") or None),
                (tx.get("ref_no") or tx.get("bank_ref") or None),
                batch_id,
                sha256,
            ),
        )
        if cur.fetchone():
            inserted += 1
        else:
            skipped += 1
    if closing_balance is not None:
        cur.execute(
            "UPDATE acct_bank_accounts SET last_closing_balance = %s, last_closing_date = %s "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
            (
                _dec(closing_balance),
                closing_date,
                tenant_id,
                workspace_client_id,
                bank_account_id,
            ),
        )
    return {"inserted": inserted, "skipped": skipped}


def file_already_imported(cur, *, tenant_id: str, workspace_client_id: int, sha256: str) -> bool:
    """同文件 sha256 已导过 → True(import 端点 409 duplicate_file)。"""
    cur.execute(
        "SELECT 1 FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND source_file_sha256 = %s LIMIT 1",
        (tenant_id, workspace_client_id, sha256),
    )
    return cur.fetchone() is not None


# --------------------------------------------------------------------------- #
# 流水列表 + 三余额
# --------------------------------------------------------------------------- #
def list_lines(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    bank_account_id=None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> list:
    sql = (
        f"SELECT {_LINE_COLS} FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s"
    )
    params: list = [tenant_id, workspace_client_id]
    if bank_account_id:
        sql += " AND bank_account_id = %s"
        params.append(bank_account_id)
    if period:
        sql += " AND to_char(line_date, 'YYYY-MM') = %s"
        params.append(period)
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY line_date DESC, created_at DESC LIMIT %s OFFSET %s"
    params += [min(int(limit), 500), max(int(offset), 0)]
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def get_line(cur, *, tenant_id: str, workspace_client_id: int, line_id) -> Optional[dict]:
    cur.execute(
        f"SELECT {_LINE_COLS}, source_file_sha256 FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, line_id),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _bank_coa_account_ids(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """本套账登记的银行账户对应的 COA 银行科目 id 集(账面余额取数范围)。"""
    cur.execute(
        "SELECT DISTINCT coa_account_id FROM acct_bank_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND coa_account_id IS NOT NULL",
        (tenant_id, workspace_client_id),
    )
    return [r["coa_account_id"] for r in cur.fetchall()]


def summary(cur, *, tenant_id: str, workspace_client_id: int) -> dict:
    """三余额闭环(V6):银行流水 closing · 账面 COA 银行科目 · 差额=未对净额 + 进度。"""
    cur.execute(
        "SELECT COALESCE(SUM(last_closing_balance), 0) AS bank_balance "
        "FROM acct_bank_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND last_closing_balance IS NOT NULL",
        (tenant_id, workspace_client_id),
    )
    bank_balance = _dec(cur.fetchone()["bank_balance"])

    book_balance = ZERO
    coa_ids = _bank_coa_account_ids(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if coa_ids:
        cur.execute(
            "SELECT COALESCE(SUM(CASE WHEN l.dr_cr = 'debit' THEN l.amount ELSE -l.amount END), 0) "
            "AS book_balance FROM journal_lines l "
            "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
            "WHERE v.tenant_id = %s AND v.workspace_client_id = %s "
            "AND v.status IN ('posted', 'auto_posted') AND l.account_id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, [str(a) for a in coa_ids]),
        )
        book_balance = _dec(cur.fetchone()["book_balance"])

    cur.execute(
        "SELECT "
        "COALESCE(SUM(CASE WHEN direction = 'in' THEN amount ELSE -amount END) "
        "  FILTER (WHERE status = 'unmatched'), 0) AS unmatched_net, "
        "count(*) FILTER (WHERE status != 'excluded') AS total_count, "
        "count(*) FILTER (WHERE status = 'matched') AS matched_count, "
        "count(*) FILTER (WHERE status = 'unmatched') AS unmatched_count "
        "FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    total = int(row["total_count"])
    matched = int(row["matched_count"])
    unmatched_net = _dec(row["unmatched_net"])
    return {
        "bank_balance": bank_balance,
        "book_balance": book_balance,
        # 04 定义:差额 = 未对净额(对完 = ฿0);balance_gap = 银行−账面(应与差额一致)供核对
        "difference": unmatched_net,
        "balance_gap": bank_balance - book_balance,
        "unmatched_net": unmatched_net,
        "total_count": total,
        "matched_count": matched,
        "unmatched_count": int(row["unmatched_count"]),
        "progress": round(matched / total, 4) if total else 1.0,
        "done": total > 0 and matched == total,
    }
