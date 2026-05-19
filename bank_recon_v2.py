# -*- coding: utf-8 -*-
"""
bank_recon_v2.py · Pearnly · v1.0.0
銀行対照 / Bank Statement vs GL Reconciliation Engine

Supported banks  : KBank · BBL · KKP · KTB · SCB · generic fallback
GL input formats : Excel (.xlsx / .xls) · PDF (pdfplumber → Gemini fallback)
Matching layers  : L1 exact date+amount  · L2 ±3-day tolerance · L3 amount only
Export           : 4-sheet openpyxl · i18n th/en/zh/ja
"""

import io
import re
import os
import json
import logging
import hashlib
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
AMOUNT_TOL = 0.02          # baht tolerance for amount matching
DATE_TOL_DAYS = 3          # days tolerance for layer-2 matching
MIN_PLUMBER_ROWS = 3       # fallback to Gemini if pdfplumber yields < this

# v118.33.13.1 · in-memory cache for Gemini OCR results, keyed by SHA-256 of file bytes.
# Same PDF re-uploaded -> instant. Capped at 256 entries (~80 MB worst case), LRU eviction.
import collections as _collections
_GEMINI_STMT_CACHE: "_collections.OrderedDict[str, Dict[str, Any]]" = _collections.OrderedDict()
_GEMINI_GL_CACHE:   "_collections.OrderedDict[str, Dict[str, Any]]" = _collections.OrderedDict()
_GEMINI_CACHE_MAX = 256

def _cache_get(cache: "_collections.OrderedDict[str, Dict[str, Any]]",
               key: str) -> Optional[Dict[str, Any]]:
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None

def _cache_put(cache: "_collections.OrderedDict[str, Dict[str, Any]]",
               key: str, value: Dict[str, Any]) -> None:
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > _GEMINI_CACHE_MAX:
        cache.popitem(last=False)

# Thai month names (full + abbreviated)
_TH_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5,
    "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10,
    "พ.ย.": 11, "ธ.ค.": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Bank detection keywords
_BANK_SIGNATURES = {
    "kbank":  ["กสิกรไทย", "kasikorn", "kbank", "k-bank"],
    "bbl":    ["กรุงเทพ", "bangkok bank", "bbl"],
    "kkp":    ["เกียรตินาคิน", "kiatnakin", "kkp"],
    "ktb":    ["กรุงไทย", "krungthai", "ktb"],
    "scb":    ["ไทยพาณิชย์", "siam commercial", "scb"],
    "bay":    ["กรุงศรี", "bank of ayudhya", "bay", "krungsri"],
    "tmb":    ["ทหารไทย", "tmbthanachart", "ttb"],
}

