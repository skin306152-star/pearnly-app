# -*- coding: utf-8 -*-
"""report_engine · 数值/日期/税号/分支/来源格式化 + 行归一化 leaf。"""

import re
from typing import Any, Dict

from i18n_reports import i18n_get


def _to_float(v) -> float:
    """安全转 float"""
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("฿", "").replace(" ", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _format_tax_id(tax_id: str) -> str:
    """泰国税号 13 位 · 自动按 1-4-5-2-1 分组"""
    if not tax_id:
        return ""
    digits = re.sub(r"\D", "", str(tax_id))
    if len(digits) == 13:
        return f"{digits[0]}-{digits[1:5]}-{digits[5:10]}-{digits[10:12]}-{digits[12]}"
    return str(tax_id)


def _format_branch(branch: str, lang: str) -> str:
    """分公司:空 → 总公司;'00000' → 总公司"""
    if not branch or str(branch).strip() in ("", "0", "00000", "head", "head_office"):
        return i18n_get(lang, "info-head-office")
    s = str(branch).strip()
    # 已经是泰文 'สำนักงานใหญ่' / 'สาขา' 直接返回
    if "สำนักงาน" in s or "สาขา" in s:
        return s
    # 数字分公司编号
    if s.isdigit():
        return f"{i18n_get(lang, 'info-branch-office')} {int(s):05d}"
    return s


def _format_branch_code(branch: str) -> str:
    """ERP 用:输出 5 位代码"""
    if not branch or str(branch).strip() in ("", "head", "head_office"):
        return "00000"
    s = str(branch).strip()
    if "สำนักงานใหญ่" in s:
        return "00000"
    digits = re.sub(r"\D", "", s)
    if digits:
        return f"{int(digits):05d}"
    return "00000"


def _format_date(v, iso: bool = False) -> str:
    """日期归一化"""
    if not v:
        return ""
    s = str(v).strip()
    # 已 ISO
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        if iso:
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        return f"{int(d):02d}/{int(mo):02d}/{y}"
    # 兜底原样返回
    return s


def _source_label(src: str, lang: str) -> str:
    """来源标记 i18n"""
    if not src:
        return ""
    src_l = str(src).lower()
    mapping = {
        "email": "source-email",
        "imap": "source-email",
        "folder": "source-folder",
        "watch": "source-folder",
        "scan": "source-scan",
        "scanner": "source-scan",
        "upload": "source-upload",
        "manual": "source-manual",
        "api": "source-api",
        "line": "source-line",
    }
    key = mapping.get(src_l, None)
    return i18n_get(lang, key) if key else str(src)


def _normalize_row(rec: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """
    把任意来源的发票数据 → 统一字段
    支持来源:
      - ocr_history 表行(seller_name / invoice_no / total_amount 等)
      - 前端 records(merged_fields 嵌套)
      - clients/{id}/export 后端拼装
    """
    # 双层尝试:rec 直接拿 + merged_fields / pages 兜底
    mf = rec.get("merged_fields") or {}
    # pages 第一页
    pages = rec.get("pages") or []
    p0 = pages[0] if isinstance(pages, list) and pages else {}
    if isinstance(p0, dict):
        pf = p0.get("fields") or p0
    else:
        pf = {}

    def pick(*keys):
        for k in keys:
            for source in (rec, mf, pf):
                if not isinstance(source, dict):
                    continue
                v = source.get(k)
                if v not in (None, "", []):
                    return v
        return ""

    subtotal = _to_float(pick("amount_before_vat", "subtotal", "amount_before_tax"))
    vat = _to_float(pick("vat_amount", "vat", "tax_amount"))
    total = _to_float(pick("total_amount", "total", "grand_total"))

    # VAT 逆算兜底:有 total 没 subtotal/vat → 按 7% 还原
    if total > 0 and subtotal == 0 and vat == 0:
        subtotal = round(total * 100 / 107, 2)
        vat = round(total - subtotal, 2)

    return {
        "no": idx,
        "filename": pick("filename", "archive_name", "file_name") or "",
        "invoice_no": pick("invoice_no", "invoice_number", "doc_no") or "",
        "invoice_date": pick("invoice_date", "date") or "",
        "seller_name": pick("seller_name", "vendor_name") or "",
        "seller_tax_id": pick("seller_tax_id", "seller_tax", "vendor_tax_id") or "",
        "seller_branch": pick("seller_branch", "branch") or "",
        "seller_addr": pick("seller_addr", "seller_address") or "",
        "buyer_name": pick("buyer_name") or "",
        "buyer_tax_id": pick("buyer_tax_id", "buyer_tax") or "",
        "buyer_addr": pick("buyer_addr", "buyer_address") or "",
        "amount_before_vat": subtotal,
        "vat_amount": vat,
        "total_amount": total,
        "wht_rate": pick("wht_rate") or "",
        "wht_amount": _to_float(pick("wht_amount")),
        "category": pick("category", "category_tag") or "",
        "source": pick("source") or "",
        "notes": pick("notes", "remark") or "",
        "items": pick("items") or [],
    }


def _render_cell_value(value: Any, col_type: str, lang: str, no_thousand: bool = False) -> Any:
    """根据列类型加工单元格值"""
    if col_type == "int":
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    if col_type in ("money", "money_raw"):
        return _to_float(value)
    if col_type == "tax_id":
        return _format_tax_id(value) if value else ""
    if col_type == "branch":
        return _format_branch(value, lang)
    if col_type == "branch_code":
        return _format_branch_code(value)
    if col_type == "date":
        return _format_date(value, iso=False)
    if col_type == "date_iso":
        return _format_date(value, iso=True)
    if col_type == "source":
        return _source_label(value, lang)
    if col_type == "blank":
        return ""
    return value if value not in (None,) else ""
