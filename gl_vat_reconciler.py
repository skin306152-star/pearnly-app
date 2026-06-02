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

import io
import re
import logging
from datetime import date, datetime  # BUG-FIX-T5 v118.35.0.46 · M3 date cell datetime 处理
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from collections import defaultdict

from field_comparator import normalize_invoice_no

# v118.35.0.3 · 包装 pydantic ValidationError 为单行用户友好提示
from services.ocr.error_format import short_error as _short_err

logger = logging.getLogger(__name__)
PARSER_VERSION = "1.0.0"

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


# ─────────────────────────────────────────────────────────────────────
# GL PDF 解析
# ─────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────
# GL Excel 解析
# ─────────────────────────────────────────────────────────────────────
def parse_gl_excel(file_bytes: bytes, revenue_prefix: str = "4") -> Dict[str, Any]:
    """
    解析 GL Excel
    自适应两种格式：
      A) 含 "account" 列：每行直接附带科目代码
      B) 科目作为分节标题行：科目代码独占一行/合并单元格
    """
    try:
        import openpyxl
    except ImportError:
        return {"ok": False, "rows": [], "row_count": 0, "error": "openpyxl 未安装"}

    rows: List[GlRow] = []
    current_account = ""
    col_map: Dict[str, int] = {}
    has_acct_col = False

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        for ws in wb.worksheets:
            current_account = ""
            col_map = {}
            has_acct_col = False
            for row in ws.iter_rows(values_only=True):
                cells = list(row)
                if not any(c is not None and str(c).strip() for c in cells):
                    continue

                # 1. 表头检测
                has_dr = any(_hit(str(c or ""), _GL_DEBIT_H) for c in cells)
                has_cr = any(_hit(str(c or ""), _GL_CRED_H) for c in cells)
                if has_dr and has_cr:
                    col_map = _map_gl_columns(cells)
                    has_acct_col = "account" in col_map
                    continue

                row_text = " ".join(str(c or "") for c in cells)

                # 2. 分节标题（无 account 列时才看）
                if not has_acct_col:
                    acct = _extract_account_code(row_text)
                    if acct and _is_revenue_acct(acct, revenue_prefix):
                        if not _row_has_amount(cells, col_map or {}):
                            current_account = acct
                            continue

                # 3. 跳过汇总行
                if _is_skip_row(cells):
                    continue

                if not col_map:
                    continue

                def _get(field: str) -> str:
                    idx = col_map.get(field)
                    if idx is None or idx >= len(cells):
                        return ""
                    v = cells[idx]
                    if v is None:
                        return ""
                    # BUG-FIX-T5 v118.35.0.46 · datetime cell 转 ISO date 字符串 + 佛历→公历
                    # 同 M4 BUG-FIX-T1 修法(bank_recon_v2._parse_date)· 让 M3 GlRow.date 字段
                    # 不再显示 "2568-12-31 00:00:00" garbage · 改 "2025-12-31" 公历干净
                    if isinstance(v, (datetime, date)):
                        y = v.year
                        if y >= 2500:
                            y -= 543
                        try:
                            return date(y, v.month, v.day).isoformat()
                        except (ValueError, AttributeError):
                            pass
                    return str(v).strip()

                # 决定 account_code
                if has_acct_col:
                    raw = _get("account")
                    acct = _extract_account_code(raw) or raw
                    if not _is_revenue_acct(acct, revenue_prefix):
                        continue
                    current_account = acct
                else:
                    if not current_account:
                        continue

                doc_no = _get("doc_no")
                if not doc_no:
                    continue
                debit = _to_float(_get("debit"))
                credit = _to_float(_get("credit"))
                if debit == 0.0 and credit == 0.0:
                    continue

                rows.append(
                    GlRow(
                        doc_no=doc_no,
                        norm_doc_no=normalize_doc_no(doc_no),
                        date=_get("date"),
                        account_code=current_account,
                        description=_get("description"),
                        debit=debit,
                        credit=credit,
                    )
                )
    except Exception as e:
        logger.error(f"[gl_excel] 解析失败: {e}", exc_info=True)
        return {"ok": False, "rows": [], "row_count": 0, "error": str(e)}

    logger.info(f"[gl_excel] 解析完成: {len(rows)} 行 · 收入前缀={revenue_prefix}")
    return {"ok": True, "rows": rows, "row_count": len(rows), "error": ""}


