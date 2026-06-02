# -*- coding: utf-8 -*-
"""
services/recon/bank_stmt_legacy.py · Pearnly

Legacy bank-statement-vs-invoice pipeline orchestrator: bank detection, the
PDF → ParsedStatement entry point, and the unified-pipeline adapters. The
per-bank parsers and shapes live in bank_stmt_legacy_parsers; field helpers in
bank_stmt_legacy_fields. Consumed by /api/bank-recon/* via bank_recon_v2.
"""

import logging
from datetime import date
from typing import List, Dict, Any

from services.recon.bank_recon_types import GlRow
from services.recon.bank_recon_utils import _to_float, _parse_date
from services.recon.bank_stmt_legacy_parsers import (
    BankTransaction,
    ParsedStatement,
    _parse_kbank_text,
    _parse_scb_text,
    _parse_bbl_text,
    _parse_generic_text,
    _parse_via_gemini,
)

logger = logging.getLogger(__name__)


# ============================================================
# 2026-05-21 multi-format refactor · adapter for the unified pipeline
# ============================================================
def parsed_from_pipeline_legacy(legacy_dict: Dict[str, Any], filename: str) -> ParsedStatement:
    """Build a ParsedStatement from services/ocr/pipeline legacy dict output.

    The unified pipeline returns one normalized JSON per uploaded file with
    `document` populated when document_type=bank_statement. We pluck the
    BankStatementDocument off the first page and convert each
    BankStatementEntry into a BankTransaction so the rest of the bank
    reconciliation flow consumes it unchanged.

    All amounts are guaranteed to come from deposit/withdrawal/balance
    columns thanks to validators.validate_bank_document — description-
    column digits will NOT leak in here.
    """
    pages = legacy_dict.get("pages") or []
    if not pages:
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
            pages=0,
            parse_method="pipeline_v1_empty",
        )

    # The unified pipeline preserves the source ParsedStatement-shaped doc
    # in pages[0].document for bank_statement uploads.
    first_doc = (pages[0] or {}).get("document") or {}
    entries = first_doc.get("entries") or []

    bank_name = (first_doc.get("bank_name") or "").lower()
    bank_code = "OTHER"
    if (
        "kasikorn" in bank_name
        or "kbank" in bank_name
        or "กสิกร" in (first_doc.get("bank_name") or "")
    ):
        bank_code = "KBANK"
    elif "siam commercial" in bank_name or "scb" in bank_name:
        bank_code = "SCB"
    elif "bangkok bank" in bank_name or "bbl" in bank_name:
        bank_code = "BBL"
    elif "krungthai" in bank_name or "ktb" in bank_name:
        bank_code = "KTB"
    elif "krungsri" in bank_name or "ayudhya" in bank_name:
        bank_code = "BAY"
    elif "ttb" in bank_name or "tmb" in bank_name:
        bank_code = "TTB"

    transactions: List[BankTransaction] = []
    total_in = 0.0
    total_out = 0.0
    for idx, e in enumerate(entries, start=1):
        deposit = _to_float(e.get("deposit"))
        withdrawal = _to_float(e.get("withdrawal"))
        balance = _to_float(e.get("balance")) if e.get("balance") else None
        direction = "IN" if deposit > 0 else ("OUT" if withdrawal > 0 else "")
        if direction == "":
            continue  # skip header / summary rows that survived the LLM
        amount = deposit if direction == "IN" else withdrawal
        if direction == "IN":
            total_in += amount
        else:
            total_out += amount
        transactions.append(
            BankTransaction(
                row_no=idx,
                tx_date=e.get("transaction_date") or None,
                value_date=None,
                direction=direction,
                amount=amount,
                balance_after=balance,
                description=e.get("description") or "",
                counterparty=None,
                ref_no=e.get("reference") or None,
                channel=None,
            )
        )

    return ParsedStatement(
        bank_code=bank_code,
        account_last4=first_doc.get("account_last4") or None,
        statement_month=(
            (first_doc.get("period_start") or "")[:7] + "-01"
            if first_doc.get("period_start")
            else None
        ),
        period_start=first_doc.get("period_start") or None,
        period_end=first_doc.get("period_end") or None,
        opening_balance=(
            _to_float(first_doc.get("opening_balance"))
            if first_doc.get("opening_balance")
            else None
        ),
        closing_balance=(
            _to_float(first_doc.get("closing_balance"))
            if first_doc.get("closing_balance")
            else None
        ),
        total_inflow=total_in,
        total_outflow=total_out,
        transactions=transactions,
        pages=int(legacy_dict.get("page_count") or 1),
        parse_method="pipeline_v1_table",
    )


def gl_rows_from_pipeline_legacy(legacy_dict: Dict[str, Any]) -> List[GlRow]:
    """Adapter: services/ocr/pipeline GL output → List[GlRow] for matching.

    Use this in `/api/recon/bank-v2/run` when the uploaded GL file is
    Excel/CSV/Word so it bypasses Gemini Vision. document_type=general_ledger
    in the pipeline call guarantees:
        - amount comes from Debit/Credit columns only
        - description-column digits (e.g. '6091') are NOT parsed as amount
    """
    out: List[GlRow] = []
    for page in legacy_dict.get("pages") or []:
        doc = (page or {}).get("document") or {}
        for e in doc.get("entries") or []:
            debit = _to_float(e.get("debit"))
            credit = _to_float(e.get("credit"))
            if debit == 0.0 and credit == 0.0:
                continue
            tx_date_str = e.get("transaction_date") or ""
            tx_date = None
            if tx_date_str:
                try:
                    yy, mm, dd = tx_date_str.split("-")
                    tx_date = date(int(yy), int(mm), int(dd))
                except (ValueError, AttributeError):
                    tx_date = _parse_date(e.get("transaction_date_raw") or tx_date_str)
            out.append(
                GlRow(
                    date=tx_date,
                    doc_no=e.get("voucher_no") or "",
                    account_code=e.get("account_code") or "",
                    description=e.get("description") or "",
                    debit=debit,
                    credit=credit,
                    source_file="",
                )
            )
    return out


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
