# -*- coding: utf-8 -*-
"""转换编排:PDF bytes → ConvertResult。

流程:抽文字层 → 无文字层则诚实拒绝 → 识别 doc_type → 按类型抽表 → 守恒校验。
守恒校验不平进 result.issues,四态诚实由 result.conserved 承载。
"""

from typing import List

from services.fileconv import ledger as ledger_mod
from services.fileconv import tables as tables_mod
from services.fileconv import validate as validate_mod
from services.fileconv.classify import classify
from services.fileconv.model import (
    ConvertResult,
    Table,
    GL_LEDGER,
    BANK_STATEMENT,
    STATUS_OK,
    STATUS_NO_TEXT_LAYER,
)
from services.fileconv.text_layer import extract_pages, has_text_layer

_LEDGER_TYPES = (GL_LEDGER, BANK_STATEMENT)


def convert_pages(pages: List[str], source_name: str) -> ConvertResult:
    """已抽好文字层的逐页文本 → ConvertResult(核心逻辑,便于单测直喂文本)。"""
    full_text = "\n".join(pages)
    doc_type = classify(full_text)

    if doc_type in _LEDGER_TYPES:
        rows, opening = ledger_mod.extract_ledger(pages)
        issues = validate_mod.validate_ledger(rows, opening)
        stats = validate_mod.ledger_stats(rows, opening)
        table = Table(
            name={GL_LEDGER: "GL Ledger", BANK_STATEMENT: "Bank Statement"}[doc_type],
            columns=ledger_mod.LEDGER_COLUMNS,
            rows=ledger_mod.to_table_rows(rows),
        )
        return ConvertResult(
            doc_type=doc_type,
            status=STATUS_OK,
            source_name=source_name,
            tables=[table],
            issues=issues,
            stats=stats,
        )

    lines = tables_mod.extract_tabular(pages)
    issues = validate_mod.validate_tabular(lines)
    stats = validate_mod.tabular_stats(lines)
    ncols = tables_mod.max_columns(lines)
    table = Table(
        name="Table",
        columns=[f"col{i}" for i in range(1, ncols + 1)],
        rows=tables_mod.to_table_rows(lines),
    )
    return ConvertResult(
        doc_type=doc_type,
        status=STATUS_OK,
        source_name=source_name,
        tables=[table],
        issues=issues,
        stats=stats,
    )


def convert_pdf(pdf_bytes: bytes, source_name: str = "") -> ConvertResult:
    """入口:带文字层的财务 PDF → ConvertResult。无文字层 → no_text_layer 拒绝。"""
    pages = extract_pages(pdf_bytes)
    if not has_text_layer(pages):
        return ConvertResult(
            doc_type="",
            status=STATUS_NO_TEXT_LAYER,
            source_name=source_name,
            stats={"reason": "无文字层(疑扫描件)· OCR 归 K1c"},
        )
    return convert_pages(pages, source_name)
