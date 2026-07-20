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
  ④ 每件最多一轮升档(不递归);
  ⑤ 逐页「渲染→读」合成单页任务并发跑(ThreadPoolExecutor):18 页串行 1.5-3 分钟压 reconcile
     步墙钟 → 并发收窄;渲染在任务内做、读完即释放,峰值内存受在飞页数(≤ max_workers)约束,
     不再全份 PNG 驻留。
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor

from services.recon.bank_recon_pipeline import statement_rows_from_entries
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_stmt_balance import finalize_rows

logger = logging.getLogger(__name__)

EYE_VISION = "vision"  # 整份一眼读(whole-PDF pdfplumber/Gemini)
EYE_DIRECT = "direct"  # 单页直读(direct_read.read_page)

# 渲染/重读上限:整份有断链才触发(罕见),但页数异常多的巨份跳过防跑飞成本。
_MAX_REREAD_PAGES = int(os.environ.get("OCR_BANK_REREAD_MAX_PAGES", "50"))
_RENDER_DPI = int(os.environ.get("OCR_BANK_REREAD_DPI", "200"))
# 换眼重读的并发度:每页一个「渲染→读」任务,在飞任务数即峰值内存与并发模型调用数的上限。
_MAX_WORKERS = max(1, int(os.environ.get("OCR_BANK_REREAD_WORKERS", "4")))


def enabled() -> bool:
    """秒级回退闸:OCR_BANK_CHAIN_REREAD=0 → 整份解析逐字节维持现状,零渲染零重读。"""
    return os.environ.get("OCR_BANK_CHAIN_REREAD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _count_breaks(rows: list[StatementRow]) -> int:
    """余额链断点数 = 逐行核对(prev+存-取==余额)对不上的动行数。依赖行已过余额链核对。"""
    return sum(1 for r in rows if r.balance_ok is False)


def _reread_one_page(
    pdf_bytes: bytes, page_number: int, filename: str, api_key: str | None
) -> list[StatementRow]:
    """单页任务:渲染该页 → 换眼直读 → StatementRow。渲染出的 PNG 只在本任务栈内存活,读完即释放
    (峰值内存受在飞任务数约束)。任一步异常向上抛,由编排层整轮弃保原读。"""
    image_bytes = _render_page(pdf_bytes, page_number)
    return _read_page_rows(image_bytes, page_number, filename, api_key)


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

    每页一个「渲染→读」任务经线程池并发跑、按页号顺序收拢保序;任一页(渲染或重读)失败 →
    取消余下任务、整轮弃保原读(半份重读会丢行,更差)。
    """
    if not enabled() or (ext or "").lower() != "pdf":
        return rows, []
    breaks_before = _count_breaks(rows)
    if breaks_before <= 0:
        return rows, []
    try:
        page_count = _pdf_page_count(file_bytes)
    except Exception as exc:  # noqa: BLE001 - 页数探测失败绝不断链整份解析
        logger.warning("[bank_reread][%s] page count failed, keep original: %r", filename, exc)
        return rows, []
    if page_count <= 0 or page_count > _MAX_REREAD_PAGES:
        return rows, []

    alt_rows: list[StatementRow] = []
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, page_count)) as pool:
        futures = [
            pool.submit(_reread_one_page, file_bytes, page_number, filename, api_key)
            for page_number in range(1, page_count + 1)
        ]
        try:
            for future in futures:  # 按页号顺序收拢,保原始行序
                alt_rows.extend(future.result())
        except Exception as exc:  # noqa: BLE001 - 单页渲染/重读崩 → 整轮弃(半份重读会丢行,更差)
            for pending in futures:
                pending.cancel()
            logger.warning("[bank_reread][%s] reread failed, keep original: %r", filename, exc)
            return rows, []

    alt = finalize_rows(alt_rows, opening)
    breaks_after = _count_breaks(alt)
    kept = bool(alt) and breaks_after < breaks_before
    escalation = {
        "pages": list(range(1, page_count + 1)),
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


def _default_pdf_page_count(pdf_bytes: bytes) -> int:
    """PDF 页数(open 一次读 page_count 即关,不驻留)。整份有断链才调,常态热路径零调用。"""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


def _default_render_page(pdf_bytes: bytes, page_number: int) -> bytes:
    """渲染单页 PNG(1-based · 与 pipeline.run_on_pdf_bytes 同渲染器 PyMuPDF/fitz)。

    每页任务内各自 open(fitz doc 不跨线程共享,逐任务独立 open 才线程安全),渲完即关。
    整份一眼读路径(pdfplumber 抽文本 / Gemini 直喂 PDF 字节)本就不产页图,无现成渲染可复用。
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        matrix = fitz.Matrix(_RENDER_DPI / 72.0, _RENDER_DPI / 72.0)
        return doc.load_page(page_number - 1).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
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


# 注入点:模块级绑定,单测用 bank_stmt_reread._pdf_page_count / _render_page / _read_page_rows
# = fake 替换,绝不触真渲染 / 真付费模型调用(照 reconcile_bank / stmt_totals 惯例)。
_pdf_page_count = _default_pdf_page_count
_render_page = _default_render_page
_read_page_rows = _default_read_page_rows
