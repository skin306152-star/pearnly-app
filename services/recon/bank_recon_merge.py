# -*- coding: utf-8 -*-
"""
services/recon/bank_recon_merge.py · Pearnly

Merge multiple parsed statement / GL files into a single ordered row set
before reconciliation.
"""

from datetime import date
from typing import List, Dict, Any, Tuple

from services.recon.bank_recon_types import StatementRow, GlRow


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-FILE MERGE
# ─────────────────────────────────────────────────────────────────────────────
def merge_statements(
    parsed_list: List[Dict[str, Any]],
) -> Tuple[List[StatementRow], float, float, str]:
    """Merge multiple parsed bank statements, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0
    bank_code = "generic"
    earliest_date = None
    latest_date = None

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("bank_code") and p["bank_code"] != "generic":
            bank_code = p["bank_code"]
        for r in p.get("rows") or []:
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)
            if r.date:
                if earliest_date is None or r.date < earliest_date:
                    earliest_date = r.date
                if latest_date is None or r.date > latest_date:
                    latest_date = r.date

    # v118.35.0.48 · 只按日期稳定排序 · 保留对账单原始打印顺序(同日多笔不重排)
    # 旧版按 (date, withdrawal, deposit) 排 · 把同一天的存/取款按金额重排 · 打乱了
    # 对账单的"上一行余额 ± 金额 = 本行余额"链条 · 导致余额验证误报 + 显示顺序错乱。
    # Python sort 稳定 → 同日行保持 append(= 解析 = PDF 顶到底)顺序。
    all_rows.sort(key=lambda r: (r.date or date.min,))

    # Opening: from first parsed file that has an opening balance
    for p in parsed_list:
        if p.get("ok") and p.get("opening", 0.0) != 0.0:
            opening = p["opening"]
            break

    # Closing: from last parsed file or recalculate
    for p in reversed(parsed_list):
        if p.get("ok") and p.get("closing", 0.0) != 0.0:
            closing = p["closing"]
            break

    if opening == 0.0 and all_rows:
        first = all_rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    if closing == 0.0 and all_rows:
        closing = all_rows[-1].balance

    # Order-independent guard: imported Excel rows may not be chronological (user
    # paste), which makes a row-order opening/closing wrong. all_rows is date-sorted
    # above, so if opening/closing don't satisfy opening + Σ(deposit − withdrawal)
    # = closing, re-derive from the balance chain (closing = latest-dated balance,
    # opening = closing − net). No-op when already consistent (PDF / sorted input).
    if all_rows and any(r.balance for r in all_rows):
        net = round(sum(r.deposit - r.withdrawal for r in all_rows), 2)
        if abs(opening + net - closing) > 0.05:
            closing = all_rows[-1].balance
            opening = round(closing - net, 2)

    return all_rows, opening, closing, bank_code


def merge_gl_files(
    parsed_list: List[Dict[str, Any]], account_code: str = ""
) -> Tuple[List[GlRow], List[str], float, float]:
    """Merge multiple parsed GL files, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[GlRow] = []
    all_accounts: set = set()
    opening = 0.0

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("opening", 0.0) != 0.0 and opening == 0.0:
            opening = p["opening"]
        for acct in p.get("accounts") or []:
            all_accounts.add(acct)
        for r in p.get("rows") or []:
            if account_code and r.account_code and not r.account_code.startswith(account_code):
                continue
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)

    all_rows.sort(key=lambda r: (r.date or date.min, r.doc_no or ""))

    # v118.33.13.5 · Cash-ledger formula (matches parse_gl_pdf v118.33.13.4):
    # debit = cash IN (balance increase), credit = cash OUT (balance decrease)
    # The OLD formula `opening + credit - debit` was the expense/revenue
    # perspective and produced wrong closing balances for bank GLs.
    total_credit = sum(r.credit for r in all_rows)
    total_debit = sum(r.debit for r in all_rows)
    closing = round(opening + total_debit - total_credit, 2)

    return all_rows, sorted(all_accounts), opening, closing