# GL skip rows
_GL_SKIP_KW = {
    "ยอดยกมา", "ยอดยกไป", "ยอดรวม", "balance forward", "carried forward",
    "brought forward", "subtotal", "opening balance", "closing balance",
    "รวมประจำเดือน", "รวมทั้งสิ้น", "รวมแต่ละหน้า",
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class StatementRow:
    date: Optional[date]
    description: str
    withdrawal: float        # money out (≥ 0)
    deposit: float           # money in (≥ 0)
    balance: float
    source_file: str = ""
    row_hash: str = ""       # for deduplication
    # v118.33.13.0 · accuracy verification fields
    confidence: str = "high"          # 'high'|'medium'|'low' (set by OCR engine)
    balance_ok: Optional[bool] = None # True/False (arithmetic verified)/None (cannot verify)

    def __post_init__(self):
        if not self.row_hash:
            key = f"{self.date}|{self.withdrawal:.2f}|{self.deposit:.2f}|{self.description[:40]}"
            self.row_hash = hashlib.md5(key.encode()).hexdigest()[:12]


@dataclass
class GlRow:
    date: Optional[date]
    doc_no: str
    account_code: str
    description: str
    debit: float             # money out (≥ 0)
    credit: float            # money in (≥ 0)
    source_file: str = ""
    row_hash: str = ""

    def __post_init__(self):
        if not self.row_hash:
            key = f"{self.date}|{self.doc_no}|{self.account_code}|{self.debit:.2f}|{self.credit:.2f}"
            self.row_hash = hashlib.md5(key.encode()).hexdigest()[:12]


@dataclass
class BankReconRow:
    match_status: str        # matched|gl_debit_only|gl_credit_only|stmt_withdrawal_only|stmt_deposit_only
    match_layer: Optional[int]  # 1=exact, 2=date_tol, 3=amount_only, None=unmatched
    # Statement side
    stmt_date: Optional[date] = None
    stmt_desc: str = ""
    stmt_withdrawal: float = 0.0
    stmt_deposit: float = 0.0
    stmt_balance: float = 0.0
    # GL side
    gl_date: Optional[date] = None
    gl_doc_no: str = ""
    gl_account_code: str = ""
    gl_desc: str = ""
    gl_debit: float = 0.0
    gl_credit: float = 0.0
    # Meta
    date_diff_days: Optional[int] = None
    source_stmt_file: str = ""
    source_gl_file: str = ""
    # v118.33.13.0 · OCR accuracy verification (from StatementRow)
    stmt_confidence: str = "high"        # 'high'|'medium'|'low'
    stmt_balance_ok: Optional[bool] = None  # True/False/None


@dataclass
class BankReconSummary:
    bank_code: str = ""
    gl_account_code: str = ""
    # Balance figures
    stmt_opening: float = 0.0
    stmt_closing: float = 0.0
    gl_opening: float = 0.0
    gl_closing: float = 0.0
    # Totals
    stmt_total_deposit: float = 0.0
    stmt_total_withdrawal: float = 0.0
    gl_total_credit: float = 0.0
    gl_total_debit: float = 0.0
    # Counts
    matched_count: int = 0
    gl_debit_only_count: int = 0
    gl_credit_only_count: int = 0
    stmt_withdrawal_only_count: int = 0
    stmt_deposit_only_count: int = 0
    # Unmatched amounts
    gl_debit_only_amount: float = 0.0
    gl_credit_only_amount: float = 0.0
    stmt_withdrawal_only_amount: float = 0.0
    stmt_deposit_only_amount: float = 0.0
    # Reconciliation check
    opening_diff: float = 0.0     # stmt_opening - gl_opening
    formula_stmt_closing: float = 0.0   # calculated from formula
    formula_diff: float = 0.0           # stmt_closing - formula_stmt_closing (ideally 0)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def _to_float(val) -> float:
    if val is None:
        return 0.0
    s = str(val).strip().replace(",", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "–", "—"}:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    if s.startswith("-"):
        neg = True
        s = s[1:]
    # Handle Thai dot-as-thousands-separator: "115.586.50" → "115586.50"
    dot_count = s.count('.')
    if dot_count > 1:
        last_dot = s.rfind('.')
        s = s[:last_dot].replace('.', '') + s[last_dot:]
    try:
        v = round(float(s), 2)
        return -v if neg else v
    except Exception:
        return 0.0


def _parse_date(raw: str) -> Optional[date]:
    """Parse Thai/English date strings into date objects."""
    if not raw:
        return None
    raw = str(raw).strip()

    # Replace common separators
    clean = raw.replace("/", "-").replace(".", "-").strip()

    # Try Thai month names first
    for th_name, month_num in _TH_MONTHS.items():
        if th_name in raw:
            # e.g. "15 มกราคม 2567" or "15 ม.ค. 67"
            nums = re.findall(r"\d+", raw)
            if len(nums) >= 2:
                day = int(nums[0])
                yr_raw = int(nums[-1])
                # BE to CE conversion
                if yr_raw >= 2500:
                    yr_raw -= 543
                elif yr_raw < 100:
                    # Thai BE short year: 68 → BE 2568 → CE 2025
                    yr_raw += 1957 if yr_raw >= 43 else 2000
                try:
                    return date(yr_raw, month_num, day)
                except ValueError:
                    pass  # 该年月组合非合法日期 · 尝试下一规则

    # Numeric formats: dd-mm-yyyy, yyyy-mm-dd, dd/mm/yy
    parts = re.split(r"[-/\s]", clean)
    if len(parts) == 3:
        p0, p1, p2 = parts
        try:
            # yyyy-mm-dd
            if len(p0) == 4 and int(p0) > 1900:
                yr, mo, dy = int(p0), int(p1), int(p2)
            # dd-mm-yyyy or dd-mm-yy
            elif len(p2) == 4 or len(p2) == 2:
                dy, mo = int(p0), int(p1)
                yr = int(p2)
                if yr >= 2500:
                    yr -= 543
                elif yr < 100:
                    # Thai BE short year: 68 → BE 2568 → CE 2025
                    yr += 1957 if yr >= 43 else 2000
            else:
                return None
            return date(yr, mo, dy)
        except (ValueError, TypeError):
            pass  # 日期/月/年解析失败 · 返回 None

    return None


def _amount_matches(a: float, b: float) -> bool:
    return abs(a - b) <= AMOUNT_TOL


def _day_diff(d1: Optional[date], d2: Optional[date]) -> Optional[int]:
    if d1 is None or d2 is None:
        return None
    return abs((d1 - d2).days)


def _is_gl_skip_row(cells: List) -> bool:
    joined = " ".join(str(c or "").strip().lower() for c in cells[:4])
    return any(kw in joined for kw in _GL_SKIP_KW)


def _detect_bank(text: str) -> str:
    """Detect bank from PDF text content."""
    tl = text.lower()
    for bank_code, keywords in _BANK_SIGNATURES.items():
        if any(kw.lower() in tl for kw in keywords):
            return bank_code
    return "generic"


# ─────────────────────────────────────────────────────────────────────────────
# BANK STATEMENT PARSERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_kbank_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Parse KBank statement tables. Returns (rows, opening, closing)."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        # Find header row
        header_idx = None
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        for i, row in enumerate(table):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if any(k in row_txt for k in ["วันที่", "date"]):
                header_idx = i
                for j, c in enumerate(cells):
                    if any(k in c for k in ["วันที่", "date"]) and col_date < 0:
                        col_date = j
                    if any(k in c for k in ["รายการ", "description", "detail"]) and col_desc < 0:
                        col_desc = j
                    if any(k in c for k in ["ถอน", "withdraw"]) and col_wd < 0:
                        col_wd = j
                    if any(k in c for k in ["ฝาก", "deposit", "credit"]) and col_dep < 0:
                        col_dep = j
                    if any(k in c for k in ["คงเหลือ", "balance"]) and col_bal < 0:
                        col_bal = j
                break

        if header_idx is None or col_date < 0:
            continue

        for row in table[header_idx + 1:]:
            if not row or len(row) <= max(col_date, col_bal):
                continue
            raw_date = str(row[col_date] or "").strip()
            if not raw_date or raw_date.lower() in ("วันที่", "date", ""):
                continue
            desc = str(row[col_desc] or "").strip() if col_desc >= 0 else ""
            # Skip opening/closing balance marker rows
            if any(kw in desc.lower() for kw in ["ยอดยกมา", "ยอดยกไป", "brought forward"]):
                bal = _to_float(row[col_bal] if col_bal >= 0 else 0)
                if not opening:
                    opening = bal
                closing = bal
                continue
            d = _parse_date(raw_date)
            if d is None:
                continue
            wd = _to_float(row[col_wd]) if col_wd >= 0 and col_wd < len(row) else 0.0
            dep = _to_float(row[col_dep]) if col_dep >= 0 and col_dep < len(row) else 0.0
            bal = _to_float(row[col_bal]) if col_bal >= 0 and col_bal < len(row) else 0.0
            if wd == 0.0 and dep == 0.0 and bal == 0.0:
                continue
            if not opening and rows:
                pass  # will compute from first balance - first txn
            closing = bal
            rows.append(StatementRow(date=d, description=desc,
                                     withdrawal=abs(wd), deposit=abs(dep), balance=bal))
    # Infer opening from first transaction
    if rows and opening == 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


def _parse_bbl_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Parse BBL statement tables (both printed and activity report formats)."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        header_idx = None

        for i, row in enumerate(table):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if any(k in row_txt for k in ["วันที่", "date", "รายการ"]):
                header_idx = i
                for j, c in enumerate(cells):
                    if any(k in c for k in ["วันที่", "date", "tran date"]) and col_date < 0:
                        col_date = j
                    if any(k in c for k in ["รายการ", "description", "particular", "detail"]) and col_desc < 0:
                        col_desc = j
                    if any(k in c for k in ["ถอน", "debit", "withdrawal"]) and col_wd < 0:
                        col_wd = j
                    if any(k in c for k in ["ฝาก", "credit", "deposit"]) and col_dep < 0:
                        col_dep = j
                    if any(k in c for k in ["คงเหลือ", "balance"]) and col_bal < 0:
                        col_bal = j
                break

        if header_idx is None or col_date < 0:
            continue

        for row in table[header_idx + 1:]:
            if not row:
                continue
            raw_date = str(row[col_date] if col_date < len(row) else "").strip()
            if not raw_date:
                continue
            desc = str(row[col_desc] if col_desc >= 0 and col_desc < len(row) else "").strip()
            if any(kw in desc.lower() for kw in ["ยอดยกมา", "ยอดนำมา", "brought forward", "opening"]):
                bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
                if not opening:
                    opening = bal
                continue
            d = _parse_date(raw_date)
            if d is None:
                continue
            wd = _to_float(row[col_wd] if col_wd >= 0 and col_wd < len(row) else 0)
            dep = _to_float(row[col_dep] if col_dep >= 0 and col_dep < len(row) else 0)
            bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
            if wd == 0.0 and dep == 0.0:
                continue
            closing = bal
            rows.append(StatementRow(date=d, description=desc,
                                     withdrawal=abs(wd), deposit=abs(dep), balance=bal))

    if rows and opening == 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


def _parse_generic_pages(tables: List) -> Tuple[List[StatementRow], float, float]:
    """Generic fallback parser for unknown bank formats."""
    rows = []
    opening = 0.0
    closing = 0.0

    for table in tables:
        if not table or len(table) < 2:
            continue
        # Auto-detect column positions from header
        col_date = col_desc = col_wd = col_dep = col_bal = -1
        header_idx = 0

        for i, row in enumerate(table[:5]):
            cells = [str(c or "").strip().lower() for c in row]
            row_txt = " ".join(cells)
            if sum(1 for k in ["date", "วันที่", "description", "รายการ"] if k in row_txt) >= 2:
                header_idx = i
                for j, c in enumerate(cells):
                    if col_date < 0 and any(k in c for k in ["date", "วันที่", "วัน"]):
                        col_date = j
                    elif col_desc < 0 and any(k in c for k in ["desc", "รายการ", "detail", "particular"]):
                        col_desc = j
                    elif col_wd < 0 and any(k in c for k in ["withdraw", "debit", "ถอน", "จ่าย"]):
                        col_wd = j
                    elif col_dep < 0 and any(k in c for k in ["deposit", "credit", "ฝาก", "รับ"]):
                        col_dep = j
                    elif col_bal < 0 and any(k in c for k in ["balance", "คงเหลือ", "ยอด"]):
                        col_bal = j
                break

        if col_date < 0:
            continue

        for row in table[header_idx + 1:]:
            if not row or len(row) < 3:
                continue
            raw_date = str(row[col_date] if col_date < len(row) else "").strip()
            d = _parse_date(raw_date)
            if d is None:
                continue
            desc = str(row[col_desc] if col_desc >= 0 and col_desc < len(row) else "").strip()
            wd = _to_float(row[col_wd] if col_wd >= 0 and col_wd < len(row) else 0)
            dep = _to_float(row[col_dep] if col_dep >= 0 and col_dep < len(row) else 0)
            bal = _to_float(row[col_bal] if col_bal >= 0 and col_bal < len(row) else 0)
            if wd == 0.0 and dep == 0.0:
                continue
            closing = bal
            rows.append(StatementRow(date=d, description=desc,
                                     withdrawal=abs(wd), deposit=abs(dep), balance=bal))

    if rows and opening == 0.0 and rows[0].balance != 0.0:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    return rows, opening, closing


def _parse_stmt_text_lines(
    text: str, bank_code: str = "generic"
) -> Tuple[List[StatementRow], float, float]:
    """
    Text-line parser for Thai bank statements with no table structure (e.g. KBank CA).
    Handles combined deposit/withdrawal column by comparing with running balance.
    Handles Thai dot-as-thousands-separator (115.586.50 → 115586.50).
    """
    rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0
    prev_balance: Optional[float] = None

    def _tok_to_float(tok: str) -> Optional[float]:
        s = tok.replace(',', '').replace(' ', '')
        if not s:
            return None
        neg = s.startswith('-')
        if neg:
            s = s[1:]
        dot_count = s.count('.')
        if dot_count > 1:
            last_dot = s.rfind('.')
            s = s[:last_dot].replace('.', '') + s[last_dot:]
        try:
            v = float(s)
            return -v if neg else v
        except ValueError:
            return None

    _DATE_PREFIX = re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$')

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Opening balance marker
        if any(kw in line for kw in ["ยอดยกมา", "brought forward", "ยอดคงเหลือยกมา"]):
            toks = line.split()
            for tok in reversed(toks):
                v = _tok_to_float(tok)
                if v is not None and v > 0:
                    opening = v
                    prev_balance = opening
                    break
            continue

        # Closing balance marker
        if any(kw in line for kw in ["ยอดยกไป", "closing balance"]):
            toks = line.split()
            for tok in reversed(toks):
                v = _tok_to_float(tok)
                if v is not None and v > 0:
                    closing = v
                    break
            continue

        toks = line.split()
        if len(toks) < 3:
            continue

        # First token must be a date (dd-mm-yy or dd/mm/yy)
        if not _DATE_PREFIX.match(toks[0]):
            continue
        d = _parse_date(toks[0])
        if d is None:
            continue

        # Group consecutive numeric tokens; pick rightmost group with >=2 members.
        # This prevents numbers embedded in descriptions (company names, cheque IDs)
        # from masking the actual amount+balance pair which always appear consecutively.
        _groups: List[List[Tuple[int, float]]] = []
        _cur: List[Tuple[int, float]] = []
        for i in range(1, len(toks)):
            v = _tok_to_float(toks[i])
            if v is not None:
                _cur.append((i, v))
            else:
                if _cur:
                    _groups.append(_cur)
                    _cur = []
        if _cur:
            _groups.append(_cur)
        num_vals: List[Tuple[int, float]] = []
        for _grp in reversed(_groups):
            if len(_grp) >= 2:
                num_vals = _grp
                break

        if len(num_vals) < 2:
            continue

        balance = num_vals[-1][1]
        amount = abs(num_vals[-2][1])
        if amount == 0.0:
            continue

        desc_end_idx = num_vals[-2][0]
        desc = " ".join(toks[1:desc_end_idx]).strip()

        # Determine direction by comparing balance with previous balance
        withdrawal = 0.0
        deposit = 0.0
        if prev_balance is not None:
            diff = round(balance - prev_balance, 2)
            if abs(diff - amount) <= AMOUNT_TOL:
                deposit = amount
            elif abs(diff + amount) <= AMOUNT_TOL:
                withdrawal = amount
            else:
                # Balance delta doesn't match amount exactly — use description hints
                desc_low = desc.lower()
                if any(kw in desc_low for kw in ["จ่าย", "ถอน", "debit", "withdraw", "โอนออก", "ชำระ"]):
                    withdrawal = amount
                else:
                    deposit = amount
        else:
            # No prev_balance yet — guess deposit
            deposit = amount

        prev_balance = balance
        closing = balance

        rows.append(StatementRow(
            date=d, description=desc,
            withdrawal=withdrawal, deposit=deposit, balance=balance,
        ))

    if not opening and rows:
        first = rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    if not closing and rows:
        closing = rows[-1].balance

    return rows, opening, closing



def _parse_kbank_text_columns(text: str) -> Tuple[List[StatementRow], float, float]:
    """
    KBank PDF text extracted by pdfminer is COLUMN-STACKED: each field on its
    own line. Pattern per transaction:
        DATE          (DD-MM-YY)
        TIME          (HH:MM)
        DESCRIPTION   (รับโอนเงิน / โอนเงิน / ...)
    Then a separate values block:
        OPENING_BAL   (alone)
        AMT1          (alone)
        BAL1 channel  (number + text)
        AMT2          (alone)
        BAL2 channel
        ...
    We match transactions to (amt, bal) pairs by position.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    DATE_RE = re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$')
    TIME_RE = re.compile(r'^\d{1,2}:\d{2}$')

    # Headers start at the FIRST date line in the document
    hdr_start = 0
    for i, line in enumerate(lines):
        if DATE_RE.match(line):
            hdr_start = i
            break
    # Values start AFTER the last column header "รายละเอียด" (so we skip the
    # 3 summary numbers — closing balance, total withdrawal, total deposit)
    val_start = hdr_start
    for i, line in enumerate(lines):
        if 'รายละเอียด' in line and i > 0:
            val_start = i + 1
            break

    hdr_data = lines[hdr_start:]
    val_data = lines[val_start:]
    data = hdr_data  # used by header extraction below

    def _is_num(s: str) -> bool:
        s = s.replace(',', '').replace(' ', '').lstrip('-')
        if not s:
            return False
        if s.count('.') > 1:
            last = s.rfind('.')
            s = s[:last].replace('.', '') + s[last:]
        try:
            float(s)
            return True
        except ValueError:
            return False

    # Phase 1: extract transaction headers (date, time, desc) in order
    headers = []
    i = 0
    while i < len(data):
        if DATE_RE.match(data[i]):
            d_obj = _parse_date(data[i])
            if d_obj is None:
                i += 1
                continue
            time_str = ''
            desc = ''
            j = i + 1
            if j < len(data) and TIME_RE.match(data[j]):
                time_str = data[j]
                j += 1
            if j < len(data) and not DATE_RE.match(data[j]):
                first_tok = data[j].split()[0] if data[j].split() else ''
                if not _is_num(first_tok):
                    desc = data[j]
                    j += 1
            headers.append({'date': d_obj, 'time': time_str, 'desc': desc})
            i = j
        else:
            i += 1

    if not headers:
        return [], 0.0, 0.0

    # Phase 2: extract value sequence (num-only vs num+text lines) from val_data
    values = []
    for line in val_data:
        toks = line.split()
        if not toks:
            continue
        v = _to_float(toks[0])
        if v is None:
            continue
        if len(toks) == 1:
            values.append(('num', v, ''))
        else:
            rest = ' '.join(toks[1:])
            values.append(('bal', v, rest))

    # Phase 3: pattern-match opening then alternating amt/bal
    opening = 0.0
    pairs = []
    state = 'opening'
    cur_amt = None
    for kind, val, rest in values:
        if state == 'opening':
            if kind == 'num':
                opening = val
                state = 'amt'
        elif state == 'amt':
            if kind == 'num':
                cur_amt = val
                state = 'bal'
        elif state == 'bal':
            if kind == 'bal':
                pairs.append((cur_amt, val, rest))
                cur_amt = None
                state = 'amt'
            elif kind == 'num':
                cur_amt = val

    # Phase 4: drop first header if it's the opening (no time)
    if headers and not headers[0]['time']:
        headers = headers[1:]

    # Phase 5: build StatementRows by zipping headers with pairs
    rows: List[StatementRow] = []
    prev_balance = opening
    n = min(len(headers), len(pairs))
    for k in range(n):
        h = headers[k]
        amt, bal, channel = pairs[k]
        if amt is None or bal is None:
            continue
        diff = round(bal - prev_balance, 2)
        wd = 0.0
        dep = 0.0
        if abs(diff - amt) <= AMOUNT_TOL:
            dep = amt
        elif abs(diff + amt) <= AMOUNT_TOL:
            wd = amt
        else:
            text_blob = (h['desc'] + ' ' + channel).lower()
            if ('รับโอน' in text_blob) or ('ฝาก' in text_blob and 'ฝากด้วยเช็ค' not in text_blob):
                dep = amt
            elif ('โอนเงิน' in text_blob) or ('ถอน' in text_blob) or ('จ่าย' in text_blob):
                wd = amt
            else:
                if diff > 0:
                    dep = amt
                else:
                    wd = amt
        prev_balance = bal
        full_desc = h['desc']
        if channel:
            full_desc = (full_desc + ' ' + channel).strip()
        rows.append(StatementRow(
            date=h['date'],
            description=full_desc,
            withdrawal=wd,
            deposit=dep,
            balance=bal,
        ))

    closing = rows[-1].balance if rows else 0.0
    return rows, opening, closing


def parse_bank_statement_pdf(
    file_bytes: bytes, filename: str, api_key: str = ""
) -> Dict[str, Any]:
    """
    Parse a bank statement PDF.
    Strategy: (1) safe text extraction (2) pdfplumber tables (3) text-line fallback (4) Gemini
    """
    # ── Step 1: extract text safely (immune to pdfplumber KeyError crash) ──
    page_texts = _pdf_extract_text_safe(file_bytes)
    all_text = "\n".join(page_texts)
    bank_code = _detect_bank(all_text) if all_text.strip() else "generic"
    # DEBUG v118.33.11.1
    logger.info(f"[stmt_parse][{filename}] pages={len(page_texts)} chars={len(all_text)} bank={bank_code}")
    if all_text.strip(): logger.info(f"[stmt_parse][{filename}] first600: " + repr(all_text[:600]))
    if all_text.strip():
        try:
            import os
            os.makedirs('/tmp/stmt_debug', exist_ok=True)
            with open(f'/tmp/stmt_debug/{filename}.txt', 'w') as _df:
                _df.write(all_text)
        except Exception: pass

    # ── Step 2: try pdfplumber table extraction ──
    all_tables: List = []
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not all_text.strip():
                all_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                bank_code = _detect_bank(all_text)
            for p in pdf.pages:
                try:
                    tbls = p.extract_tables() or []
                    all_tables.extend(tbls)
                except Exception:
                    pass  # 该页 extract_tables 失败 · 跳过(每页容错)
    except Exception as e:
        logger.warning(f"pdfplumber stmt [{filename}] skipped: {e}")

    # ── Step 3: table-based parsing ──
    rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0

    if all_tables:
        if bank_code == "kbank":
            rows, opening, closing = _parse_kbank_pages(all_tables)
        elif bank_code == "bbl":
            rows, opening, closing = _parse_bbl_pages(all_tables)
        else:
            rows, opening, closing = _parse_generic_pages(all_tables)

        if len(rows) < MIN_PLUMBER_ROWS and bank_code == "generic":
            rows2, op2, cl2 = _parse_kbank_pages(all_tables)
            if len(rows2) > len(rows):
                rows, opening, closing = rows2, op2, cl2

    # ── Step 4a: KBank column-stacked text (pdfminer-extracted) ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip() and bank_code == 'kbank':
        col_rows, col_op, col_cl = _parse_kbank_text_columns(all_text)
        logger.info(f"[stmt_parse][{filename}] step4a kbank-columns: rows={len(col_rows)}")
        if len(col_rows) > len(rows):
            rows, opening, closing = col_rows, col_op, col_cl
    # ── Step 4b: generic text-line fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip():
        text_rows, text_op, text_cl = _parse_stmt_text_lines(all_text, bank_code)
        logger.info(f"[stmt_parse][{filename}] step4b text-line: tbl_rows={len(rows)} text_rows={len(text_rows)} bank={bank_code}")
        if len(text_rows) > len(rows):
            rows, opening, closing = text_rows, text_op, text_cl

    # ── Step 5: Gemini fallback (OCR for scanned PDFs) ──
    if len(rows) < MIN_PLUMBER_ROWS:
        logger.info(f"[stmt_parse][{filename}] step5 gemini: api_key_present={bool(api_key)} text_chars={len(all_text)}")
    if len(rows) < MIN_PLUMBER_ROWS and api_key:
        gemini_result = _gemini_parse_statement(file_bytes, filename, api_key)
        logger.info(f"[stmt_parse][{filename}] step5 gemini result: ok={gemini_result.get('ok')} rows={len(gemini_result.get('rows', []))}")
        if gemini_result.get("ok") and gemini_result.get("rows"):
            rows = gemini_result["rows"]
            opening = gemini_result.get("opening", opening)
            closing = gemini_result.get("closing", closing)
            bank_code = gemini_result.get("bank_code", bank_code)

    for r in rows:
        r.source_file = filename

    # v118.33.13.0 · row-by-row balance arithmetic verification
    # For each row: prev_balance + deposit - withdrawal should equal current balance.
    # If it doesn't, set balance_ok=False so the UI can flag for human review.
    _verify_row_balances(rows, opening)
    balance_warn_count = sum(1 for r in rows if r.balance_ok is False)
    low_conf_count = sum(1 for r in rows if r.confidence == "low")
    if balance_warn_count or low_conf_count:
        logger.info(
            f"[stmt_parse][{filename}] verification: "
            f"balance_warn={balance_warn_count} low_conf={low_conf_count} total={len(rows)}"
        )

    if not rows:
        hint = " (PDF has no extractable text)" if not all_text.strip() else ""
        return {"ok": False, "error": f"No statement rows found in PDF{hint}",
                "rows": [], "opening": 0.0, "closing": 0.0}

    return {
        "ok": True,
        "rows": rows,
        "opening": opening,
        "closing": closing,
        "bank_code": bank_code,
        "row_count": len(rows),
        "balance_warn_count": balance_warn_count,
        "low_conf_count": low_conf_count,
    }


def _verify_row_balances(rows: List[StatementRow], opening: float) -> None:
    """Walk rows in order; for each row check whether
        prev_balance + deposit - withdrawal == row.balance (within AMOUNT_TOL).
    Sets row.balance_ok = True / False / None (None when cannot verify).
    Operates in-place. Tolerance accommodates rounding (0.05).

    v118.33.13.1 · Skip rows that have NO movement (deposit=0 AND withdrawal=0).
    These are typically the opening-balance row ("ยอดยกมา"/"brought forward"),
    a closing-balance row, or a section header — they don't represent a
    transaction and shouldn't be verified. balance_ok is set to None, and we
    still update prev=row.balance so subsequent rows verify against it."""
    if not rows:
        return
    _OPENING_KW = ("ยอดยกมา", "ยอดคงเหลือยกมา", "brought forward",
                   "opening balance", "balance b/f", "期初余额", "上期结转")
    prev = opening
    for r in rows:
        if r.balance is None:
            r.balance_ok = None
            continue
        dep = r.deposit or 0
        wd  = r.withdrawal or 0
        desc_low = (r.description or "").lower()
        is_opening_row = any(kw in r.description for kw in _OPENING_KW) or \
                         any(kw in desc_low for kw in (k.lower() for k in _OPENING_KW))
        # No-movement rows (opening/closing/headers) — record balance, skip verify
        if (dep == 0 and wd == 0) or is_opening_row:
            r.balance_ok = None
            prev = r.balance
            continue
        expected = round(prev + dep - wd, 2)
        diff = abs(expected - r.balance)
        amt = max(abs(dep), abs(wd))
        tol = min(max(AMOUNT_TOL, amt * 0.005), 1.0)
        r.balance_ok = diff <= tol
        prev = r.balance


def _gemini_parse_statement(file_bytes: bytes, filename: str, api_key: str) -> Dict[str, Any]:
    """
    Gemini fallback: extract bank statement data from scanned PDF.
    Returns {ok, rows, opening, closing, bank_code}.

    v118.33.13.1 · Caches by SHA-256(file_bytes). Same PDF re-uploaded skips the
    API call entirely. Uses gemini-2.5-flash-lite (faster + cheaper than 2.5-flash).
    """
    # Check cache first — instant return if same PDF was OCR'd before
    cache_key = hashlib.sha256(file_bytes).hexdigest()
    cached = _cache_get(_GEMINI_STMT_CACHE, cache_key)
    if cached is not None:
        logger.info(f"[stmt_parse][{filename}] gemini cache HIT key={cache_key[:12]}")
        # Re-materialize StatementRow objects (cache stores dicts)
        rebuilt = []
        for d in cached.get("_rows_raw", []):
            rebuilt.append(StatementRow(
                date=_parse_date(d["date"]) if d.get("date") else None,
                description=d.get("description", ""),
                withdrawal=float(d.get("withdrawal", 0) or 0),
                deposit=float(d.get("deposit", 0) or 0),
                balance=float(d.get("balance", 0) or 0),
                confidence=d.get("confidence", "high"),
            ))
        return {
            "ok": cached.get("ok", True),
            "rows": rebuilt,
            "opening": cached.get("opening", 0.0),
            "closing": cached.get("closing", 0.0),
            "bank_code": cached.get("bank_code", "generic"),
        }
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)
        # gemini-2.5-flash-lite: faster + cheaper for OCR tasks (~2x faster than 2.5-flash)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        b64 = base64.b64encode(file_bytes).decode()
        # v118.33.13.0 · strict accounting-grade prompt — no guessing, no hallucination
        prompt = (
            "You are extracting bank statement data from a scanned PDF for FINANCIAL "
            "RECONCILIATION. Wrong digits cause hours of debugging — accuracy beats "
            "completeness.\n"
            "\n"
            "CRITICAL ACCURACY RULES:\n"
            "1. NEVER guess or fill in unclear digits. If a number is blurry, partially "
            "obscured, ambiguous, or you cannot read it with FULL confidence, return null "
            "for that field and mark confidence='low'.\n"
            "2. NEVER infer values from context — do NOT 'fix' balance math by adjusting "
            "amounts. Extract exactly what is printed, even if the math looks wrong.\n"
            "3. NEVER add rows that aren't clearly visible. If you're unsure whether a row "
            "exists at all, skip it.\n"
            "4. Thai number formats: '115.586,50' and '115,586.50' both mean 115586.50. "
            "'115.586.50' (dot thousands separator) also means 115586.50.\n"
            "5. withdrawal and deposit are MUTUALLY EXCLUSIVE — one is the amount, the "
            "other must be 0.\n"
            "\n"
            "Return JSON only (no markdown fences) with this exact schema:\n"
            "{\n"
            '  "bank_code": "kbank"|"bbl"|"kkp"|"ktb"|"scb"|"generic",\n'
            '  "opening_balance": number|null,\n'
            '  "closing_balance": number|null,\n'
            '  "rows": [{"date":"YYYY-MM-DD"|null, "description":"text exactly as printed",'
            '"withdrawal":number|null, "deposit":number|null, "balance":number|null,'
            '"confidence":"high"|"medium"|"low"}]\n'
            "}\n"
            "Mark confidence='low' if ANY field in the row required interpretation of "
            "unclear characters. Mark confidence='medium' if mostly clear but you had "
            "minor doubts. Mark 'high' only when every digit is unambiguous."
        )
        resp = model.generate_content([
            {"mime_type": "application/pdf", "data": b64},
            prompt,
        ])
        text = (resp.text or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
        data = json.loads(text)

        raw_rows = data.get("rows") or []
        rows = []
        _OPENING_KW = ("ยอดยกมา", "brought forward", "opening balance",
                       "balance b/f", "期初余额", "上期结转")
        # If Gemini missed opening_balance, try to recover from the first no-movement row
        opening_extracted = float(data.get("opening_balance", 0) or 0)
        for r in raw_rows:
            d = _parse_date(str(r.get("date", "")))
            if d is None:
                continue
            wd_raw = r.get("withdrawal")
            dep_raw = r.get("deposit")
            bal_raw = r.get("balance")
            desc = str(r.get("description", ""))
            conf = (r.get("confidence") or "high").lower()
            if conf not in ("high", "medium", "low"):
                conf = "high"
            if wd_raw is None and dep_raw is None:
                conf = "low"
            if bal_raw is None:
                conf = "low"
            wd_v  = float(wd_raw or 0)
            dep_v = float(dep_raw or 0)
            bal_v = float(bal_raw or 0)
            # v118.33.13.1 · Detect opening-balance row: no movement + keyword
            is_opening = (wd_v == 0 and dep_v == 0) and any(
                kw in desc or kw in desc.lower() for kw in _OPENING_KW
            )
            if is_opening:
                # Use as opening balance; do NOT create as transaction row
                if not opening_extracted and bal_v:
                    opening_extracted = bal_v
                continue
            rows.append(StatementRow(
                date=d,
                description=desc,
                withdrawal=wd_v,
                deposit=dep_v,
                balance=bal_v,
                confidence=conf,
            ))

        result_closing = float(data.get("closing_balance", 0) or 0)
        result_bank = data.get("bank_code", "generic")
        # v118.33.13.1 · Save raw row dicts to cache (StatementRow has datetime — store str)
        try:
            _cache_put(_GEMINI_STMT_CACHE, cache_key, {
                "ok": True,
                "opening": opening_extracted,
                "closing": result_closing,
                "bank_code": result_bank,
                "_rows_raw": [
                    {"date": rr.date.isoformat() if rr.date else None,
                     "description": rr.description,
                     "withdrawal": rr.withdrawal,
                     "deposit": rr.deposit,
                     "balance": rr.balance,
                     "confidence": rr.confidence}
                    for rr in rows
                ],
            })
            logger.info(f"[stmt_parse][{filename}] gemini cache STORED key={cache_key[:12]} rows={len(rows)}")
        except Exception as _e:
            logger.warning(f"[stmt_parse][{filename}] cache store failed: {_e}")

        return {
            "ok": True,
            "rows": rows,
            "opening": opening_extracted,
            "closing": result_closing,
            "bank_code": data.get("bank_code", "generic"),
        }

    except Exception as e:
        logger.warning(f"_gemini_parse_statement failed: {e}")
        return {"ok": False, "rows": []}


# ─────────────────────────────────────────────────────────────────────────────
# GL PARSERS
# ─────────────────────────────────────────────────────────────────────────────
_GL_DATE_H  = {"วันที่", "date", "วัน", "日期"}
_GL_DOC_H   = {"ใบสำคัญ", "เลขที่เอกสาร", "doc", "voucher", "reference", "เอกสาร", "凭证", "ref"}
_GL_DESC_H  = {"คำอธิบาย", "รายการ", "description", "detail", "รายละเอียด", "摘要"}
_GL_DEBIT_H = {"เดบิต", "เดบิท", "debit", "dr", "借方", "ถอน", "จ่าย"}
_GL_CRED_H  = {"เครดิต", "credit", "cr", "贷方", "ฝาก", "รับ"}
_GL_ACCT_H  = {"รหัสบัญชี", "account", "gl account", "เลขที่บัญชี", "รหัส", "账号", "科目"}

_ACCT_RE = re.compile(r'(?<![\d.])([1-9]\d{3,6}(?:[-–]\d{2,3})?)(?![\d.])')


def _hit(header: str, hints: set) -> bool:
    h = str(header or "").strip().lower()
    return any(hint.lower() in h for hint in hints)


def _map_gl_cols(header_row: List) -> Dict[str, int]:
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


def _extract_acct_code(text: str) -> str:
    m = _ACCT_RE.search(str(text or ""))
    return m.group(1) if m else ""


def parse_gl_excel(
    file_bytes: bytes, filename: str, account_code: str = ""
) -> Dict[str, Any]:
    """
    Parse GL from Excel file.
    Returns {ok, rows, accounts, opening, closing, row_count, error}
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        all_rows_raw = list(ws.values)
    except Exception:
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=file_bytes)
            ws = wb.sheet_by_index(0)
            all_rows_raw = [ws.row_values(i) for i in range(ws.nrows)]
        except Exception as e:
            return {"ok": False, "error": f"Cannot read Excel: {e}"}

    # Find header row (within first 10 rows)
    header_idx = 0
    col_map: Dict[str, int] = {}
    for i, row in enumerate(all_rows_raw[:10]):
        row_list = [str(c or "").strip() for c in row]
        cm = _map_gl_cols(row_list)
        if len(cm) >= 3:  # at least date + (debit or credit) + something
            col_map = cm
            header_idx = i
            break

    if not col_map:
        return {"ok": False, "error": "Cannot detect GL column headers"}

    rows = []
    accounts_seen = set()
    opening = 0.0
    closing = 0.0
    gl_opening_found = False
    last_row_date = None  # carry-forward for blank date cells (Mr.erp style)

    for row in all_rows_raw[header_idx + 1:]:
        if not any(row):
            continue
        row_list = [str(c or "").strip() for c in row]
        if _is_gl_skip_row(row_list):
            # Check if this is an opening/closing balance row
            desc_idx = col_map.get("description", col_map.get("doc_no", -1))
            desc = row_list[desc_idx] if desc_idx >= 0 and desc_idx < len(row_list) else ""
            if any(kw in desc.lower() for kw in ["ยอดยกมา", "brought forward", "opening"]):
                cr_idx = col_map.get("credit", -1)
                dr_idx = col_map.get("debit", -1)
                if cr_idx >= 0 and cr_idx < len(row_list):
                    cr = _to_float(row_list[cr_idx])
                    dr = _to_float(row_list[dr_idx] if dr_idx >= 0 and dr_idx < len(row_list) else 0)
                    opening = cr - dr  # net opening
                    gl_opening_found = True
            continue

        # Extract fields
        d_str = row_list[col_map["date"]] if "date" in col_map and col_map["date"] < len(row_list) else ""
        d = _parse_date(d_str) if d_str else None
        if d is not None:
            last_row_date = d
        elif last_row_date is not None:
            d = last_row_date  # carry-forward blank date (Mr.erp prints date once per day)
        else:
            continue

        doc_no = row_list[col_map["doc_no"]] if "doc_no" in col_map and col_map["doc_no"] < len(row_list) else ""
        desc = row_list[col_map["description"]] if "description" in col_map and col_map["description"] < len(row_list) else ""
        debit = _to_float(row_list[col_map["debit"]] if "debit" in col_map and col_map["debit"] < len(row_list) else 0)
        credit = _to_float(row_list[col_map["credit"]] if "credit" in col_map and col_map["credit"] < len(row_list) else 0)

        # Account code: from column or auto-extract from description
        acct = ""
        if "account" in col_map and col_map["account"] < len(row_list):
            acct = str(row_list[col_map["account"]]).strip()
        if not acct:
            acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)

        if debit == 0.0 and credit == 0.0:
            continue

        # Filter by account_code if specified
        if account_code and acct and not acct.startswith(account_code):
            continue

        accounts_seen.add(acct or "?")
        rows.append(GlRow(
            date=d, doc_no=doc_no, account_code=acct,
            description=desc, debit=abs(debit), credit=abs(credit),
        ))

    # Calculate opening/closing if not found
    if not gl_opening_found:
        opening = 0.0
    total_credit = sum(r.credit for r in rows)
    total_debit = sum(r.debit for r in rows)
    closing = round(opening + total_credit - total_debit, 2)

    return {
        "ok": True,
        "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening,
        "closing": closing,
        "row_count": len(rows),
    }


