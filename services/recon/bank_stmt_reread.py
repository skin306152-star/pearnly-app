# -*- coding: utf-8 -*-
"""断链页换眼重读(GC-D-2)· Pearnly

多页银行对账单的整份解析(whole-PDF 一眼读)会系统性吞掉折行的结算行(SM 2569-05 实锤:
EDC/K SHOP ฿28,363 两代同位置被吞),而运维用「单页直读」重读同页即把页内断链补回。本模块把
这套换眼动作自动化:整份解析出的行集里余额链有断点时,把 PDF 逐页渲染、用另一只眼
(direct_read 单页直读)重读,严格更少断链才采纳,否则原样保留(fail-safe,绝不越改越差)。

纪律:
  ① 断链检测复用 bank_stmt_balance 的现成余额链纯函数(单一事实源),不另写一套算法;
  ② 另一只眼走现成入口 direct_read.read_page,不新造第三条模型调用路径;
  ③ 无断链 → 零渲染零重读零成本;渲染/重读任何异常 → 保原读,不让升档把整件搞挂;
  ④ 每件最多一轮升档(不递归)。
"""

from __future__ import annotations

import logging
import os

from services.recon.bank_recon_pipeline import statement_rows_from_entries
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_stmt_balance import (
    _correct_direction_from_balance,
    _repair_amount_from_balance,
    _verify_row_balances,
)
from services.recon.bank_table_io import _is_summary_row

logger = logging.getLogger(__name__)

EYE_VISION = "vision"  # 整份一眼读(whole-PDF pdfplumber/Gemini)
EYE_DIRECT = "direct"  # 单页直读(direct_read.read_page)

# 渲染/重读上限:整份有断链才触发(罕见),但页数异常多的巨份跳过防跑飞成本。
_MAX_REREAD_PAGES = int(os.environ.get("OCR_BANK_REREAD_MAX_PAGES", "50"))
_RENDER_DPI = int(os.environ.get("OCR_BANK_REREAD_DPI", "200"))


