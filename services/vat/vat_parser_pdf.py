# -*- coding: utf-8 -*-
"""VAT 报告解析 · 电子版 PDF 文本/表格提取(pdfplumber · 零成本)。"""

import io
import re
import logging
from typing import List, Dict, Any, Optional

from services.recon.field_comparator import normalize_tax_id, normalize_branch, parse_date

from services.vat.vat_parser_common import (
    _to_float,
    _SKIP_H,
    PARSER_VERSION,
    _map_columns,
    _build_row,
)

logger = logging.getLogger(__name__)


# ======================================================================
# 2. PDF 文本提取(电子版 PDF · 零成本)
# ======================================================================


def parse_pdf_text(file_bytes: bytes) -> Optional[Dict[str, Any]]:
    """成功返回 dict · 失败/扫描件返回 None(回退 Gemini)"""
    try:
        import pdfplumber
    except ImportError:
        logger.info("[vat_pdf_text] pdfplumber 未安装 · 直接回退 Gemini")
        return None

    try:
        rows: List[Dict] = []
        meta: Dict[str, Any] = {}
        total_text_len = 0
        row_no = 0
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    header = None
                    hi = 0
                    for i, r in enumerate(table[:10]):
                        joined = " ".join(str(c or "").lower() for c in r)
                        if "เลขที่" in joined or "invoice" in joined or "วันที่" in joined:
                            header = r
                            hi = i
                            break
                    if not header:
                        continue
                    col_map = _map_columns(header)
                    for body in table[hi + 1 :]:
                        if not body or not any(c for c in body if c):
                            continue
                        first = str(body[0] or "").strip().lower()
                        if any(k in first for k in _SKIP_H):
                            if "amount_pre_vat" in col_map and col_map["amount_pre_vat"] < len(
                                body
                            ):
                                meta["total_amount_pre_vat"] = _to_float(
                                    body[col_map["amount_pre_vat"]]
                                )
                            if "vat_amount" in col_map and col_map["vat_amount"] < len(body):
                                meta["total_vat"] = _to_float(body[col_map["vat_amount"]])
                            continue
                        row_no += 1
                        rows.append(_build_row(row_no, body, col_map))
                total_text_len += len(page.extract_text() or "")

        # 文本极少 → 扫描件 · 回退 Gemini
        if total_text_len < 200 and not rows:
            logger.info(f"[vat_pdf_text] 文本仅 {total_text_len} 字符 · 判定扫描件 · 回退 Gemini")
            return None
        if not rows:
            # v118.32.5 · 表抽取 0 行但文字层存在 → 试文字行 regex
            # 很多泰文会计软件导出的 VAT 报告没有可见表格线，pdfplumber 抓不到 tables
            logger.info(f"[vat_pdf_text] 表抽取 0 行，文本 {total_text_len} 字符 · 试文字行 regex")
            text_rows = _parse_vat_pdf_text_lines(file_bytes)
            if text_rows:
                logger.info(f"[vat_pdf_text.regex] 文字行模式抽到 {len(text_rows)} 行")
                return {
                    "ok": True,
                    "rows": text_rows,
                    "meta": {},
                    "warnings": [],
                    "parser_version": PARSER_VERSION,
                    "row_count": len(text_rows),
                    "method": "pdf_text_regex",
                }
            return None

        return {
            "ok": True,
            "rows": rows,
            "meta": meta,
            "warnings": [],
            "parser_version": PARSER_VERSION,
            "row_count": len(rows),
            "method": "pdf_text",
        }
    except Exception as e:
        logger.warning(f"[vat_pdf_text] 失败 · 回退 Gemini · {type(e).__name__}: {e}")
        return None


# ── v118.32.5 · VAT 报告文字行 regex 解析（备用通道）──────────────────
# 触发条件：pdfplumber 找不到表格框线（多数泰文会计软件导出的 PDF）
# 行模式：[seq?] DATE INV_NO [REF_NO] BUYER_NAME [TAX_ID] [BRANCH] AMT_PRE_VAT VAT_AMT
# 用启发式：行末必须两个 .2 小数，行内含一个 DD/MM/YYYY
_VAT_DATE_RE = re.compile(r"(\d{1,2}[\-/.]\d{1,2}[\-/.]\d{2,4})")
_VAT_TAIL_2N = re.compile(
    r"((?:\(\s*[\d,]+\.\d{2}\s*\)|-?[\d,]+\.\d{2}))"
    r"\s+"
    r"((?:\(\s*[\d,]+\.\d{2}\s*\)|-?[\d,]+\.\d{2}))"
    r"\s*$"
)
_TAX_ID_RE = re.compile(r"\b(\d{13})\b")
_BRANCH_RE = re.compile(r"\b(0\d{4})\b")
# v118.32.5.5.5 · ref_no token 严格判定:字母开头 + 必须含数字
# 兼容 IV6812001 / OHC06/2025 / DXATM25-010 · 排除纯字母客户名(OHANAHAN/ASAHI/TSUKEMONO/SIM)
_REF_TOKEN_RE = re.compile(r"^(?=.*\d)[A-Za-z][A-Za-z0-9\-/.]+$")
# v118.32.5.5.5 · 切 invoice_no 粘连尾(wnf PDF 字距导致 "DXOHC25-006OHANAHAN" 粘成 1 个 token)
# 主部分 = 字母+数字(可含横杠/斜杠) · 尾巴 = ≥3 个大写字母粘连客户名
_GLUED_TAIL_RE = re.compile(r"^([A-Za-z]+\d+(?:[\-/]\d+)?)([A-Z]{3,}.*)$")