def _pdf_extract_text_safe(file_bytes: bytes) -> List[str]:
    """
    Extract text from PDF without crashing on malformed metadata.
    Tries pdfminer first (no KeyError('date') bug), then pdfplumber, then pypdf.
    Returns list of page text strings.
    """
    # pdfminer is a dependency of pdfplumber and doesn't have the KeyError('date') bug
    try:
        from pdfminer.high_level import extract_text as _pm_extract
        text = _pm_extract(io.BytesIO(file_bytes)) or ""
        if text.strip():
            return [text]
    except Exception:
        pass  # pdfminer 失败 · 走 pypdf 兜底
    # pypdf fallback
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return [pg.extract_text() or "" for pg in reader.pages]
    except Exception:
        pass  # pypdf 也失败 · 返回空列表 · 调用方走 Gemini 视觉兜底
    return []


def _norm_thai(s: str) -> str:
    """v118.33.13.4 · Normalize Thai PUA characters that some PDF fonts emit
    instead of the standard Unicode codepoints. Thai PDFs encode combining
    tone marks in the Private Use Area (U+F70A..U+F712) rather than the
    standard U+0E47..U+0E4D range. The text renders identically but compares
    as a different string, breaking any keyword match against book types
    or other Thai tokens. Maps PUA glyphs back to standard combining marks."""
    if not s:
        return s
    return (s
             .replace("\uf70a", "\u0e48")   # mai-ek
             .replace("\uf70b", "\u0e49")   # mai-tho
             .replace("\uf70c", "\u0e4a")   # mai-tri
             .replace("\uf70d", "\u0e4b")   # mai-chattawa
             .replace("\uf70e", "\u0e4c")   # thantakhat
             .replace("\uf710", "\u0e4d")   # nikhahit
             .replace("\uf711", "\u0e31")   # mai-han-akat
             .replace("\uf712", "\u0e47")   # mai-taikhu
            )

def _is_numeric_tok(tok: str) -> bool:
    """v118.33.13.4 · Strict numeric-token test (unlike _to_float which returns 0.0
    for any garbage input). Accepts comma thousands, paren-negatives, Thai
    dot-thousands ('115.586.50' → 115586.50). Rejects dates, text, dashes, empty."""
    s = (tok or "").strip().replace(",", "")
    if not s or s in {"-", "–", "—"}:
        return False
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    if s.startswith("-"):
        s = s[1:]
    if not s:
        return False
    if s.count(".") > 1:
        last = s.rfind(".")
        s = s[:last].replace(".", "") + s[last:]
    try:
        float(s)
        return True
    except ValueError:
        return False


def _parse_gl_mrerp_table(table_rows, account_code: str = "") -> Tuple[List["GlRow"], List[str], float]:
    """
    v118.33.13.4 · Parse Mr.erp-style Thai GL PDFs where pdfplumber outputs
    each transaction as a SINGLE merged cell containing the whole row text.

    Row format:
        DD/MM/YY  สมุด  ใบสำคัญ  คำอธิบาย  เดบิท/เครดิต  ยอดคงเหลือ
        (date)    (book)(voucher) (desc...) (amount)      (balance)

    Book types: "รับ"=receipt→debit, "จ่าย"=payment→credit, "ทั่วไป"=general
    (general direction inferred from running-balance delta).

    Special rows:
        • Account header: "1112-01 CA K-BANK006-8-83962-9 ... 215,228.06" → opening
        • Totals/dividers/page-headers → skipped
        • Date is printed only when it changes — subsequent same-day rows omit it
    """
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0
    last_date: Optional[date] = None
    last_balance: Optional[float] = None
    current_acct = ""

    DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
    BOOK_RECEIPT = "รับ"
    BOOK_PAYMENT = "จ่าย"
    BOOK_GENERAL = "ทั่วไป"
    BOOK_TYPES = {BOOK_RECEIPT, BOOK_PAYMENT, BOOK_GENERAL}
    # Header / footer / divider patterns to skip.
    # NB: keywords like "หน้า" (page) appear as a substring inside legitimate
    # transaction descriptions (e.g. "รับล่วงหน้า" = "advance receipt"), so we
    # only use phrase-level patterns that are unique to header/footer rows.
    SKIP_KEYWORDS = (
        "รายงานแยกประเภท", "(รวมแผนก)", "วันที่จาก", "เลขที่บัญชี",
        "รวมทั้งสิ้น", "หมายเหตุ ในช่อง",
        "ชื่อบัญชี", ">>>>", "<<<<",
    )
    # Page header pattern: "หน้า : 1" (always has the colon)
    SKIP_REGEX = re.compile(r"หน้า\s*[:：]\s*\d|^\s*Page\s+\d|^E\s+จะหมายถึง")

    for table_row in (table_rows or []):
        # Each pdfplumber row is a list of cells. For Mr.erp PDFs the whole
        # transaction is in cell 0; cells 1+ are typically None or fragments.
        cells = [str(c).strip() for c in table_row if c is not None and str(c).strip()]
        if not cells:
            continue
        # v118.33.13.4 · Normalize Thai PUA tone-marks so book-type matches work
        line = _norm_thai(" ".join(cells).strip())
        if not line:
            continue

        # Skip pure dividers
        if re.match(r"^-+\s*-*$|^=+\s*=*$|^_+$", line):
            continue
        # Skip headers/footers/notes
        if any(kw in line for kw in SKIP_KEYWORDS):
            continue
        if SKIP_REGEX.search(line):
            continue
        # Skip the column-header row
        if ("วันที่" in line and "สมุด" in line) or ("เดบิท" in line and "เครดิต" in line and "ยอดคงเหลือ" in line):
            continue
        # Skip pure totals rows: "รวม 1,689,872.00 1,780,000.00" or two numbers only
        if line.startswith("รวม") and len(line.split()) <= 6:
            continue
        if re.match(r"^[\d,]+\.\d+(\s+[\d,]+\.\d+)+\s*$", line):
            continue

        # Account header: "1112-01 CA K-BANK006-8-83962-9 ... 215,228.06"
        # Starts with N-N digits where N is 3-6 digits and a dash
        m_acct = re.match(r"^(\d{3,6}-\d+)\s+", line)
        if m_acct:
            current_acct = m_acct.group(1)
            accounts_seen.add(current_acct)
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums and not opening:
                opening = _to_float(nums[-1])
                last_balance = opening
            continue
        # Opening-balance keyword line
        if any(kw in line for kw in ("ยอดยกมา", "brought forward", "ยอดคงเหลือยกมา")):
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums:
                opening = _to_float(nums[-1])
                last_balance = opening
            continue

        # Tokenize on whitespace
        toks = line.split()
        if len(toks) < 4:
            continue

        # Collect contiguous numeric tokens at the RIGHT (strict check — NOT _to_float)
        num_vals: List[float] = []
        cut_idx = len(toks)
        for i in range(len(toks) - 1, -1, -1):
            if _is_numeric_tok(toks[i]):
                num_vals.insert(0, _to_float(toks[i]))
                cut_idx = i
            else:
                break
        if len(num_vals) < 2:
            continue

        balance = num_vals[-1]
        amount = num_vals[-2]
        # If 3 numerics: [debit, credit, balance] explicit format
        explicit_debit = None
        explicit_credit = None
        if len(num_vals) >= 3:
            explicit_debit = num_vals[-3]
            explicit_credit = num_vals[-2]

        # Parse front: DATE? BOOK VOUCHER DESC...
        front = toks[:cut_idx]
        if not front:
            continue

        d: Optional[date] = None
        d_idx = -1
        if DATE_RE.match(front[0]):
            d = _parse_date(front[0])
            if d:
                d_idx = 0
        if d is None:
            d = last_date
        else:
            last_date = d
        if d is None:
            continue

        after = front[d_idx + 1:] if d_idx >= 0 else front
        if not after:
            continue

        # Book type (อาจมีหรือไม่มี)
        book = ""
        if after[0] in BOOK_TYPES:
            book = after[0]
            after = after[1:]
        if not after:
            continue

        # Voucher number + description (everything else)
        doc_no = after[0]
        desc = " ".join(after[1:]) if len(after) > 1 else ""

        # Determine direction
        if explicit_debit is not None and explicit_credit is not None:
            debit_v = explicit_debit
            credit_v = explicit_credit
        else:
            debit_v = 0.0
            credit_v = 0.0
            if book == BOOK_RECEIPT:
                debit_v = amount
            elif book == BOOK_PAYMENT:
                credit_v = amount
            else:
                # General/unknown: infer from balance delta
                if last_balance is not None:
                    delta = round(balance - last_balance, 2)
                    if abs(delta - amount) <= 0.05:
                        debit_v = amount
                    elif abs(delta + amount) <= 0.05:
                        credit_v = amount
                    else:
                        # Math doesn't pin down direction — default to debit
                        debit_v = amount
                else:
                    debit_v = amount  # default: cash-in

        last_balance = balance

        acct = current_acct or _extract_acct_code(doc_no) or _extract_acct_code(desc) or ""
        if account_code and acct and not acct.startswith(account_code):
            continue
        if debit_v == 0.0 and credit_v == 0.0:
            continue

        accounts_seen.add(acct or "?")
        rows.append(GlRow(
            date=d, doc_no=doc_no, account_code=acct,
            description=desc, debit=abs(debit_v), credit=abs(credit_v),
        ))

    return rows, sorted(accounts_seen - {"?"}), opening


def _gl_direction_sanity_check(rows: List["GlRow"]) -> Optional[str]:
    """v118.33.13.4 · Detect GL files that are clearly NOT a cash-account ledger.

    Bank-reconciliation requires the **cash/bank account** GL — where deposits
    appear as debits and withdrawals as credits. If the user uploads an
    expense-perspective ledger (everything in debit) or revenue-perspective
    (everything in credit), reconciliation will produce 0% match.

    Returns a warning message string if the GL looks one-sided, else None."""
    if not rows or len(rows) < 3:
        return None
    total_debit = sum(r.debit for r in rows)
    total_credit = sum(r.credit for r in rows)
    if total_debit + total_credit == 0:
        return None
    debit_ratio = total_debit / (total_debit + total_credit)
    n_debit = sum(1 for r in rows if r.debit > 0)
    n_credit = sum(1 for r in rows if r.credit > 0)

    # All on one side (no opposite transactions at all)
    if total_credit == 0 and n_debit >= 3:
        return ("GL appears to be debit-only (no credit entries). This is likely "
                "an expense or asset ledger, not the cash/bank account ledger. "
                "Bank reconciliation expects the BANK ACCOUNT ledger where "
                "withdrawals appear as credits.")
    if total_debit == 0 and n_credit >= 3:
        return ("GL appears to be credit-only (no debit entries). This is likely "
                "a revenue or liability ledger, not the cash/bank account ledger.")
    # Heavily imbalanced (>= 95% one side) — less certain but worth noting
    if debit_ratio >= 0.95 and total_credit > 0:
        return f"GL is {debit_ratio*100:.0f}% debit-side — verify this is the bank-account ledger."
    if debit_ratio <= 0.05 and total_debit > 0:
        return f"GL is {(1-debit_ratio)*100:.0f}% credit-side — verify this is the bank-account ledger."
    return None


def parse_gl_pdf(
    file_bytes: bytes, filename: str, account_code: str = "", api_key: str = ""
) -> Dict[str, Any]:
    """
    Parse GL from PDF.
    Strategy: (1) extract text safely via pdfminer/pypdf (immune to KeyError('date'))
              (2) try pdfplumber table extraction (may crash on some PDFs — fully isolated)
              (3) Mr.erp-format single-cell row parser (v118.33.13.4)
              (3b) Old column-mapping table parser (fallback)
              (4) Text-line parser fallback
              (5) Gemini fallback if api_key provided
    """
    # ── Step 1: extract raw text independently (never crashes the whole function) ──
    page_texts = _pdf_extract_text_safe(file_bytes)

    # ── Step 2: try pdfplumber table extraction (fully isolated) ──
    all_tables: List = []
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pdf.pages:
                try:
                    tbls = p.extract_tables() or []
                    all_tables.extend(tbls)
                except Exception:
                    pass  # 该页 extract_tables 失败 · 跳过(每页容错)
                if not page_texts:
                    try:
                        page_texts.append(p.extract_text() or "")
                    except Exception:
                        pass  # 该页 extract_text 失败 · 跳过(每页容错)
    except Exception as e:
        logger.warning(f"pdfplumber [{filename}] skipped: {e}")

    # ── Step 3: parse table rows ──
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0

    # v118.33.13.4 · Step 3a · Mr.erp single-cell-row parser (FIRST priority)
    # Many Thai GL PDFs come out of pdfplumber as one merged cell per row
    # containing the entire transaction text. The old per-column mapper can't
    # see headers because everything's in cell 0. We handle that here.
    if all_tables:
        flat_rows = []
        for tbl in all_tables:
            flat_rows.extend(tbl or [])
        mr_rows, mr_accts, mr_open = _parse_gl_mrerp_table(flat_rows, account_code)
        if mr_rows:
            rows = mr_rows
            accounts_seen = set(mr_accts)
            opening = mr_open
            logger.info(f"[gl_parse][{filename}] step3a mrerp: rows={len(rows)} accts={len(accounts_seen)}")

    # Step 3b · Fall back to column-mapped table parser (other GL formats where
    # pdfplumber DOES split columns correctly)
    if not rows:
        for table in all_tables:
            if not table or len(table) < 2:
                continue
            col_map: Dict[str, int] = {}
            header_idx = 0
            for i, row in enumerate(table[:5]):
                cm = _map_gl_cols([str(c or "").strip() for c in row])
                if len(cm) >= 2:
                    col_map = cm
                    header_idx = i
                    break
            if not col_map:
                continue

            last_tbl_date = None
            for row in table[header_idx + 1:]:
                if not row:
                    continue
                row_list = [str(c or "").strip() for c in row]
                if _is_gl_skip_row(row_list):
                    continue
                d_str = row_list[col_map["date"]] if "date" in col_map and col_map["date"] < len(row_list) else ""
                d = _parse_date(d_str) if d_str else None
                if d is not None:
                    last_tbl_date = d
                elif last_tbl_date is not None:
                    d = last_tbl_date
                else:
                    continue
                doc_no = row_list[col_map["doc_no"]] if "doc_no" in col_map and col_map["doc_no"] < len(row_list) else ""
                desc = row_list[col_map["description"]] if "description" in col_map and col_map["description"] < len(row_list) else ""
                debit = _to_float(row_list[col_map["debit"]] if "debit" in col_map and col_map["debit"] < len(row_list) else 0)
                credit = _to_float(row_list[col_map["credit"]] if "credit" in col_map and col_map["credit"] < len(row_list) else 0)
                acct = ""
                if "account" in col_map and col_map["account"] < len(row_list):
                    acct = str(row_list[col_map["account"]]).strip()
                if not acct:
                    acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)
                if debit == 0.0 and credit == 0.0:
                    continue
                if account_code and acct and not acct.startswith(account_code):
                    continue
                accounts_seen.add(acct or "?")
                rows.append(GlRow(date=d, doc_no=doc_no, account_code=acct,
                                  description=desc, debit=abs(debit), credit=abs(credit)))
        if rows:
            logger.info(f"[gl_parse][{filename}] step3b col-map: rows={len(rows)} accts={len(accounts_seen)}")

    # ── Step 4: text-line fallback (Mr.erp Thai GL format) ──
    if len(rows) < MIN_PLUMBER_ROWS and page_texts:
        full_text = "\n".join(page_texts)
        text_rows, text_accts, text_opening = _parse_gl_text_lines(full_text, account_code)
        if len(text_rows) >= len(rows):
            rows = text_rows
            accounts_seen = set(text_accts)
            opening = text_opening
            logger.info(f"[gl_parse][{filename}] step4 text-line: rows={len(rows)}")

    # ── Step 5: Gemini fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and api_key:
        return _gemini_parse_gl(file_bytes, filename, account_code, api_key)

    if not rows:
        hint = " (PDF has no extractable text)" if not any(t.strip() for t in page_texts) else ""
        return {"ok": False, "error": f"No GL rows found in PDF{hint}", "rows": []}

    total_credit = sum(r.credit for r in rows)
    total_debit = sum(r.debit for r in rows)
    closing = round(opening + total_debit - total_credit, 2)

    # v118.33.13.4 · Direction sanity check — warn when GL is one-sided
    direction_warning = _gl_direction_sanity_check(rows)
    if direction_warning:
        logger.warning(f"[gl_parse][{filename}] {direction_warning}")
    result = {
        "ok": True, "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening, "closing": closing, "row_count": len(rows),
    }
    if direction_warning:
        result["warning"] = direction_warning
    return result


def _parse_gl_text_lines(
    text: str, account_code: str = ""
) -> Tuple[List[GlRow], List[str], float]:
    """
    Text-line fallback for Mr.erp Thai GL PDFs.
    Format: วันที่  สมุด  ใบสำคัญ  คำอธิบาย  เดบิต  เครดิต  สถานะ  ยอดคงเหลือ
    Date is printed once per day; subsequent same-day rows have blank date.
    Returns (rows, account_list, opening_balance).
    """
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0
    last_date: Optional[date] = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip header/report title/total lines
        low = line.lower()
        if any(kw in low for kw in ["รายงาน", "account", "page", "หน้า", "บัญชี:", "ชื่อ",
                                     "รวม", "total", "สรุป", "หมายเหตุ", "note"]):
            continue

        # Account code header: "1112-01 CA K-BANK006-8-83962-9 215,228.06"
        # Starts with 3-6 digits then dash (NOT a date like "02/06/68")
        if re.match(r'^\d{3,6}-\d', line):
            nums = re.findall(r'[\d,]+\.\d+', line)
            if nums and not opening:
                opening = _to_float(nums[-1])
            continue

        # Opening balance line
        if any(kw in line for kw in ["ยอดยกมา", "brought forward", "ยอดคงเหลือยกมา"]):
            nums = re.findall(r"[\d,]+\.\d+", line)
            if nums:
                opening = _to_float(nums[-1])
            continue

        # Split on 2+ whitespace to get token columns
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 3:
            continue

        # Try to identify date token (first or second part)
        d = None
        d_offset = 0
        for offset in range(min(2, len(parts))):
            d = _parse_date(parts[offset])
            if d is not None:
                d_offset = offset
                last_date = d
                break

        if d is None:
            if last_date is not None:
                d = last_date
                d_offset = -1  # no date token consumed
            else:
                continue

        # After date token, remaining parts: book, doc_no, description, amounts...
        rest = parts[d_offset + 1:] if d_offset >= 0 else parts
        if len(rest) < 2:
            continue

        # Find numeric tokens from the right, skipping D/C/DR/CR status tokens
        num_vals: List[float] = []
        num_start = len(rest)
        status_tok = ""
        for i in range(len(rest) - 1, -1, -1):
            tok = rest[i].strip()
            tok_up = tok.upper()
            # Capture status token (D/C/DR/CR) but don't break
            if tok_up in ("D", "C", "DR", "CR") and not status_tok:
                status_tok = tok_up
                continue
            tok_clean = tok.replace(",", "")
            if re.match(r"^\d+(\.\d+)?$", tok_clean):
                num_vals.insert(0, float(tok_clean))
                num_start = i
            elif len(num_vals) > 0:
                break

        # Need at least 2 numerics (amount + balance, or debit + credit + balance)
        if len(num_vals) < 2:
            continue

        # Determine debit/credit using status token or positional heuristic
        debit = credit = 0.0
        if status_tok in ("D", "DR"):
            # Amount is debit; last numeric is balance, second-to-last is amount
            debit = num_vals[-2]
            credit = 0.0
        elif status_tok in ("C", "CR"):
            credit = num_vals[-2]
            debit = 0.0
        else:
            # No explicit status: 3 numerics → [debit, credit, balance]; 2 → [amount, balance]
            if len(num_vals) >= 3:
                debit = num_vals[-3]
                credit = num_vals[-2]
            else:
                # 2 numerics, no status — use first as debit (common for debit-only GL lines)
                debit = num_vals[-2]
                credit = 0.0

        if debit == 0.0 and credit == 0.0:
            continue

        desc_parts = rest[:num_start]
        doc_no = desc_parts[0] if desc_parts else ""
        desc = " ".join(desc_parts[1:]) if len(desc_parts) > 1 else doc_no

        acct = _extract_acct_code(doc_no) or _extract_acct_code(desc)
        if account_code and acct and not acct.startswith(account_code):
            continue

        accounts_seen.add(acct or "?")
        rows.append(GlRow(
            date=d, doc_no=doc_no, account_code=acct,
            description=desc, debit=abs(debit), credit=abs(credit),
        ))

    return rows, sorted(accounts_seen - {"?"}), opening


