# -*- coding: utf-8 -*-
"""税表汇总引擎(docs/tax-filing/02 ★核心):从做账账本/进项算出每张表,不重算业务。

PP30:销项税/进项税取 journal(口径与 books.vat_report / closing.vat_totals 一致:
只数 posted/auto_posted、剔除 vat_closing 自身、红冲反向行记负)。进项侧逐行回溯
purchase_docs 做【有效可抵】过滤:开票超 6 个月剔除、供应商缺税号不计,手工凭证
(无源单)视为人工确认照计。税务口径 net 可能 ≠ 账面 R9 结转(账面不剔除),
breakdown 两个数都给,差异可追溯。

PND53/PND3:取本期 posted 进项单 wht_amount>0,按收款人类型分表。泰国税号首位
0=法人(DBD 注册号)、1-8=自然人身份证号,据此分流;缺税号默认进 PND53 并标
missing_tax_id(硬异常,体检拦提交)。金额全 Decimal,基数/代扣额反解进项单已算好的数。
"""

from __future__ import annotations

from decimal import Decimal

from services.accounting import store as acct_store
from services.accounting.closing import validate_period

ZERO = Decimal("0")

PP30 = "pp30"
PND53 = "pnd53"
PND3 = "pnd3"
KINDS = (PP30, PND53, PND3)

# 泰国进项税:开票月起 6 个月内可抵,逾期失效(02 有效可抵过滤)
INPUT_VAT_CLAIM_MONTHS = 6


def _dec(v) -> Decimal:
    return Decimal(str(v if v is not None else 0))


def _months_apart(period: str, doc_date) -> int:
    return (int(period[:4]) - doc_date.year) * 12 + (int(period[5:7]) - doc_date.month)


def classify_payee(tax_id) -> tuple[str, bool]:
    """税号 → (payee_type, missing)。0 开头=法人→PND53,其余=个人→PND3;缺=默认法人+标缺。"""
    t = (tax_id or "").strip()
    if not t:
        return "juristic", True
    return ("juristic" if t.startswith("0") else "individual"), False


def _vat_side_total(cur, *, tenant_id, workspace_client_id, period, account_id, positive_side):
    """单科目本期净额+行数(贷/借为正向,反向行记负)。剔除 vat_closing 防自我抵消。"""
    if account_id is None:
        return ZERO, 0
    cur.execute(
        "SELECT COALESCE(SUM(CASE WHEN l.dr_cr = %s THEN l.amount ELSE -l.amount END), 0) "
        "  AS total, COUNT(*) AS n "
        "FROM journal_lines l "
        "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s AND v.period = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.source_type != 'vat_closing' "
        "AND l.account_id = %s",
        (positive_side, tenant_id, workspace_client_id, period, account_id),
    )
    row = cur.fetchone()
    return _dec(row["total"]), int(row["n"])


def _input_exclusions(cur, *, tenant_id, workspace_client_id, period, account_id):
    """进项税逐行回溯源进项单 → (超期剔除额, 缺税号不计额)。

    只有 source_type='purchase' 的行能回溯到票(doc_date/供应商税号);手工凭证无源单,
    视为人工确认的可抵进项,不剔。超期优先于缺税号(一行只剔一次)。
    """
    expired = no_taxid = ZERO
    if account_id is None:
        return expired, no_taxid
    cur.execute(
        "SELECT l.dr_cr, l.amount, p.doc_date, s.tax_id AS supplier_tax_id "
        "FROM journal_lines l "
        "JOIN journal_vouchers v ON v.id = l.voucher_id AND v.tenant_id = l.tenant_id "
        "JOIN purchase_docs p ON p.id = v.source_id AND p.tenant_id = v.tenant_id "
        "LEFT JOIN suppliers s ON s.id = p.supplier_id AND s.tenant_id = p.tenant_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s AND v.period = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.source_type = 'purchase' "
        "AND l.account_id = %s",
        (tenant_id, workspace_client_id, period, account_id),
    )
    for r in cur.fetchall():
        amount = _dec(r["amount"])
        if r["dr_cr"] == "credit":
            amount = -amount
        if r["doc_date"] and _months_apart(period, r["doc_date"]) > INPUT_VAT_CLAIM_MONTHS:
            expired += amount
        elif not (r["supplier_tax_id"] or "").strip():
            no_taxid += amount
    return expired, no_taxid


