# -*- coding: utf-8 -*-
"""
services/recon/bank_recon_reconcile.py · Pearnly

Statement-vs-GL reconciliation core: matches parsed bank-statement rows
against GL rows (L1 exact date+amount, L2 ±DATE_TOL_DAYS tolerance, L3
amount-only) and builds the per-row result + summary. Pure function.
"""

from datetime import date
from typing import List, Optional, Tuple

from services.recon.bank_recon_types import StatementRow, GlRow, BankReconRow, BankReconSummary
from services.recon.bank_recon_utils import _day_diff, _amount_matches, DATE_TOL_DAYS


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def reconcile(
    stmt_rows: List[StatementRow],
    gl_rows: List[GlRow],
    stmt_opening: float = 0.0,
    gl_opening: float = 0.0,
    stmt_closing: float = 0.0,
    gl_closing: float = 0.0,
    bank_code: str = "",
    gl_account_code: str = "",
) -> Tuple[List[BankReconRow], BankReconSummary]:
    """
    3-layer matching: L1 exact date+amount, L2 ±3-day+amount, L3 amount only.
    Returns (recon_rows, summary).
    """
    recon_rows: List[BankReconRow] = []

    # Work with indices to track matched/unmatched
    gl_used = [False] * len(gl_rows)
    stmt_used = [False] * len(stmt_rows)

    def try_match_gl(stmt_row: StatementRow, layer: int) -> Optional[int]:
        """Find best GL match for a statement row. Returns GL index or None."""
        target_amount = stmt_row.withdrawal if stmt_row.withdrawal > 0 else stmt_row.deposit
        # Withdrawal from bank = company paid out = GL Credit; Deposit = GL Debit
        direction = "C" if stmt_row.withdrawal > 0 else "D"

        best_idx = None
        best_day_diff = 999

        for gi, gr in enumerate(gl_rows):
            if gl_used[gi]:
                continue
            gl_amount = gr.debit if direction == "D" else gr.credit
            if not _amount_matches(target_amount, gl_amount):
                continue
            if gl_amount == 0:
                continue

            dd = _day_diff(stmt_row.date, gr.date)
            if layer == 1:
                if dd is None or dd > 0:
                    continue
                best_idx = gi
                break
            elif layer == 2:
                if dd is None or dd > DATE_TOL_DAYS:
                    continue
                if dd < best_day_diff:
                    best_day_diff = dd
                    best_idx = gi
            elif layer == 3:
                if best_idx is None:
                    best_idx = gi

        return best_idx

    # Layer 1: exact date + exact amount
    for si, sr in enumerate(stmt_rows):
        gi = try_match_gl(sr, layer=1)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=1,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=0,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 2: ±3-day tolerance
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=2)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date) or 0
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=2,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 3: amount only (no date constraint) — flagged
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=3)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date)
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=3,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Remaining unmatched statement rows
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        status = "stmt_withdrawal_only" if sr.withdrawal > 0 else "stmt_deposit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                stmt_date=sr.date,
                stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal,
                stmt_deposit=sr.deposit,
                stmt_balance=sr.balance,
                stmt_confidence=sr.confidence,
                stmt_balance_ok=sr.balance_ok,
                stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                source_stmt_file=sr.source_file,
            )
        )

    # Remaining unmatched GL rows
    for gi, gr in enumerate(gl_rows):
        if gl_used[gi]:
            continue
        status = "gl_debit_only" if gr.debit > 0 else "gl_credit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                gl_date=gr.date,
                gl_doc_no=gr.doc_no,
                gl_account_code=gr.account_code,
                gl_desc=gr.description,
                gl_debit=gr.debit,
                gl_credit=gr.credit,
                source_gl_file=gr.source_file,
            )
        )

    # Sort: matched first (by stmt_date), then unmatched
    def _sort_key(r: BankReconRow):
        order = 0 if r.match_status == "matched" else 1
        d = r.stmt_date or r.gl_date or date.min
        return (order, d)

    recon_rows.sort(key=_sort_key)

    # Build summary
    matched_rows = [r for r in recon_rows if r.match_status == "matched"]
    gl_debit_only = [r for r in recon_rows if r.match_status == "gl_debit_only"]
    gl_credit_only = [r for r in recon_rows if r.match_status == "gl_credit_only"]
    stmt_wd_only = [r for r in recon_rows if r.match_status == "stmt_withdrawal_only"]
    stmt_dep_only = [r for r in recon_rows if r.match_status == "stmt_deposit_only"]

    gl_debit_only_amt = round(sum(r.gl_debit for r in gl_debit_only), 2)
    gl_credit_only_amt = round(sum(r.gl_credit for r in gl_credit_only), 2)
    stmt_wd_only_amt = round(sum(r.stmt_withdrawal for r in stmt_wd_only), 2)
    stmt_dep_only_amt = round(sum(r.stmt_deposit for r in stmt_dep_only), 2)

    # Reconciliation formula:
    # stmt_closing ≈ gl_closing + opening_diff - gl_debit_only + gl_credit_only
    #                           - stmt_wd_only + stmt_dep_only
    opening_diff = round(stmt_opening - gl_opening, 2)
    formula_closing = round(
        gl_closing
        + opening_diff
        - gl_debit_only_amt
        + gl_credit_only_amt
        - stmt_wd_only_amt
        + stmt_dep_only_amt,
        2,
    )
    formula_diff = round(stmt_closing - formula_closing, 2)

    summary = BankReconSummary(
        bank_code=bank_code,
        gl_account_code=gl_account_code,
        stmt_opening=stmt_opening,
        stmt_closing=stmt_closing,
        gl_opening=gl_opening,
        gl_closing=gl_closing,
        stmt_total_deposit=round(sum(r.deposit for r in stmt_rows), 2),
        stmt_total_withdrawal=round(sum(r.withdrawal for r in stmt_rows), 2),
        gl_total_credit=round(sum(r.credit for r in gl_rows), 2),
        gl_total_debit=round(sum(r.debit for r in gl_rows), 2),
        matched_count=len(matched_rows),
        gl_debit_only_count=len(gl_debit_only),
        gl_credit_only_count=len(gl_credit_only),
        stmt_withdrawal_only_count=len(stmt_wd_only),
        stmt_deposit_only_count=len(stmt_dep_only),
        gl_debit_only_amount=gl_debit_only_amt,
        gl_credit_only_amount=gl_credit_only_amt,
        stmt_withdrawal_only_amount=stmt_wd_only_amt,
        stmt_deposit_only_amount=stmt_dep_only_amt,
        opening_diff=opening_diff,
        formula_stmt_closing=formula_closing,
        formula_diff=formula_diff,
    )

    return recon_rows, summary