def _gemini_parse_gl(file_bytes: bytes, filename: str,
                     account_code: str, api_key: str) -> Dict[str, Any]:
    """Gemini fallback for GL PDF parsing."""
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        b64 = base64.b64encode(file_bytes).decode()
        acct_hint = f" Filter to account code starting with '{account_code}'." if account_code else ""
        prompt = (
            "This is a General Ledger (GL) document.{hint} "
            "Extract ALL transaction rows as JSON with keys:\n"
            '  "opening_balance": number,\n'
            '  "accounts": [list of account codes found],\n'
            '  "rows": [{date:"YYYY-MM-DD", doc_no:string, account_code:string, '
            "description:string, debit:number, credit:number}]\n"
            "Return ONLY valid JSON."
        ).format(hint=acct_hint)

        resp = model.generate_content([
            {"mime_type": "application/pdf", "data": b64},
            prompt,
        ])
        text = (resp.text or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
        data = json.loads(text)

        raw_rows = data.get("rows") or []
        rows = []
        accounts_seen = set()
        for r in raw_rows:
            d = _parse_date(str(r.get("date", "")))
            if d is None:
                continue
            acct = str(r.get("account_code", "")).strip()
            if account_code and acct and not acct.startswith(account_code):
                continue
            accounts_seen.add(acct or "?")
            rows.append(GlRow(
                date=d, doc_no=str(r.get("doc_no", "")),
                account_code=acct, description=str(r.get("description", "")),
                debit=float(r.get("debit", 0) or 0),
                credit=float(r.get("credit", 0) or 0),
            ))

        opening = float(data.get("opening_balance", 0) or 0)
        closing = round(opening + sum(r.credit for r in rows) - sum(r.debit for r in rows), 2)
        return {
            "ok": True, "rows": rows,
            "accounts": sorted(accounts_seen - {"?"}),
            "opening": opening, "closing": closing, "row_count": len(rows),
        }

    except Exception as e:
        logger.warning(f"_gemini_parse_gl failed: {e}")
        return {"ok": False, "rows": [], "error": str(e)}


def parse_gl(file_bytes: bytes, filename: str,
             account_code: str = "", api_key: str = "") -> Dict[str, Any]:
    """Route to Excel or PDF GL parser based on file extension."""
    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls", "xlsm"):
        result = parse_gl_excel(file_bytes, filename, account_code)
    else:
        result = parse_gl_pdf(file_bytes, filename, account_code, api_key)

    if result.get("ok"):
        for r in result.get("rows", []):
            r.source_file = filename

    return result


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-FILE MERGE
# ─────────────────────────────────────────────────────────────────────────────
def merge_statements(parsed_list: List[Dict[str, Any]]) -> Tuple[List[StatementRow], float, float, str]:
    """Merge multiple parsed bank statements, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0
    bank_code = "generic"
    earliest_date = None
    latest_date = None

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("bank_code") and p["bank_code"] != "generic":
            bank_code = p["bank_code"]
        for r in (p.get("rows") or []):
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)
            if r.date:
                if earliest_date is None or r.date < earliest_date:
                    earliest_date = r.date
                if latest_date is None or r.date > latest_date:
                    latest_date = r.date

    # Sort by date then by deposit/withdrawal (date first, then the transactions)
    all_rows.sort(key=lambda r: (r.date or date.min, r.withdrawal, r.deposit))

    # Opening: from first parsed file that has an opening balance
    for p in parsed_list:
        if p.get("ok") and p.get("opening", 0.0) != 0.0:
            opening = p["opening"]
            break

    # Closing: from last parsed file or recalculate
    for p in reversed(parsed_list):
        if p.get("ok") and p.get("closing", 0.0) != 0.0:
            closing = p["closing"]
            break

    if opening == 0.0 and all_rows:
        first = all_rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    if closing == 0.0 and all_rows:
        closing = all_rows[-1].balance

    return all_rows, opening, closing, bank_code


def merge_gl_files(parsed_list: List[Dict[str, Any]],
                   account_code: str = "") -> Tuple[List[GlRow], List[str], float, float]:
    """Merge multiple parsed GL files, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[GlRow] = []
    all_accounts: set = set()
    opening = 0.0

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("opening", 0.0) != 0.0 and opening == 0.0:
            opening = p["opening"]
        for acct in (p.get("accounts") or []):
            all_accounts.add(acct)
        for r in (p.get("rows") or []):
            if account_code and r.account_code and not r.account_code.startswith(account_code):
                continue
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)

    all_rows.sort(key=lambda r: (r.date or date.min, r.doc_no or ""))

    # v118.33.13.5 · Cash-ledger formula (matches parse_gl_pdf v118.33.13.4):
    # debit = cash IN (balance increase), credit = cash OUT (balance decrease)
    # The OLD formula `opening + credit - debit` was the expense/revenue
    # perspective and produced wrong closing balances for bank GLs.
    total_credit = sum(r.credit for r in all_rows)
    total_debit = sum(r.debit for r in all_rows)
    closing = round(opening + total_debit - total_credit, 2)

    return all_rows, sorted(all_accounts), opening, closing


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def reconcile(
    stmt_rows: List[StatementRow],
    gl_rows: List[GlRow],
    stmt_opening: float = 0.0,
    gl_opening: float = 0.0,
    stmt_closing: float = 0.0,
    gl_closing: float = 0.0,
    bank_code: str = "",
    gl_account_code: str = "",
) -> Tuple[List[BankReconRow], BankReconSummary]:
    """
    3-layer matching: L1 exact date+amount, L2 ±3-day+amount, L3 amount only.
    Returns (recon_rows, summary).
    """
    recon_rows: List[BankReconRow] = []

    # Work with indices to track matched/unmatched
    gl_used = [False] * len(gl_rows)
    stmt_used = [False] * len(stmt_rows)

    def try_match_gl(stmt_row: StatementRow, layer: int) -> Optional[int]:
        """Find best GL match for a statement row. Returns GL index or None."""
        target_amount = stmt_row.withdrawal if stmt_row.withdrawal > 0 else stmt_row.deposit
        # Withdrawal from bank = company paid out = GL Credit; Deposit = GL Debit
        direction = "C" if stmt_row.withdrawal > 0 else "D"

        best_idx = None
        best_day_diff = 999

        for gi, gr in enumerate(gl_rows):
            if gl_used[gi]:
                continue
            gl_amount = gr.debit if direction == "D" else gr.credit
            if not _amount_matches(target_amount, gl_amount):
                continue
            if gl_amount == 0:
                continue

            dd = _day_diff(stmt_row.date, gr.date)
            if layer == 1:
                if dd is None or dd > 0:
                    continue
                best_idx = gi
                break
            elif layer == 2:
                if dd is None or dd > DATE_TOL_DAYS:
                    continue
                if dd < best_day_diff:
                    best_day_diff = dd
                    best_idx = gi
            elif layer == 3:
                if best_idx is None:
                    best_idx = gi

        return best_idx

    # Layer 1: exact date + exact amount
    for si, sr in enumerate(stmt_rows):
        gi = try_match_gl(sr, layer=1)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            recon_rows.append(BankReconRow(
                match_status="matched", match_layer=1,
                stmt_date=sr.date, stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal, stmt_deposit=sr.deposit, stmt_balance=sr.balance,
                stmt_confidence=sr.confidence, stmt_balance_ok=sr.balance_ok,
                gl_date=gr.date, gl_doc_no=gr.doc_no, gl_account_code=gr.account_code,
                gl_desc=gr.description, gl_debit=gr.debit, gl_credit=gr.credit,
                date_diff_days=0,
                source_stmt_file=sr.source_file, source_gl_file=gr.source_file,
            ))

    # Layer 2: ±3-day tolerance
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=2)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date) or 0
            recon_rows.append(BankReconRow(
                match_status="matched", match_layer=2,
                stmt_date=sr.date, stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal, stmt_deposit=sr.deposit, stmt_balance=sr.balance,
                stmt_confidence=sr.confidence, stmt_balance_ok=sr.balance_ok,
                gl_date=gr.date, gl_doc_no=gr.doc_no, gl_account_code=gr.account_code,
                gl_desc=gr.description, gl_debit=gr.debit, gl_credit=gr.credit,
                date_diff_days=dd,
                source_stmt_file=sr.source_file, source_gl_file=gr.source_file,
            ))

    # Layer 3: amount only (no date constraint) — flagged
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=3)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date)
            recon_rows.append(BankReconRow(
                match_status="matched", match_layer=3,
                stmt_date=sr.date, stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal, stmt_deposit=sr.deposit, stmt_balance=sr.balance,
                stmt_confidence=sr.confidence, stmt_balance_ok=sr.balance_ok,
                gl_date=gr.date, gl_doc_no=gr.doc_no, gl_account_code=gr.account_code,
                gl_desc=gr.description, gl_debit=gr.debit, gl_credit=gr.credit,
                date_diff_days=dd,
                source_stmt_file=sr.source_file, source_gl_file=gr.source_file,
            ))

    # Remaining unmatched statement rows
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        status = "stmt_withdrawal_only" if sr.withdrawal > 0 else "stmt_deposit_only"
        recon_rows.append(BankReconRow(
            match_status=status, match_layer=None,
            stmt_date=sr.date, stmt_desc=sr.description,
            stmt_withdrawal=sr.withdrawal, stmt_deposit=sr.deposit, stmt_balance=sr.balance,
            stmt_confidence=sr.confidence, stmt_balance_ok=sr.balance_ok,
            source_stmt_file=sr.source_file,
        ))

    # Remaining unmatched GL rows
    for gi, gr in enumerate(gl_rows):
        if gl_used[gi]:
            continue
        status = "gl_debit_only" if gr.debit > 0 else "gl_credit_only"
        recon_rows.append(BankReconRow(
            match_status=status, match_layer=None,
            gl_date=gr.date, gl_doc_no=gr.doc_no, gl_account_code=gr.account_code,
            gl_desc=gr.description, gl_debit=gr.debit, gl_credit=gr.credit,
            source_gl_file=gr.source_file,
        ))

    # Sort: matched first (by stmt_date), then unmatched
    def _sort_key(r: BankReconRow):
        order = 0 if r.match_status == "matched" else 1
        d = r.stmt_date or r.gl_date or date.min
        return (order, d)

    recon_rows.sort(key=_sort_key)

    # Build summary
    matched_rows = [r for r in recon_rows if r.match_status == "matched"]
    gl_debit_only = [r for r in recon_rows if r.match_status == "gl_debit_only"]
    gl_credit_only = [r for r in recon_rows if r.match_status == "gl_credit_only"]
    stmt_wd_only = [r for r in recon_rows if r.match_status == "stmt_withdrawal_only"]
    stmt_dep_only = [r for r in recon_rows if r.match_status == "stmt_deposit_only"]

    gl_debit_only_amt = round(sum(r.gl_debit for r in gl_debit_only), 2)
    gl_credit_only_amt = round(sum(r.gl_credit for r in gl_credit_only), 2)
    stmt_wd_only_amt = round(sum(r.stmt_withdrawal for r in stmt_wd_only), 2)
    stmt_dep_only_amt = round(sum(r.stmt_deposit for r in stmt_dep_only), 2)

    # Reconciliation formula:
    # stmt_closing ≈ gl_closing + opening_diff - gl_debit_only + gl_credit_only
    #                           - stmt_wd_only + stmt_dep_only
    opening_diff = round(stmt_opening - gl_opening, 2)
    formula_closing = round(
        gl_closing + opening_diff
        - gl_debit_only_amt + gl_credit_only_amt
        - stmt_wd_only_amt + stmt_dep_only_amt,
        2
    )
    formula_diff = round(stmt_closing - formula_closing, 2)

    summary = BankReconSummary(
        bank_code=bank_code,
        gl_account_code=gl_account_code,
        stmt_opening=stmt_opening,
        stmt_closing=stmt_closing,
        gl_opening=gl_opening,
        gl_closing=gl_closing,
        stmt_total_deposit=round(sum(r.deposit for r in stmt_rows), 2),
        stmt_total_withdrawal=round(sum(r.withdrawal for r in stmt_rows), 2),
        gl_total_credit=round(sum(r.credit for r in gl_rows), 2),
        gl_total_debit=round(sum(r.debit for r in gl_rows), 2),
        matched_count=len(matched_rows),
        gl_debit_only_count=len(gl_debit_only),
        gl_credit_only_count=len(gl_credit_only),
        stmt_withdrawal_only_count=len(stmt_wd_only),
        stmt_deposit_only_count=len(stmt_dep_only),
        gl_debit_only_amount=gl_debit_only_amt,
        gl_credit_only_amount=gl_credit_only_amt,
        stmt_withdrawal_only_amount=stmt_wd_only_amt,
        stmt_deposit_only_amount=stmt_dep_only_amt,
        opening_diff=opening_diff,
        formula_stmt_closing=formula_closing,
        formula_diff=formula_diff,
    )

    return recon_rows, summary


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────────────────────────────────────
_I18N_EXPORT: Dict[str, Dict[str, str]] = {
    # Sheet names
    "sh_summary":      {"th": "สรุป", "en": "Summary", "zh": "汇总", "ja": "サマリー"},
    "sh_matched":      {"th": "จับคู่แล้ว", "en": "Matched", "zh": "已匹配", "ja": "一致"},
    "sh_unmatched_gl": {"th": "GL ที่จับคู่ไม่ได้", "en": "Unmatched GL", "zh": "GL未匹配", "ja": "GL不一致"},
    "sh_unmatched_st": {"th": "Statement ที่จับคู่ไม่ได้", "en": "Unmatched Statement", "zh": "账单未匹配", "ja": "明細不一致"},
    # v118.34 · Consolidated Match Results sheet (matched + gl-only + stmt-only with Status col)
    "sh_match_results": {"th": "ผลการจับคู่", "en": "Match Results", "zh": "对账结果", "ja": "照合結果"},
    "status_matched":   {"th": "✓ จับคู่แล้ว", "en": "✓ Matched", "zh": "✓ 已匹配", "ja": "✓ 一致"},
    # Column headers
    "col_date":        {"th": "วันที่", "en": "Date", "zh": "日期", "ja": "日付"},
    "col_desc":        {"th": "รายการ", "en": "Description", "zh": "摘要", "ja": "摘要"},
    "col_withdrawal":  {"th": "ถอนเงิน", "en": "Withdrawal", "zh": "提款", "ja": "出金"},
    "col_deposit":     {"th": "ฝากเงิน", "en": "Deposit", "zh": "存款", "ja": "入金"},
    "col_balance":     {"th": "ยอดคงเหลือ", "en": "Balance", "zh": "余额", "ja": "残高"},
    "col_gl_date":     {"th": "วันที่ GL", "en": "GL Date", "zh": "GL日期", "ja": "GL日付"},
    "col_gl_doc":      {"th": "เลขที่ GL", "en": "GL Doc No", "zh": "GL凭证号", "ja": "GL伝票番号"},
    "col_gl_acct":     {"th": "รหัสบัญชี", "en": "Account Code", "zh": "科目代码", "ja": "科目コード"},
    "col_gl_desc":     {"th": "รายการ GL", "en": "GL Description", "zh": "GL摘要", "ja": "GL摘要"},
    "col_gl_debit":    {"th": "เดบิต GL", "en": "GL Debit", "zh": "GL借方", "ja": "GL借方"},
    "col_gl_credit":   {"th": "เครดิต GL", "en": "GL Credit", "zh": "GL贷方", "ja": "GL貸方"},
    "col_match_layer": {"th": "ชั้นจับคู่", "en": "Match Layer", "zh": "匹配层", "ja": "マッチ層"},
    "col_date_diff":   {"th": "ต่างวัน", "en": "Day Diff", "zh": "日期差", "ja": "日付差"},
    "col_status":      {"th": "สถานะ", "en": "Status", "zh": "状态", "ja": "状態"},
    "col_source_stmt": {"th": "ไฟล์บัญชี", "en": "Statement File", "zh": "对账单文件", "ja": "明細ファイル"},
    "col_source_gl":   {"th": "ไฟล์ GL", "en": "GL File", "zh": "GL文件", "ja": "GLファイル"},
    # Summary labels
    "lbl_bank":        {"th": "ธนาคาร", "en": "Bank", "zh": "银行", "ja": "銀行"},
    "lbl_gl_acct":     {"th": "รหัสบัญชี GL", "en": "GL Account", "zh": "GL科目", "ja": "GL科目"},
    "lbl_stmt_open":   {"th": "ยอดยกมา (Statement)", "en": "Stmt Opening Balance", "zh": "对账单期初余额", "ja": "明細期首残高"},
    "lbl_stmt_close":  {"th": "ยอดยกไป (Statement)", "en": "Stmt Closing Balance", "zh": "对账单期末余额", "ja": "明細期末残高"},
    "lbl_gl_open":     {"th": "ยอดยกมา (GL)", "en": "GL Opening Balance", "zh": "GL期初余额", "ja": "GL期首残高"},
    "lbl_gl_close":    {"th": "ยอดยกไป (GL)", "en": "GL Closing Balance", "zh": "GL期末余额", "ja": "GL期末残高"},
    "lbl_open_diff":   {"th": "ผลต่างยอดยกมา", "en": "Opening Diff", "zh": "期初差异", "ja": "期首差異"},
    "lbl_matched":     {"th": "รายการที่จับคู่ได้", "en": "Matched Items", "zh": "已匹配项目", "ja": "一致項目"},
    "lbl_gl_debit_only": {"th": "GL เดบิตเท่านั้น (ไม่มีในบัญชีธนาคาร)", "en": "GL Debit Only (not in Statement)", "zh": "仅 GL 有借方（对账单中缺失）", "ja": "GL の借方のみ（明細にない）"},
    "lbl_gl_credit_only": {"th": "GL เครดิตเท่านั้น (ไม่มีในบัญชีธนาคาร)", "en": "GL Credit Only (not in Statement)", "zh": "仅 GL 有贷方（对账单中缺失）", "ja": "GL の貸方のみ（明細にない）"},
    "lbl_stmt_wd_only": {"th": "รายการถอนใน Statement เท่านั้น (ไม่มีใน GL)", "en": "Stmt Withdrawal Only (not in GL)", "zh": "仅对账单有提款（GL 中缺失）", "ja": "明細の出金のみ（GL にない）"},
    "lbl_stmt_dep_only": {"th": "รายการฝากใน Statement เท่านั้น (ไม่มีใน GL)", "en": "Stmt Deposit Only (not in GL)", "zh": "仅对账单有存款（GL 中缺失）", "ja": "明細の入金のみ（GL にない）"},
    "lbl_formula_calc": {"th": "ยอดปิดคำนวณ (สูตร)", "en": "Calculated Closing (formula)", "zh": "公式计算期末余额", "ja": "計算期末残高（計算式）"},
    "lbl_formula_diff": {"th": "ผลต่าง (ควรเป็น 0)", "en": "Difference (should be 0)", "zh": "差异（应为0）", "ja": "差異（0が理想）"},
    "lbl_count":        {"th": "จำนวน", "en": "Count", "zh": "数量", "ja": "件数"},
    "lbl_amount":       {"th": "จำนวนเงิน", "en": "Amount", "zh": "金额", "ja": "金額"},
    "lbl_formula_title": {"th": "สูตรการกระทบยอด", "en": "Reconciliation Formula", "zh": "对账公式", "ja": "照合計算式"},
    "lbl_stats":        {"th": "สถิติ", "en": "Statistics", "zh": "统计", "ja": "統計"},
    # Match layer labels
    "layer_1":  {"th": "L1-ตรงวันที่", "en": "L1 - Exact Date", "zh": "L1-精确日期", "ja": "L1-日付一致"},
    "layer_2":  {"th": "L2-ใกล้วันที่", "en": "L2 - Date Tolerance", "zh": "L2-日期容差", "ja": "L2-日付許容"},
    "layer_3":  {"th": "L3-เฉพาะยอด", "en": "L3 - Amount Only", "zh": "L3-仅金额", "ja": "L3-金額のみ"},
    # Status labels
    "st_gl_debit_only": {"th": "GL เดบิตเท่านั้น", "en": "GL Debit Only", "zh": "仅 GL 借方", "ja": "GL の借方のみ"},
    "st_gl_credit_only": {"th": "GL เครดิตเท่านั้น", "en": "GL Credit Only", "zh": "仅 GL 贷方", "ja": "GL の貸方のみ"},
    "st_stmt_wd_only": {"th": "รายการถอนเท่านั้น", "en": "Stmt Withdrawal Only", "zh": "仅对账单提款", "ja": "明細の出金のみ"},
    "st_stmt_dep_only": {"th": "รายการฝากเท่านั้น", "en": "Stmt Deposit Only", "zh": "仅对账单存款", "ja": "明細の入金のみ"},
    # File-info diagnostics sheet
    "sh_fileinfo":      {"th": "ข้อมูลไฟล์", "en": "File Info", "zh": "文件信息", "ja": "ファイル情報"},
    "fi_type":          {"th": "ประเภท", "en": "Type", "zh": "类型", "ja": "種別"},
    "fi_file":          {"th": "ชื่อไฟล์", "en": "File", "zh": "文件名", "ja": "ファイル"},
    "fi_rows":          {"th": "แถวที่พบ", "en": "Rows Found", "zh": "解析行数", "ja": "解析行数"},
    "fi_bank_acct":     {"th": "ธนาคาร/บัญชี", "en": "Bank/Account", "zh": "银行/科目", "ja": "銀行/科目"},
    "fi_status":        {"th": "สถานะ", "en": "Status", "zh": "状态", "ja": "状態"},
    "fi_error":         {"th": "ข้อผิดพลาด", "en": "Error", "zh": "错误", "ja": "エラー"},
    "fi_stmt_type":     {"th": "Statement ธนาคาร", "en": "Bank Statement", "zh": "银行对账单", "ja": "銀行明細"},
    "fi_gl_type":       {"th": "GL", "en": "GL", "zh": "总账（GL）", "ja": "GL"},
    "fi_ok":            {"th": "✓ สำเร็จ", "en": "✓ OK", "zh": "✓ 成功", "ja": "✓ 成功"},
    "fi_warn":          {"th": "⚠ 0 แถว", "en": "⚠ 0 Rows", "zh": "⚠ 0行", "ja": "⚠ 0行"},
    "fi_fail":          {"th": "✗ ล้มเหลว", "en": "✗ Failed", "zh": "✗ 失败", "ja": "✗ 失敗"},
    # v118.33.13.0 · OCR verification labels
    "lbl_ocr_check":    {"th": "ตรวจสอบความถูกต้องของ OCR", "en": "OCR Accuracy Check",
                         "zh": "OCR 准确性核查", "ja": "OCR精度チェック"},
    "lbl_ocr_bal_warn": {"th": "ยอดคงเหลือไม่ตรง (โปรดตรวจสอบ)", "en": "Balance mismatch (review)",
                         "zh": "余额验证未通过", "ja": "残高検証エラー"},
    "lbl_ocr_lowconf":  {"th": "ความมั่นใจต่ำ (เลือนราง)", "en": "Low confidence (blurry)",
                         "zh": "低置信度（模糊）", "ja": "信頼度低（不鮮明）"},
    "col_confidence":   {"th": "ความมั่นใจ", "en": "Confidence", "zh": "置信度", "ja": "信頼度"},
    "col_balance_ok":   {"th": "ตรวจยอด", "en": "Balance Check", "zh": "余额校验", "ja": "残高検証"},
    # Statement detail sheet
    "sh_stmt_detail":   {"th": "รายละเอียดSTATEMENT", "en": "Statement Detail",
                         "zh": "银行对账单明细", "ja": "明細"},
    "sh_gl_detail":     {"th": "รายละเอียดบัญชีแยกประเภท", "en": "GL Detail",
                         "zh": "总账明细", "ja": "元帳明細"},
    # v118.34 · GL Detail Sheet column labels (no "GL" suffix · Sheet name already implies context)
    "col_doc_no":       {"th": "เลขที่เอกสาร", "en": "Doc No",
                         "zh": "凭证号", "ja": "伝票番号"},
    "col_account_code": {"th": "รหัสบัญชี", "en": "Account Code",
                         "zh": "科目代码", "ja": "科目コード"},
    "col_debit":        {"th": "เดบิต", "en": "Debit",
                         "zh": "借方", "ja": "借方"},
    "col_credit":       {"th": "เครดิต", "en": "Credit",
                         "zh": "贷方", "ja": "貸方"},
    "sh_usage":         {"th": "วิธีใช้งาน", "en": "How to Use",
                         "zh": "使用说明", "ja": "使い方"},
    "col_source_file":  {"th": "ไฟล์ต้นทาง", "en": "Source File",
                         "zh": "原文件", "ja": "ファイル"},
    "conf_high":        {"th": "✓ สูง", "en": "✓ High", "zh": "✓ 高", "ja": "✓ 高"},
    "conf_medium":      {"th": "△ กลาง", "en": "△ Medium", "zh": "△ 中", "ja": "△ 中"},
    "conf_low":         {"th": "◌ ต่ำ", "en": "◌ Low", "zh": "◌ 低", "ja": "◌ 低"},
    "bal_ok":           {"th": "✓ ผ่าน", "en": "✓ Pass", "zh": "✓ 通过", "ja": "✓ 合格"},
    "bal_warn":         {"th": "⚠ ตรวจ", "en": "⚠ Review", "zh": "⚠ 核对", "ja": "⚠ 要確認"},
    "bal_na":           {"th": "—", "en": "—", "zh": "—", "ja": "—"},
    # v118.33.13.2 · Vertical itemized summary labels
    "col_summary_item":   {"th": "รายการ", "en": "Item Description",
                           "zh": "项目说明", "ja": "項目"},
    "col_summary_amount": {"th": "จำนวนเงิน", "en": "Amount",
                           "zh": "金额", "ja": "金額"},
    "detail_no_items":    {"th": "ไม่มี", "en": "(none)",
                           "zh": "无", "ja": "なし"},
    "sec_open_diff_expand": {"th": "ผลต่างยอดยกมา (ยอดยกมา Statement − ยอดยกมา GL)",
                             "en": "Opening Diff (Stmt Open − GL Open)",
                             "zh": "期初差异（账单期初 − GL期初）",
                             "ja": "期首差異（明細期首 − GL期首）"},
    "sec_gl_debit_only_full":  {"th": "GL เดบิตเท่านั้น (ไม่มีในบัญชีธนาคาร)",
                                "en": "GL Debit Only (not in Statement)",
                                "zh": "GL 借方仅有（账单中不存在）",
                                "ja": "GLのみ借方（明細に存在しない）"},
    "sec_gl_credit_only_full": {"th": "GL เครดิตเท่านั้น (ไม่มีในบัญชีธนาคาร)",
                                "en": "GL Credit Only (not in Statement)",
                                "zh": "GL 贷方仅有（账单中不存在）",
                                "ja": "GLのみ貸方（明細に存在しない）"},
    "sec_stmt_wd_only_full":   {"th": "ถอนเงินในบัญชีเท่านั้น (ไม่มีใน GL)",
                                "en": "Statement Withdrawal Only (not in GL)",
                                "zh": "账单提款仅有（GL 中不存在）",
                                "ja": "明細出金のみ（GLに存在しない）"},
    "sec_stmt_dep_only_full":  {"th": "ฝากเงินในบัญชีเท่านั้น (ไม่มีใน GL)",
                                "en": "Statement Deposit Only (not in GL)",
                                "zh": "账单存款仅有（GL 中不存在）",
                                "ja": "明細入金のみ（GLに存在しない）"},
}


def _t(key: str, lang: str) -> str:
    lang = lang if lang in ("th", "en", "zh", "ja") else "th"
    return (_I18N_EXPORT.get(key) or {}).get(lang) or (_I18N_EXPORT.get(key) or {}).get("en") or key


