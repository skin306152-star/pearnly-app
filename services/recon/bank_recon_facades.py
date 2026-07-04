# -*- coding: utf-8 -*-
"""Thin OCR-controller facades for bank reconciliation parsers."""

from __future__ import annotations

from typing import Any, Dict, Optional


def parse_bank_statement_pdf(
    file_bytes: bytes,
    filename: str,
    api_key: str = "",
    tenant_id: Optional[str] = None,
    *,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse a bank statement (any format). Facade -> controller(task=bank_statement)."""
    from services.ocr import controller
    from services.ocr.contracts import OcrRequest

    return controller.run(
        OcrRequest(
            task="bank_statement",
            file_bytes=file_bytes,
            filename=filename,
            api_key=api_key,
            tenant_id=tenant_id,
            plan_code=plan_code,
            is_exempt=is_exempt,
            user_type=user_type,
        )
    ).data


def parse_gl(
    file_bytes: bytes,
    filename: str,
    account_code: str = "",
    api_key: str = "",
    tenant_id: Optional[str] = None,
    *,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse a general ledger (any format). Facade -> controller(task=gl_ledger)."""
    from services.ocr import controller
    from services.ocr.contracts import OcrRequest

    return controller.run(
        OcrRequest(
            task="gl_ledger",
            file_bytes=file_bytes,
            filename=filename,
            api_key=api_key,
            tenant_id=tenant_id,
            plan_code=plan_code,
            is_exempt=is_exempt,
            user_type=user_type,
            options={"account_code": account_code},
        )
    ).data
