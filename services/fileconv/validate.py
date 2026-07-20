# -*- coding: utf-8 -*-
"""守恒校验。不平的行进 issues,带行号 + 期望 + 实际,绝不静默。

· 台账/流水:逐行余额链
    - 借贷三栏:上行余额 + 本行借 − 本行贷 = 本行余额
    - 单金额两栏:|本行余额 − 上行余额| = 本行金额
· 税报表/通用表:明细金额列之和 = 合计行
"""

from decimal import Decimal
from typing import Dict, List

from services.fileconv.model import (
    Issue,
    LedgerRow,
    ISSUE_GL_BALANCE_CHAIN,
    ISSUE_RUNNING_BALANCE,
    ISSUE_FOOTER_TOTAL,
)
from services.fileconv.tables import TabularLine, reconcile_totals

_TOL = Decimal("0.01")


def validate_ledger(rows: List[LedgerRow], opening: Dict[str, Decimal]) -> List[Issue]:
    """逐科目跑余额链。返回不平行的 issues。"""
    issues: List[Issue] = []
    prev: Dict[str, Decimal] = {}
    for row in rows:
        acct = row.account
        base = prev.get(acct)
        if base is None:
            base = opening.get(acct, Decimal("0"))

        if row.debit is not None or row.credit is not None:
            debit = row.debit or Decimal("0")
            credit = row.credit or Decimal("0")
            expected = base + debit - credit
            if abs(expected - row.balance) > _TOL:
                issues.append(
                    Issue(
                        kind=ISSUE_GL_BALANCE_CHAIN,
                        line_no=row.line_no,
                        account=acct,
                        message=f"{row.date} {row.doc_no}: 上行余额 {base} + 借 {debit} − 贷 {credit} ≠ 本行余额",
                        expected=f"{expected}",
                        actual=f"{row.balance}",
                    )
                )
        elif row.amount is not None:
            moved = abs(row.balance - base)
            if abs(moved - abs(row.amount)) > _TOL:
                issues.append(
                    Issue(
                        kind=ISSUE_RUNNING_BALANCE,
                        line_no=row.line_no,
                        account=acct,
                        message=f"{row.date} {row.doc_no}: 余额变动 {moved} ≠ 本行金额",
                        expected=f"{abs(row.amount)}",
                        actual=f"{moved}",
                    )
                )

        prev[acct] = row.balance
    return issues


def ledger_stats(rows: List[LedgerRow], opening: Dict[str, Decimal]) -> Dict:
    sum_debit = sum((r.debit or Decimal("0")) for r in rows)
    sum_credit = sum((r.credit or Decimal("0")) for r in rows)
    accounts = sorted({r.account for r in rows})
    stats = {
        "row_count": len(rows),
        "accounts": accounts,
        "sum_debit": f"{sum_debit}",
        "sum_credit": f"{sum_credit}",
    }
    if rows:
        first_acct = rows[0].account
        stats["opening_balance"] = f"{opening.get(first_acct, Decimal('0'))}"
        stats["closing_balance"] = f"{rows[-1].balance}"
    return stats


def validate_tabular(lines: List[TabularLine]) -> List[Issue]:
    """明细合计闭合校验。"""
    issues: List[Issue] = []
    for line_no, column, expected, actual in reconcile_totals(lines):
        issues.append(
            Issue(
                kind=ISSUE_FOOTER_TOTAL,
                line_no=line_no,
                message=f"合计行{column} 金额列:明细之和 ≠ 合计",
                expected=f"{expected}",
                actual=f"{actual}",
            )
        )
    return issues


def tabular_stats(lines: List[TabularLine]) -> Dict:
    total_lines = [ln for ln in lines if ln.is_total]
    return {
        "row_count": len(lines),
        "data_rows": len([ln for ln in lines if not ln.is_total]),
        "total_rows": len(total_lines),
        "total_found": bool(total_lines),
    }
