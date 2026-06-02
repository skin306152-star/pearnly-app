# -*- coding: utf-8 -*-
"""GL PDF/文本行解析（gl_vat_reconciler 拆分）。"""

import io
import re
import logging
from typing import List, Dict, Any

from services.recon.gl_vat_types import GlRow
from services.recon.gl_vat_parse_common import (
    _to_float,
    _is_revenue_acct,
    _hit,
    _extract_account_code,
    _is_debit_line,
    _is_skip_row,
    normalize_doc_no,
    _map_gl_columns,
    _row_has_amount,
    _GL_DEBIT_H,
    _GL_CRED_H,
    _SKIP_ROWS,
)

logger = logging.getLogger(__name__)


# GL PDF 数据行的"文字行模式"正则：
# <日期 DD/MM/YYYY> ... <doc_no> ... <num1> <num2> <num3>
# 简化：取行末 3 个数字 = debit / credit / balance
_DATE_RE = re.compile(r"(\d{1,2}[\-/.]\d{1,2}[\-/.]\d{2,4})")
_TAIL_NUMS = re.compile(
    r"((?:\(\s*[\d,]+\.?\d*\s*\)|-?[\d,]+\.\d{2}|-?[\d,]{4,}))"
    r"\s+"
    r"((?:\(\s*[\d,]+\.?\d*\s*\)|-?[\d,]+\.\d{2}|-?[\d,]{4,}))"
    r"\s+"
    r"((?:\(\s*[\d,]+\.?\d*\s*\)|-?[\d,]+\.\d{2}|-?[\d,]{4,}))"
    r"\s*$"
)

# v118.32.5.5 · 兼容 Express / Mr.ERP "省略零列" 格式:行末只有 amount + balance(2 个数字)
# debit / credit 二选一显示 · 另一列省略 · 借贷方向通过余额变化判
_TAIL_NUMS_2 = re.compile(
    r"((?:\(\s*[\d,]+\.?\d*\s*\)|-?[\d,]+\.\d{2}|-?[\d,]{4,}))"
    r"\s+"
    r"((?:\(\s*[\d,]+\.?\d*\s*\)|-?[\d,]+\.\d{2}|-?[\d,]{4,}))"
    r"\s*$"
)

# v118.32.5.5 · 凭证号格式:字母前缀 + 数字 / 斜杠 / 中划线
# 兼容 IV6812001 / OHC06/2025 / DXATM25-010 / SBT10/2025 / JV-2025-001 等
_DOCNO_RE = re.compile(r"\b[A-Z][A-Z0-9/\-]{2,}\b")


