# -*- coding: utf-8 -*-
"""
gl_vat_reconciler.py · v1.0.0
GL(总账) vs 销项税报告 对账核心引擎

匹配规则（客户 2026-05-15 确认）：
- 主键：VAT.เลขที่เอกสารอ้างอิง（参考单号）↔ GL.ใบสำคัญ（凭证号），归一化后比对
- VAT.มูลค่าสินค้าและบริการ 正数 → 取 GL Credit
- VAT.มูลค่าสินค้าและบริการ 负数 → 取 GL Debit 并转为负数
- 末列附加 GL 的 รหัสบัญชี（收入科目代码）
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# DATA CLASSES · moved to services/recon/gl_vat_types.py
from services.recon.gl_vat_types import (  # noqa: F401,E402  re-export (recon_routes/tests) + facade-internal
    GlRow,
    ReconRow,
    GlVatSummary,
)

# EXCEL EXPORT · moved to services/recon/gl_vat_excel.py
from services.recon.gl_vat_excel import (  # noqa: F401,E402  re-export (recon_routes)
    export_gl_vat_excel,
)

# PARSE COMMON · moved to services/recon/gl_vat_parse_common.py
from services.recon.gl_vat_parse_common import (  # noqa: F401  re-export (tests) + facade-internal
    _to_float,
    _is_revenue_acct,
    _hit,
    _extract_account_code,
    _is_debit_line,
    _is_skip_row,
    normalize_doc_no,
    _map_gl_columns,
    _row_has_amount,
    _GL_DATE_H,
    _GL_DOC_H,
    _GL_DESC_H,
    _GL_DEBIT_H,
    _GL_CRED_H,
    _GL_ACCT_H,
    _ACCT_RE,
    _SKIP_ROWS,
    _DEBIT_LINE_KW,
)

# PARSE PDF · moved to services/recon/gl_vat_parse_pdf.py
from services.recon.gl_vat_parse_pdf import (  # noqa: F401  re-export + facade-internal(parse_gl dispatch)
    _parse_gl_text_lines,
    parse_gl_pdf,
)


# PARSE EXCEL/DISPATCH · moved to services/recon/gl_vat_parse_excel.py
from services.recon.gl_vat_parse_excel import (  # noqa: F401  re-export (recon_routes/tests)
    parse_gl_excel,
    parse_gl,
)
# ─────────────────────────────────────────────────────────────────────
# 对账核心
# ─────────────────────────────────────────────────────────────────────
def _vat_doc_no(vat_row: Dict[str, Any]) -> str:
    """从 VAT 行取参考单号（优先 ref_no，回退 invoice_no）"""
    # vat_report_parser 当前输出 report_invoice_no；客户确认参考单号优先
    # 若解析器额外提供 report_ref_no（参考单据号列），优先使用
    raw = (
        vat_row.get("report_ref_no")
        or vat_row.get("report_reference_no")
        or vat_row.get("report_invoice_no")
        or ""
    )
    return str(raw).strip()


def reconcile_gl_vat(
    gl_rows: List[GlRow],
    vat_rows: List[Dict[str, Any]],
    amount_tolerance: float = 0.01,
) -> Tuple[List[ReconRow], GlVatSummary]:
    """
    对账主流程
    返回（明细列表，汇总）
    v118.35.0.26 · 金额容差(默认 ฿0.01)· |diff| <= tolerance 算匹配
    """
    # GL 索引: norm_doc_no -> [GlRow]
    gl_idx: Dict[str, List[GlRow]] = defaultdict(list)
    for r in gl_rows:
        if r.norm_doc_no:
            gl_idx[r.norm_doc_no].append(r)

    # VAT 单据号集合（已规范化）
    vat_norm_set = set()
    for v in vat_rows:
        nm = normalize_doc_no(_vat_doc_no(v))
        if nm:
            vat_norm_set.add(nm)

    # 1. 明细：以 VAT 为主表
    detail: List[ReconRow] = []
    for vat in vat_rows:
        raw_no = _vat_doc_no(vat)
        norm_no = normalize_doc_no(raw_no)
        vat_amt = vat.get("report_amount_pre_vat") or 0.0
        try:
            vat_amt = float(vat_amt)
        except Exception:
            vat_amt = 0.0

        gl_matches = gl_idx.get(norm_no, [])
        if not gl_matches:
            detail.append(
                ReconRow(
                    doc_no=raw_no,
                    date=str(vat.get("report_date") or ""),
                    customer_name=str(vat.get("report_buyer_name") or ""),
                    vat_amount=round(vat_amt, 2),
                    gl_amount=None,
                    diff=None,
                    account_codes="",
                )
            )
        else:
            is_credit_note = vat_amt < 0
            if is_credit_note:
                gl_amt = round(-sum(r.debit for r in gl_matches), 2)
            else:
                gl_amt = round(sum(r.credit for r in gl_matches), 2)
            raw_diff = round(vat_amt - gl_amt, 2)
            # v118.35.0.26 · |diff| <= tolerance 视为匹配 · diff 显式 0
            effective_diff = 0.0 if abs(raw_diff) <= amount_tolerance else raw_diff
            accts = ",".join(sorted({r.account_code for r in gl_matches if r.account_code}))
            detail.append(
                ReconRow(
                    doc_no=raw_no,
                    date=str(vat.get("report_date") or ""),
                    customer_name=str(vat.get("report_buyer_name") or ""),
                    vat_amount=round(vat_amt, 2),
                    gl_amount=gl_amt,
                    diff=effective_diff,
                    account_codes=accts,
                )
            )

    # 排序：date → doc_no
    detail.sort(key=lambda r: (r.date or "", r.doc_no or ""))

    # 2. 汇总 + v118.32.5.5.11 调整项明细
    gl_only_credit = 0.0
    gl_only_debit = 0.0
    gl_only_credit_items: List[Dict[str, Any]] = []
    gl_only_debit_items: List[Dict[str, Any]] = []
    for r in gl_rows:
        if r.norm_doc_no in vat_norm_set:
            continue
        if r.credit > 0:
            gl_only_credit += r.credit
            gl_only_credit_items.append(
                {
                    "doc_no": r.doc_no,
                    "date": r.date,
                    "name": r.description,
                    "amount": round(r.credit, 2),
                }
            )
        if r.debit > 0:
            gl_only_debit += r.debit
            gl_only_debit_items.append(
                {
                    "doc_no": r.doc_no,
                    "date": r.date,
                    "name": r.description,
                    "amount": round(r.debit, 2),
                }
            )

    vat_only_pos = 0.0
    vat_only_neg = 0.0
    vat_only_positive_items: List[Dict[str, Any]] = []
    vat_only_negative_items: List[Dict[str, Any]] = []
    for v in vat_rows:
        nm = normalize_doc_no(_vat_doc_no(v))
        if nm in gl_idx:
            continue
        amt = v.get("report_amount_pre_vat") or 0.0
        try:
            amt = float(amt)
        except Exception:
            amt = 0.0
        if amt > 0:
            vat_only_pos += amt
            vat_only_positive_items.append(
                {
                    "doc_no": _vat_doc_no(v),
                    "date": str(v.get("report_date") or ""),
                    "name": str(v.get("report_buyer_name") or ""),
                    "amount": round(amt, 2),
                }
            )
        elif amt < 0:
            vat_only_neg += amt
            vat_only_negative_items.append(
                {
                    "doc_no": _vat_doc_no(v),
                    "date": str(v.get("report_date") or ""),
                    "name": str(v.get("report_buyer_name") or ""),
                    "amount": round(amt, 2),
                }
            )

    gl_total = sum(r.credit for r in gl_rows) - sum(r.debit for r in gl_rows)
    vat_total = sum(float(v.get("report_amount_pre_vat") or 0) for v in vat_rows)

    summary = GlVatSummary(
        gl_total=round(gl_total, 2),
        gl_only_credit=round(gl_only_credit, 2),
        gl_only_debit=round(gl_only_debit, 2),
        vat_only_positive=round(vat_only_pos, 2),
        vat_only_negative=round(vat_only_neg, 2),
        vat_total=round(vat_total, 2),
        gl_only_credit_items=gl_only_credit_items,
        gl_only_debit_items=gl_only_debit_items,
        vat_only_positive_items=vat_only_positive_items,
        vat_only_negative_items=vat_only_negative_items,
    )
    return detail, summary


# ─────────────────────────────────────────────────────────────────────
# 序列化（用于 DB 存储 & 前端响应）
# ─────────────────────────────────────────────────────────────────────
def detail_to_json(detail: List[ReconRow]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in detail]


def summary_to_json(summary: GlVatSummary) -> Dict[str, float]:
    return asdict(summary)


def detail_from_json(data: List[Dict[str, Any]]) -> List[ReconRow]:
    return [ReconRow(**r) for r in (data or [])]


def summary_from_json(data: Dict[str, Any]) -> GlVatSummary:
    return GlVatSummary(
        **(
            data
            or {
                "gl_total": 0,
                "gl_only_credit": 0,
                "gl_only_debit": 0,
                "vat_only_positive": 0,
                "vat_only_negative": 0,
                "vat_total": 0,
            }
        )
    )