# v118.34 · Usage instructions block (4-sheet consolidated structure)
# Each (text, bold) tuple is one row. bold=True rows get a light-grey fill.
_USAGE_BLOCKS: Dict[str, List[Tuple[str, bool]]] = {
    "zh": [
        ("银行对账表 · 使用说明", True),
        ("", False),
        ("Sheet 结构(共 4 个):", True),
        ("• 「汇总」              本表 · 含文件信息、对账公式、统计数据、本说明", False),
        ("• 「对账结果」          已匹配 + 仅 GL 有 + 仅对账单有,以「状态」列区分", False),
        ("• 「银行对账单明细」    OCR 提取的全部对账单行 + 置信度 + 余额校验状态", False),
        ("• 「总账明细」          OCR 提取的全部 GL 总账行", False),
        ("", False),
        ("OCR 准确性图例:", True),
        ("• 置信度 ✓高: 数字清晰无歧义可直接信任", False),
        ("• 置信度 △中: 多数清晰但有少量疑点", False),
        ("• 置信度 ◌低: 数字模糊或难以辨认,请核对原 PDF", False),
        ("• 余额校验 ✓通过: 上一行余额 ± 金额 == 本行余额 (容差 0.05)", False),
        ("• 余额校验 ⚠核对: 不平衡 — 多半是 OCR 看错某个数字,请核对原 PDF", False),
        ("• 余额校验 —    : 无法校验 (首行或缺失余额)", False),
        ("", False),
        ("对账公式:", True),
        ("  GL 期末 + 期初差异 − 仅 GL 借方 + 仅 GL 贷方 − 仅对账单提款 + 仅对账单存款 = 计算期末", False),
        ("  计算期末 应等于 对账单期末; 差异 = 计算期末 − 对账单期末 (应为 0)", False),
        ("", False),
        ("重要提示: 扫描件 PDF 通过 AI OCR 识别 · 不可避免存在识别风险 · 凡是看到 ⚠ 或 ◌ 的行必须人工核对原 PDF 后才能采信。"
         "Pearnly 永远不会自行填充模糊的数字 — 看不清就标红,决不替你猜。", False),
    ],
    "en": [
        ("Bank Reconciliation · How to Use", True),
        ("", False),
        ("Sheet structure (4 total):", True),
        ("• 'Summary'              This sheet · file info, reconciliation formula, stats, these instructions", False),
        ("• 'Match Results'        Matched + Unmatched GL + Unmatched Statement, distinguished by Status column", False),
        ("• 'Statement Detail'     All OCR-extracted statement rows + confidence + balance check", False),
        ("• 'GL Detail'            All OCR-extracted GL ledger rows", False),
        ("", False),
        ("OCR Accuracy legend:", True),
        ("• Confidence ✓High: every digit is clear, can be trusted", False),
        ("• Confidence △Medium: mostly clear with minor doubts", False),
        ("• Confidence ◌Low: digit was blurry or hard to read — verify against the original PDF", False),
        ("• Balance check ✓Pass: prev_balance ± amount == this row balance (tolerance 0.05)", False),
        ("• Balance check ⚠Review: not balanced — likely a misread digit. Verify against the original PDF", False),
        ("• Balance check —      : cannot verify (first row or missing balance)", False),
        ("", False),
        ("Reconciliation formula:", True),
        ("  GL_close + Open_diff − GL_debit_only + GL_credit_only − Stmt_WD_only + Stmt_Dep_only = Calc_close", False),
        ("  Calc_close should equal Statement_close; Diff = Calc_close − Statement_close (should be 0)", False),
        ("", False),
        ("IMPORTANT: Scanned PDFs go through AI OCR. There is always residual OCR risk. "
         "Any row marked ⚠ or ◌ MUST be cross-checked against the original PDF before trusting it. "
         "Pearnly will NEVER auto-fill an unclear digit — if we can't read it, we flag it; we don't guess for you.", False),
    ],
    "th": [
        ("รายงานการกระทบยอด GL กับบัญชีธนาคาร · วิธีใช้งาน", True),
        ("", False),
        ("โครงสร้าง Sheet (รวม 4 แผ่น):", True),
        ("• 'สรุป'                          แผ่นนี้ · ข้อมูลไฟล์ สูตรกระทบยอด สถิติ และคำแนะนำการใช้งาน", False),
        ("• 'ผลการจับคู่'                   รายการจับคู่ + GL ที่จับคู่ไม่ได้ + Statement ที่จับคู่ไม่ได้ พร้อมคอลัมน์สถานะ", False),
        ("• 'รายละเอียดSTATEMENT'           รายการบัญชีที่ OCR อ่านได้ทั้งหมด + ความมั่นใจ + ผลตรวจยอด", False),
        ("• 'รายละเอียดบัญชีแยกประเภท'      รายการบัญชีแยกประเภท (GL) ที่ OCR อ่านได้ทั้งหมด", False),
        ("", False),
        ("คำอธิบายสัญลักษณ์ OCR:", True),
        ("• ความมั่นใจ ✓สูง: ตัวเลขชัดเจน ไว้ใจได้", False),
        ("• ความมั่นใจ △กลาง: ส่วนใหญ่ชัด แต่มีจุดน่าสงสัยเล็กน้อย", False),
        ("• ความมั่นใจ ◌ต่ำ: ตัวเลขเบลอหรืออ่านยาก — โปรดตรวจ PDF ต้นฉบับ", False),
        ("• ตรวจยอด ✓ผ่าน: ยอดก่อน ± จำนวน == ยอดบรรทัดนี้ (ค่าเผื่อ 0.05)", False),
        ("• ตรวจยอด ⚠ตรวจ: ไม่ตรง — น่าจะ OCR อ่านผิด โปรดตรวจ PDF ต้นฉบับ", False),
        ("• ตรวจยอด —    : ตรวจไม่ได้ (บรรทัดแรกหรือไม่มียอด)", False),
        ("", False),
        ("สูตรการกระทบยอด:", True),
        ("  ปิด GL + ผลต่างยอดยกมา − GL เดบิตเท่านั้น + GL เครดิตเท่านั้น − รายการถอนเท่านั้น + รายการฝากเท่านั้น = ปิดคำนวณ", False),
        ("  ปิดคำนวณ ควรเท่ากับ ยอดยกไป Statement; ผลต่าง = ปิดคำนวณ − ยอดยกไป Statement (ควรเป็น 0)", False),
        ("", False),
        ("สำคัญ: PDF ที่สแกนผ่าน AI OCR ย่อมมีความเสี่ยงในการอ่านผิดเสมอ "
         "แถวที่ติด ⚠ หรือ ◌ ต้องตรวจสอบกับ PDF ต้นฉบับก่อนเชื่อถือทุกครั้ง "
         "Pearnly จะไม่เติมตัวเลขที่ไม่ชัดเจนเอง — ถ้าอ่านไม่ออก เราติดสัญลักษณ์ ไม่เดาแทนคุณ", False),
    ],
    "ja": [
        ("銀行照合レポート · 使い方", True),
        ("", False),
        ("シート構成 (全 4 シート):", True),
        ("• 「サマリー」               本シート · ファイル情報、照合計算式、件数、使い方", False),
        ("• 「照合結果」               一致 + GL不一致 + 明細不一致 を状態列で区別", False),
        ("• 「明細」                  OCR抽出した全明細行 + 信頼度 + 残高検証結果", False),
        ("• 「元帳明細」               OCR抽出した全 GL 元帳行", False),
        ("", False),
        ("OCR精度凡例:", True),
        ("• 信頼度 ✓高: 数字明瞭、信頼可能", False),
        ("• 信頼度 △中: 概ね明瞭だが軽微な疑問あり", False),
        ("• 信頼度 ◌低: 数字がぼやけている — 元のPDFを照合してください", False),
        ("• 残高検証 ✓合格: 前残高 ± 金額 == この行残高 (誤差 0.05)", False),
        ("• 残高検証 ⚠要確認: 不一致 — OCR誤読の可能性。元のPDFを照合してください", False),
        ("• 残高検証 —      : 検証不可 (初行または残高欠落)", False),
        ("", False),
        ("照合計算式:", True),
        ("  GL 期末 + 期首差 − GL の借方のみ + GL の貸方のみ − 明細の出金のみ + 明細の入金のみ = 計算期末", False),
        ("  計算期末 は 明細期末 と等しいはず; 差異 = 計算期末 − 明細期末 (0 が理想)", False),
        ("", False),
        ("重要: スキャンPDFはAI OCRを使用 · OCR誤読リスクは常に存在します "
         "⚠ または ◌ が付いた行は必ず元のPDFと照合してから利用してください "
         "Pearnly は不明瞭な数字を自動で埋めません — 読めないものはマークし、推測しません", False),
    ],
}


def _layer_label(layer: Optional[int], lang: str) -> str:
    if layer == 1:
        return _t("layer_1", lang)
    if layer == 2:
        return _t("layer_2", lang)
    if layer == 3:
        return _t("layer_3", lang)
    return ""


def _status_label(status: str, lang: str) -> str:
    mapping = {
        "gl_debit_only": "st_gl_debit_only",
        "gl_credit_only": "st_gl_credit_only",
        "stmt_withdrawal_only": "st_stmt_wd_only",
        "stmt_deposit_only": "st_stmt_dep_only",
    }
    key = mapping.get(status, status)
    return _t(key, lang)