def _parse_vat_pdf_text_lines(file_bytes: bytes) -> List[Dict[str, Any]]:
    """对每页 extract_text() 的行做 regex 抽取
    返回 rows · 失败返回 []
    """
    try:
        import pdfplumber
    except ImportError:
        return []

    rows: List[Dict[str, Any]] = []
    row_no = 0
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                for raw_line in txt.split("\n"):
                    line = raw_line.strip()
                    if not line:
                        continue
                    # 必须行末两个 .2 金额
                    m_tail = _VAT_TAIL_2N.search(line)
                    if not m_tail:
                        continue
                    # 必须有日期
                    m_date = _VAT_DATE_RE.search(line)
                    if not m_date:
                        continue
                    # 跳过表头/合计：含 "เลขที่" "ยอดรวม" "รวมทั้งสิ้น" 等
                    low = line.lower()
                    if "เลขที่" in line and "ใบกำกับ" in line:
                        continue
                    if any(k in low for k in {"รวมทั้งสิ้น", "รวมแต่ละหน้า", "grand total"}):
                        continue

                    amount_pre_vat = _to_float(m_tail.group(1))
                    vat_amount = _to_float(m_tail.group(2))
                    if amount_pre_vat is None and vat_amount is None:
                        continue

                    # 中间部分：日期之后到行末 2 金额之前
                    mid = line[m_date.end() : m_tail.start()].strip()
                    # 启发：mid 头几个 token 通常是 invoice_no / ref_no
                    tokens = mid.split()
                    invoice_no = ""
                    ref_no = ""
                    if tokens:
                        # v118.32.5.5.4 · 跳过开头的序号(纯数字 1-3 位 · wnf 格式行首是序号)
                        idx = 0
                        if idx < len(tokens) and re.fullmatch(r"\d{1,3}", tokens[idx]):
                            idx += 1
                        if idx < len(tokens):
                            invoice_no = tokens[idx]
                            # v118.32.5.5.5 · 切粘连尾巴(DXOHC25-006OHANAHAN → DXOHC25-006)
                            m_glued = _GLUED_TAIL_RE.match(invoice_no)
                            if m_glued:
                                invoice_no = m_glued.group(1)
                            # ref_no 必须含数字 · 不接受纯字母客户名
                            if (
                                idx + 1 < len(tokens)
                                and _REF_TOKEN_RE.match(tokens[idx + 1])
                                and not _TAX_ID_RE.match(tokens[idx + 1])
                            ):
                                ref_no = tokens[idx + 1]
                    # 提取 13 位税号
                    m_tax = _TAX_ID_RE.search(mid)
                    tax_id = m_tax.group(1) if m_tax else ""
                    # 提取 5 位分支码（0xxxx）· 默认 "00000"
                    m_br = _BRANCH_RE.search(mid)
                    branch = m_br.group(1) if m_br else ("00000" if tax_id else "")
                    # 买方名：去掉这些已识别的 token 后的剩余串
                    name = mid
                    for cut in (tax_id, branch, invoice_no, ref_no):
                        if cut and cut in name:
                            name = name.replace(cut, " ", 1)
                    # v118.32.5.2 · 清洗 PDF 抽文残留：
                    # 1) "00000" 等分支码（pdfplumber 字距问题可能把它从分支号位置漏掉）
                    name = re.sub(r"\b0\d{4}\b", " ", name)
                    # 2) 行首 "SI 1" / "I26 1" 等 — pdfplumber 字距问题把 "SI000001" 抽成 "SI 1"
                    name = re.sub(r"^\s*(?:[A-Za-z]{1,4}\s+\d+\s+){1,3}", " ", name)
                    # 3) 行尾纯数字（残留的金额/seq）
                    name = re.sub(r"\s+\d{1,5}\s*$", "", name)
                    # 4) 合并多空格
                    name = re.sub(r"\s+", " ", name).strip()

                    # 日期归一化（佛历→西历）
                    d = parse_date(m_date.group(1))
                    date_str = d.isoformat() if d else m_date.group(1)

                    row_no += 1
                    rows.append(
                        {
                            "row_no": row_no,
                            "report_date": date_str,
                            "report_invoice_no": invoice_no,
                            "report_ref_no": ref_no,
                            "report_buyer_name": name,
                            "report_buyer_tax_id": normalize_tax_id(tax_id),
                            "report_buyer_branch": normalize_branch(branch),
                            "report_amount_pre_vat": amount_pre_vat,
                            "report_vat_amount": vat_amount,
                            "report_amount": (amount_pre_vat or 0) + (vat_amount or 0),
                            "is_individual": not bool(tax_id),
                        }
                    )
    except Exception as e:
        logger.warning(f"[vat_pdf_text.regex] 失败: {e}")
        return []
    return rows
