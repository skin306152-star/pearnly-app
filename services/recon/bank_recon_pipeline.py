# -*- coding: utf-8 -*-
"""
services/recon/bank_recon_pipeline.py · Pearnly

Adapters bridging the unified services/ocr pipeline output to the recon
engine: parse statements / GL via the pipeline (Excel/CSV/Word/image) and
normalise into StatementRow / GlRow. The pdfplumber+Gemini paths stay in the
bank_recon_v2 orchestrators.
"""

import logging
from datetime import date
from typing import List, Dict, Any, Optional

from services.ocr.error_format import short_error as _short_err
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import _to_float, _parse_date, _BANK_SIGNATURES
from services.recon.bank_stmt_balance import finalize_rows
from services.recon.bank_stmt_xlsx import parse_bank_stmt_xlsx_direct
from services.recon.bank_stmt_legacy import gl_rows_from_pipeline_legacy

logger = logging.getLogger(__name__)


def statement_rows_from_entries(entries: List[Dict[str, Any]], filename: str) -> List[StatementRow]:
    """管线银行文档 entries → StatementRow 列表(单一转换事实源:pipeline 适配路与断链换眼
    重读路共用)。deposit/withdrawal/balance 由校验器保证来自各自列;两侧皆 0 的无动行跳过;
    日期优先取印刷原文(transaction_date_raw),回退归一化 transaction_date。"""
    rows: List[StatementRow] = []
    for e in entries:
        deposit = _to_float(e.get("deposit"))
        withdrawal = _to_float(e.get("withdrawal"))
        balance = _to_float(e.get("balance"))
        if deposit == 0.0 and withdrawal == 0.0:
            continue
        tx_date = _parse_date(e.get("transaction_date_raw") or "")
        if tx_date is None and e.get("transaction_date"):
            try:
                yy, mm, dd = e["transaction_date"].split("-")
                tx_date = date(int(yy), int(mm), int(dd))
            except (ValueError, AttributeError):
                tx_date = None
        rows.append(
            StatementRow(
                date=tx_date,
                description=e.get("description") or "",
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
                source_file=filename,
            )
        )
    return rows


def _parse_bank_stmt_via_pipeline(
    file_bytes: bytes, filename: str, tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route non-PDF bank statements through the
    unified pipeline with document_type='bank_statement', then convert to
    List[StatementRow] so the rest of bank-v2/run consumes it unchanged.

    Validators guarantee deposit/withdrawal/balance came from their
    respective columns — description / reference / account-number digits
    are rejected and cleared before this adapter runs.
    """
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
        from services.ocr.engine_policy import engine_context
    except ImportError as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": f"pipeline import failed: {e}",
        }

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]

    # v118.35.0.19 · xlsx/xls 优先走直读 fallback(零成本 · 跳 Gemini)
    # 用户上传自家导出 / 银行下载 / 自己整理的 Excel · 表头清晰时直读即可
    # 直读不命中(表头识别不出) → 自动降级到 Gemini pipeline
    if ext_dot in (".xlsx", ".xls", ".xlsm", ".csv", ".tsv"):
        direct = parse_bank_stmt_xlsx_direct(file_bytes, filename, tenant_id=tenant_id)
        if direct.get("ok"):
            logger.info(
                f"[stmt_parse][{filename}] xlsx_direct OK · {direct['row_count']} rows · skip Gemini"
            )
            return direct
        # ADR-006 · 新模板拿不准 → 走"确认列对应"· 不烧 Gemini · 原样上抛
        if direct.get("needs_mapping"):
            logger.info(f"[stmt_parse][{filename}] xlsx_direct needs_mapping · skip Gemini")
            return direct
        logger.info(
            f"[stmt_parse][{filename}] xlsx_direct miss({direct.get('error_code')}) · falling back to Gemini"
        )

    # 引擎策略生效域:本适配器 2026-05 写成直调 pipeline,而策略层 2026-07-04 才出生,
    # 只接了 recognize/core 与 controller 两处——银行整份解析从此一直吃 env 默认档,
    # 后台的 overrides_by_task.bank_statement 是白设(GC-D 记债 #3)。这里补上生效域,
    # 那条配置才真管得到银行。engine_context 可重入(已在域内原样透传),不会覆盖外层套餐档。
    try:
        with engine_context("bank_statement"):
            if ext_dot in IMAGE_EXTENSIONS:
                pr = _run_image(file_bytes, document_type="bank_statement")
            elif ext_dot in TABLE_EXTENSIONS:
                pr = _run_table(
                    file_bytes, filename=filename or "stmt", document_type="bank_statement"
                )
            else:
                return {
                    "ok": False,
                    "rows": [],
                    "row_count": 0,
                    "bank_code": "generic",
                    "error_code": "file_not_supported",
                    "error": f"unsupported format {ext_dot}",
                }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    pages = legacy.get("pages") or []
    if not pages:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": "no pages parsed",
        }
    doc = (pages[0] or {}).get("document") or {}
    bank_name_l = (doc.get("bank_name") or "").lower()
    bank_code = "generic"
    for code, sigs in _BANK_SIGNATURES.items():
        if any(s in bank_name_l or s in (doc.get("bank_name") or "") for s in sigs):
            bank_code = code
            break

    rows: List[StatementRow] = statement_rows_from_entries(doc.get("entries") or [], filename)

    # 台账#11 · 图片/扫描件路此前拿到行就直接返回,余额链定案序列(过滤汇总/方向纠正/逐行
    # 核对/金额反推修复)只跑 PDF 与 xlsx 路 → 实弹 5/56 行方向翻转静默放行。经 finalize_rows
    # 与其余两路同序接线;期初取文档级字段(无动行已被过滤,行内无从兜底)。
    opening = _to_float(doc.get("opening_balance"))
    closing = _to_float(doc.get("closing_balance"))
    rows = finalize_rows(rows, opening)
    balance_warn_count = sum(1 for r in rows if r.balance_ok is False)
    # A-4:改写过金额的行 balance_ok 已翻 True,不进 warn 口径 —— 单独计数,机器改的钱必须有人看。
    amount_fixed_count = sum(1 for r in rows if getattr(r, "amount_autocorrected", False))
    if not closing:
        closing = next((r.balance for r in reversed(rows) if r.balance), 0.0)

    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "opening": opening,
        "closing": closing,
        "bank_code": bank_code,
        "balance_warn_count": balance_warn_count,
        "amount_fixed_count": amount_fixed_count,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": bool(
            legacy.get("_needs_review", False) or balance_warn_count or amount_fixed_count
        ),
    }


def _parse_gl_via_pipeline(
    file_bytes: bytes, filename: str, account_code: str = ""
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route GL through services/ocr/pipeline with
    document_type='general_ledger', then convert to List[GlRow].

    记债:本路与银行整份解析同源,同样绕过 engine_context(overrides_by_task.gl_ledger
    对它无效,一直吃 env 默认档)。银行那条已于 2026-07-22 接上,GL 没接——接上会把 GL
    从 env 默认换成 economy 的轻量档,而 GL 长表的真料对照一次没做过,不在收尾顺手改。
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
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error": f"pipeline import failed: {e}",
        }
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
                "accounts": [],
                "error_code": "file_not_supported",
                "error": f"unsupported format {ext_dot}",
            }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    rows = gl_rows_from_pipeline_legacy(legacy)
    if account_code:
        rows = [r for r in rows if r.account_code == account_code]
    accounts = sorted({r.account_code for r in rows if r.account_code})
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "accounts": accounts,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }
