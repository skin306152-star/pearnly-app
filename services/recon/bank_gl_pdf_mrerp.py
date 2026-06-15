# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_pdf_mrerp.py · Pearnly

MR.ERP GL PDF table parser: Thai text normalisation, strict numeric-token
detection, and the column-positional row reader that turns flattened pdf table
rows into GlRow. Used by the bank_gl_pdf orchestrator.
"""

import re
from datetime import date
from typing import List, Tuple, Optional

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import _to_float, _parse_date
from services.recon.bank_gl_common import _extract_acct_code


def _norm_thai(s: str) -> str:
    """v118.33.13.4 · Normalize Thai PUA characters that some PDF fonts emit
    instead of the standard Unicode codepoints. Thai PDFs encode combining
    tone marks in the Private Use Area (U+F70A..U+F712) rather than the
    standard U+0E47..U+0E4D range. The text renders identically but compares
    as a different string, breaking any keyword match against book types
    or other Thai tokens. Maps PUA glyphs back to standard combining marks."""
    if not s:
        return s
    return (
        s.replace("\uf70a", "\u0e48")  # mai-ek
        .replace("\uf70b", "\u0e49")  # mai-tho
        .replace("\uf70c", "\u0e4a")  # mai-tri
        .replace("\uf70d", "\u0e4b")  # mai-chattawa
        .replace("\uf70e", "\u0e4c")  # thantakhat
        .replace("\uf710", "\u0e4d")  # nikhahit
        .replace("\uf711", "\u0e31")  # mai-han-akat
        .replace("\uf712", "\u0e47")  # mai-taikhu
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


def _parse_gl_mrerp_table(
    table_rows, account_code: str = ""
) -> Tuple[List["GlRow"], List[str], float]:
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
        "รายงานแยกประเภท",
        "(รวมแผนก)",
        "วันที่จาก",
        "เลขที่บัญชี",
        "รวมทั้งสิ้น",
        "หมายเหตุ ในช่อง",
        "ชื่อบัญชี",
        ">>>>",
        "<<<<",
    )
    # Page header pattern: "หน้า : 1" (always has the colon)
    SKIP_REGEX = re.compile(r"หน้า\s*[:：]\s*\d|^\s*Page\s+\d|^E\s+จะหมายถึง")

    for table_row in table_rows or []:
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
        if ("วันที่" in line and "สมุด" in line) or (
            "เดบิท" in line and "เครดิต" in line and "ยอดคงเหลือ" in line
        ):
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

        # Collect contiguous monetary tokens at the RIGHT (strict check — NOT _to_float).
        # 金额必须带小数点或千分位(. 或 ,)· 裸整数(如泰文公司名/工号后缀「111」
        # 「บริษัท แจแปน 111 227,418.00」)是描述的一部分,不是金额 · 否则会被当成借/贷误读。
        num_vals: List[float] = []
        cut_idx = len(toks)
        for i in range(len(toks) - 1, -1, -1):
            tok = toks[i]
            if _is_numeric_tok(tok) and ("." in tok or "," in tok):
                num_vals.insert(0, _to_float(tok))
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

        after = front[d_idx + 1 :] if d_idx >= 0 else front
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
        rows.append(
            GlRow(
                date=d,
                doc_no=doc_no,
                account_code=acct,
                description=desc,
                debit=abs(debit_v),
                credit=abs(credit_v),
            )
        )

    return rows, sorted(accounts_seen - {"?"}), opening
