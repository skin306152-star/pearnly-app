# -*- coding: utf-8 -*-
"""VAT 报告解析 · 共享工具与列名/垃圾行常量(零依赖叶子)。"""

import re
from typing import List, Dict, Any, Optional

PARSER_VERSION = "1.1.0"

# ── 列名关键词(中英泰混合) ────────────────────────────
_DATE_H = {"วันที่", "date", "วัน/เดือน/ปี", "วันที่ใบกำกับ", "วันที่เอกสาร"}
_NO_H = {"เลขที่", "invoice no", "เลขที่ใบกำกับ", "เลขที่เอกสาร", "no."}
# v118.32.5 · GL对账·参考单据号列(优先于 invoice_no 检测，专给 GL 匹配用)
_REF_H = {"อ้างอิง", "reference", "ref no", "เอกสารอ้างอิง", "เลขอ้างอิง"}
_NAME_H = {"ชื่อ", "name", "ผู้ซื้อ", "customer"}
_TAX_H = {"เลขประจำตัว", "tax id", "เลขภาษี", "tin"}
_BRANCH_H = {"สาขา", "branch"}
_NET_H = {"ยอดก่อน vat", "มูลค่า", "net", "ก่อน vat", "ยอดก่อน"}
_VAT_H = {"ภาษี", "vat", "7%"}
_TOTAL_H = {"ยอดรวม", "total", "รวม"}
_SKIP_H = {"รวม", "total", "ยอดรวม", "grand", "รวมทั้งสิ้น", "รวมแต่ละหน้า"}


def _hit(header: str, hints: set) -> bool:
    h = header.strip().lower()
    return any(hint in h for hint in hints)


def _to_float(val) -> Optional[float]:
    try:
        s = str(val or "").strip().replace(",", "").replace(" ", "").replace(" ", "")
        if not s or s in {"-", "–"}:
            return None
        neg = False
        if s.startswith("(") and s.endswith(")"):
            neg = True
            s = s[1:-1]
        v = round(float(s), 2)
        return -v if neg else v
    except Exception:
        return None


# v118.32.5.5.3 · 统一过滤 Gemini / pdfplumber 误抓的页眉/分隔/表头行
# 判定：发票号必须含 ≥2 字母数字组合 · 且不全是装饰符 · 不含 VAT 报告表头关键词
_VAT_HEAD_KW = (
    "ใบกำกับภาษี",
    "ใบกํากับภาษี",
    "ลำดับ",
    "ลําดับ",
    "ภาษีมูลค่า",
    "ภาษีมูลคา",
    "เลขที่ออก",
    "เลขประจำตัว",
    "เลขประจําตัว",
    "หมายเหตุ",
    "ผู้ซื้อ",
    "ผูซื้อ",
    "ผู้รับบริการ",
    "ผูรับบริการ",
    "หรือบริการ",
    "ชื่อสถาน",
    "ชื่อผู้",
    "ชื่อผู",
)
_VAT_ORN_RE = re.compile(r"^[\-=<>.\s|*_+]+$")
_VAT_ALNUM_RE = re.compile(r"[A-Za-z0-9]{2,}")


def _filter_garbage_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """剔除 PDF/Gemini 误识别的页眉、分隔线、表头行 · 数据行的 doc_no 应是单 token"""
    out = []
    for r in rows:
        inv = str(r.get("report_invoice_no") or "").strip()
        ref = str(r.get("report_ref_no") or "").strip()
        key = ref or inv
        if not key or len(key) < 3 or len(key) > 30:
            continue
        if _VAT_ORN_RE.match(key):
            continue
        if not _VAT_ALNUM_RE.search(key):
            continue
        if any(kw in key for kw in _VAT_HEAD_KW):
            continue
        # 数据行的 doc_no 是单 token · 不应含多空格(整行误抓会有很多空格)
        if key.count(" ") > 1:
            continue
        out.append(r)
    return out