def _parse_gl_text_lines(file_bytes: bytes, revenue_prefix: str = "4") -> Dict[str, Any]:
    """
    pdfplumber 表格抽取失败时的备用：直接走文字行 regex
    v118.32.5.5 · 兼容两种泰国 GL PDF 风格：
      A) 老 BAKELAB 风格：行末 3 数字（debit + credit + balance · 0 值显 "0.00"）
      B) Express / Mr.ERP 风格：行末 2 数字（amount + balance · 0 值列省略）
         + 同日多笔省略日期（用上一行继承）
         + 借贷方向通过余额括号变化判定
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "error": "pdfplumber 未安装",
            "diag": "no_pdfplumber",
        }

    rows: List[GlRow] = []
    current_account = ""
    diag_acct_seen: List[str] = []
    diag_data_lines = 0
    last_date = ""  # 同日多笔继承
    prev_balance = None  # 余额变化判借贷

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                for raw_line in txt.split("\n"):
                    line = raw_line.strip()
                    if not line:
                        continue

                    # 1. 科目分节标题（"411000 รายได้..." 等）
                    acct = _extract_account_code(line)
                    if acct and _is_revenue_acct(acct, revenue_prefix):
                        # 标题行特征：含科目代码但行末没有 ≥ 2 个金额
                        if not _TAIL_NUMS.search(line) and not _TAIL_NUMS_2.search(line):
                            current_account = acct
                            last_date = ""
                            # 取期初余额（括号格式）用于后续借贷判定
                            m_bal = re.search(r"\(\s*[\d,]+\.\d{2}\s*\)", line)
                            prev_balance = _to_float(m_bal.group(0)) if m_bal else None
                            if acct not in diag_acct_seen:
                                diag_acct_seen.append(acct)
                            continue

                    if not current_account:
                        continue

                    # 2. 跳过汇总/小计（扩展：行首 "รวม" + 无 doc_no = 小计行）
                    low = line.lower()
                    if any(k in low for k in _SKIP_ROWS):
                        continue
                    if line.startswith("รวม") and not _DOCNO_RE.search(line):
                        continue

                    # 3. 数据行：必须含 doc_no + 行末 ≥ 2 个金额
                    m_tail3 = _TAIL_NUMS.search(line)
                    m_tail2 = None if m_tail3 else _TAIL_NUMS_2.search(line)
                    if not (m_tail3 or m_tail2):
                        continue
                    if not _DOCNO_RE.search(line):
                        continue

                    diag_data_lines += 1

                    # 日期（可选 · 缺失时继承上一行）
                    m_date = _DATE_RE.search(line)
                    if m_date:
                        date_str = m_date.group(1)
                        last_date = date_str
                        after_date = line[m_date.end() :].strip()
                    else:
                        date_str = last_date
                        after_date = line

                    tokens = after_date.split()
                    if len(tokens) < 3:
                        continue

                    # doc_no：第 1 个匹配 _DOCNO_RE 的 token
                    doc_no = ""
                    for tk in tokens:
                        if _DOCNO_RE.fullmatch(tk):
                            doc_no = tk
                            break
                    if not doc_no:
                        continue

                    # 借贷解析
                    if m_tail3:
                        # 老 3 列格式
                        debit = _to_float(m_tail3.group(1))
                        credit = _to_float(m_tail3.group(2))
                        prev_balance = _to_float(m_tail3.group(3))
                        m_tail = m_tail3
                    else:
                        # 新 2 列格式 · 余额变化判借贷
                        amount = abs(_to_float(m_tail2.group(1)))
                        new_balance = _to_float(m_tail2.group(2))
                        debit, credit = 0.0, 0.0
                        # v118.32.5.5.29 · 退货关键词优先：ลดหนี้/รับคืน 等 → debit
                        if _is_debit_line(after_date):
                            debit = amount
                        elif prev_balance is not None:
                            delta = abs(new_balance) - abs(prev_balance)
                            if abs(delta - amount) < 0.01:
                                credit = amount  # 余额绝对值↑ = credit
                            elif abs(delta + amount) < 0.01:
                                debit = amount  # 余额绝对值↓ = debit
                            else:
                                credit = amount  # 兜底：收入类默认 credit
                        else:
                            credit = amount  # 无期初 · 默认 credit
                        prev_balance = new_balance
                        m_tail = m_tail2

                    if debit == 0.0 and credit == 0.0:
                        continue

                    # description = doc_no 之后到第 1 个金额之前
                    rest = after_date
                    idx_doc = rest.find(doc_no)
                    desc_start = idx_doc + len(doc_no) if idx_doc >= 0 else 0
                    amt1_str = m_tail.group(1)
                    desc_end = rest.rfind(amt1_str)
                    description = rest[desc_start:desc_end].strip() if desc_end > desc_start else ""

                    rows.append(
                        GlRow(
                            doc_no=doc_no,
                            norm_doc_no=normalize_doc_no(doc_no),
                            date=date_str,
                            account_code=current_account,
                            description=description,
                            debit=debit,
                            credit=credit,
                        )
                    )
    except Exception as e:
        logger.error(f"[gl_pdf.text] 失败: {e}", exc_info=True)
        return {"ok": False, "rows": [], "row_count": 0, "error": str(e), "diag": f"exception:{e}"}

    diag = {
        "method": "text_lines",
        "accounts_seen": diag_acct_seen[:10],
        "candidate_data_lines": diag_data_lines,
        "rows_kept": len(rows),
    }
    logger.info(f"[gl_pdf.text] 完成 · {diag}")
    return {"ok": True, "rows": rows, "row_count": len(rows), "error": "", "diag": diag}


def parse_gl_pdf(file_bytes: bytes, revenue_prefix: str = "4") -> Dict[str, Any]:
    """
    解析泰文 GL PDF（科目分节格式）
    策略：
      1. pdfplumber extract_tables() 优先（含可见框线的 PDF 命中率高）
      2. 0 行 → 退回文字行 regex 模式（多数泰文 GL 导出无可见框线）
    返回 {"ok", "rows", "row_count", "error", "diag"}
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "error": "pdfplumber 未安装",
            "diag": "no_pdfplumber",
        }

    rows: List[GlRow] = []
    current_account = ""
    col_map: Dict[str, int] = {}
    diag_acct_seen: List[str] = []
    diag_tables = 0
    diag_header_found = False

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                diag_tables += len(tables)
                # 同时扫描页面文本提取科目分节标题（表外的标题行）
                page_text = page.extract_text() or ""
                for line in page_text.split("\n"):
                    acct = _extract_account_code(line)
                    if acct and _is_revenue_acct(acct, revenue_prefix):
                        current_account = acct
                        if acct not in diag_acct_seen:
                            diag_acct_seen.append(acct)
                        break

                for table in tables:
                    if not table:
                        continue
                    for row in table:
                        if not row or not any(c for c in row if c):
                            continue
                        cells = list(row)
                        row_text = " ".join(str(c or "") for c in cells)

                        acct = _extract_account_code(row_text)
                        if acct and _is_revenue_acct(acct, revenue_prefix):
                            if not _row_has_amount(cells, col_map or {}):
                                current_account = acct
                                if acct not in diag_acct_seen:
                                    diag_acct_seen.append(acct)
                                continue

                        has_dr = any(_hit(str(c or ""), _GL_DEBIT_H) for c in cells)
                        has_cr = any(_hit(str(c or ""), _GL_CRED_H) for c in cells)
                        if has_dr and has_cr:
                            col_map = _map_gl_columns(cells)
                            diag_header_found = True
                            continue

                        if _is_skip_row(cells):
                            continue
                        if not col_map or not current_account:
                            continue

                        def _get(field: str) -> str:
                            idx = col_map.get(field)
                            if idx is None or idx >= len(cells):
                                return ""
                            return str(cells[idx] or "").strip()

                        doc_no = _get("doc_no")
                        if not doc_no:
                            continue
                        date_str = _get("date")
                        debit = _to_float(_get("debit"))
                        credit = _to_float(_get("credit"))
                        if debit == 0.0 and credit == 0.0:
                            continue

                        rows.append(
                            GlRow(
                                doc_no=doc_no,
                                norm_doc_no=normalize_doc_no(doc_no),
                                date=date_str,
                                account_code=current_account,
                                description=_get("description"),
                                debit=debit,
                                credit=credit,
                            )
                        )
    except Exception as e:
        logger.error(f"[gl_pdf] 表抽取失败 · 准备回退文字行 · {e}")
        # 不直接 return；继续走文字行回退
        rows = []

    if rows:
        diag = {
            "method": "tables",
            "tables_seen": diag_tables,
            "header_found": diag_header_found,
            "accounts_seen": diag_acct_seen[:10],
            "rows_kept": len(rows),
        }
        logger.info(f"[gl_pdf] 表模式完成 · {diag}")
        return {"ok": True, "rows": rows, "row_count": len(rows), "error": "", "diag": diag}

    # 表模式 0 行 → 退到文字行
    logger.info(
        f"[gl_pdf] 表模式 0 行（tables={diag_tables}, header={diag_header_found}, "
        f"accts={diag_acct_seen}）· 回退文字行 regex"
    )
    fallback = _parse_gl_text_lines(file_bytes, revenue_prefix)
    if isinstance(fallback.get("diag"), dict):
        fallback["diag"]["primary_tried"] = "tables"
        fallback["diag"]["primary_tables_seen"] = diag_tables
        fallback["diag"]["primary_header_found"] = diag_header_found
        fallback["diag"]["primary_accts"] = diag_acct_seen[:10]
    return fallback
