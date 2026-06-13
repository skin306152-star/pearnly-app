# -*- coding: utf-8 -*-
"""VAT 报告解析 · 共享工具与列名/垃圾行常量(零依赖叶子)。"""

import re
from typing import List, Dict, Any, Optional

from services.recon.field_comparator import normalize_tax_id, normalize_branch, parse_date

PARSER_VERSION = "1.1.0"

# ── 列名关键词(泰/英/中/日 · 跟随用户 UI 语言生成的模板都要认) ──────────
# 加中/日时避开"税"裸字:税号/税前/税额/含税 子串会互抢,故只用更长的具体词。
_DATE_H = {"วันที่", "date", "วัน/เดือน/ปี", "วันที่ใบกำกับ", "วันที่เอกสาร", "日期", "日付"}
_NO_H = {
    "เลขที่",
    "invoice no",
    "เลขที่ใบกำกับ",
    "เลขที่เอกสาร",
    "no.",
    "发票号",
    "发票号码",
    "发票编号",
    "票号",
    "請求書番号",
    "請求書",
    "インボイス番号",
    "インボイス",
}
# v118.32.5 · GL对账·参考单据号列(优先于 invoice_no 检测，专给 GL 匹配用)
_REF_H = {"อ้างอิง", "reference", "ref no", "เอกสารอ้างอิง", "เลขอ้างอิง", "参考", "参照", "参考号"}
_NAME_H = {
    "ชื่อ",
    "name",
    "ผู้ซื้อ",
    "customer",
    "买方名称",
    "买方",
    "购买方",
    "客户名",
    "客户名称",
    "名称",
    "取引先",
    "顧客",
    "得意先",
}
_TAX_H = {
    "เลขประจำตัว",
    "tax id",
    "เลขภาษี",
    "tin",
    "税号",
    "税务登记号",
    "纳税人识别号",
    "买方税号",
    "税务编号",
    "納税者番号",
}
_BRANCH_H = {"สาขา", "branch", "分支", "分公司", "分店", "支店", "支社"}
_NET_H = {
    "ยอดก่อน vat",
    "มูลค่า",
    "net",
    "ก่อน vat",
    "ยอดก่อน",
    "税前",
    "税前金额",
    "不含税",
    "不含税金额",
    "净额",
    "税抜",
    "税抜金額",
}
_VAT_H = {
    "ภาษี",
    "vat",
    "7%",
    "税额",
    "增值税",
    "增值税额",
    "销项税",
    "销项税额",
    "消费税",
    "消費税",
}
_TOTAL_H = {
    "ยอดรวม",
    "total",
    "รวม",
    "合计",
    "合计金额",
    "含税",
    "含税金额",
    "总计",
    "总额",
    "合計",
    "税込",
    "税込金額",
}
_SKIP_H = {
    "รวม",
    "total",
    "ยอดรวม",
    "grand",
    "รวมทั้งสิ้น",
    "รวมแต่ละหน้า",
    "合计",
    "总计",
    "小计",
    "合計",
}


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


def _map_columns(headers) -> Dict[str, int]:
    col_map: Dict[str, int] = {}
    for i, h in enumerate(headers):
        h = (str(h) or "").strip()
        if not h:
            continue
        if _hit(h, _DATE_H) and "date" not in col_map:
            col_map["date"] = i
        # v118.32.5 · 参考单据号优先检测（关键词更specific，避免被 _NO_H 抢走）
        elif _hit(h, _REF_H) and "ref_no" not in col_map:
            col_map["ref_no"] = i
        elif _hit(h, _NO_H) and "invoice_no" not in col_map:
            col_map["invoice_no"] = i
        elif _hit(h, _NAME_H) and "buyer_name" not in col_map:
            col_map["buyer_name"] = i
        elif _hit(h, _TAX_H) and "buyer_tax_id" not in col_map:
            col_map["buyer_tax_id"] = i
        elif _hit(h, _BRANCH_H) and "buyer_branch" not in col_map:
            col_map["buyer_branch"] = i
        elif _hit(h, _NET_H) and "amount_pre_vat" not in col_map:
            col_map["amount_pre_vat"] = i
        elif _hit(h, _VAT_H) and "vat_amount" not in col_map:
            col_map["vat_amount"] = i
        elif _hit(h, _TOTAL_H) and "total_amount" not in col_map:
            col_map["total_amount"] = i
    return col_map


def _build_row(row_no: int, cells: list, col_map: Dict[str, int]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {"row_no": row_no}
    for field, ci in col_map.items():
        raw = cells[ci] if ci < len(cells) else None
        val = str(raw).strip() if raw is not None else ""
        if field == "date":
            d = parse_date(val)
            parsed["report_date"] = d.isoformat() if d else val
        elif field == "invoice_no":
            parsed["report_invoice_no"] = val
        elif field == "ref_no":
            parsed["report_ref_no"] = val  # v118.32.5 · GL对账匹配键
        elif field == "buyer_name":
            parsed["report_buyer_name"] = val
        elif field == "buyer_tax_id":
            parsed["report_buyer_tax_id"] = normalize_tax_id(val)
        elif field == "buyer_branch":
            parsed["report_buyer_branch"] = normalize_branch(val)
        elif field == "amount_pre_vat":
            parsed["report_amount_pre_vat"] = _to_float(val)
        elif field == "vat_amount":
            parsed["report_vat_amount"] = _to_float(val)
        elif field == "total_amount":
            parsed["report_amount"] = _to_float(val)
    parsed["is_individual"] = not bool(parsed.get("report_buyer_tax_id"))
    return parsed
