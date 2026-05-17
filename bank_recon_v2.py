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
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
AMOUNT_TOL = 0.02          # baht tolerance for amount matching
DATE_TOL_DAYS = 3          # days tolerance for layer-2 matching
MIN_PLUMBER_ROWS = 3       # fallback to Gemini if pdfplumber yields < this

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
                    pass

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
            pass

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
                    pass
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
    }


def _gemini_parse_statement(file_bytes: bytes, filename: str, api_key: str) -> Dict[str, Any]:
    """
    Gemini fallback: extract bank statement data from scanned PDF.
    Returns {ok, rows, opening, closing, bank_code}
    """
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        b64 = base64.b64encode(file_bytes).decode()
        prompt = (
            "This is a bank statement PDF. Extract ALL transaction rows as JSON.\n"
            "Return a JSON object with keys:\n"
            '  "bank_code": string (kbank/bbl/kkp/ktb/scb/generic),\n'
            '  "opening_balance": number,\n'
            '  "closing_balance": number,\n'
            '  "rows": array of {date: "YYYY-MM-DD", description: string, '
            'withdrawal: number, deposit: number, balance: number}\n'
            "withdrawal and deposit are always positive numbers.\n"
            "Return ONLY valid JSON, no markdown."
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
        for r in raw_rows:
            d = _parse_date(str(r.get("date", "")))
            if d is None:
                continue
            rows.append(StatementRow(
                date=d,
                description=str(r.get("description", "")),
                withdrawal=float(r.get("withdrawal", 0) or 0),
                deposit=float(r.get("deposit", 0) or 0),
                balance=float(r.get("balance", 0) or 0),
            ))

        return {
            "ok": True,
            "rows": rows,
            "opening": float(data.get("opening_balance", 0) or 0),
            "closing": float(data.get("closing_balance", 0) or 0),
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
        pass
    # pypdf fallback
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return [pg.extract_text() or "" for pg in reader.pages]
    except Exception:
        pass
    return []


def parse_gl_pdf(
    file_bytes: bytes, filename: str, account_code: str = "", api_key: str = ""
) -> Dict[str, Any]:
    """
    Parse GL from PDF.
    Strategy: (1) extract text safely via pdfminer/pypdf (immune to KeyError('date'))
              (2) try pdfplumber table extraction (may crash on some PDFs — fully isolated)
              (3) if tables give < MIN_PLUMBER_ROWS, try text-line parser on extracted text
              (4) Gemini fallback if still < MIN_PLUMBER_ROWS and api_key provided
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
                    pass
                if not page_texts:
                    try:
                        page_texts.append(p.extract_text() or "")
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"pdfplumber [{filename}] skipped: {e}")

    # ── Step 3: parse table rows ──
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0

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

    # ── Step 4: text-line fallback (Mr.erp Thai GL format) ──
    if len(rows) < MIN_PLUMBER_ROWS and page_texts:
        full_text = "\n".join(page_texts)
        text_rows, text_accts, text_opening = _parse_gl_text_lines(full_text, account_code)
        if len(text_rows) >= len(rows):
            rows = text_rows
            accounts_seen = set(text_accts)
            opening = text_opening

    # ── Step 5: Gemini fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and api_key:
        return _gemini_parse_gl(file_bytes, filename, account_code, api_key)

    if not rows:
        hint = " (PDF has no extractable text)" if not any(t.strip() for t in page_texts) else ""
        return {"ok": False, "error": f"No GL rows found in PDF{hint}", "rows": []}

    total_credit = sum(r.credit for r in rows)
    total_debit = sum(r.debit for r in rows)
    closing = round(opening + total_credit - total_debit, 2)
    return {
        "ok": True, "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening, "closing": closing, "row_count": len(rows),
    }


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
        model = genai.GenerativeModel("gemini-2.0-flash")

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

    total_credit = sum(r.credit for r in all_rows)
    total_debit = sum(r.debit for r in all_rows)
    closing = round(opening + total_credit - total_debit, 2)

    return all_rows, sorted(all_accounts), opening, closing


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def _build_index(gl_rows: List[GlRow]) -> Dict[str, List[int]]:
    """Build amount→indices index for fast lookup."""
    idx: Dict[str, List[int]] = {}
    for i, r in enumerate(gl_rows):
        if r.debit > 0:
            key = f"D{r.debit:.2f}"
            idx.setdefault(key, []).append(i)
        if r.credit > 0:
            key = f"C{r.credit:.2f}"
            idx.setdefault(key, []).append(i)
    return idx


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
    "sh_unmatched_gl": {"th": "GL ไม่ตรง", "en": "Unmatched GL", "zh": "GL未匹配", "ja": "GL不一致"},
    "sh_unmatched_st": {"th": "บัญชีไม่ตรง", "en": "Unmatched Stmt", "zh": "账单未匹配", "ja": "明細不一致"},
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
    "col_source_stmt": {"th": "ไฟล์บัญชี", "en": "Stmt File", "zh": "账单文件", "ja": "明細ファイル"},
    "col_source_gl":   {"th": "ไฟล์ GL", "en": "GL File", "zh": "GL文件", "ja": "GLファイル"},
    # Summary labels
    "lbl_bank":        {"th": "ธนาคาร", "en": "Bank", "zh": "银行", "ja": "銀行"},
    "lbl_gl_acct":     {"th": "รหัสบัญชี GL", "en": "GL Account", "zh": "GL科目", "ja": "GL科目"},
    "lbl_stmt_open":   {"th": "ยอดเปิดต้นงวด (บัญชีธนาคาร)", "en": "Stmt Opening Balance", "zh": "账单期初余额", "ja": "明細期首残高"},
    "lbl_stmt_close":  {"th": "ยอดปิดปลายงวด (บัญชีธนาคาร)", "en": "Stmt Closing Balance", "zh": "账单期末余额", "ja": "明細期末残高"},
    "lbl_gl_open":     {"th": "ยอดเปิดต้นงวด (GL)", "en": "GL Opening Balance", "zh": "GL期初余额", "ja": "GL期首残高"},
    "lbl_gl_close":    {"th": "ยอดปิดปลายงวด (GL)", "en": "GL Closing Balance", "zh": "GL期末余额", "ja": "GL期末残高"},
    "lbl_open_diff":   {"th": "ผลต่างยอดเปิด", "en": "Opening Diff", "zh": "期初差异", "ja": "期首差異"},
    "lbl_matched":     {"th": "รายการที่จับคู่ได้", "en": "Matched Items", "zh": "已匹配项目", "ja": "一致項目"},
    "lbl_gl_debit_only": {"th": "GL เดบิตเท่านั้น (ไม่มีในบัญชีธนาคาร)", "en": "GL Debit Only (not in stmt)", "zh": "GL仅借方（账单无）", "ja": "GLのみ借方"},
    "lbl_gl_credit_only": {"th": "GL เครดิตเท่านั้น (ไม่มีในบัญชีธนาคาร)", "en": "GL Credit Only (not in stmt)", "zh": "GL仅贷方（账单无）", "ja": "GLのみ貸方"},
    "lbl_stmt_wd_only": {"th": "บัญชีถอนเท่านั้น (ไม่มีใน GL)", "en": "Stmt Withdrawal Only (not in GL)", "zh": "账单仅提款（GL无）", "ja": "明細のみ出金"},
    "lbl_stmt_dep_only": {"th": "บัญชีฝากเท่านั้น (ไม่มีใน GL)", "en": "Stmt Deposit Only (not in GL)", "zh": "账单仅存款（GL无）", "ja": "明細のみ入金"},
    "lbl_formula_calc": {"th": "ยอดปิดคำนวณ (สูตร)", "en": "Calculated Closing (formula)", "zh": "公式计算期末余额", "ja": "計算期末残高（公式）"},
    "lbl_formula_diff": {"th": "ผลต่าง (ควรเป็น 0)", "en": "Difference (should be 0)", "zh": "差异（应为0）", "ja": "差異（0が理想）"},
    "lbl_count":        {"th": "จำนวน", "en": "Count", "zh": "数量", "ja": "件数"},
    "lbl_amount":       {"th": "จำนวนเงิน", "en": "Amount", "zh": "金额", "ja": "金額"},
    "lbl_formula_title": {"th": "สูตรการสอบทาน", "en": "Reconciliation Formula", "zh": "对账公式", "ja": "照合公式"},
    "lbl_stats":        {"th": "สถิติ", "en": "Statistics", "zh": "统计", "ja": "統計"},
    # Match layer labels
    "layer_1":  {"th": "L1-ตรงวันที่", "en": "L1-ExactDate", "zh": "L1-精确日期", "ja": "L1-日付一致"},
    "layer_2":  {"th": "L2-ใกล้วันที่", "en": "L2-DateTol", "zh": "L2-日期容差", "ja": "L2-日付許容"},
    "layer_3":  {"th": "L3-เฉพาะยอด", "en": "L3-AmtOnly", "zh": "L3-仅金额", "ja": "L3-金額のみ"},
    # Status labels
    "st_gl_debit_only": {"th": "GL เดบิตเท่านั้น", "en": "GL Debit Only", "zh": "GL仅借方", "ja": "GLのみ借方"},
    "st_gl_credit_only": {"th": "GL เครดิตเท่านั้น", "en": "GL Credit Only", "zh": "GL仅贷方", "ja": "GLのみ貸方"},
    "st_stmt_wd_only": {"th": "บัญชีถอนเท่านั้น", "en": "Stmt Withdrawal Only", "zh": "账单仅提款", "ja": "明細のみ出金"},
    "st_stmt_dep_only": {"th": "บัญชีฝากเท่านั้น", "en": "Stmt Deposit Only", "zh": "账单仅存款", "ja": "明細のみ入金"},
    # File-info diagnostics sheet
    "sh_fileinfo":      {"th": "ข้อมูลไฟล์", "en": "File Info", "zh": "文件信息", "ja": "ファイル情報"},
    "fi_type":          {"th": "ประเภท", "en": "Type", "zh": "类型", "ja": "種別"},
    "fi_file":          {"th": "ชื่อไฟล์", "en": "File", "zh": "文件名", "ja": "ファイル"},
    "fi_rows":          {"th": "แถวที่พบ", "en": "Rows Found", "zh": "解析行数", "ja": "解析行数"},
    "fi_bank_acct":     {"th": "ธนาคาร/บัญชี", "en": "Bank/Account", "zh": "银行/科目", "ja": "銀行/科目"},
    "fi_status":        {"th": "สถานะ", "en": "Status", "zh": "状态", "ja": "状態"},
    "fi_error":         {"th": "ข้อผิดพลาด", "en": "Error", "zh": "错误", "ja": "エラー"},
    "fi_stmt_type":     {"th": "บัญชีธนาคาร", "en": "Bank Stmt", "zh": "银行账单", "ja": "銀行明細"},
    "fi_gl_type":       {"th": "GL", "en": "GL", "zh": "总账(GL)", "ja": "GL"},
    "fi_ok":            {"th": "✓ สำเร็จ", "en": "✓ OK", "zh": "✓ 成功", "ja": "✓ 成功"},
    "fi_warn":          {"th": "⚠ 0 แถว", "en": "⚠ 0 rows", "zh": "⚠ 0行", "ja": "⚠ 0行"},
    "fi_fail":          {"th": "✗ ล้มเหลว", "en": "✗ Failed", "zh": "✗ 失败", "ja": "✗ 失敗"},
}


def _t(key: str, lang: str) -> str:
    lang = lang if lang in ("th", "en", "zh", "ja") else "th"
    return (_I18N_EXPORT.get(key) or {}).get(lang) or (_I18N_EXPORT.get(key) or {}).get("en") or key


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
    # SHEET 0: File Info (parse diagnostics — always first sheet)
    # ══════════════════════════════════════════════════════════════════
    ws0 = wb.active
    ws0.title = _t("sh_fileinfo", lang)
    ws0.sheet_view.showGridLines = False
    ws0.column_dimensions["A"].width = 14
    ws0.column_dimensions["B"].width = 36
    ws0.column_dimensions["C"].width = 12
    ws0.column_dimensions["D"].width = 20
    ws0.column_dimensions["E"].width = 14
    ws0.column_dimensions["F"].width = 40

    # Title row
    ws0.merge_cells("A1:F1")
    t0 = ws0["A1"]
    t0.value = _t("sh_fileinfo", lang)
    t0.font = Font(bold=True, color="FFFFFF", size=12)
    t0.fill = PatternFill("solid", fgColor=COLOR_HEADER)
    t0.alignment = Alignment(horizontal="center", vertical="center")
    ws0.row_dimensions[1].height = 26

    # Column headers
    hdrs0 = [_t(k, lang) for k in ("fi_type", "fi_file", "fi_rows", "fi_bank_acct", "fi_status", "fi_error")]
    for ci, h in enumerate(hdrs0, 1):
        _hdr_style(ws0, 2, ci, h, color=COLOR_SUBHEAD)

    # Build rows from parse_info (or reconstruct from task_info)
    fi_rows: List[tuple] = []
    if parse_info:
        for f in (parse_info.get("stmt_files") or []):
            status = _t("fi_ok", lang) if (f.get("ok") and f.get("rows", 0) > 0) \
                else (_t("fi_warn", lang) if (f.get("ok") and f.get("rows", 0) == 0) \
                else _t("fi_fail", lang))
            fi_rows.append((_t("fi_stmt_type", lang), f.get("file",""),
                            f.get("rows", 0), f.get("bank_code",""), status, f.get("error","") or ""))
        for f in (parse_info.get("gl_files") or []):
            status = _t("fi_ok", lang) if (f.get("ok") and f.get("rows", 0) > 0) \
                else (_t("fi_warn", lang) if (f.get("ok") and f.get("rows", 0) == 0) \
                else _t("fi_fail", lang))
            accts = ", ".join(f.get("accounts") or [])
            fi_rows.append((_t("fi_gl_type", lang), f.get("file",""),
                            f.get("rows", 0), accts, status, f.get("error","") or ""))
    elif task_info:
        for fname in (task_info.get("stmt_files") or "").split(";"):
            fname = fname.strip()
            if not fname:
                continue
            rc = task_info.get("stmt_row_count", 0)
            status = _t("fi_ok", lang) if rc > 0 else _t("fi_warn", lang)
            fi_rows.append((_t("fi_stmt_type", lang), fname, rc,
                            task_info.get("bank_code",""), status, ""))
        for fname in (task_info.get("gl_files") or "").split(";"):
            fname = fname.strip()
            if not fname:
                continue
            rc = task_info.get("gl_row_count", 0)
            status = _t("fi_ok", lang) if rc > 0 else _t("fi_warn", lang)
            fi_rows.append((_t("fi_gl_type", lang), fname, rc,
                            task_info.get("gl_account",""), status, ""))

    STATUS_COLORS = {
        _t("fi_ok", lang):   "D8F3DC",
        _t("fi_warn", lang): "FFF3CD",
        _t("fi_fail", lang): "FFDAD6",
    }
    for ri, row_data in enumerate(fi_rows, 3):
        status_val = row_data[4]
        fill_color = STATUS_COLORS.get(status_val, None)
        for ci, val in enumerate(row_data, 1):
            cell = ws0.cell(row=ri, column=ci, value=val)
            cell.font = Font(size=9)
            cell.alignment = Alignment(vertical="center",
                                       horizontal="right" if ci == 3 else "left")
            if fill_color:
                cell.fill = PatternFill("solid", fgColor=fill_color)
        ws0.row_dimensions[ri].height = 18

    if fi_rows:
        _border_range(ws0, 2, 2 + len(fi_rows), 1, 6)
    ws0.freeze_panes = "A3"

    # ══════════════════════════════════════════════════════════════════
    # SHEET 1: Summary
    # ══════════════════════════════════════════════════════════════════
    ws1 = wb.create_sheet(_t("sh_summary", lang))
    ws1.sheet_view.showGridLines = False
    ws1.column_dimensions["A"].width = 42
    ws1.column_dimensions["B"].width = 16
    ws1.column_dimensions["C"].width = 14
    ws1.row_dimensions[1].height = 28

    # Title
    ws1.merge_cells("A1:C1")
    title_cell = ws1["A1"]
    _RECON_TITLE = {"en": "Bank Reconciliation", "zh": "银行对账", "th": "สอบทาน GL กับบัญชีธนาคาร", "ja": "銀行照合"}
    title_cell.value = f"{_RECON_TITLE.get(lang, 'Bank Reconciliation')} · {summary.bank_code.upper()}"
    title_cell.font = Font(bold=True, size=13, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor=COLOR_HEADER)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")

    r = 2
    # Info rows
    info_rows = [
        (_t("lbl_bank", lang), summary.bank_code.upper()),
        (_t("lbl_gl_acct", lang), summary.gl_account_code or "—"),
    ]
    for label, value in info_rows:
        _label_style(ws1, r, 1, label, bold=True)
        ws1.cell(r, 2, value).alignment = Alignment(vertical="center")
        r += 1

    r += 1
    # Balance table header
    ws1.merge_cells(f"A{r}:C{r}")
    _hdr_style(ws1, r, 1, _t("lbl_stats", lang), color=COLOR_SUBHEAD, size=9)
    r += 1

    balance_data = [
        (_t("lbl_stmt_open", lang),   summary.stmt_opening),
        (_t("lbl_stmt_close", lang),  summary.stmt_closing),
        (_t("lbl_gl_open", lang),     summary.gl_opening),
        (_t("lbl_gl_close", lang),    summary.gl_closing),
        (_t("lbl_open_diff", lang),   summary.opening_diff),
    ]
    for label, val in balance_data:
        _label_style(ws1, r, 1, label)
        _num_style(ws1, r, 2, val)
        r += 1

    r += 1
    # Reconciliation formula table
    ws1.merge_cells(f"A{r}:C{r}")
    _hdr_style(ws1, r, 1, _t("lbl_formula_title", lang), color=COLOR_SUBHEAD, size=9)
    r += 1

    formula_rows = [
        (_t("lbl_gl_close", lang),      summary.gl_closing,              ""),
        (_t("lbl_open_diff", lang),      summary.opening_diff,            "+/−"),
        (_t("lbl_gl_debit_only", lang),  -summary.gl_debit_only_amount,   "−"),
        (_t("lbl_gl_credit_only", lang), summary.gl_credit_only_amount,   "+"),
        (_t("lbl_stmt_wd_only", lang),   -summary.stmt_withdrawal_only_amount, "−"),
        (_t("lbl_stmt_dep_only", lang),  summary.stmt_deposit_only_amount, "+"),
        (_t("lbl_formula_calc", lang),   summary.formula_stmt_closing,    "="),
        (_t("lbl_stmt_close", lang),     summary.stmt_closing,            ""),
        (_t("lbl_formula_diff", lang),   summary.formula_diff,            ""),
    ]
    for label, val, sign in formula_rows:
        _label_style(ws1, r, 1, label)
        ws1.cell(r, 3, sign).alignment = Alignment(horizontal="center")
        fill = None
        if label == _t("lbl_formula_diff", lang):
            fill = COLOR_OK if abs(summary.formula_diff) < 0.05 else COLOR_DIFF
        _num_style(ws1, r, 2, val, fill_color=fill)
        r += 1

    r += 1
    # Count summary
    ws1.merge_cells(f"A{r}:C{r}")
    _hdr_style(ws1, r, 1, _t("lbl_count", lang), color=COLOR_SUBHEAD, size=9)
    r += 1

    _hdr_style(ws1, r, 1, _t("col_status", lang), color="555555", size=9)
    _hdr_style(ws1, r, 2, _t("lbl_count", lang), color="555555", size=9)
    _hdr_style(ws1, r, 3, _t("lbl_amount", lang), color="555555", size=9)
    r += 1

    count_data = [
        (_t("lbl_matched", lang), summary.matched_count, summary.stmt_total_deposit + summary.stmt_total_withdrawal - summary.stmt_deposit_only_amount - summary.stmt_withdrawal_only_amount),
        (_t("lbl_gl_debit_only", lang), summary.gl_debit_only_count, summary.gl_debit_only_amount),
        (_t("lbl_gl_credit_only", lang), summary.gl_credit_only_count, summary.gl_credit_only_amount),
        (_t("lbl_stmt_wd_only", lang), summary.stmt_withdrawal_only_count, summary.stmt_withdrawal_only_amount),
        (_t("lbl_stmt_dep_only", lang), summary.stmt_deposit_only_count, summary.stmt_deposit_only_amount),
    ]
    for label, cnt, amt in count_data:
        _label_style(ws1, r, 1, label)
        ws1.cell(r, 2, cnt).alignment = Alignment(horizontal="center")
        _num_style(ws1, r, 3, amt)
        r += 1

    _border_range(ws1, 1, r - 1, 1, 3)

    # ══════════════════════════════════════════════════════════════════
    # SHEET 2: Matched Rows
    # ══════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet(_t("sh_matched", lang))
    ws2.sheet_view.showGridLines = False

    matched_cols = [
        (_t("col_match_layer", lang), 14),
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 30),
        (_t("col_withdrawal", lang), 14),
        (_t("col_deposit", lang), 14),
        (_t("col_balance", lang), 14),
        (_t("col_gl_date", lang), 12),
        (_t("col_gl_doc", lang), 16),
        (_t("col_gl_acct", lang), 12),
        (_t("col_gl_desc", lang), 28),
        (_t("col_gl_debit", lang), 14),
        (_t("col_gl_credit", lang), 14),
        (_t("col_date_diff", lang), 10),
        (_t("col_source_stmt", lang), 20),
        (_t("col_source_gl", lang), 20),
    ]

    for ci, (hdr, width) in enumerate(matched_cols, 1):
        _hdr_style(ws2, 1, ci, hdr)
        ws2.column_dimensions[get_column_letter(ci)].width = width

    data_rows = [r for r in recon_rows if r.match_status == "matched"]
    for ri, row in enumerate(data_rows, 2):
        layer_fill = COLOR_MATCHED if row.match_layer == 1 else \
                     COLOR_L2 if row.match_layer == 2 else COLOR_L3
        fill = PatternFill("solid", fgColor=layer_fill)

        vals = [
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

    _border_range(ws2, 1, max(1, len(data_rows) + 1), 1, len(matched_cols))

    # ══════════════════════════════════════════════════════════════════
    # SHEET 3: Unmatched GL
    # ══════════════════════════════════════════════════════════════════
    ws3 = wb.create_sheet(_t("sh_unmatched_gl", lang))
    ws3.sheet_view.showGridLines = False

    gl_cols = [
        (_t("col_status", lang), 20),
        (_t("col_gl_date", lang), 12),
        (_t("col_gl_doc", lang), 16),
        (_t("col_gl_acct", lang), 12),
        (_t("col_gl_desc", lang), 32),
        (_t("col_gl_debit", lang), 14),
        (_t("col_gl_credit", lang), 14),
        (_t("col_source_gl", lang), 20),
    ]
    for ci, (hdr, width) in enumerate(gl_cols, 1):
        _hdr_style(ws3, 1, ci, hdr)
        ws3.column_dimensions[get_column_letter(ci)].width = width

    gl_only_rows = [r for r in recon_rows if r.match_status in ("gl_debit_only", "gl_credit_only")]
    for ri, row in enumerate(gl_only_rows, 2):
        fill = PatternFill("solid", fgColor=COLOR_GL_ONLY if ri % 2 == 0 else "F3E8FF")
        vals = [
            _status_label(row.match_status, lang),
            _fmt_date(row.gl_date),
            row.gl_doc_no, row.gl_account_code, row.gl_desc,
            row.gl_debit or "", row.gl_credit or "",
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws3.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            cell.font = Font(size=9)

    _border_range(ws3, 1, max(1, len(gl_only_rows) + 1), 1, len(gl_cols))

    # ══════════════════════════════════════════════════════════════════
    # SHEET 4: Unmatched Statement
    # ══════════════════════════════════════════════════════════════════
    ws4 = wb.create_sheet(_t("sh_unmatched_st", lang))
    ws4.sheet_view.showGridLines = False

    st_cols = [
        (_t("col_status", lang), 22),
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 32),
        (_t("col_withdrawal", lang), 14),
        (_t("col_deposit", lang), 14),
        (_t("col_balance", lang), 14),
        (_t("col_source_stmt", lang), 20),
    ]
    for ci, (hdr, width) in enumerate(st_cols, 1):
        _hdr_style(ws4, 1, ci, hdr)
        ws4.column_dimensions[get_column_letter(ci)].width = width

    stmt_only_rows = [r for r in recon_rows if r.match_status in ("stmt_withdrawal_only", "stmt_deposit_only")]
    for ri, row in enumerate(stmt_only_rows, 2):
        fill = PatternFill("solid", fgColor=COLOR_ST_ONLY if ri % 2 == 0 else "EBF5FB")
        vals = [
            _status_label(row.match_status, lang),
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "", row.stmt_deposit or "", row.stmt_balance or "",
            row.source_stmt_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws4.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            cell.font = Font(size=9)

    _border_range(ws4, 1, max(1, len(stmt_only_rows) + 1), 1, len(st_cols))

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