def pp30(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """PP30 汇总:output − input(仅有效可抵)= net(正应交/负留抵)。"""
    period = validate_period(period)
    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    out_total, out_count = _vat_side_total(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        account_id=mappings.get("output_vat"),
        positive_side="credit",
    )
    in_gross, in_count = _vat_side_total(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        account_id=mappings.get("input_vat"),
        positive_side="debit",
    )
    expired, no_taxid = _input_exclusions(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        account_id=mappings.get("input_vat"),
    )
    claimable = in_gross - expired - no_taxid
    net = out_total - claimable
    return {
        "kind": PP30,
        "period": period,
        "net": net,
        "breakdown": {
            "output_vat": out_total,
            "output_count": out_count,
            "input_vat_gross": in_gross,
            "input_count": in_count,
            "input_vat_excluded_expired": expired,
            "input_vat_excluded_missing_tax_id": no_taxid,
            "input_vat_claimable": claimable,
            "net": net,
            "carry_forward": -net if net < ZERO else ZERO,
        },
    }


def pnd(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """PND 明细:本期 posted 进项单 wht_amount>0 逐张成行,按收款人类型分 PND53/PND3。

    base = 该单计提了 WHT 的行(wht_rate>0)合计;rate 取其最大档(同单多档少见,
    wht_amount 本身是权威数,rate 仅展示)。扣缴凭证 URL 取进项已登记的生成附件。
    """
    period = validate_period(period)
    cur.execute(
        "SELECT d.id, d.doc_no, d.doc_date, d.wht_amount, "
        "s.name AS payee_name, s.tax_id AS payee_tax_id, "
        "COALESCE(SUM(pl.line_total) FILTER (WHERE pl.wht_rate > 0), 0) AS wht_base, "
        "MAX(pl.wht_rate) FILTER (WHERE pl.wht_rate > 0) AS wht_rate, "
        "(SELECT a.url FROM purchase_attachments a "
        " WHERE a.tenant_id = d.tenant_id AND a.purchase_doc_id = d.id "
        " AND a.kind = 'wht_cert' AND a.generated LIMIT 1) AS cert_url "
        "FROM purchase_docs d "
        "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id "
        "LEFT JOIN purchase_lines pl "
        "  ON pl.purchase_doc_id = d.id AND pl.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.status = 'posted' "
        "AND d.wht_amount > 0 AND to_char(d.doc_date, 'YYYY-MM') = %s "
        "GROUP BY d.id, d.doc_no, d.doc_date, d.wht_amount, s.name, s.tax_id "
        "ORDER BY d.doc_date, d.doc_no",
        (tenant_id, workspace_client_id, period),
    )
    tables = {
        PND53: {"lines": [], "total": ZERO, "missing_tax_id": 0},
        PND3: {"lines": [], "total": ZERO, "missing_tax_id": 0},
    }
    for r in cur.fetchall():
        payee_type, missing = classify_payee(r["payee_tax_id"])
        kind = PND53 if payee_type == "juristic" else PND3
        wht = _dec(r["wht_amount"])
        table = tables[kind]
        table["lines"].append(
            {
                "payee_name": r["payee_name"],
                "payee_tax_id": (r["payee_tax_id"] or "").strip() or None,
                "payee_type": payee_type,
                "income_type": "service",
                "base_amount": _dec(r["wht_base"]),
                "wht_rate": _dec(r["wht_rate"]) if r["wht_rate"] is not None else None,
                "wht_amount": wht,
                "source_purchase_id": str(r["id"]),
                "cert_url": r["cert_url"],
                "cert_status": "missing_tax_id" if missing else "generated",
            }
        )
        table["total"] += wht
        if missing:
            table["missing_tax_id"] += 1
    return {"period": period, "tables": tables}
