# -*- coding: utf-8 -*-
"""
v118.32.4.9 · Pearnly · 逐字段对照模式 · 两轮强配对
输入:invoice_rows + report_rows
输出:pairs / invoice_orphans / report_orphans / stats

设计哲学(Zihao 2026-05-12 拍板):
- Pearnly = 核对表生成器 · 不是匹配判定器
- 配对只用"用户一眼能看出是同一笔"的强键 · 不做模糊匹配
- 弱关联留给用户在 orphan 区自己对照
"""

import logging
from typing import List, Dict, Any

from services.recon.field_comparator import (
    normalize_invoice_no,
    normalize_tax_id,
    parse_date,
)

logger = logging.getLogger(__name__)


def _get_total(row: Dict, is_report: bool = False) -> float:
    """v118.32.3 · 金额字段对齐
    报告侧 report_amount 是「前税金额」(มูลค่าสินค้าหรือบริการ)
    所以发票侧也用 amount_pre_vat 对比 · total_amount(含税)只作 fallback
    """
    if is_report:
        # 报告侧:报告本身就是前税金额
        v = row.get("report_amount") or row.get("amount_pre_vat") or 0
    else:
        # 发票侧:优先用前税金额对齐 · 都没有再退含税
        v = row.get("amount_pre_vat") or row.get("total_amount") or 0
    try:
        return round(float(str(v).replace(",", "")), 2)
    except Exception:
        return 0.0


def run_matching(
    invoice_rows: List[Dict],
    report_rows: List[Dict],
) -> Dict[str, Any]:
    """
    三轮配对
    invoice_rows: 每行含 id / invoice_no / invoice_date / buyer_tax_id /
                         buyer_name / total_amount / amount_pre_vat / vat_amount
    report_rows:  每行含 row_no / report_invoice_no / report_date /
                         report_buyer_tax_id / report_buyer_name /
                         report_amount / report_amount_pre_vat / report_vat_amount
    """
    pairs: List[Dict] = []
    unmatched_inv = list(range(len(invoice_rows)))
    unmatched_rep = set(range(len(report_rows)))

    # ── 第一轮:标准化发票号完全一致 → confidence 1.0
    rep_no_idx: Dict[str, List[int]] = {}
    for ri in unmatched_rep:
        key = normalize_invoice_no(
            report_rows[ri].get("report_invoice_no") or report_rows[ri].get("invoice_no") or ""
        )
        if key:
            rep_no_idx.setdefault(key, []).append(ri)

    still_unmatched_inv = []
    for ii in unmatched_inv:
        inv = invoice_rows[ii]
        key = normalize_invoice_no(inv.get("invoice_no") or "")
        if key and rep_no_idx.get(key):
            ri = rep_no_idx[key].pop(0)
            pairs.append(_make_pair(ii, ri, invoice_rows, report_rows, 1.0, 1))
            unmatched_rep.discard(ri)
        else:
            still_unmatched_inv.append(ii)
    unmatched_inv = still_unmatched_inv

    # ── 第二轮:date + buyer_tax_id + total → confidence 0.95
    still_unmatched_inv2 = []
    used_rep2: set = set()
    for ii in unmatched_inv:
        inv = invoice_rows[ii]
        d1 = parse_date(inv.get("invoice_date"))
        t1 = normalize_tax_id(str(inv.get("buyer_tax_id") or ""))
        a1 = _get_total(inv, is_report=False)
        found = None
        for ri in unmatched_rep:
            if ri in used_rep2:
                continue
            rep = report_rows[ri]
            d2 = parse_date(rep.get("report_date"))
            t2 = normalize_tax_id(str(rep.get("report_buyer_tax_id") or ""))
            a2 = _get_total(rep, is_report=True)
            if d1 and d2 and d1 == d2 and t1 and t1 == t2 and abs(a1 - a2) <= 0.01:
                found = ri
                break
        if found is not None:
            used_rep2.add(found)
            pairs.append(_make_pair(ii, found, invoice_rows, report_rows, 0.95, 2))
            unmatched_rep.discard(found)
        else:
            still_unmatched_inv2.append(ii)
    unmatched_inv = still_unmatched_inv2

    # v118.32.4.9 · 第三轮 fuzzy 名称 + date±1 已永久砍 · 替用户做决定违反新铁律
    # 剩余 unmatched 全部归入 orphan · 由用户在前端 orphan 区自己对照判定

    return {
        "pairs": pairs,
        "invoice_orphans": [invoice_rows[i].get("id") for i in unmatched_inv],
        "report_orphans": [report_rows[i].get("row_no") for i in unmatched_rep],
        "stats": {
            "total_invoices": len(invoice_rows),
            "total_report_rows": len(report_rows),
            "matched": len(pairs),
            "invoice_orphan_count": len(unmatched_inv),
            "report_orphan_count": len(unmatched_rep),
            "pass1_count": sum(1 for p in pairs if p["pass"] == 1),
            "pass2_count": sum(1 for p in pairs if p["pass"] == 2),
            "pass3_count": 0,
        },
    }


def _make_pair(
    ii: int,
    ri: int,
    invoice_rows: List[Dict],
    report_rows: List[Dict],
    confidence: float,
    pass_no: int,
) -> Dict:
    return {
        "invoice_idx": ii,
        "report_idx": ri,
        "invoice_id": invoice_rows[ii].get("id"),
        "report_row_no": report_rows[ri].get("row_no"),
        "pair_confidence": confidence,
        "pass": pass_no,
    }
