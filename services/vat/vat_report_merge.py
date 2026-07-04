# -*- coding: utf-8 -*-
"""VAT 报告多份拼接(校验同卖方同期间)· vat_excel_export 拆分。"""

import os
import logging
from typing import List, Dict, Any, Optional

from services.vat.vat_report_parser import parse_vat_report
from services.recon.vat_recon_core import _dominant_report_period
from services.vat.vat_ocr_extract import _ocr_with_hard_timeout

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# VAT 报告多份拼接 · 校验同卖方同期间
# ════════════════════════════════════════════════════════════════════════
def merge_vat_reports(
    report_files: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    *,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """多份 VAT 报告 PDF 串行解析 · 拼接 rows · 校验同卖方同期间
    report_files: [{filename, bytes}]
    返回:{ok, rows, seller_name, seller_tax_id, period_year, period_month,
           sources(各文件解析摘要), error}
    """
    if not report_files:
        return {"ok": False, "error": "未上传 VAT 报告", "rows": []}

    parsed_list: List[Dict] = []
    sources: List[Dict] = []
    _rep_in_tok = 0
    _rep_out_tok = 0
    policy_kwargs: Dict[str, Any] = {}
    if plan_code:
        policy_kwargs["plan_code"] = plan_code
    if is_exempt:
        policy_kwargs["is_exempt"] = True
    if user_type:
        policy_kwargs["user_type"] = user_type
    for f in report_files:
        # P0-2:报告 OCR 加线程层硬超时 · 偶发挂起的 Gemini 调用不再让 job 无限 running
        _fb, _fn = f["bytes"], f["filename"]
        r = _ocr_with_hard_timeout(
            lambda fb=_fb, fn=_fn: parse_vat_report(
                fb,
                fn,
                api_key=api_key,
                **policy_kwargs,
            ),
            timeout_sec=int(os.environ.get("VEX_REPORT_OCR_TIMEOUT_SEC", "120")),
            on_timeout=lambda: {
                "ok": False,
                "rows": [],
                "error": "OCR 超时",
                "error_code": "ocr_timeout",
            },
        )
        if not r.get("ok"):
            return {
                "ok": False,
                "rows": [],
                "error": f"「{f['filename']}」解析失败: {r.get('error', '未知')}",
            }
        parsed_list.append(r)
        _rep_in_tok += int(r.get("_input_tokens") or 0)
        _rep_out_tok += int(r.get("_output_tokens") or 0)
        sources.append(
            {
                "filename": f["filename"],
                "row_count": r.get("row_count", len(r.get("rows", []))),
                "method": r.get("method", ""),
            }
        )

    # 校验:多份必须同卖方 + 同期间(从第 1 份起对照)
    # P1-2 修(2026-05-25 销项税回归):此前 period 只在 meta 有时才比 · 但 pdf_text_regex /
    #   pipeline 路径 meta={} → 永远拿不到 period → 混月份不拦(TC04 两月报告被合并成 6 行继续对账)。
    #   改:每份报告用 _dominant_report_period(meta 优先 · 否则行日期众数)· 跨文件比对期间。
    metas = [p.get("meta", {}) for p in parsed_list]
    sellers = set()
    for m in metas:
        sid = m.get("seller_tax_id") or m.get("issuer_tax_id") or ""
        if sid:
            sellers.add(sid)
    periods = set()
    for p in parsed_list:
        dp = _dominant_report_period(p)
        if dp:
            periods.add(dp)

    if len(sellers) > 1:
        return {
            "ok": False,
            "rows": [],
            "error": f"多份报告卖方不一致(税号: {' / '.join(sorted(sellers))})· 请检查",
        }
    if len(periods) > 1:
        _ps = " / ".join(f"{y}-{mn:02d}" for (y, mn) in sorted(periods))
        return {"ok": False, "rows": [], "error": f"多份报告期间不一致({_ps})· 请检查"}

    # 合并 rows · 重排 row_no 连续递增
    # v118.35.0.27 · 多页 PDF 溯源:每行加 source_filename + source_page
    # 让对账差异行能定位回原 PDF 第几页
    all_rows: List[Dict] = []
    seq = 0
    for p, src in zip(parsed_list, report_files):
        src_filename = src.get("filename", "")
        for row in p.get("rows", []):
            seq += 1
            row = dict(row)
            row["row_no"] = seq
            row["source_filename"] = src_filename
            # 保留原 row 里的 page_no(如果 parse_vat_report 返回)· 否则空
            row.setdefault("source_page", row.get("page_no") or row.get("page") or "")
            all_rows.append(row)

    seller_tax_id = next(iter(sellers)) if sellers else ""
    seller_name = ""
    for m in metas:
        if m.get("seller_name"):
            seller_name = m["seller_name"]
            break
    period_year = next(iter(periods))[0] if periods else None
    period_month = next(iter(periods))[1] if periods else None

    return {
        "ok": True,
        "rows": all_rows,
        "seller_tax_id": seller_tax_id,
        "seller_name": seller_name,
        "period_year": period_year,
        "period_month": period_month,
        "sources": sources,
        "row_count": len(all_rows),
        "_input_tokens": _rep_in_tok,
        "_output_tokens": _rep_out_tok,
    }