# ─────────────────────────────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────────────────────────────
def parse_gl(file_bytes: bytes, filename: str, revenue_prefix: str = "4") -> Dict[str, Any]:
    """按后缀分发解析 GL 文件。

    2026-05-21 multi-format refactor:
    - .xlsx / .xls      → parse_gl_excel (structural, reliable)
    - .pdf              → parse_gl_pdf   (existing Gemini Vision path)
    - .csv / .tsv / .docx / .doc / .txt / 图片 → 新统一 pipeline,
      显式 document_type='general_ledger' 让 prompt + validators 防止
      description 列的数字(例如 6091)被识别成 debit/credit/amount。
    """
    import os as _os

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls"):
        return parse_gl_excel(file_bytes, revenue_prefix)
    if ext == "pdf":
        # 2026-05-21: PDF GL defaults to the new pipeline so description-column
        # numbers (e.g. 6091) can't leak into debit/credit. Set
        # OCR_PDF_GL_LEGACY=true to opt back into the older Gemini-Vision
        # parse_gl_pdf path (kept for emergency rollback).
        if _os.environ.get("OCR_PDF_GL_LEGACY", "").strip().lower() == "true":
            return parse_gl_pdf(file_bytes, revenue_prefix)
        result = _parse_gl_via_pipeline(file_bytes, filename, revenue_prefix)
        if result.get("ok") and result.get("rows"):
            return result
        # Pipeline returned 0 rows or errored — fall back to legacy so we
        # don't worsen the worst case (legacy at least extracted SOMETHING
        # for the production customers we already serve).
        logger.warning(
            f"[parse_gl] pipeline yielded {result.get('row_count')} rows / "
            f"err={result.get('error')!r} · falling back to parse_gl_pdf"
        )
        return parse_gl_pdf(file_bytes, revenue_prefix)
    return _parse_gl_via_pipeline(file_bytes, filename, revenue_prefix)


def _parse_gl_via_pipeline(file_bytes: bytes, filename: str, revenue_prefix: str) -> Dict[str, Any]:
    """Route non-PDF/non-Excel GL files through services/ocr/pipeline with
    document_type=general_ledger, then convert the normalized JSON into the
    List[GlRow] shape gl_vat_reconciler.reconcile_gl_vat expects.

    Supported here: CSV / TSV / Word / image / TXT.
    Excludes Excel and PDF on purpose — those paths already work well and
    have been tested with real customer data; not worth the regression risk
    in this refactor.
    """
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {"ok": False, "rows": [], "row_count": 0, "error": f"pipeline import failed: {e}"}

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, document_type="general_ledger")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(file_bytes, filename=filename or "gl", document_type="general_ledger")
        else:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "error": f"暂不支持 {ext_dot} · 请上传 Excel / PDF / CSV / Word / 图片",
            }
    except Exception as e:
        return {"ok": False, "rows": [], "row_count": 0, "error": _short_err(e)}

    legacy = pipeline_result_to_legacy_dict(pr)
    rows = _gl_rows_from_pipeline_legacy(legacy, revenue_prefix)
    warnings = []
    for p in legacy.get("pages") or []:
        warnings.extend(p.get("_validation_warnings") or [])
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "parser_version": f"{PARSER_VERSION}+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
        "validation_warnings": warnings,
    }


def _gl_rows_from_pipeline_legacy(legacy_dict: Dict[str, Any], revenue_prefix: str) -> List[GlRow]:
    """Convert pipeline normalized JSON (general_ledger) → List[GlRow] for
    reconcile_gl_vat. Filters to revenue rows (account_code starts with
    revenue_prefix, e.g. "4") and ensures amounts came from Debit/Credit
    (not from description) — validators already cleared mis-sourced fields,
    so any debit/credit value left here is provenance-clean.
    """
    out: List[GlRow] = []
    for page in legacy_dict.get("pages") or []:
        doc = (page or {}).get("document") or {}
        for e in doc.get("entries") or []:
            account_code = (e.get("account_code") or "").strip()
            if revenue_prefix and not account_code.startswith(revenue_prefix):
                continue
            try:
                debit = float(e.get("debit") or 0)
            except (ValueError, TypeError):
                debit = 0.0
            try:
                credit = float(e.get("credit") or 0)
            except (ValueError, TypeError):
                credit = 0.0
            if debit == 0.0 and credit == 0.0:
                continue
            doc_no_raw = (e.get("voucher_no") or "").strip()
            try:
                norm = normalize_invoice_no(doc_no_raw) if doc_no_raw else ""
            except Exception:
                norm = doc_no_raw
            out.append(
                GlRow(
                    doc_no=doc_no_raw,
                    norm_doc_no=norm,
                    date=e.get("transaction_date") or "",
                    account_code=account_code,
                    description=e.get("description") or "",
                    debit=debit,
                    credit=credit,
                )
            )
    return out


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