def export_bank_recon_excel(
    recon_rows: List[BankReconRow],
    summary: BankReconSummary,
    lang: str = "th",
    task_info: Optional[Dict[str, Any]] = None,
    parse_info: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Generate Excel report with File Info + 4 data sheets, all headers i18n."""
    try:
        import openpyxl
        from openpyxl.styles import (
            Font, Alignment, PatternFill, Border, Side, numbers
        )
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("openpyxl not installed")

    lang = lang if lang in ("th", "en", "zh", "ja") else "th"

    wb = openpyxl.Workbook()

    # ── Color palette ──────────────────────────────────────────────────
    COLOR_HEADER   = "2D6A4F"   # dark green
    COLOR_SUBHEAD  = "52B788"   # medium green
    COLOR_MATCHED  = "D8F3DC"   # light green
    COLOR_L2       = "FFF3CD"   # amber (date tolerance)
    COLOR_L3       = "FFE0CC"   # orange (amount only)
    COLOR_GL_ONLY  = "E8D5F5"   # purple
    COLOR_ST_ONLY  = "D4E6F1"   # blue
    COLOR_DIFF     = "FFDAD6"   # red for non-zero diff
    COLOR_OK       = "D8F3DC"   # green for zero diff
    COLOR_ROW_ALT  = "F8F9FA"   # alternating row

    def _hdr_style(ws, row, col, text, color=COLOR_HEADER, bold=True, size=10):
        cell = ws.cell(row=row, column=col, value=text)
        cell.font = Font(bold=bold, color="FFFFFF", size=size)
        cell.fill = PatternFill("solid", fgColor=color)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        return cell

    def _label_style(ws, row, col, text, bold=False):
        cell = ws.cell(row=row, column=col, value=text)
        cell.font = Font(bold=bold, size=9)
        cell.alignment = Alignment(vertical="center")
        return cell

    def _num_style(ws, row, col, val, fmt="#,##0.00", fill_color=None):
        cell = ws.cell(row=row, column=col, value=val)
        cell.number_format = fmt
        cell.alignment = Alignment(horizontal="right", vertical="center")
        if fill_color:
            cell.fill = PatternFill("solid", fgColor=fill_color)
        return cell

    def _border_range(ws, min_row, max_row, min_col, max_col):
        thin = Side(style="thin", color="CCCCCC")
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                ws.cell(r, c).border = Border(
                    left=thin, right=thin, top=thin, bottom=thin
                )

    def _fmt_date(d: Optional[date]) -> str:
        if d is None:
            return ""
        return d.strftime("%d/%m/%Y")

    # ══════════════════════════════════════════════════════════════════
    # SHEET 1: สรุป (Consolidated Summary · v118.34)
    # 3 sections in one sheet (was 3 separate sheets pre-v118.34):
    #   A. Reconciliation summary (vertical itemized layout, 2 cols)
    #   B. File Info (parse diagnostics, folded to 2 cols)
    #   C. How to Use (usage instructions, merged A:B)
    # Style: 2-col (label | amount/status), clear color tiers:
    #   - Dark navy: title + main anchor rows (GL期末/账单期末)
    #   - Light gray: section headers
    #   - White: detail rows (each unmatched item itemized)
    #   - Blue: subtotal (计算期末余额)
    #   - Red/green: final diff
    # ══════════════════════════════════════════════════════════════════
    ws1 = wb.active   # reuse auto-created first sheet (was File Info pre-v118.34)
    ws1.title = _t("sh_summary", lang)
    ws1.sheet_view.showGridLines = False
    ws1.column_dimensions["A"].width = 78
    ws1.column_dimensions["B"].width = 22  # v118.33.13.6 · fit (7-digit) amounts with parens

    # Color palette
    NAVY        = "1F2937"   # dark slate - main anchor rows
    NAVY_LIGHT  = "374151"   # slightly lighter for sub-anchor
    SECTION_BG  = "EEF2F6"   # very light blue-gray for section headers
    DETAIL_BG   = "FFFFFF"
    DETAIL_ALT  = "FAFBFC"
    SUBTOTAL_BG = "DBEAFE"   # soft blue for calc-close subtotal
    DIFF_OK_BG  = "D1FAE5"   # mint green for zero diff
    DIFF_BAD_BG = "FEE2E2"   # soft red for non-zero diff
    INFO_BG     = "F9FAFB"   # very subtle gray for bank/acct info

    NUM_FORMAT = '#,##0.00;[Red](#,##0.00)'

    def _fmt_d(d):
        if not d:
            return ""
        try:
            return d.strftime("%d/%m/%Y")
        except Exception:
            return ""

    def _title_row(row, text):
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c = ws1.cell(row, 1, text)
        c.font = Font(bold=True, size=14, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws1.row_dimensions[row].height = 32

    def _header_row(row, label_text, amount_text):
        for col, txt in ((1, label_text), (2, amount_text)):
            c = ws1.cell(row, col, txt)
            c.font = Font(bold=True, size=11, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=NAVY)
            c.alignment = Alignment(horizontal="center", vertical="center")
        ws1.row_dimensions[row].height = 26

    def _anchor_row(row, label, value, *, bg=NAVY, fg="FFFFFF", size=12, bold=True):
        a = ws1.cell(row, 1, label)
        a.font = Font(bold=bold, size=size, color=fg)
        a.fill = PatternFill("solid", fgColor=bg)
        a.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        b = ws1.cell(row, 2, value)
        b.font = Font(bold=bold, size=size, color=fg)
        b.fill = PatternFill("solid", fgColor=bg)
        b.alignment = Alignment(horizontal="right", vertical="center", indent=1)
        b.number_format = NUM_FORMAT
        ws1.row_dimensions[row].height = 24

    def _section_row(row, label):
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c = ws1.cell(row, 1, label)
        c.font = Font(bold=True, size=10, color="111827")
        c.fill = PatternFill("solid", fgColor=SECTION_BG)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws1.row_dimensions[row].height = 22

    def _detail_row(row, label, value, alt=False, italic=False, color="333333"):
        bg = DETAIL_ALT if alt else DETAIL_BG
        a = ws1.cell(row, 1, "  · " + (label if label else ""))
        a.font = Font(size=9, color=color, italic=italic)
        a.fill = PatternFill("solid", fgColor=bg)
        a.alignment = Alignment(horizontal="left", vertical="center",
                                indent=2, wrap_text=False)
        b = ws1.cell(row, 2, value)
        b.font = Font(size=10, color=color, italic=italic)
        b.fill = PatternFill("solid", fgColor=bg)
        b.alignment = Alignment(horizontal="right", vertical="center", indent=1)
        if isinstance(value, (int, float)):
            b.number_format = NUM_FORMAT
        ws1.row_dimensions[row].height = 18

    def _info_row(row, label, value):
        a = ws1.cell(row, 1, label)
        a.font = Font(size=10, color="6B7280")
        a.fill = PatternFill("solid", fgColor=INFO_BG)
        a.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        b = ws1.cell(row, 2, value)
        b.font = Font(size=10, color="111827", bold=True)
        b.fill = PatternFill("solid", fgColor=INFO_BG)
        b.alignment = Alignment(horizontal="right", vertical="center", indent=1)
        ws1.row_dimensions[row].height = 20

    # ── 1. Title ──
    _RECON_TITLE = {"en": "Bank Reconciliation", "zh": "银行对账",
                    "th": "กระทบยอด GL กับบัญชีธนาคาร", "ja": "銀行照合"}
    r = 1
    _title_row(r, f"{_RECON_TITLE.get(lang, 'Bank Reconciliation')} · {summary.bank_code.upper()}")
    r += 1

    # ── 2. Info: bank + GL account ──
    _info_row(r, _t("lbl_bank", lang), summary.bank_code.upper())
    r += 1
    _info_row(r, _t("lbl_gl_acct", lang), summary.gl_account_code or "—")
    r += 2  # blank-row spacer

    # ── 3. Column headers: 项目说明 | 金额 ──
    _header_row(r, _t("col_summary_item", lang), _t("col_summary_amount", lang))
    r += 1

    # ── 4. Start anchor: GL 期末余额 ──
    _anchor_row(r, _t("lbl_gl_close", lang), summary.gl_closing, bg=NAVY, size=12)
    r += 1

    # ── 5. + 期初差异 (signed) ──
    sign_char = "+" if summary.opening_diff >= 0 else "−"
    _section_row(r, f"{sign_char} {_t('sec_open_diff_expand', lang)}")
    r += 1
    open_diff_label = f"{summary.stmt_opening:,.2f} − {summary.gl_opening:,.2f}"
    _detail_row(r, open_diff_label, summary.opening_diff)
    r += 1

    # ── 6. Itemized unmatched sections (4 categories) ──
    def _add_itemized(sign_int, section_key, status_filter, get_fields):
        """sign_int ∈ {-1, +1}.  get_fields(row) → (date_str, doc, desc, amt)."""
        nonlocal r
        ch = "+" if sign_int > 0 else "−"
        rows_match = [rr for rr in recon_rows if rr.match_status == status_filter]
        _section_row(r, f"{ch} {_t(section_key, lang)}")
        r += 1
        if not rows_match:
            _detail_row(r, _t("detail_no_items", lang), 0.0, italic=True, color="9CA3AF")
            r += 1
            return
        for i, rr in enumerate(rows_match):
            date_str, doc, desc, amt = get_fields(rr)
            parts = [p for p in (date_str, doc, desc) if p]
            label = " · ".join(parts) if parts else ""
            _detail_row(r, label, sign_int * (amt or 0), alt=(i % 2 == 1))
            r += 1

    def _gl_fields(rr):
        amt = rr.gl_debit if rr.match_status == "gl_debit_only" else rr.gl_credit
        return _fmt_d(rr.gl_date), rr.gl_doc_no or "", rr.gl_desc or "", amt

    def _stmt_fields(rr):
        amt = rr.stmt_withdrawal if rr.match_status == "stmt_withdrawal_only" else rr.stmt_deposit
        return _fmt_d(rr.stmt_date), "", rr.stmt_desc or "", amt

    _add_itemized(-1, "sec_gl_debit_only_full",  "gl_debit_only",  _gl_fields)
    _add_itemized(+1, "sec_gl_credit_only_full", "gl_credit_only", _gl_fields)
    _add_itemized(-1, "sec_stmt_wd_only_full",   "stmt_withdrawal_only", _stmt_fields)
    _add_itemized(+1, "sec_stmt_dep_only_full",  "stmt_deposit_only",    _stmt_fields)

    # ── 7. Subtotal: 计算期末余额 (light blue) ──
    r += 1  # spacer
    _anchor_row(r, _t("lbl_formula_calc", lang), summary.formula_stmt_closing,
                bg=SUBTOTAL_BG, fg="1E3A8A", size=12)
    r += 1

    # ── 8. Target: 账单期末余额 (dark anchor, same style as GL_close) ──
    _anchor_row(r, _t("lbl_stmt_close", lang), summary.stmt_closing, bg=NAVY, size=12)
    r += 1

    # ── 9. Final: 差异 (green if 0, red otherwise) ──
    diff_ok = abs(summary.formula_diff) < 0.05
    diff_bg = DIFF_OK_BG if diff_ok else DIFF_BAD_BG
    diff_fg = "065F46" if diff_ok else "991B1B"
    _anchor_row(r, _t("lbl_formula_diff", lang), summary.formula_diff,
                bg=diff_bg, fg=diff_fg, size=13)
    r += 1

    # ── 10. OCR accuracy check (only if any warnings) ──
    warn_balance = sum(1 for rr in recon_rows if rr.stmt_balance_ok is False)
    warn_lowconf = sum(1 for rr in recon_rows if rr.stmt_confidence == "low")
    if warn_balance or warn_lowconf:
        r += 1  # spacer
        _section_row(r, _t("lbl_ocr_check", lang))
        r += 1
        if warn_balance:
            _detail_row(r, _t("lbl_ocr_bal_warn", lang), warn_balance, color="DC2626")
            r += 1
        if warn_lowconf:
            _detail_row(r, _t("lbl_ocr_lowconf", lang), warn_lowconf, color="EA580C", alt=True)
            r += 1

    # ── 11. File Info sub-section ──
    r += 2  # spacer between summary and file info
    _section_row(r, _t("sh_fileinfo", lang))
    r += 1

    fi_pairs: List[Tuple[str, str]] = []
    if parse_info:
        for f in (parse_info.get("stmt_files") or []):
            ok_status = _t("fi_ok", lang) if (f.get("ok") and f.get("rows", 0) > 0) \
                else (_t("fi_warn", lang) if (f.get("ok") and f.get("rows", 0) == 0) \
                else _t("fi_fail", lang))
            bank_part = f" · {f.get('bank_code')}" if f.get("bank_code") else ""
            err_part = f" · {f.get('error')}" if f.get("error") else ""
            label = f"{_t('fi_stmt_type', lang)}: {f.get('file', '')} · {f.get('rows', 0)} {_t('fi_rows', lang).lower()}{bank_part}{err_part}"
            fi_pairs.append((label, ok_status))
        for f in (parse_info.get("gl_files") or []):
            ok_status = _t("fi_ok", lang) if (f.get("ok") and f.get("rows", 0) > 0) \
                else (_t("fi_warn", lang) if (f.get("ok") and f.get("rows", 0) == 0) \
                else _t("fi_fail", lang))
            accts = ", ".join(f.get("accounts") or [])
            acct_part = f" · {accts}" if accts else ""
            err_part = f" · {f.get('error')}" if f.get("error") else ""
            label = f"{_t('fi_gl_type', lang)}: {f.get('file', '')} · {f.get('rows', 0)} {_t('fi_rows', lang).lower()}{acct_part}{err_part}"
            fi_pairs.append((label, ok_status))
    elif task_info:
        for fname in (task_info.get("stmt_files") or "").split(";"):
            fname = fname.strip()
            if not fname:
                continue
            rc = task_info.get("stmt_row_count", 0)
            ok_status = _t("fi_ok", lang) if rc > 0 else _t("fi_warn", lang)
            bank_code = task_info.get("bank_code", "")
            bank_part = f" · {bank_code}" if bank_code else ""
            label = f"{_t('fi_stmt_type', lang)}: {fname} · {rc} {_t('fi_rows', lang).lower()}{bank_part}"
            fi_pairs.append((label, ok_status))
        for fname in (task_info.get("gl_files") or "").split(";"):
            fname = fname.strip()
            if not fname:
                continue
            rc = task_info.get("gl_row_count", 0)
            ok_status = _t("fi_ok", lang) if rc > 0 else _t("fi_warn", lang)
            gl_acct = task_info.get("gl_account", "")
            acct_part = f" · {gl_acct}" if gl_acct else ""
            label = f"{_t('fi_gl_type', lang)}: {fname} · {rc} {_t('fi_rows', lang).lower()}{acct_part}"
            fi_pairs.append((label, ok_status))

    _fi_status_colors = {
        _t("fi_ok", lang):   "D8F3DC",
        _t("fi_warn", lang): "FFF3CD",
        _t("fi_fail", lang): "FFDAD6",
    }
    if fi_pairs:
        for label, status_text in fi_pairs:
            a = ws1.cell(r, 1, label)
            a.font = Font(size=9, color="111827")
            a.fill = PatternFill("solid", fgColor=INFO_BG)
            a.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
            b = ws1.cell(r, 2, status_text)
            b.font = Font(size=9, bold=True, color="111827")
            b.fill = PatternFill("solid", fgColor=_fi_status_colors.get(status_text, INFO_BG))
            b.alignment = Alignment(horizontal="center", vertical="center")
            ws1.row_dimensions[r].height = 22
            r += 1
    else:
        a = ws1.cell(r, 1, _t("detail_no_items", lang))
        a.font = Font(size=9, italic=True, color="9CA3AF")
        a.fill = PatternFill("solid", fgColor=INFO_BG)
        a.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        r += 1

    # ── 12. How to Use sub-section ──
    r += 2  # spacer
    _section_row(r, _t("sh_usage", lang))
    r += 1

    usage_block = _USAGE_BLOCKS.get(lang, _USAGE_BLOCKS["en"])
    for text, bold in usage_block:
        ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        cell = ws1.cell(row=r, column=1, value=text)
        cell.font = Font(bold=bold, size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        if bold and text:
            cell.fill = PatternFill("solid", fgColor="E5E7EB")
        ws1.row_dimensions[r].height = 22 if bold else 18
        r += 1

    # ── 13. Final border around the whole Summary sheet ──
    _border_range(ws1, 1, r - 1, 1, 2)
    # Freeze header so it stays visible while scrolling
    ws1.freeze_panes = "A6"

    # ══════════════════════════════════════════════════════════════════
    # SHEET 2: ผลการจับคู่ (Consolidated Match Results · v118.34)
    # Combines what were previously 3 sheets (matched + unmatched_gl + unmatched_stmt).
    # First column "Status" distinguishes:
    #   - "✓ Matched"  (matched rows, color by match layer L1/L2/L3)
    #   - "GL Debit/Credit Only"  (purple tint)
    #   - "Stmt Withdrawal/Deposit Only"  (blue tint)
    # Match Layer column shows L1/L2/L3 for matched rows, "—" for unmatched.
    # ══════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet(_t("sh_match_results", lang))
    ws2.sheet_view.showGridLines = False

    match_cols = [
        (_t("col_status", lang), 18),
        (_t("col_match_layer", lang), 12),
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 26),
        (_t("col_withdrawal", lang), 12),
        (_t("col_deposit", lang), 12),
        (_t("col_balance", lang), 12),
        (_t("col_gl_date", lang), 12),
        (_t("col_gl_doc", lang), 14),
        (_t("col_gl_acct", lang), 11),
        (_t("col_gl_desc", lang), 26),
        (_t("col_gl_debit", lang), 12),
        (_t("col_gl_credit", lang), 12),
        (_t("col_date_diff", lang), 10),
        (_t("col_source_stmt", lang), 18),
        (_t("col_source_gl", lang), 18),
    ]
    for ci, (hdr, width) in enumerate(match_cols, 1):
        _hdr_style(ws2, 1, ci, hdr)
        ws2.column_dimensions[get_column_letter(ci)].width = width

    # Group + sort the recon_rows by category
    matched_rows_for_export = sorted(
        [rr for rr in recon_rows if rr.match_status == "matched"],
        key=lambda x: (x.stmt_date or date.min, x.gl_date or date.min),
    )
    gl_only_rows_for_export = sorted(
        [rr for rr in recon_rows if rr.match_status in ("gl_debit_only", "gl_credit_only")],
        key=lambda x: (x.gl_date or date.min, x.gl_doc_no or ""),
    )
    stmt_only_rows_for_export = sorted(
        [rr for rr in recon_rows if rr.match_status in ("stmt_withdrawal_only", "stmt_deposit_only")],
        key=lambda x: (x.stmt_date or date.min, x.stmt_desc or ""),
    )

    _DASH = "—"

    ri = 2
    # Matched block (tinted by match layer)
    for row in matched_rows_for_export:
        layer_fill_color = COLOR_MATCHED if row.match_layer == 1 else \
                           COLOR_L2 if row.match_layer == 2 else COLOR_L3
        fill = PatternFill("solid", fgColor=layer_fill_color)
        vals = [
            _t("status_matched", lang),
            _layer_label(row.match_layer, lang),
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit or "",
            row.gl_credit or "",
            row.date_diff_days if row.date_diff_days is not None else "",
            row.source_stmt_file,
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    # GL-only block (purple tint)
    for row in gl_only_rows_for_export:
        fill = PatternFill("solid", fgColor=COLOR_GL_ONLY if ri % 2 == 0 else "F3E8FF")
        vals = [
            _status_label(row.match_status, lang),
            _DASH,
            "",  # stmt date
            "",  # stmt desc
            "",  # stmt withdrawal
            "",  # stmt deposit
            "",  # stmt balance
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit or "",
            row.gl_credit or "",
            "",  # date diff
            "",  # source stmt
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    # Stmt-only block (blue tint)
    for row in stmt_only_rows_for_export:
        fill = PatternFill("solid", fgColor=COLOR_ST_ONLY if ri % 2 == 0 else "EBF5FB")
        vals = [
            _status_label(row.match_status, lang),
            _DASH,
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            "",  # gl date
            "",  # gl doc
            "",  # gl acct
            "",  # gl desc
            "",  # gl debit
            "",  # gl credit
            "",  # date diff
            row.source_stmt_file,
            "",  # source gl
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    _border_range(ws2, 1, max(1, ri - 1), 1, len(match_cols))
    ws2.freeze_panes = "C2"  # freeze status + match layer cols

    # ══════════════════════════════════════════════════════════════════
    # SHEET 5: Statement Detail (all parsed statement rows + OCR check)
    # v118.33.13.0
    # ══════════════════════════════════════════════════════════════════
    ws5 = wb.create_sheet(_t("sh_stmt_detail", lang))
    ws5.sheet_view.showGridLines = False

    sd_cols = [
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 38),
        (_t("col_withdrawal", lang), 14),
        (_t("col_deposit", lang), 14),
        (_t("col_balance", lang), 14),
        (_t("col_confidence", lang), 12),
        (_t("col_balance_ok", lang), 12),
        (_t("col_source_file", lang), 22),
    ]
    for ci, (hdr, width) in enumerate(sd_cols, 1):
        _hdr_style(ws5, 1, ci, hdr)
        ws5.column_dimensions[get_column_letter(ci)].width = width

    CONF_LBL = {
        "high":   _t("conf_high", lang),
        "medium": _t("conf_medium", lang),
        "low":    _t("conf_low", lang),
    }
    CONF_FILL = {"high": "D8F3DC", "medium": "FFF3CD", "low": "FFDAD6"}

    # Source: stmt-side rows (all of them — matched + stmt-only)
    stmt_side_rows = [r for r in recon_rows if r.stmt_date is not None or r.stmt_balance != 0
                      or r.stmt_withdrawal != 0 or r.stmt_deposit != 0]
    # Sort by stmt_date
    stmt_side_rows.sort(key=lambda x: (x.stmt_date or date.min, x.stmt_desc))

    for ri, row in enumerate(stmt_side_rows, 2):
        conf = (row.stmt_confidence or "high").lower()
        if row.stmt_balance_ok is True:
            bal_str = _t("bal_ok", lang); bal_fill = "D8F3DC"
        elif row.stmt_balance_ok is False:
            bal_str = _t("bal_warn", lang); bal_fill = "FFDAD6"
        else:
            bal_str = _t("bal_na", lang); bal_fill = None
        vals = [
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            CONF_LBL.get(conf, conf),
            bal_str,
            row.source_stmt_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws5.cell(ri, ci, val)
            cell.font = Font(size=9)
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            # Highlight confidence/balance columns
            if ci == 6:
                cell.fill = PatternFill("solid", fgColor=CONF_FILL.get(conf, "FFFFFF"))
                cell.alignment = Alignment(horizontal="center")
            if ci == 7 and bal_fill:
                cell.fill = PatternFill("solid", fgColor=bal_fill)
                cell.alignment = Alignment(horizontal="center")
        # Tint the whole row red if balance check failed
        if row.stmt_balance_ok is False:
            for ci in range(1, len(vals) + 1):
                if ws5.cell(ri, ci).fill.fgColor.rgb in (None, "00000000", "FFFFFFFF"):
                    ws5.cell(ri, ci).fill = PatternFill("solid", fgColor="FEF2F2")

    _border_range(ws5, 1, max(1, len(stmt_side_rows) + 1), 1, len(sd_cols))
    ws5.freeze_panes = "A2"

    # ══════════════════════════════════════════════════════════════════
    # SHEET 6: GL Detail (all GL rows reconstructed from recon_rows)
    # v118.34 · Mirrors Sheet 5 (Statement Detail) — same visual idiom
    # ══════════════════════════════════════════════════════════════════
    ws_gl = wb.create_sheet(_t("sh_gl_detail", lang))
    ws_gl.sheet_view.showGridLines = False

    gld_cols = [
        (_t("col_date", lang), 12),
        (_t("col_doc_no", lang), 16),
        (_t("col_account_code", lang), 14),
        (_t("col_desc", lang), 38),
        (_t("col_debit", lang), 14),
        (_t("col_credit", lang), 14),
        (_t("col_source_file", lang), 22),
    ]
    for ci, (hdr, width) in enumerate(gld_cols, 1):
        _hdr_style(ws_gl, 1, ci, hdr)
        ws_gl.column_dimensions[get_column_letter(ci)].width = width

    # Source: every recon_row that carries GL data
    # (matched rows + gl_debit_only + gl_credit_only).
    # Stmt-only rows have no GL data → excluded.
    gl_data_rows = [
        r for r in recon_rows
        if r.match_status == "matched"
        or r.match_status in ("gl_debit_only", "gl_credit_only")
    ]
    gl_data_rows.sort(
        key=lambda x: (x.gl_date or date.min, x.gl_doc_no or "", x.gl_account_code or "")
    )

    for ri, row in enumerate(gl_data_rows, 2):
        alt_fill = "F8F9FA" if ri % 2 == 0 else None
        vals = [
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit if row.gl_debit else "",
            row.gl_credit if row.gl_credit else "",
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws_gl.cell(ri, ci, val)
            cell.font = Font(size=9)
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            if alt_fill:
                cell.fill = PatternFill("solid", fgColor=alt_fill)

    _border_range(ws_gl, 1, max(1, len(gl_data_rows) + 1), 1, len(gld_cols))
    ws_gl.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# JSON SERIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def _date_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _date_from_str(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def rows_to_json(rows: List[BankReconRow]) -> List[Dict[str, Any]]:
    result = []
    for r in rows:
        result.append({
            "match_status": r.match_status,
            "match_layer": r.match_layer,
            "stmt_date": _date_str(r.stmt_date),
            "stmt_desc": r.stmt_desc,
            "stmt_withdrawal": r.stmt_withdrawal,
            "stmt_deposit": r.stmt_deposit,
            "stmt_balance": r.stmt_balance,
            "gl_date": _date_str(r.gl_date),
            "gl_doc_no": r.gl_doc_no,
            "gl_account_code": r.gl_account_code,
            "gl_desc": r.gl_desc,
            "gl_debit": r.gl_debit,
            "gl_credit": r.gl_credit,
            "date_diff_days": r.date_diff_days,
            "source_stmt_file": r.source_stmt_file,
            "source_gl_file": r.source_gl_file,
            # v118.33.13.0 · OCR accuracy verification
            "stmt_confidence": r.stmt_confidence,
            "stmt_balance_ok": r.stmt_balance_ok,
        })
    return result


def rows_from_json(data: List[Dict[str, Any]]) -> List[BankReconRow]:
    rows = []
    for d in (data or []):
        rows.append(BankReconRow(
            match_status=d.get("match_status", ""),
            match_layer=d.get("match_layer"),
            stmt_date=_date_from_str(d.get("stmt_date")),
            stmt_desc=d.get("stmt_desc", ""),
            stmt_withdrawal=float(d.get("stmt_withdrawal", 0) or 0),
            stmt_deposit=float(d.get("stmt_deposit", 0) or 0),
            stmt_balance=float(d.get("stmt_balance", 0) or 0),
            gl_date=_date_from_str(d.get("gl_date")),
            gl_doc_no=d.get("gl_doc_no", ""),
            gl_account_code=d.get("gl_account_code", ""),
            gl_desc=d.get("gl_desc", ""),
            gl_debit=float(d.get("gl_debit", 0) or 0),
            gl_credit=float(d.get("gl_credit", 0) or 0),
            date_diff_days=d.get("date_diff_days"),
            source_stmt_file=d.get("source_stmt_file", ""),
            source_gl_file=d.get("source_gl_file", ""),
            stmt_confidence=d.get("stmt_confidence", "high"),
            stmt_balance_ok=d.get("stmt_balance_ok"),
        ))
    return rows


def summary_to_json(s: BankReconSummary) -> Dict[str, Any]:
    return asdict(s)


def summary_from_json(d: Dict[str, Any]) -> BankReconSummary:
    if not d:
        return BankReconSummary()
    try:
        return BankReconSummary(**{k: v for k, v in d.items() if k in BankReconSummary.__dataclass_fields__})
    except Exception:
        return BankReconSummary()

# -----------------------------------------------------------------------------
# v118.34 - LEGACY BANK RECONCILIATION (migrated from bank_reconcile.py)
# Bank-statement-vs-invoice matching pipeline. Different product from
# bank_recon_v2's primary bank-statement-vs-GL reconciliation above -
# kept here so the project has a single home for bank reconciliation code.
# Used by /api/bank-recon/* routes in app.py.
# -----------------------------------------------------------------------------


@dataclass
class BankTransaction:
    """一条银行流水(解析后的标准结构)"""
    row_no: int
    tx_date: Optional[str]          # YYYY-MM-DD 字符串
    value_date: Optional[str]
    direction: str                  # "IN" / "OUT"
    amount: float
    balance_after: Optional[float]
    description: str
    counterparty: Optional[str] = None
    ref_no: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class ParsedStatement:
    """对账单完整解析结果"""
    bank_code: str                  # KBANK / SCB / BBL / OTHER
    account_last4: Optional[str]
    statement_month: Optional[str]  # YYYY-MM-01
    period_start: Optional[str]
    period_end: Optional[str]
    opening_balance: Optional[float]
    closing_balance: Optional[float]
    total_inflow: float
    total_outflow: float
    transactions: List[BankTransaction]
    pages: int
    parse_method: str               # "text_layer" / "gemini_vision"

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["transactions"] = [asdict(t) for t in self.transactions]
        return d


# ============================================================
# 银行识别:从 PDF 首页文字推断是哪家银行
# ============================================================
def detect_bank(full_text: str) -> str:
    """从文本判断银行 · 返回 bank_code"""
    lower = full_text.lower()
    # KBank (กสิกรไทย) · 关键词:KASIKORNBANK / K PLUS / กสิกรไทย
    if any(k in lower for k in ["kasikorn", "kbank", "k plus"]) or "กสิกรไทย" in full_text:
        return "KBANK"
    # SCB (ไทยพาณิชย์) · Siam Commercial Bank
    if "siam commercial" in lower or "scb" in lower or "ไทยพาณิชย์" in full_text:
        return "SCB"
    # BBL (กรุงเทพ) · Bangkok Bank
    if "bangkok bank" in lower or "bbl" in lower or "ธนาคารกรุงเทพ" in full_text:
        return "BBL"
    # KTB (กรุงไทย)
    if "krungthai" in lower or "ktb" in lower or "กรุงไทย" in full_text:
        return "KTB"
    # TMB / TTB
    if "ttb" in lower or "tmb" in lower or "ธนชาต" in full_text:
        return "TTB"
    return "OTHER"


# ============================================================
# 主入口:解析 PDF · 返回 ParsedStatement
# ============================================================
def parse_statement_pdf(pdf_bytes: bytes, filename: str = "") -> ParsedStatement:
    """
    解析银行对账单 PDF
    策略:
      1. 先尝试文本层提取(pdfminer)· 扫描的 PDF 则降级
      2. 根据关键词识别银行
      3. 按银行走专用模板解析 · 未识别银行走通用 Gemini vision
    """
    full_text = _extract_text_layer(pdf_bytes)
    pages = _count_pages(pdf_bytes)

    if full_text and len(full_text) > 200:
        bank_code = detect_bank(full_text)
        logger.info(f"[bank_recon] 文本层提取成功 · {len(full_text)} 字符 · 识别为 {bank_code}")
        try:
            if bank_code == "KBANK":
                return _parse_kbank_text(full_text, pages)
            if bank_code == "SCB":
                return _parse_scb_text(full_text, pages)
            if bank_code == "BBL":
                return _parse_bbl_text(full_text, pages)
            # 其他银行走通用正则
            return _parse_generic_text(full_text, pages, bank_code)
        except Exception as e:
            logger.warning(f"[bank_recon] 文本模板解析失败 · 降级 Gemini: {e}")

    # 文本层太少(扫描件)· 交给 Gemini vision
    logger.info("[bank_recon] 文本层不足 · 走 Gemini vision 解析")
    return _parse_via_gemini(pdf_bytes, pages)


# ============================================================
# 辅助:pdf 文本 + 页数提取
# ============================================================
def _extract_text_layer(pdf_bytes: bytes) -> str:
    """用 pdfminer 提文本层 · 无文本返回空串"""
    try:
        from io import BytesIO
        from pdfminer.high_level import extract_text
        return extract_text(BytesIO(pdf_bytes)) or ""
    except Exception as e:
        logger.warning(f"[bank_recon] pdfminer 提取失败: {e}")
        return ""


def _count_pages(pdf_bytes: bytes) -> int:
    try:
        from io import BytesIO
        from pypdf import PdfReader
        return len(PdfReader(BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


# ============================================================
# KBank 模板 · 列顺序:Date | Description | Cheque No | Deposit | Withdrawal | Balance
# ============================================================
# 示例行:01/12/24  TRANSFER FROM XXXX1234  5,000.00  123,456.78
# KBank 对账单一般是 DD/MM/YY 或 DD/MM/YYYY
_KBANK_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"       # date
    r"(.+?)\s+"                            # description
    r"(?:([\d,]+\.\d{2})\s+)?"             # deposit (optional)
    r"(?:([\d,]+\.\d{2})\s+)?"             # withdrawal (optional)
    r"([\d,]+\.\d{2})"                     # balance
)


def _parse_kbank_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening  # 用余额差推方向

    for i, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line:
            continue
        m = _KBANK_ROW.search(line)
        if not m:
            continue
        d_str, desc, dep, wdr, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        deposit = _parse_amount(dep)
        withdraw = _parse_amount(wdr)
        balance = _parse_amount(bal)

        # 先按"存款/取款"列判断(两列都有时用金额非零的那个)
        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        # 当有 2 个非零金额 · 或只有 1 个金额 · 用"余额差"兜底推方向
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                # 余额没变 · 看金额列
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            # 首行没有 prev_balance · 用关键词 + 金额列
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                # 都有金额,默认按第一个
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=_guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="KBANK",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


def _looks_like_outflow(desc: str) -> bool:
    """从描述判断是否为出账流水"""
    if not desc:
        return False
    u = desc.upper()
    out_kw = ["WITHDRAW", "WDRL", "FEE", "CHARGE", "PAY", "PAYMENT",
              "OUT", "DEBIT", "PURCHASE", "BUY",
              "ถอน", "ค่าธรรมเนียม", "ชำระ"]
    return any(k in u or k in desc for k in out_kw)


# ============================================================
# SCB 模板 · 列顺序:Date | Time | Code | Channel | Description | Debit | Credit | Balance
# ============================================================
_SCB_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"                 # date
    r"(?:\d{1,2}:\d{2}\s+)?"                         # time (optional)
    r"(?:([A-Z]{2,}\d*)\s+)?"                        # code (optional, like X0)
    r"(.+?)\s+"                                      # description
    r"(?:([\d,]+\.\d{2})\s+)?"                       # debit
    r"(?:([\d,]+\.\d{2})\s+)?"                       # credit
    r"([\d,]+\.\d{2})"                               # balance
)


def _parse_scb_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _SCB_ROW.search(line)
        if not m:
            continue
        d_str, code, desc, debit, credit, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        dr = _parse_amount(debit)
        cr = _parse_amount(credit)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (cr, dr) if v and v > 0]
        if not amount_pool:
            continue

        # 余额差兜底(当 PDF 文本空白被压缩导致列错位时尤为重要)
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if cr and cr > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif cr and cr > 0 and not (dr and dr > 0):
                direction = "IN"
                amount = cr
            elif dr and dr > 0 and not (cr and cr > 0):
                direction = "OUT"
                amount = dr
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=code or _guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="SCB",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# BBL 模板 · 列顺序和 KBank 接近
# ============================================================
_BBL_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"([A-Z]{2,5})?\s*"                              # channel code(可选)
    r"(.+?)\s+"
    r"(?:([\d,]+\.\d{2})\s+)?"                       # withdrawal
    r"(?:([\d,]+\.\d{2})\s+)?"                       # deposit
    r"([\d,]+\.\d{2})"                               # balance
)


def _parse_bbl_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _BBL_ROW.search(line)
        if not m:
            continue
        d_str, channel, desc, wdr, dep, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        withdraw = _parse_amount(wdr)
        deposit = _parse_amount(dep)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=channel or _guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="BBL",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 其他银行 · 通用正则(找 日期 + 金额 + 余额 的行)
# ============================================================
_GENERIC_ROW = re.compile(
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s+"
    r"(.+?)\s+"
    r"(-?[\d,]+\.\d{2})\s+"                          # 金额(可带负号)
    r"([\d,]+\.\d{2})"                                # 余额
)


def _parse_generic_text(text: str, pages: int, bank_code: str) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _GENERIC_ROW.search(line)
        if not m:
            continue
        d_str, desc, amt_str, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        amt = _parse_amount(amt_str)
        balance = _parse_amount(bal)
        if not amt:
            continue

        direction = "OUT" if amt < 0 else "IN"
        amount = abs(amt)
        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=_guess_channel(desc),
        ))

    return ParsedStatement(
        bank_code=bank_code,
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 扫描件 · Gemini vision 兜底(M10 轮 2 会真接通 · 本轮留 placeholder)
# ============================================================
def _parse_via_gemini(pdf_bytes: bytes, pages: int) -> ParsedStatement:
    """
    TODO M10 轮 2:接入 gemini_engine.recognize_pdf 的 vision 模式
    用一个专用 prompt 让 Gemini 输出 JSON:
    {
      "bank_code": "...",
      "account_last4": "...",
      "period_start": "YYYY-MM-DD",
      "transactions": [{"tx_date":"...","direction":"IN","amount":1000,"description":"..."}]
    }
    本轮:返回空结果 + 错误提示 · 让前端显示"扫描件暂不支持 · 请上传带文字层的 PDF"
    """
    return ParsedStatement(
        bank_code="OTHER",
        account_last4=None,
        statement_month=None,
        period_start=None,
        period_end=None,
        opening_balance=None,
        closing_balance=None,
        total_inflow=0.0,
        total_outflow=0.0,
        transactions=[],
        pages=pages,
        parse_method="gemini_vision_pending",
    )


# ============================================================
# 工具函数
# ============================================================
def _parse_amount(s: Optional[str]) -> Optional[float]:
    """'1,234.56' → 1234.56 · None / 空 → None"""
    if not s:
        return None
    try:
        return float(s.replace(",", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def _normalize_thai_date(s: str, reference: Optional[str] = None) -> Optional[str]:
    """
    DD/MM/YY 或 DD/MM/YYYY → YYYY-MM-DD
    泰国银行对账单年份经常用佛历(+543)· 自动转公历
    若年份只有 2 位 · 用 reference 年推断
    """
    if not s:
        return None
    # 支持 / 和 -
    parts = re.split(r"[/\-]", s.strip())
    if len(parts) != 3:
        return None
    try:
        dd, mm, yy = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    # 年份归一化
    if yy < 100:
        # 2 位 · 推测:> 50 归 19xx,其余归 20xx · 泰国一般都是近期
        yy = 2000 + yy if yy < 70 else 1900 + yy
    elif yy > 2400:
        # 佛历 → 公历
        yy -= 543
    # 基本验证
    if not (1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yy <= 2099):
        return None
    try:
        return date(yy, mm, dd).isoformat()
    except ValueError:
        return None


def _find_account_last4(text: str) -> Optional[str]:
    """从对账单头部找账号末 4 位"""
    # 匹配如 "Account No. xxx-x-xxxx1234" 或 "Acct XXX1234"
    patterns = [
        r"[Aa]ccount\s*(?:No|Number|#)?\.?\s*[:\s]*\S*?(\d{4})\b",
        r"[Aa]cct\.?\s*[:\s]*\S*?(\d{4})\b",
        r"เลขที่บัญชี\s*[:\s]*\S*?(\d{4})\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def _find_period(text: str) -> Tuple[Optional[str], Optional[str]]:
    """找对账周期起止 · 英文 'Period' / 泰文 'ประจำเดือน'"""
    # 'Period: 01/12/2024 - 31/12/2024'
    m = re.search(
        r"(?:Period|Statement\s*Period|Date\s*Range)[:\s]*"
        r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|to|ถึง)\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        text, re.IGNORECASE
    )
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    # 泰文格式:ตั้งแต่วันที่ X ถึง Y
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|ถึง|to)\s*(\d{1,2}/\d{1,2}/\d{2,4})", text)
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    return None, None


def _find_opening_closing(text: str) -> Tuple[Optional[float], Optional[float]]:
    """找期初 / 期末余额"""
    opening = None
    closing = None
    for pat in [
        r"[Oo]pening\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Bb]rought\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดยกมา[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            opening = _parse_amount(m.group(1))
            break
    for pat in [
        r"[Cc]losing\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Cc]arried\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดคงเหลือ[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            closing = _parse_amount(m.group(1))
            break
    return opening, closing


def _month_of(d_str: Optional[str]) -> Optional[str]:
    """'2024-12-15' → '2024-12-01'"""
    if not d_str:
        return None
    try:
        d = date.fromisoformat(d_str)
        return d.replace(day=1).isoformat()
    except ValueError:
        return None


def _guess_channel(desc: str) -> str:
    """根据描述猜测渠道类型"""
    if not desc:
        return ""
    u = desc.upper()
    if "ATM" in u:
        return "ATM"
    if "TRANSFER" in u or "TRF" in u or "โอน" in desc:
        return "TRANSFER"
    if "FEE" in u or "CHARGE" in u or "ค่าธรรมเนียม" in desc:
        return "FEE"
    if "CHEQUE" in u or "CHQ" in u or "เช็ค" in desc:
        return "CHEQUE"
    if "INTEREST" in u or "ดอกเบี้ย" in desc:
        return "INTEREST"
    if "SALARY" in u or "PAYROLL" in u or "เงินเดือน" in desc:
        return "SALARY"
    if "BILL" in u or "PAY" in u:
        return "BILLPAY"
    return ""


# ============================================================
# v0.18 · 匹配算法
# ============================================================

# 权重配置(总和 100)
_W_AMOUNT    = 50
_W_DATE      = 30
_W_DIRECTION = 15
_W_KEYWORD   = 5

# 阈值
THRESH_AUTO     = 85  # 自动选中
THRESH_SUGGEST  = 60  # 可显示为疑似

# 发票金额/日期误差容忍
AMOUNT_TOL_EQUAL    = 0.01    # 小于这个差值 = 金额精确一致
AMOUNT_TOL_SMALL    = 1.00    # 1 泰铢内
AMOUNT_TOL_MEDIUM   = 10.00   # 10 泰铢内(手续费差 / 汇率小差)
DATE_TOL_DAYS       = 7       # 超过 7 天不计候选


def score_amount(bank_amount: float, invoice_amount: float) -> float:
    """金额接近度 → 0..50"""
    if not bank_amount or not invoice_amount:
        return 0.0
    diff = abs(float(bank_amount) - float(invoice_amount))
    if diff <= AMOUNT_TOL_EQUAL:
        return float(_W_AMOUNT)                     # 完全一致
    if diff <= AMOUNT_TOL_SMALL:
        return float(_W_AMOUNT) - 5                 # 1 泰铢内:45
    if diff <= AMOUNT_TOL_MEDIUM:
        return float(_W_AMOUNT) - 15                # 10 泰铢内:35
    # 更大差距:按比例打分(误差 ≤ 1% 给 20 分,≤ 5% 给 10 分)
    pct = diff / max(float(invoice_amount), 0.01)
    if pct <= 0.01:
        return 20.0
    if pct <= 0.05:
        return 10.0
    return 0.0


def score_date(bank_date: Optional[str], invoice_date: Optional[str]) -> float:
    """日期接近度 → 0..30"""
    if not bank_date or not invoice_date:
        return 0.0
    try:
        d1 = date.fromisoformat(bank_date)
        d2 = date.fromisoformat(invoice_date)
    except (ValueError, TypeError):
        return 0.0
    days = abs((d1 - d2).days)
    if days == 0:
        return float(_W_DATE)                       # 同日:30
    if days <= 1:
        return 25.0
    if days <= 3:
        return 20.0
    if days <= 7:
        return 10.0
    return 0.0


def score_direction(bank_direction: str, invoice_meta: Dict[str, Any]) -> float:
    """方向一致性 → 0 或 15
    银行 OUT = 付出去钱 = 对应 采购/费用 发票(应付)
    银行 IN  = 收到钱    = 对应 销售/收入 发票(应收)
    判断依据:ocr_history 里的 category_tag / vendor 字段
    """
    if not bank_direction:
        return 0.0
    cat = (invoice_meta.get("category_tag") or "").lower()
    # 简单分类:销售/收入类 vs 采购/费用类
    income_words = ["sale", "sales", "revenue", "income", "销售", "收入"]
    expense_words = ["purchase", "expense", "cost", "fee",
                     "采购", "费用", "开支"]
    is_income = any(w in cat for w in income_words)
    is_expense = any(w in cat for w in expense_words)

    if bank_direction == "IN" and is_income:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and is_expense:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and not is_income:
        # 大多数 OCR 历史是采购发票(默认场景)
        return float(_W_DIRECTION) * 0.7            # 约 10 分
    # 其他情况:不扣分但不加分
    return float(_W_DIRECTION) * 0.3                # 约 4.5 分


def score_keyword(bank_desc: str, invoice_meta: Dict[str, Any]) -> float:
    """描述关键词相似 → 0..5 · 软加分"""
    if not bank_desc:
        return 0.0
    desc_lower = bank_desc.lower()
    vendor = (invoice_meta.get("vendor") or "").lower()
    ref = (invoice_meta.get("invoice_no") or "").lower()

    score = 0.0
    # 供应商名在描述里出现(取前 6 字符以上的片段)
    if vendor and len(vendor) >= 3:
        # 拆 vendor 单词 · 任一个在 desc 中出现就给分
        for w in re.findall(r"[A-Za-z\u0E00-\u0E7F\u4e00-\u9fff]{3,}", vendor):
            if w in desc_lower:
                score += 3.0
                break
    # 发票号在描述里
    if ref and ref in desc_lower:
        score += 2.0
    return min(score, float(_W_KEYWORD))


def match_one_tx(bank_tx: Dict[str, Any],
                 candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """对一条银行流水 · 在候选发票集合中打分排序 · 返回 [{history_id, score, reason, breakdown}, ...]"""
    scored: List[Dict[str, Any]] = []
    for inv in candidates:
        s_amt = score_amount(bank_tx.get("amount") or 0,
                              inv.get("amount_total") or inv.get("total") or 0)
        if s_amt <= 0:
            continue                                 # 金额差太大 · 直接跳过
        s_date = score_date(bank_tx.get("tx_date"), inv.get("invoice_date"))
        s_dir  = score_direction(bank_tx.get("direction") or "", inv)
        s_kw   = score_keyword(bank_tx.get("description") or "", inv)
        total = round(s_amt + s_date + s_dir + s_kw, 2)

        # 生成人类可读原因
        parts = []
        if s_amt >= _W_AMOUNT - 0.5:
            parts.append("金额精确")
        elif s_amt >= _W_AMOUNT - 5.5:
            parts.append("金额接近")
        if s_date >= _W_DATE - 0.5:
            parts.append("同日")
        elif s_date >= 25:
            parts.append("日期差 1 天")
        elif s_date >= 20:
            parts.append("日期差 3 天内")
        elif s_date >= 10:
            parts.append("日期差 7 天内")
        if s_kw > 0:
            parts.append("描述匹配")
        reason = " + ".join(parts) if parts else "低置信"

        scored.append({
            "history_id": inv["id"],
            "score": total,
            "reason": reason,
            "breakdown": {
                "amount":    s_amt,
                "date":      s_date,
                "direction": s_dir,
                "keyword":   s_kw,
            },
        })
    # 按分降序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]                                # 最多留 5 个候选


# ============================================================
# Session 级匹配:遍历所有流水 · 查候选 · 写结果
# ============================================================
def run_matching_for_session(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    对一个对账会话下的所有流水跑匹配
    返回统计:{tx_total, matched, suggested, unmatched, elapsed_ms}
    """
    import time
    import db

    t0 = time.time()
    txs = db.list_bank_recon_transactions(session_id, user_id, limit=2000)
    if not txs:
        return {"tx_total": 0, "matched": 0, "suggested": 0, "unmatched": 0,
                "elapsed_ms": 0, "error": "no_transactions"}

    stat = {"matched": 0, "suggested": 0, "unmatched": 0}

    for tx in txs:
        # 只处理 unmatched / suggested(已被用户确认的 matched 跳过)
        if tx.get("match_status") == "matched":
            stat["matched"] += 1
            continue

        amt = tx.get("amount")
        tx_date = tx.get("tx_date")
        if not amt or not tx_date:
            stat["unmatched"] += 1
            continue

        # 预筛选候选
        if hasattr(tx_date, "isoformat"):
            tx_date_str = tx_date.isoformat()
        else:
            tx_date_str = str(tx_date)

        candidates = db.find_invoice_candidates_for_tx(
            user_id=user_id,
            amount=float(amt),
            tx_date=tx_date_str,
            amount_tol=AMOUNT_TOL_MEDIUM,
            date_tol_days=DATE_TOL_DAYS,
        )

        if not candidates:
            db.save_match_result(tx["id"], [],
                                  THRESH_AUTO, THRESH_SUGGEST)
            stat["unmatched"] += 1
            continue

        # 打分
        tx_for_score = {
            "amount":      float(amt),
            "tx_date":     tx_date_str,
            "direction":   tx.get("direction") or "",
            "description": tx.get("description") or "",
        }
        scored = match_one_tx(tx_for_score, candidates)

        # 写结果(算法内只保留 ≥ THRESH_SUGGEST 的)
        scored_kept = [s for s in scored if s["score"] >= THRESH_SUGGEST]
        final_status = db.save_match_result(
            tx["id"], scored_kept, THRESH_AUTO, THRESH_SUGGEST
        )
        stat[final_status] = stat.get(final_status, 0) + 1

    # 更新 session 头统计
    db.update_session_match_stats(session_id)

    elapsed = int((time.time() - t0) * 1000)
    return {
        "tx_total":   len(txs),
        "matched":    stat.get("matched", 0),
        "suggested":  stat.get("suggested", 0),
        "unmatched":  stat.get("unmatched", 0),
        "elapsed_ms": elapsed,
    }
