# -*- coding: utf-8 -*-
"""转换编排:PDF/图片 bytes → ConvertResult。

流程:抽文字层 → 有文字层按类型抽表 → 无文字层(扫描件)/图片走 OCR 桥(K1c)→ 守恒校验。
守恒校验不平进 result.issues,四态诚实由 result.conserved 承载。文字层路(convert_pages)
纯函数核心零改;OCR 路收在 ocr_bridge,本文件只做入口分流。
"""

from typing import List, Optional

from services.fileconv import ledger as ledger_mod
from services.fileconv import pdf_grid
from services.fileconv import tables as tables_mod
from services.fileconv import validate as validate_mod
from services.fileconv.classify import classify
from services.fileconv.model import (
    ConvertResult,
    Table,
    GL_LEDGER,
    BANK_STATEMENT,
    STATUS_OK,
)
from services.fileconv.text_layer import extract_pages, has_text_layer

_LEDGER_TYPES = (GL_LEDGER, BANK_STATEMENT)


def convert_pages(pages: List[str], source_name: str, grid=None) -> ConvertResult:
    """已抽好文字层的逐页文本 → ConvertResult(核心逻辑,便于单测直喂文本)。

    grid 是 pdf_grid 切出的规整网格(只有 PDF 入口拿得到)。给了就按真列位建表并按列下标做
    合计闭合校验;没给退回纯文字行 + 右对齐配对(行为与此前逐字节一致)。
    """
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

    lines = (
        tables_mod.from_grid(grid.rows) if grid is not None else tables_mod.extract_tabular(pages)
    )
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


def convert_pdf(
    pdf_bytes: bytes, source_name: str = "", *, tenant_id: Optional[str] = None
) -> ConvertResult:
    """入口:财务 PDF → ConvertResult。带文字层走纯函数路;无文字层(扫描件)转 OCR 桥。

    通用表另切一份真列位网格(pdf_grid 三级链)喂给 convert_pages:纯文字行在列间只有单空格
    的 PDF 上切不开(整行一格),那正是"33 行 × 1 列"与假差额的来源。
    """
    pages = extract_pages(pdf_bytes)
    if not has_text_layer(pages):
        from services.fileconv import ocr_bridge  # 懒加载:文字层路不牵连 OCR/pydantic 依赖

        return ocr_bridge.convert_scanned_pdf(pdf_bytes, source_name, tenant_id=tenant_id)
    layout = extract_pages(pdf_bytes, layout=True)
    return convert_pages(
        pages, source_name, grid=pdf_grid.extract_grid(pdf_bytes, pages_text=layout)
    )


def convert_image(
    image_bytes: bytes, source_name: str = "", *, tenant_id: Optional[str] = None
) -> ConvertResult:
    """入口:财务文件图片(jpg/png/webp)→ OCR 桥 → ConvertResult。"""
    from services.fileconv import ocr_bridge

    return ocr_bridge.convert_image(image_bytes, source_name, tenant_id=tenant_id)
