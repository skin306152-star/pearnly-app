# -*- coding: utf-8 -*-
"""银行流水匹配候选检索(docs/accounting/bank-recon-mj/04 §3 candidates)。

评分复用 services/recon/bank_recon_scoring(纯函数 import,零重写);候选源换成做账域:
  ① 已过账触及银行科目的凭证(关联型)  ② 未收款销项单(IN)  ③ 未付款进项单(OUT)
  ⑤ review_learned 命中(desc 指纹 → 新建建议)
POS 按日聚合(④)留作后续:POS 成交已自动生成 R5 凭证(借 bank),再按日聚合建新凭证
会与 R5 重复计账,去重需另设计 → 不在本层臆造,避免双计。
每句 WHERE tenant_id + workspace_client_id 双隔离;候选窗口 90 天 + LIMIT 防全表扫。
"""

from __future__ import annotations

import hashlib
from datetime import timedelta

from services.recon.bank_recon_scoring import match_one_tx

_WINDOW_DAYS = 90
_PER_SOURCE_LIMIT = 50


def bank_scope_key(description) -> str:
    """学习记忆查找键:描述指纹(扩 bank_line 的 scope_key,机制照 purchase desc_hash)。"""
    norm = (description or "").strip().lower()
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
    return f"bank_desc:{h}"


def _iso(d) -> str:
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


def candidates_for_line(cur, *, tenant_id: str, workspace_client_id: int, line: dict) -> list:
    """汇集多源候选 → 统一打分(bank_recon_scoring)→ 返回带 kind/action 的建议(降序)。"""
    direction = line["direction"]  # 'in' / 'out'
    line_date = line["line_date"]
    lo = line_date - timedelta(days=_WINDOW_DAYS)
    hi = line_date + timedelta(days=_WINDOW_DAYS)

    pool: list = []
    meta: dict = {}
    for fetch in (_src_vouchers, _src_sales, _src_purchases):
        fetch(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            line=line,
            lo=lo,
            hi=hi,
            pool=pool,
            meta=meta,
        )

    bank_tx = {
        "amount": float(line["amount"]),
        "tx_date": _iso(line_date),
        "direction": "IN" if direction == "in" else "OUT",
        "description": line.get("description") or "",
    }
    scored = match_one_tx(bank_tx, pool)
    out = []
    for s in scored:
        info = meta.get(s["history_id"])
        if not info:
            continue
        out.append({**info, "score": s["score"], "reason": s["reason"]})

    learned = _src_learned(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line=line
    )
    if learned:
        out.insert(0, learned)
    return out


def _src_vouchers(cur, *, tenant_id, workspace_client_id, line, lo, hi, pool, meta):
    """① 已过账触及银行科目、尚未被任一流水关联的凭证(关联型匹配)。

    IN 流水 ↔ 凭证里银行科目借方(收钱);OUT 流水 ↔ 银行科目贷方(付钱)。
    """
    bank_side = "debit" if line["direction"] == "in" else "credit"
    cur.execute(
        "SELECT v.id, v.voucher_no, v.voucher_date, v.description, v.source_type, "
        "l.amount AS bank_amount "
        "FROM journal_vouchers v "
        "JOIN journal_lines l ON l.voucher_id = v.id AND l.tenant_id = v.tenant_id "
        "JOIN acct_bank_accounts ba ON ba.coa_account_id = l.account_id "
        "  AND ba.tenant_id = v.tenant_id AND ba.workspace_client_id = v.workspace_client_id "
        "WHERE v.tenant_id = %s AND v.workspace_client_id = %s "
        "AND v.status IN ('posted', 'auto_posted') AND v.source_type != 'bank_line' "
        "AND l.dr_cr = %s AND v.voucher_date BETWEEN %s AND %s "
        "AND NOT EXISTS (SELECT 1 FROM acct_bank_lines bl "
        "  WHERE bl.tenant_id = v.tenant_id "
        "  AND bl.workspace_client_id = v.workspace_client_id "
        "  AND bl.matched_voucher_id = v.id) "
        "ORDER BY v.voucher_date DESC LIMIT %s",
        (tenant_id, workspace_client_id, bank_side, lo, hi, _PER_SOURCE_LIMIT),
    )
    income = line["direction"] == "in"
    for r in cur.fetchall():
        vid = str(r["id"])
        pool.append(
            {
                "id": vid,
                "amount_total": float(r["bank_amount"] or 0),
                "invoice_date": _iso(r["voucher_date"]),
                "category_tag": "sales" if income else "purchase",
                "vendor": "",
                "invoice_no": r["voucher_no"] or "",
            }
        )
        meta[vid] = {
            "kind": "voucher",
            "action": "link",
            "voucher_id": vid,
            "voucher_no": r["voucher_no"],
            "date": _iso(r["voucher_date"]),
            "amount": float(r["bank_amount"] or 0),
            "label": r["description"] or r["voucher_no"],
            "source_type": r["source_type"],
        }


