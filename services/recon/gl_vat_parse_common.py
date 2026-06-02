# -*- coding: utf-8 -*-
"""GL 解析共享叶子 helper + 列名常量（gl_vat_reconciler 拆分）。"""

import re
from typing import List, Dict, Optional

from field_comparator import normalize_invoice_no

# ── 列名关键词（中英泰混合，匹配宽容） ─────────────────────────────
_GL_DATE_H = {"วันที่", "date", "วัน", "日期"}
_GL_DOC_H = {"ใบสำคัญ", "เลขที่เอกสาร", "doc no", "voucher", "reference", "เอกสาร", "凭证", "单据"}
_GL_DESC_H = {"คำอธิบาย", "รายการ", "description", "detail", "รายละเอียด", "摘要", "说明"}
_GL_DEBIT_H = {"เดบิต", "debit", "dr", "借方", "借"}
_GL_CRED_H = {"เครดิต", "credit", "cr", "贷方", "贷"}
_GL_ACCT_H = {"รหัสบัญชี", "account code", "gl account", "เลขที่บัญชี", "รหัส", "账号", "科目"}

# 科目代码模式：4-7 位整数 + 可选(- + 2-3位)，例如 4110、4110-01、41100-001、411000(WNF/Mr.ERP 6 位)
# v118.32.5.1 · 严格化：不允许小数点分隔（避免误把 "419.57" 金额当成科目）
# v118.32.5.5 · 放宽到 4-7 位（兼容 WNF/Mr.ERP/Express 6 位科目 411000 / 412000）
_ACCT_RE = re.compile(r"(?<![\d.])([4-9]\d{3,6}(?:[\-–]\d{2,3})?)(?![\d.])")

# 汇总/小计行关键词（跳过）· "รวม" 太宽不收，避免误杀客户名带"รวม"
_SKIP_ROWS = {
    "ยอดยกมา",
    "ยอดยกไป",
    "ยอดรวมยกมา",
    "ยอดรวมยกไป",
    "balance forward",
    "carried forward",
    "brought forward",
    "subtotal",
    "opening balance",
    "closing balance",
    "รวมประจำเดือน",
    "รวมแต่ละหน้า",
    "รวมทั้งสิ้น",
}


# ─────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────
def _to_float(val) -> float:
    """字符串/数字 → float，失败返回 0.0；支持千分位/括号负数/泰文数字"""
    if val is None:
        return 0.0
    s = str(val).strip().replace(",", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "–"}:
        return 0.0
    # 括号表示负数 (e.g. (1,000.00) = -1000)
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        v = round(float(s), 2)
        return -v if neg else v
    except Exception:
        return 0.0


def _is_revenue_acct(code: str, prefix: str = "4") -> bool:
    """判断科目代码是否为收入类（默认 4 开头）"""
    c = str(code or "").strip()
    return bool(c and c.startswith(prefix))


def _hit(header: str, hints: set) -> bool:
    h = str(header or "").strip().lower()
    return any(hint.lower() in h for hint in hints)


def _extract_account_code(text: str) -> Optional[str]:
    """从一行文本中提取科目代码"""
    m = _ACCT_RE.search(str(text or ""))
    return m.group(1) if m else None


_DEBIT_LINE_KW = frozenset({"ลดหนี้", "รับคืน", "คืนสินค้า", "ส่งคืน"})


def _is_debit_line(text: str) -> bool:
    """True if the GL line contains return/debit-note keywords (ลดหนี้/รับคืน etc.)."""
    return any(k in text for k in _DEBIT_LINE_KW)


def _is_skip_row(cells: List) -> bool:
    """是否汇总/小计/余额行（跳过）"""
    if not cells:
        return False
    joined = " ".join(str(c or "").strip().lower() for c in cells)
    return any(k in joined for k in _SKIP_ROWS) and not _ACCT_RE.search(joined)


def normalize_doc_no(s: str) -> str:
    """单据号归一化（复用现有 invoice_no 归一化器）"""
    return normalize_invoice_no(s)


# ─────────────────────────────────────────────────────────────────────
# 列映射
# ─────────────────────────────────────────────────────────────────────
def _map_gl_columns(header_row: List) -> Dict[str, int]:
    """表头行 → {field_name: col_idx}"""
    col_map: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = str(cell or "").strip().lower()
        if not h:
            continue
        if "date" not in col_map and _hit(h, _GL_DATE_H):
            col_map["date"] = i
        elif "doc_no" not in col_map and _hit(h, _GL_DOC_H):
            col_map["doc_no"] = i
        elif "description" not in col_map and _hit(h, _GL_DESC_H):
            col_map["description"] = i
        elif "debit" not in col_map and _hit(h, _GL_DEBIT_H):
            col_map["debit"] = i
        elif "credit" not in col_map and _hit(h, _GL_CRED_H):
            col_map["credit"] = i
        elif "account" not in col_map and _hit(h, _GL_ACCT_H):
            col_map["account"] = i
    return col_map


def _row_has_amount(cells: List, col_map: Dict[str, int]) -> bool:
    d = (
        _to_float(cells[col_map["debit"]])
        if "debit" in col_map and col_map["debit"] < len(cells)
        else 0.0
    )
    c = (
        _to_float(cells[col_map["credit"]])
        if "credit" in col_map and col_map["credit"] < len(cells)
        else 0.0
    )
    return d != 0.0 or c != 0.0
