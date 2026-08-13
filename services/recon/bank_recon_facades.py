# -*- coding: utf-8 -*-
"""Thin OCR-controller facades for bank reconciliation parsers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.cost.usage_context import usage_context
from services.ocr.pdf_utils import doc_page_count


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

    # 归因在 facade 而非各路由:两个调用点(网页 run + 异步 job)都是银行对账,
    # 且 doc_type 只有这一层分得清。上层若已设入口(如工单),外层入口优先,这里只补单据类型;
    # pages 同理在此补齐(PDF/图片的物理页数),否则 recon 行每页成本永远算不出。
    with usage_context(
        "bank_recon", doc_type="bank_statement", pages=doc_page_count(file_bytes, filename)
    ):
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

    with usage_context(
        "bank_recon", doc_type="gl_ledger", pages=doc_page_count(file_bytes, filename)
    ):
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
