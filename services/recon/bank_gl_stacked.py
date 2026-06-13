# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_stacked.py · Pearnly

Coordinate-driven GL parser for MR.ERP-style PDF ledgers.

These ledgers have no ruled table, so pdfplumber.extract_tables() returns
nothing; and the plain-text extractors emit the page in column-blocks (every
date+description first, then every amount, then every balance) which destroys
the row association. Both failures push GL parsing onto the costly,
truncation-prone Gemini path.

Here we reconstruct the visual table from word coordinates: cluster words by
their vertical position into rows, order each row left-to-right, then read the
date / doc / account / money columns by x-position. Debit vs credit is taken
from the running-balance movement (a deposit raises the bank balance → GL
debit; a withdrawal lowers it → GL credit), which matches the reconciler's
pairing (stmt.deposit ↔ gl.debit, stmt.withdrawal ↔ gl.credit) and is immune
to which raw column a figure lands in.
"""

import io
import re
import logging
from typing import List, Optional, Tuple

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import _to_float, _parse_date
from services.recon.bank_gl_common import _extract_acct_code

logger = logging.getLogger(__name__)

# Words within this many points of vertical offset belong to the same row.
_ROW_TOL = 3.0
# Money columns (debit/credit/balance) start well to the right of the account
# column; anything left of this is date / doc_no / description / account code.
_MONEY_X_MIN = 305.0
# Account-code column sits between the description and the money columns.
_ACCT_X_RANGE = (250.0, 305.0)
# All money figures are right-aligned, so the right edge (x1) identifies the
# column independent of the number's width. The running balance aligns far to
# the right (x1 ≈ 512); debit/credit amounts end well left of it (x1 ≲ 449).
# Anything ending at/after this boundary is the balance column.
_BALANCE_X1_MIN = 480.0

_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
_NUMERIC_RE = re.compile(r"^[\d.,]+$")
_ACCT_RE = re.compile(r"^[A-Za-z]?\d{3,}$")
_OPENING_KEYS = ("balance forward", "ยอดยกมา", "ยอดคงเหลือยกมา", "brought forward")


def _rows_by_position(file_bytes: bytes) -> List[List[dict]]:
    """Reconstruct visual rows (lists of word dicts, left-to-right) in page order."""
    import pdfplumber

    out: List[List[dict]] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            buckets: dict = {}
            for w in page.extract_words(use_text_flow=False):
                buckets.setdefault(round(w["top"] / _ROW_TOL), []).append(w)
            for key in sorted(buckets):
                out.append(sorted(buckets[key], key=lambda w: w["x0"]))
    return out


def _amount_and_balance(words: List[dict]) -> Tuple[Optional[float], Optional[float]]:
    """Read the (amount, balance) figures from a row by column position.

    Figures are split into the balance column (right edge ≥ _BALANCE_X1_MIN) and
    the debit/credit column (everything else right of the account). Fragments of
    one figure split by a grouping glyph are re-joined within their own column,
    so the balance can never absorb the amount even when they sit only a few
    points apart.
    """
    frags = [w for w in words if w["x0"] >= _MONEY_X_MIN and _NUMERIC_RE.match(w["text"])]
    bal_text = "".join(w["text"] for w in frags if w["x1"] >= _BALANCE_X1_MIN)
    amt_text = "".join(w["text"] for w in frags if w["x1"] < _BALANCE_X1_MIN)
    balance = _to_float(bal_text) if bal_text else None
    amount = _to_float(amt_text) if amt_text else None
    return amount, balance


def _row_fields(words: List[dict]) -> Optional[dict]:
    """Pull date / doc_no / description / account / amount / balance from one row."""
    date_str = next((w["text"] for w in words if _DATE_RE.match(w["text"])), None)
    if not date_str:
        return None
    amount, balance = _amount_and_balance(words)
    if balance is None:
        return None

    acct = next(
        (
            w["text"].strip()
            for w in words
            if _ACCT_X_RANGE[0] <= w["x0"] < _ACCT_X_RANGE[1] and _ACCT_RE.match(w["text"])
        ),
        "",
    )
    desc_tokens = [
        w["text"] for w in words if not _DATE_RE.match(w["text"]) and w["x0"] < _ACCT_X_RANGE[0]
    ]
    head = " ".join(desc_tokens).strip()

    return {
        "date_str": date_str,
        "head": head,
        "acct": acct,
        "amount": amount,
        "balance": balance,
    }


def parse_gl_stacked_pdf(
    file_bytes: bytes, account_code: str = ""
) -> Tuple[List[GlRow], List[str], float]:
    """Parse a coordinate-laid-out GL PDF. Returns (rows, account_codes, opening)."""
    try:
        visual_rows = _rows_by_position(file_bytes)
    except Exception as e:  # pdfplumber can throw on malformed PDFs — stay isolated
        logger.warning(f"_rows_by_position failed: {e}")
        return [], [], 0.0
    return _build_rows(visual_rows, account_code)


def _build_rows(
    visual_rows: List[List[dict]], account_code: str = ""
) -> Tuple[List[GlRow], List[str], float]:
    """Turn ordered visual rows into GlRows. Direction comes from balance movement."""
    rows: List[GlRow] = []
    accounts_seen: set = set()
    opening = 0.0
    prev_balance: Optional[float] = None

    for words in visual_rows:
        fields = _row_fields(words)
        if fields is None:
            continue

        if any(k in fields["head"].lower() for k in _OPENING_KEYS):
            opening = fields["balance"]
            prev_balance = opening
            continue

        balance = fields["balance"]
        if prev_balance is None:
            prev_balance = balance - (fields["amount"] or 0.0)
        delta = round(balance - prev_balance, 2)
        prev_balance = balance

        # Balance movement is authoritative for direction and magnitude; fall
        # back to the printed amount only when the balance held flat.
        amount = abs(delta) if delta != 0 else (fields["amount"] or 0.0)
        if amount == 0.0:
            continue
        debit = amount if delta >= 0 else 0.0
        credit = amount if delta < 0 else 0.0

        d = _parse_date(fields["date_str"])
        if d is None:
            continue

        head = fields["head"]
        doc_no = head.split(maxsplit=1)[0] if head else ""
        desc = head[len(doc_no) :].strip() or head
        acct = fields["acct"] or _extract_acct_code(doc_no) or _extract_acct_code(desc)
        if account_code and acct and not acct.startswith(account_code):
            continue

        accounts_seen.add(acct or "?")
        rows.append(
            GlRow(
                date=d,
                doc_no=doc_no,
                account_code=acct,
                description=desc,
                debit=debit,
                credit=credit,
            )
        )

    return rows, sorted(accounts_seen - {"?"}), opening
