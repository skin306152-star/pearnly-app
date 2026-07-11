# -*- coding: utf-8 -*-
"""出账本 / 报税材料 / 财报(docs/accounting/03 §5 · 屏4 月末出口)。

全部从 journal_vouchers/lines 派生(单一事实源),只数已过账(posted/auto_posted):
  gl 总账(期初/借/贷/期末) · subsidiary 明细账(按科目逐笔) · trial_balance 试算表
  vat 进/销项税报告(PP30 附 · 剔除结转凭证自身) · wht 预扣税明细
  financials 损益表 + 资产负债表(本期累计净利挂权益方配平)
PDF 用 reportlab 表格(泰文/CJK 字体复用 usage_report 注册);打包 = 各 PDF 进 zip。
"""

from __future__ import annotations

from decimal import Decimal

from services.accounting import store as acct_store
from services.accounting.closing import validate_period

ZERO = Decimal("0")

BOOK_KINDS = ("gl", "subsidiary", "trial_balance")
TAX_KINDS = ("vat", "wht")


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def _account_period_sums(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> list:
    """逐科目:期初净额(借-贷·period 之前)+ 本期借/贷合计。试算表/总账共用。"""
    cur.execute(
        "SELECT a.id, a.code, a.name_zh, a.name_th, a.acct_type, "
        "COALESCE(SUM(l.amount) FILTER (WHERE l.dr_cr = 'debit' AND v.period = %s), 0) "
        "  AS period_debit, "
        "COALESCE(SUM(l.amount) FILTER (WHERE l.dr_cr = 'credit' AND v.period = %s), 0) "
        "  AS period_credit, "
        "COALESCE(SUM(CASE WHEN l.dr_cr = 'debit' THEN l.amount ELSE -l.amount END) "
        "  FILTER (WHERE v.period < %s), 0) AS opening_net "
        "FROM journal_lines l "
        "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
        "JOIN chart_of_accounts a ON a.id = l.account_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.period <= %s "
        "GROUP BY a.id, a.code, a.name_zh, a.name_th, a.acct_type "
        "ORDER BY a.code",
        (period, period, period, tenant_id, workspace_client_id, period),
    )
    return [dict(r) for r in cur.fetchall()]


def general_ledger_from_sums(sums: list, period: str) -> dict:
    """注入式纯变换:逐科目 account_sums(期初净额 + 本期借/贷)→ 总账(期初/借/贷/期末)。

    period 视为已校验(cur 入口先 validate_period 再注入)。法定表走 _account_period_sums 从
    journal_vouchers 取 sums;影子路径直接喂内存 sums(不碰法定表),两者共用同一变换,报表口径
    机械一致。sums 行契约 = _account_period_sums 输出(id/code/name_zh/name_th/acct_type/
    period_debit/period_credit/opening_net)。"""
    accounts, td, tc = [], ZERO, ZERO
    for r in sums:
        debit, credit = _dec(r["period_debit"]), _dec(r["period_credit"])
        opening = _dec(r["opening_net"])
        closing = opening + debit - credit
        td += debit
        tc += credit
        accounts.append(
            {
                "account_id": r["id"],
                "code": r["code"],
                "name_zh": r["name_zh"],
                "name_th": r["name_th"],
                "acct_type": r["acct_type"],
                "opening": opening,
                "debit": debit,
                "credit": credit,
                "closing": closing,
            }
        )
    return {"period": period, "accounts": accounts, "totals": {"debit": td, "credit": tc}}


def general_ledger(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    period = validate_period(period)
    sums = _account_period_sums(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    return general_ledger_from_sums(sums, period)


def trial_balance_from_sums(sums: list, period: str) -> dict:
    """试算表(注入式纯变换):期末净额正=借栏 负=贷栏,Σ借=Σ贷 即平。"""
    gl = general_ledger_from_sums(sums, period)
    rows, td, tc = [], ZERO, ZERO
    for a in gl["accounts"]:
        bal = a["closing"]
        if bal == ZERO:
            continue
        debit, credit = (bal, ZERO) if bal > ZERO else (ZERO, -bal)
        td += debit
        tc += credit
        rows.append(
            {
                "code": a["code"],
                "name_zh": a["name_zh"],
                "name_th": a["name_th"],
                "debit": debit,
                "credit": credit,
            }
        )
    return {
        "period": gl["period"],
        "rows": rows,
        "totals": {"debit": td, "credit": tc},
        "balanced": td == tc,
    }


def trial_balance(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    period = validate_period(period)
    sums = _account_period_sums(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    return trial_balance_from_sums(sums, period)


def subsidiary_ledger(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """明细账:按科目逐笔(凭证号/日期/摘要/借/贷/滚动余额)。"""
    period = validate_period(period)
    cur.execute(
        "SELECT a.id AS account_id, a.code, a.name_zh, a.name_th, a.acct_type, "
        "v.voucher_no, v.voucher_date, v.description, l.memo, l.dr_cr, l.amount "
        "FROM journal_lines l "
        "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
        "JOIN chart_of_accounts a ON a.id = l.account_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.period = %s "
        "ORDER BY a.code, v.voucher_date, v.voucher_no, l.sort",
        (tenant_id, workspace_client_id, period),
    )
    accounts: dict = {}
    for r in cur.fetchall():
        acct = accounts.setdefault(
            r["code"],
            {
                "account_id": r["account_id"],
                "code": r["code"],
                "name_zh": r["name_zh"],
                "name_th": r["name_th"],
                "acct_type": r["acct_type"],
                "lines": [],
                "debit_total": ZERO,
                "credit_total": ZERO,
            },
        )
        amount = _dec(r["amount"])
        debit = amount if r["dr_cr"] == "debit" else ZERO
        credit = amount if r["dr_cr"] == "credit" else ZERO
        acct["debit_total"] += debit
        acct["credit_total"] += credit
        acct["lines"].append(
            {
                "voucher_no": r["voucher_no"],
                "date": r["voucher_date"],
                "description": r["memo"] or r["description"],
                "debit": debit,
                "credit": credit,
            }
        )
    return {"period": period, "accounts": list(accounts.values())}


def vat_report(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """进/销项税报告(PP30 附表底稿)。剔除 vat_closing 自身防自我抵消;
    红冲(销项税借方/进项税贷方)记负数照实列。"""
    period = validate_period(period)
    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    out_id, in_id = mappings.get("output_vat"), mappings.get("input_vat")

    def _rows(account_id, positive_side):
        if account_id is None:
            # 角色未映射 ⇒ 不存在该科目分录(空套账),空报表是诚实状态
            return [], ZERO
        cur.execute(
            "SELECT v.voucher_no, v.voucher_date, v.source_type, v.source_ref, "
            "v.description, l.dr_cr, l.amount "
            "FROM journal_lines l "
            "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
            "WHERE v.tenant_id = %s AND v.workspace_client_id = %s AND v.period = %s "
            "AND v.status IN ('posted', 'auto_posted') AND v.source_type != 'vat_closing' "
            "AND l.account_id = %s "
            "ORDER BY v.voucher_date, v.voucher_no",
            (tenant_id, workspace_client_id, period, account_id),
        )
        rows, total = [], ZERO
        for r in cur.fetchall():
            amount = _dec(r["amount"])
            if r["dr_cr"] != positive_side:
                amount = -amount
            total += amount
            rows.append(
                {
                    "voucher_no": r["voucher_no"],
                    "date": r["voucher_date"],
                    "source_type": r["source_type"],
                    "ref": r["source_ref"],
                    "description": r["description"],
                    "amount": amount,
                }
            )
        return rows, total

    sales_rows, sales_total = _rows(out_id, "credit")
    purchase_rows, purchase_total = _rows(in_id, "debit")
    return {
        "period": period,
        "sales": {"rows": sales_rows, "total": sales_total},
        "purchase": {"rows": purchase_rows, "total": purchase_total},
        "vat_payable": sales_total - purchase_total,
    }


def wht_report(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """预扣税明细(PND3/53 底稿):wht_payable 贷方=本期代扣。"""
    period = validate_period(period)
    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    wht_id = mappings.get("wht_payable")
    rows, total = [], ZERO
    if wht_id:
        cur.execute(
            "SELECT v.voucher_no, v.voucher_date, v.source_ref, v.description, l.dr_cr, l.amount "
            "FROM journal_lines l "
            "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
            "WHERE v.tenant_id = %s AND v.workspace_client_id = %s AND v.period = %s "
            "AND v.status IN ('posted', 'auto_posted') AND l.account_id = %s "
            "ORDER BY v.voucher_date, v.voucher_no",
            (tenant_id, workspace_client_id, period, wht_id),
        )
        for r in cur.fetchall():
            amount = _dec(r["amount"])
            if r["dr_cr"] == "debit":
                amount = -amount
            total += amount
            rows.append(
                {
                    "voucher_no": r["voucher_no"],
                    "date": r["voucher_date"],
                    "ref": r["source_ref"],
                    "description": r["description"],
                    "amount": amount,
                }
            )
    return {"period": period, "rows": rows, "total": total}


def financials_from_sums(sums: list, period: str) -> dict:
    """损益表 + 资产负债表(注入式纯变换)。法定表与影子路径共用,配平口径机械一致。"""
    gl = general_ledger_from_sums(sums, period)
    pnl_rev, pnl_exp = [], []
    rev_total = exp_total = ZERO
    assets, liabilities, equity = [], [], []
    asset_total = liab_total = equity_total = ZERO
    earnings = ZERO
    for a in gl["accounts"]:
        period_net = a["debit"] - a["credit"]
        closing = a["closing"]
        row = {"code": a["code"], "name_zh": a["name_zh"], "name_th": a["name_th"]}
        if a["acct_type"] == "revenue":
            amount = -period_net
            rev_total += amount
            if amount != ZERO:
                pnl_rev.append({**row, "amount": amount})
        elif a["acct_type"] == "expense":
            amount = period_net
            exp_total += amount
            if amount != ZERO:
                pnl_exp.append({**row, "amount": amount})
        if a["acct_type"] == "asset" and closing != ZERO:
            assets.append({**row, "amount": closing})
            asset_total += closing
        elif a["acct_type"] == "liability" and closing != ZERO:
            liabilities.append({**row, "amount": -closing})
            liab_total += -closing
        elif a["acct_type"] == "equity" and closing != ZERO:
            equity.append({**row, "amount": -closing})
            equity_total += -closing
        if a["acct_type"] in ("revenue", "expense"):
            earnings += -closing  # 收入贷余-费用借余 = 开账以来累计净利

    equity_total += earnings
    return {
        "period": gl["period"],
        "pnl": {
            "revenue": pnl_rev,
            "expense": pnl_exp,
            "revenue_total": rev_total,
            "expense_total": exp_total,
            "net_profit": rev_total - exp_total,
        },
        "balance_sheet": {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "current_earnings": earnings,
            "asset_total": asset_total,
            "liability_total": liab_total,
            "equity_total": equity_total,
            "balanced": asset_total == liab_total + equity_total,
        },
    }


def financials(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """损益表(本期)+ 资产负债表(期末累计 · 本期累计净利挂权益方配平)。"""
    period = validate_period(period)
    sums = _account_period_sums(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    return financials_from_sums(sums, period)
