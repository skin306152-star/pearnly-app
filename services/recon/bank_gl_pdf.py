# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_pdf.py · Pearnly

PDF GL parser orchestration: pdfplumber table extraction → MR.ERP column
reader (bank_gl_pdf_mrerp) or text-line fallback, GL direction sanity check,
and the Gemini-vision fallback. Shared column recognition in bank_gl_common.
"""

import io
import re
import json
import logging
from datetime import date
from typing import List, Dict, Any, Optional, Tuple

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import (
    _to_float,
    _parse_date,
    _is_gl_skip_row,
    MIN_PLUMBER_ROWS,
)
from services.recon.bank_table_io import _pdf_extract_text_safe
from services.recon.bank_gl_common import _map_gl_cols, _extract_acct_code
from services.recon.bank_gl_pdf_mrerp import _parse_gl_mrerp_table

logger = logging.getLogger(__name__)


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
        return (
            "GL appears to be debit-only (no credit entries). This is likely "
            "an expense or asset ledger, not the cash/bank account ledger. "
            "Bank reconciliation expects the BANK ACCOUNT ledger where "
            "withdrawals appear as credits."
        )
    if total_debit == 0 and n_credit >= 3:
        return (
            "GL appears to be credit-only (no debit entries). This is likely "
            "a revenue or liability ledger, not the cash/bank account ledger."
        )
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
            logger.info(
                f"[gl_parse][{filename}] step3a mrerp: rows={len(rows)} accts={len(accounts_seen)}"
            )

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
            for row in table[header_idx + 1 :]:
                if not row:
                    continue
                row_list = [str(c or "").strip() for c in row]
                if _is_gl_skip_row(row_list):
                    continue
                d_str = (
                    row_list[col_map["date"]]
                    if "date" in col_map and col_map["date"] < len(row_list)
                    else ""
                )
                d = _parse_date(d_str) if d_str else None
                if d is not None:
                    last_tbl_date = d
                elif last_tbl_date is not None:
                    d = last_tbl_date
                else:
                    continue
                doc_no = (
                    row_list[col_map["doc_no"]]
                    if "doc_no" in col_map and col_map["doc_no"] < len(row_list)
                    else ""
                )
                desc = (
                    row_list[col_map["description"]]
                    if "description" in col_map and col_map["description"] < len(row_list)
                    else ""
                )
                debit = _to_float(
                    row_list[col_map["debit"]]
                    if "debit" in col_map and col_map["debit"] < len(row_list)
                    else 0
                )
                credit = _to_float(
                    row_list[col_map["credit"]]
                    if "credit" in col_map and col_map["credit"] < len(row_list)
                    else 0
                )
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
                rows.append(
                    GlRow(
                        date=d,
                        doc_no=doc_no,
                        account_code=acct,
                        description=desc,
                        debit=abs(debit),
                        credit=abs(credit),
                    )
                )
        if rows:
            logger.info(
                f"[gl_parse][{filename}] step3b col-map: rows={len(rows)} accts={len(accounts_seen)}"
            )

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
        "ok": True,
        "rows": rows,
        "accounts": sorted(accounts_seen - {"?"}),
        "opening": opening,
        "closing": closing,
        "row_count": len(rows),
    }
    if direction_warning:
        result["warning"] = direction_warning
    return result


def _parse_gl_text_lines(text: str, account_code: str = "") -> Tuple[List[GlRow], List[str], float]:
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
        if any(
            kw in low
            for kw in [
                "รายงาน",
                "account",
                "page",
                "หน้า",
                "บัญชี:",
                "ชื่อ",
                "รวม",
                "total",
                "สรุป",
                "หมายเหตุ",
                "note",
            ]
        ):
            continue

        # Account code header: "1112-01 CA K-BANK006-8-83962-9 215,228.06"
        # Starts with 3-6 digits then dash (NOT a date like "02/06/68")
        if re.match(r"^\d{3,6}-\d", line):
            nums = re.findall(r"[\d,]+\.\d+", line)
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
        rest = parts[d_offset + 1 :] if d_offset >= 0 else parts
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
        rows.append(
            GlRow(
                date=d,
                doc_no=doc_no,
                account_code=acct,
                description=desc,
                debit=abs(debit),
                credit=abs(credit),
            )
        )

    return rows, sorted(accounts_seen - {"?"}), opening


def _gemini_parse_gl(
    file_bytes: bytes, filename: str, account_code: str, api_key: str
) -> Dict[str, Any]:
    """Gemini fallback for GL PDF parsing."""
    try:
        import google.generativeai as genai
        import base64

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        b64 = base64.b64encode(file_bytes).decode()
        acct_hint = (
            f" Filter to account code starting with '{account_code}'." if account_code else ""
        )
        prompt = (
            "This is a General Ledger (GL) document.{hint} "
            "Extract ALL transaction rows as JSON with keys:\n"
            '  "opening_balance": number,\n'
            '  "accounts": [list of account codes found],\n'
            '  "rows": [{{date:"YYYY-MM-DD", doc_no:string, account_code:string, '
            "description:string, debit:number, credit:number}}]\n"
            "Return ONLY valid JSON."
        ).format(hint=acct_hint)

        # v118.35.0.62 · temperature=0 · GL 抽取同样要确定性(同源 PDF 每次结果一致)
        resp = model.generate_content(
            [{"mime_type": "application/pdf", "data": b64}, prompt],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "candidate_count": 1,
                "max_output_tokens": 32768,
            },
        )
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
            rows.append(
                GlRow(
                    date=d,
                    doc_no=str(r.get("doc_no", "")),
                    account_code=acct,
                    description=str(r.get("description", "")),
                    debit=float(r.get("debit", 0) or 0),
                    credit=float(r.get("credit", 0) or 0),
                )
            )

        opening = float(data.get("opening_balance", 0) or 0)
        closing = round(opening + sum(r.credit for r in rows) - sum(r.debit for r in rows), 2)
        return {
            "ok": True,
            "rows": rows,
            "accounts": sorted(accounts_seen - {"?"}),
            "opening": opening,
            "closing": closing,
            "row_count": len(rows),
        }

    except Exception as e:
        logger.warning(f"_gemini_parse_gl failed: {e}")
        return {"ok": False, "rows": [], "error": str(e)}
