# -*- coding: utf-8 -*-
"""bank_stmt_text.py · Pearnly · raw text-line bank statement parsers.

Split verbatim from bank_recon_v2.py. Line-oriented fallback used when neither
pdfplumber tables nor word coordinates yield a usable statement.
"""

import logging
import re
from typing import List, Optional, Tuple

from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import (
    AMOUNT_TOL,
    _to_float,
    _parse_date,
)

logger = logging.getLogger(__name__)


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
        s = tok.replace(",", "").replace(" ", "")
        if not s:
            return None
        neg = s.startswith("-")
        if neg:
            s = s[1:]
        dot_count = s.count(".")
        if dot_count > 1:
            last_dot = s.rfind(".")
            s = s[:last_dot].replace(".", "") + s[last_dot:]
        try:
            v = float(s)
            return -v if neg else v
        except ValueError:
            return None

    _DATE_PREFIX = re.compile(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$")

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
                if any(
                    kw in desc_low for kw in ["จ่าย", "ถอน", "debit", "withdraw", "โอนออก", "ชำระ"]
                ):
                    withdrawal = amount
                else:
                    deposit = amount
        else:
            # No prev_balance yet — guess deposit
            deposit = amount

        prev_balance = balance
        closing = balance

        rows.append(
            StatementRow(
                date=d,
                description=desc,
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
            )
        )

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

    DATE_RE = re.compile(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$")
    TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")

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
        if "รายละเอียด" in line and i > 0:
            val_start = i + 1
            break

    hdr_data = lines[hdr_start:]
    val_data = lines[val_start:]
    data = hdr_data  # used by header extraction below

    def _is_num(s: str) -> bool:
        s = s.replace(",", "").replace(" ", "").lstrip("-")
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

    # Phase 1: extract transaction headers (date, time, desc) in order
    headers = []
    i = 0
    while i < len(data):
        if DATE_RE.match(data[i]):
            d_obj = _parse_date(data[i])
            if d_obj is None:
                i += 1
                continue
            time_str = ""
            desc = ""
            j = i + 1
            if j < len(data) and TIME_RE.match(data[j]):
                time_str = data[j]
                j += 1
            if j < len(data) and not DATE_RE.match(data[j]):
                first_tok = data[j].split()[0] if data[j].split() else ""
                if not _is_num(first_tok):
                    desc = data[j]
                    j += 1
            headers.append({"date": d_obj, "time": time_str, "desc": desc})
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
            values.append(("num", v, ""))
        else:
            rest = " ".join(toks[1:])
            values.append(("bal", v, rest))

    # Phase 3: pattern-match opening then alternating amt/bal
    opening = 0.0
    pairs = []
    state = "opening"
    cur_amt = None
    for kind, val, rest in values:
        if state == "opening":
            if kind == "num":
                opening = val
                state = "amt"
        elif state == "amt":
            if kind == "num":
                cur_amt = val
                state = "bal"
        elif state == "bal":
            if kind == "bal":
                pairs.append((cur_amt, val, rest))
                cur_amt = None
                state = "amt"
            elif kind == "num":
                cur_amt = val

    # Phase 4: drop first header if it's the opening (no time)
    if headers and not headers[0]["time"]:
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
            text_blob = (h["desc"] + " " + channel).lower()
            if ("รับโอน" in text_blob) or ("ฝาก" in text_blob and "ฝากด้วยเช็ค" not in text_blob):
                dep = amt
            elif ("โอนเงิน" in text_blob) or ("ถอน" in text_blob) or ("จ่าย" in text_blob):
                wd = amt
            else:
                if diff > 0:
                    dep = amt
                else:
                    wd = amt
        prev_balance = bal
        full_desc = h["desc"]
        if channel:
            full_desc = (full_desc + " " + channel).strip()
        rows.append(
            StatementRow(
                date=h["date"],
                description=full_desc,
                withdrawal=wd,
                deposit=dep,
                balance=bal,
            )
        )

    closing = rows[-1].balance if rows else 0.0
    return rows, opening, closing