def enabled() -> bool:
    """秒级回退闸:OCR_BANK_CHAIN_REREAD=0 → 整份解析逐字节维持现状,零渲染零重读。"""
    return os.environ.get("OCR_BANK_CHAIN_REREAD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _count_breaks(rows: list[StatementRow]) -> int:
    """余额链断点数 = 逐行核对(prev+存-取==余额)对不上的动行数。依赖行已过 _verify_row_balances。"""
    return sum(1 for r in rows if r.balance_ok is False)


def _finalize(rows: list[StatementRow], opening: float) -> list[StatementRow]:
    """按主解析器同序把行集过一遍(过滤汇总行 → 方向纠正 → 逐行核对 → 金额反推修复),使重读
    结果与原读在同一口径下比较断链数。就地复用 bank_stmt_balance 现成纯函数(单一事实源)。"""
    kept = [r for r in rows if not _is_summary_row(r.description)]
    _correct_direction_from_balance(kept, opening)
    _verify_row_balances(kept, opening)
    _repair_amount_from_balance(kept, opening)
    return kept


def find_break_pages(page_groups: list[list[StatementRow]], opening: float) -> list[int]:
    """页级断链定位(纯函数)。page_groups = 按页有序的行组;返回含断链或紧邻断点的页号(0-based)。

    跨页交接的断链(前一页末行余额 → 后一页首行对不上)两侧的页都算候选——补拍/重读时相邻
    两页要一起换眼,单读一页补不回交接缺口。页内断则只标该页。复用 _verify_row_balances 标断点。
    """
    flat: list[StatementRow] = []
    page_of: list[int] = []
    for page_index, group in enumerate(page_groups):
        for row in group:
            flat.append(row)
            page_of.append(page_index)
    _verify_row_balances(flat, opening)
    pages: set[int] = set()
    for idx, row in enumerate(flat):
        if row.balance_ok is False:
            pages.add(page_of[idx])
            if idx > 0:
                pages.add(page_of[idx - 1])  # 断点另一侧(可能是上一页)
    return sorted(pages)


def maybe_reread_chain_breaks(
    rows: list[StatementRow],
    opening: float,
    *,
    file_bytes: bytes,
    filename: str,
    ext: str,
    api_key: str | None = None,
) -> tuple[list[StatementRow], list[dict]]:
    """整份 PDF 有余额链断链 → 逐页换眼(单页直读)重读,严格更少断链才采纳。

    返回 (rows, escalations)。escalations 为一条文件级留痕(pages/eye_from/eye_to/breaks_before/
    breaks_after/kept),供 item_bank_parsed 事件审计回放;无升档 → 空列表,调用方据此不加字段。

    只覆盖 PDF:xlsx/csv 直读路零成本零模型不入本路;单图直读路本身已是「另一只眼」,不重读。
    整份一眼读丢的是「哪几行」而非「哪一页」(页级来源信息在整份解析里已抹平),故无法把断点定位
    回具体页 → 有断链即逐页整份换眼重读、按文件级断链数仲裁,与运维手动补读同构。
    """
    if not enabled() or (ext or "").lower() != "pdf":
        return rows, []
    breaks_before = _count_breaks(rows)
    if breaks_before <= 0:
        return rows, []
    try:
        pages = _render_pages(file_bytes)
    except Exception as exc:  # noqa: BLE001 - 渲染失败绝不断链整份解析
        logger.warning("[bank_reread][%s] render failed, keep original: %r", filename, exc)
        return rows, []
    if not pages or len(pages) > _MAX_REREAD_PAGES:
        return rows, []

    alt_rows: list[StatementRow] = []
    for page_number, image_bytes in enumerate(pages, start=1):
        try:
            alt_rows.extend(_read_page_rows(image_bytes, page_number, filename, api_key))
        except Exception as exc:  # noqa: BLE001 - 单页重读崩 → 整轮弃(半份重读会丢行,更差)
            logger.warning(
                "[bank_reread][%s] page %d reread failed, keep original: %r",
                filename,
                page_number,
                exc,
            )
            return rows, []

    alt = _finalize(alt_rows, opening)
    breaks_after = _count_breaks(alt)
    kept = bool(alt) and breaks_after < breaks_before
    escalation = {
        "pages": list(range(1, len(pages) + 1)),
        "eye_from": EYE_VISION,
        "eye_to": EYE_DIRECT,
        "breaks_before": breaks_before,
        "breaks_after": breaks_after,
        "kept": kept,
    }
    if kept:
        logger.info(
            "[bank_reread][%s] adopted direct reread: breaks %d→%d",
            filename,
            breaks_before,
            breaks_after,
        )
        return alt, [escalation]
    logger.info(
        "[bank_reread][%s] kept original: breaks %d vs reread %d",
        filename,
        breaks_before,
        breaks_after,
    )
    return rows, [escalation]


def _default_render_pages(pdf_bytes: bytes) -> list[bytes]:
    """PDF 逐页渲染 PNG(与 pipeline.run_on_pdf_bytes 同渲染器 PyMuPDF/fitz)。

    整份一眼读路径(pdfplumber 抽文本 / Gemini 直喂 PDF 字节)本就不产页图,无现成渲染可复用;
    这里是唯一一次渲染,一页只渲一次。渲染只在整份有断链时发生(罕见),常态热路径零渲染。
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        matrix = fitz.Matrix(_RENDER_DPI / 72.0, _RENDER_DPI / 72.0)
        return [
            doc.load_page(i).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
            for i in range(doc.page_count)
        ]
    finally:
        doc.close()


def _default_read_page_rows(
    image_bytes: bytes, page_number: int, filename: str, api_key: str | None
) -> list[StatementRow]:
    """单页直读(现成入口 direct_read.read_page)→ StatementRow 列表。entries→行转换复用
    bank_recon_pipeline.statement_rows_from_entries(与整份 pipeline 路同一转换,单一事实源)。"""
    from services.ocr import direct_read

    result = direct_read.read_page(
        image_bytes, page_number, document_type="bank_statement", api_key=api_key
    )
    doc = result.document.model_dump(mode="json") if result.document is not None else {}
    return statement_rows_from_entries(doc.get("entries") or [], filename)


# 注入点:模块级绑定,单测用 bank_stmt_reread._render_pages / _read_page_rows = fake 替换,
# 绝不触真渲染 / 真付费模型调用(照 reconcile_bank / stmt_totals 惯例)。
_render_pages = _default_render_pages
_read_page_rows = _default_read_page_rows