def _src_sales(cur, *, tenant_id, workspace_client_id, line, lo, hi, pool, meta):
    """② 未收款销项单(仅 IN 流水:客户回款 → 冲应收)。"""
    if line["direction"] != "in":
        return
    cur.execute(
        # 仅全额未付(paid_amount=0):组合冲销整笔,撤销可干净还原(不毁既有部分付款)
        "SELECT id, doc_number, issue_date, buyer_name, grand_total, paid_amount "
        "FROM sales_documents "
        "WHERE tenant_id = %s AND seller_workspace_client_id = %s AND status = 'issued' "
        "AND payment_status = 'unpaid' AND paid_amount = 0 AND grand_total > 0 "
        "AND issue_date BETWEEN %s AND %s "
        "ORDER BY issue_date DESC LIMIT %s",
        (tenant_id, workspace_client_id, lo, hi, _PER_SOURCE_LIMIT),
    )
    for r in cur.fetchall():
        did = str(r["id"])
        outstanding = float((r["grand_total"] or 0) - (r["paid_amount"] or 0))
        pool.append(
            {
                "id": did,
                "amount_total": outstanding,
                "invoice_date": _iso(r["issue_date"]),
                "category_tag": "sales",
                "vendor": r["buyer_name"] or "",
                "invoice_no": r["doc_number"] or "",
            }
        )
        meta[did] = {
            "kind": "sale",
            "action": "combo",
            "doc_id": did,
            "doc_no": r["doc_number"],
            "date": _iso(r["issue_date"]),
            "amount": outstanding,
            "label": r["buyer_name"] or r["doc_number"],
        }


def _src_purchases(cur, *, tenant_id, workspace_client_id, line, lo, hi, pool, meta):
    """③ 未付款进项单(仅 OUT 流水:付供应商 → 冲应付)。"""
    if line["direction"] != "out":
        return
    cur.execute(
        # 仅全额未付(paid_amount=0):同销项,撤销可干净还原
        "SELECT pd.id, pd.doc_no, pd.doc_date, pd.net_payable, pd.paid_amount, "
        "COALESCE(s.name, '') AS vendor "
        "FROM purchase_docs pd "
        "LEFT JOIN suppliers s ON s.id = pd.supplier_id AND s.tenant_id = pd.tenant_id "
        "WHERE pd.tenant_id = %s AND pd.workspace_client_id = %s AND pd.status = 'posted' "
        "AND pd.payment_status = 'unpaid' AND pd.paid_amount = 0 AND pd.net_payable > 0 "
        "AND pd.doc_date BETWEEN %s AND %s "
        "ORDER BY pd.doc_date DESC LIMIT %s",
        (tenant_id, workspace_client_id, lo, hi, _PER_SOURCE_LIMIT),
    )
    for r in cur.fetchall():
        did = str(r["id"])
        outstanding = float((r["net_payable"] or 0) - (r["paid_amount"] or 0))
        pool.append(
            {
                "id": did,
                "amount_total": outstanding,
                "invoice_date": _iso(r["doc_date"]),
                "category_tag": "purchase",
                "vendor": r["vendor"],
                "invoice_no": r["doc_no"] or "",
            }
        )
        meta[did] = {
            "kind": "purchase",
            "action": "combo",
            "doc_id": did,
            "doc_no": r["doc_no"],
            "date": _iso(r["doc_date"]),
            "amount": outstanding,
            "label": r["vendor"] or r["doc_no"],
        }


def _src_learned(cur, *, tenant_id, workspace_client_id, line):
    """⑤ review_learned 命中(同描述定过的分类)→ 新建建议(置顶高置信)。"""
    from services.accounting import review

    scope_key = bank_scope_key(line.get("description"))
    decision = review.find_learned(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        scope_keys=[scope_key],
    )
    if not decision or not decision.get("account_id"):
        return None
    return {
        "kind": "learned",
        "action": "new_tx",
        "account_id": str(decision["account_id"]),
        "tx_kind": decision.get("tx_kind")
        or ("income" if line["direction"] == "in" else "expense"),
        "amount": float(line["amount"]),
        "label": decision.get("label") or "已学规则",
        "score": 100.0,
        "reason": "已学规则",
    }
