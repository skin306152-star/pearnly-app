# -*- coding: utf-8 -*-
"""
services/ocr/pipeline.py

Pipeline: orchestrate layer 1 + layer 2 + layer 3 for a complete OCR task.

What the pipeline does per page:
    1. Renders the page to PNG bytes (PDF input) / takes image bytes (image input)
    2. Runs layer 1 (Vision API): OCR text + word-level confidence + bboxes
    3. Runs layer 2 (Flash-Lite): text -> ThaiInvoice fields
    4. Evaluates trigger conditions (see _evaluate_triggers)
    5. Runs layer 3 (Flash visual fallback) ONLY for triggered pages
    6. Returns a unified PipelinePageResult per page + aggregate cost / latency

Trigger conditions (any one fires layer 3):
    - layer 1 page avg_confidence < CONFIDENCE_THRESHOLD (default 0.85)
    - layer 2 missing critical fields (invoice_number / total_amount)
    - amount math fails: |subtotal + vat - total_amount| > AMOUNT_TOLERANCE_THB
    - tax_id format invalid (non-empty but not 13 digits)
    - exception: `is_not_invoice=True` short-circuits — never trigger L3

Cost accounting (Gemini pricing as of 2026; updated to THB via THB_PER_USD):
    - Vision DOCUMENT_TEXT_DETECTION: $0.00150 / page (1000 free/month, ignored here)
    - Flash-Lite: $0.10/M input, $0.40/M output
    - Flash:      $0.30/M input, $2.50/M output

Public API:
    run_on_path(path, ...)         -> PipelineResult
    run_on_pdf_bytes(bytes, ...)   -> PipelineResult
    run_on_image_bytes(bytes, ...) -> PipelineResult

Env (all optional):
    OCR_PIPELINE_CONF_THRESHOLD   default 0.85
    OCR_PIPELINE_AMOUNT_TOL       default 0.5 (THB)
    OCR_PIPELINE_THB_PER_USD      default 35
    GOOGLE_APPLICATION_CREDENTIALS (required, for layer 1 / Vision)
    GOOGLE_API_KEY or GEMINI_API_KEY (required, for layers 2 + 3)

This module does NOT integrate with app.py. The integration (single
feature-flag swap of the 4 OCR entry points) is migration-plan step.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Union

from . import direct_read
from .layer1_base import Layer1TransientError
from .layer1_vision import (
    Layer1PDFError,
)
from .layer2_gemini import Layer2TransientError
from .text_path import try_extract as _try_text_extract
from .table_path import (
    SUPPORTED_TABLE_EXTENSIONS,
    extract_from_table_file as _table_extract,
)
from .schemas import (
    BusinessDocumentType,
    Page,
    PipelinePageResult,
    PipelineResult,
)

logger = logging.getLogger(__name__)

from .triggers import (  # noqa: F401 · P-B 纯搬家 re-export(调用方 0 改动)
    AMOUNT_TOLERANCE_THB,
    CONFIDENCE_AUTO_THRESHOLD,
    CONFIDENCE_REVIEW_THRESHOLD,
    CONFIDENCE_THRESHOLD,
    CRITICAL_FIELDS,
    _aggregate_page_confidence,
    _bucket_confidence,
    _check_amount_math,
    _count_invoice_no_candidates,
    _evaluate_triggers,
)


from .pattern_memory import (  # noqa: F401 · P-C 纯搬家 re-export(调用方 0 改动)
    MIN_INSTANCES_BEFORE_FLAGGING,
    InvoicePatternMemory,
)


from .cost import (  # noqa: F401 · P-A 纯搬家 re-export(调用方 0 改动)
    COST_FLASHLITE_INPUT_PER_M_USD,
    COST_FLASHLITE_OUTPUT_PER_M_USD,
    COST_FLASH_INPUT_PER_M_USD,
    COST_FLASH_OUTPUT_PER_M_USD,
    COST_VISION_PER_PAGE_USD,
    THB_PER_USD,
    _compute_total_cost,
)


from .page_runner import (  # noqa: F401 · P-D verbatim 搬家 re-export(run_on_*/Step2-3 测 0 改动)
    OCR_PDF_PAGE_WORKERS,
    _process_one_page,
    _process_pages,
)

# ============================================================
# Constants / env-tunable thresholds
# ============================================================
# Step3(REFACTOR-WA-OCRPERF)· 图片上传送 Layer1 Vision 前的最长边上限(只缩不放)·
# 0 = 关闭压缩。A/B 已验 2400px 对真泰票 7 关键字段 0 变化 + L3 不升 + 更快。
# 仅作用于【图片上传】的 Layer1 输入;PDF 渲染图 + L3 兜底用全分辨率原图(不经此)。
OCR_IMG_MAX_LONG_EDGE = int(os.environ.get("OCR_IMG_MAX_LONG_EDGE", "2400"))


def downscale_image_bytes(image_bytes: bytes, max_long_edge: int) -> bytes:
    """图片上传送 Layer1 Vision 前按最长边 cap 压缩 · 只缩不放 · 小图原样。

    Step3(REFACTOR-WA-OCRPERF)· 仅用于【图片上传】路径的 Layer1 输入(run_on_image_bytes)·
    PDF 渲染图 / L3 视觉兜底用全分辨率原图(不调本函数)。
    任何异常 / 不需要 / 压完反而更大 → 返回原 bytes(绝不破坏识别)。
    保留格式(PNG→PNG · JPEG→JPEG q90);A/B 验证用 PNG resize·此处同口径。
    """
    if not image_bytes or not max_long_edge or max_long_edge <= 0:
        return image_bytes
    try:
        import io as _io
        from PIL import Image

        im = Image.open(_io.BytesIO(image_bytes))
        w, h = im.size
        longest = max(w, h)
        if longest <= max_long_edge:
            return image_bytes  # 小图原样 · 不放大
        sc = max_long_edge / longest
        fmt = (im.format or "PNG").upper()
        im2 = im.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
        buf = _io.BytesIO()
        if fmt in ("JPEG", "JPG"):
            im2.convert("RGB").save(buf, format="JPEG", quality=90)
        else:
            im2.save(buf, format="PNG")
        out = buf.getvalue()
        return out if 0 < len(out) < len(image_bytes) else image_bytes
    except Exception as e:  # 压缩绝不破坏识别 · 失败回退原图
        logger.warning("downscale_image_bytes failed (use original): %s", e)
        return image_bytes


DEFAULT_DPI = 200
DEFAULT_MAX_PAGES = 50

# Layer 0: pypdf text extraction fast path. When True and a PDF has an
# embedded text layer (avg chars/page >= 200), pipeline skips Vision API
# entirely — only Flash-Lite (+ optional Flash) runs. See text_path.py.
# Default False; production toggles via env once verified on real traffic.
DEFAULT_ENABLE_TEXT_PATH = (
    os.environ.get("OCR_FAST_PATH_ENABLED", "false").strip().lower() == "true"
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp", ".gif"}
PDF_EXTENSIONS = {".pdf"}
# 2026-05-21 multi-format refactor: Excel/CSV/Word bypass OCR entirely
# (table_path direct read). Final set comes from table_path.SUPPORTED_TABLE_EXTENSIONS.
TABLE_EXTENSIONS = SUPPORTED_TABLE_EXTENSIONS

# ============================================================
# Public API
# ============================================================
def run_on_path(
    path: Union[str, Path],
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
    enable_text_path: Optional[bool] = None,
    document_type: BusinessDocumentType = "auto",
) -> PipelineResult:
    """End-to-end pipeline on a file path (auto-detects PDF vs image).

    Args:
        path: file path (PDF or image)
        max_pages: max pages to process from PDF (default 50)
        dpi: DPI for PDF page render (default 200; architecture.md §7.5)
        api_key: Gemini API key override (else from env GOOGLE_API_KEY / GEMINI_API_KEY)
        enable_layer3: disable to test L1+L2 only (default True)
        fallback_to_layer2_on_layer3_error: when L3 fails (Layer3FallbackError,
            quota, transient), keep L2's invoice and mark needs_manual_review.
            False = re-raise the L3 exception.

    Returns:
        PipelineResult with per-page details + aggregate cost

    Raises:
        FileNotFoundError: path not found
        ValueError: unsupported extension
        Layer1PDFError / Layer1AuthError / etc.: layer 1 failures (always propagate)
        Layer2AuthError / Layer2QuotaError / Layer2TransientError / Layer2Error:
            layer 2 failures (always propagate)
        Layer3AuthError: always propagate (auth not recoverable)
        Layer3FallbackError / Layer3QuotaError / Layer3TransientError:
            if fallback_to_layer2_on_layer3_error=False, propagate; else captured
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"pipeline: file not found: {p}")
    file_bytes = p.read_bytes()
    ext = p.suffix.lower()
    if ext in PDF_EXTENSIONS:
        return run_on_pdf_bytes(
            file_bytes,
            max_pages=max_pages,
            dpi=dpi,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
            enable_text_path=enable_text_path,
            document_type=document_type,
        )
    if ext in IMAGE_EXTENSIONS:
        # Layer 0 text_path only applies to PDFs — images go straight to Vision
        return run_on_image_bytes(
            file_bytes,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
            document_type=document_type,
        )
    if ext in TABLE_EXTENSIONS:
        # 2026-05-21 multi-format refactor: Excel/CSV/Word bypass OCR
        # entirely. table_path reads the file structurally and produces
        # Layer1Result-shaped pages with table_rows / table_headers set.
        return run_on_table_bytes(
            file_bytes,
            filename=p.name,
            api_key=api_key,
            pattern_memory=pattern_memory,
            document_type=document_type,
        )
    raise ValueError(
        f"pipeline: unsupported extension {ext!r}; "
        f"supported: {sorted(PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS)}"
    )


def run_on_pdf_bytes(
    pdf_bytes: bytes,
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
    enable_text_path: Optional[bool] = None,
    document_type: BusinessDocumentType = "auto",
) -> PipelineResult:
    """Run pipeline on PDF bytes.

    Pipeline owns the PDF -> image rendering (so the image bytes are
    available for layer 3 visual fallback regardless of layer 0 outcome).

    When enable_text_path is True (or None and OCR_FAST_PATH_ENABLED env
    is true), pipeline first tries pypdf text extraction (layer 0). On
    hit, Vision API is skipped for all pages; text from pypdf feeds
    directly into Layer 2. On miss (avg chars < threshold, or pypdf
    error), falls back to the normal Vision -> Flash-Lite -> Flash chain.
    """
    if not pdf_bytes:
        raise Layer1PDFError("pipeline: empty PDF bytes")

    # Resolve enable_text_path: explicit arg > env default
    if enable_text_path is None:
        enable_text_path = DEFAULT_ENABLE_TEXT_PATH

    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        raise ImportError("pipeline: PyMuPDF (fitz) required for PDF rendering") from e

    t0 = time.time()

    # === Layer 0: try pypdf text extraction (cheap, free, electronic PDFs only) ===
    # If hit, we'll use these Page objects as layer 1 result, skipping Vision.
    # If miss, layer1_pages_override stays None and we run Vision normally.
    layer1_pages_override: Optional[List[Page]] = None
    if enable_text_path:
        try:
            text_l1 = _try_text_extract(pdf_bytes, max_pages=max_pages)
            if text_l1 is not None:
                layer1_pages_override = list(text_l1.pages)
        except Exception as _tpe:  # pragma: no cover  (defensive)
            logger.warning(
                "pipeline: text_path exception (fallback to Vision): %s",
                _tpe,
            )

    # === Render PDF pages (always, since layer 3 may need them even if text_path hit) ===
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise Layer1PDFError(f"pipeline: cannot open PDF: {type(e).__name__}: {e}") from e

    page_image_bytes_list: List[bytes] = []
    try:
        total = doc.page_count
        if total == 0:
            raise Layer1PDFError("pipeline: PDF has 0 pages")
        process = min(total, max_pages)
        if total > max_pages:
            logger.warning("pipeline: PDF has %d pages, processing first %d", total, max_pages)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for i in range(process):
            try:
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                page_image_bytes_list.append(pix.tobytes("png"))
            except Exception as e:
                raise Layer1PDFError(
                    f"pipeline: render page {i + 1}/{total} failed: " f"{type(e).__name__}: {e}"
                ) from e
    finally:
        doc.close()

    # Defensive: if text_path returned a different page count than render
    # (rare — implies pypdf and fitz disagree about page count), drop the
    # override and run full Vision to keep them consistent.
    if layer1_pages_override is not None and len(layer1_pages_override) != len(
        page_image_bytes_list
    ):
        logger.warning(
            "pipeline: text_path/render page count mismatch (%d vs %d) — "
            "dropping text_path override",
            len(layer1_pages_override),
            len(page_image_bytes_list),
        )
        layer1_pages_override = None

    # image-direct 直读(2026-07-05 S2 分流):扫描件短文档跳过 Vision。
    # 电子 PDF(text_path 命中)不经此;长表/多页对账件路由器直接放行到 Vision 路。
    engine = "pipeline_v1"
    if (
        layer1_pages_override is None
        and direct_read.enabled()
        and direct_read.route_direct(len(page_image_bytes_list), document_type)
    ):
        try:
            return direct_read.run_file(
                page_image_bytes_list, document_type=document_type, api_key=api_key
            )
        except direct_read.DirectReadFallback as e:
            logger.warning("pipeline: pdf direct-read fell back to Vision path: %s", e)
            engine = direct_read.ENGINE_FALLBACK

    page_results: List[PipelinePageResult] = _process_pages(
        page_image_bytes_list,
        layer1_pages_override,
        api_key=api_key,
        enable_layer3=enable_layer3,
        fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
        pattern_memory=pattern_memory,
        document_type=document_type,
    )

    elapsed_ms = int((time.time() - t0) * 1000)
    cost_thb = _compute_total_cost(page_results)
    return PipelineResult(
        pages=page_results,
        page_count=len(page_results),
        elapsed_ms=elapsed_ms,
        engine=engine,
        estimated_cost_thb=cost_thb,
    )


# L1/L2 瞬态(504 DeadlineExceeded / 5xx / 网络)重试次数。L3 瞬态已自回落 L2(page_runner),
# 但 L1/L2 瞬态此前直接抛 →「识别失败」让用户重拍(真票偶发)。重试 1 次治这类误失败。
OCR_TRANSIENT_RETRY = int(os.environ.get("OCR_TRANSIENT_RETRY", "1"))
_TRANSIENT_RETRY_SLEEP_S = 1.0


def _process_one_page_resilient(*args, **kwargs) -> PipelinePageResult:
    """对 L1/L2 瞬态错误重试再失败(图片上传路径)。Auth/Quota/解析错不重试(非瞬态)。"""
    for attempt in range(OCR_TRANSIENT_RETRY + 1):
        try:
            return _process_one_page(*args, **kwargs)
        except (Layer1TransientError, Layer2TransientError) as e:
            if attempt >= OCR_TRANSIENT_RETRY:
                raise
            logger.warning(
                "pipeline: L1/L2 transient (attempt %d/%d) · retrying: %s",
                attempt + 1,
                OCR_TRANSIENT_RETRY + 1,
                e,
            )
            time.sleep(_TRANSIENT_RETRY_SLEEP_S)


def run_on_image_bytes(
    image_bytes: bytes,
    api_key: Optional[str] = None,
    enable_layer3: bool = True,
    fallback_to_layer2_on_layer3_error: bool = True,
    pattern_memory: Optional[InvoicePatternMemory] = None,
    document_type: BusinessDocumentType = "auto",
) -> PipelineResult:
    """Run pipeline on a single image's bytes (PNG / JPG / WEBP / etc.)."""
    if not image_bytes:
        raise ValueError("pipeline: empty image bytes")

    t0 = time.time()
    # image-direct 直读(2026-07-05 S2 分流):单图默认跳过 Vision,原图直喂多模态。
    engine = "pipeline_v1"
    if direct_read.enabled() and direct_read.route_direct(1, document_type):
        try:
            return direct_read.run_file(
                [image_bytes], document_type=document_type, api_key=api_key
            )
        except direct_read.DirectReadFallback as e:
            logger.warning("pipeline: image direct-read fell back to Vision path: %s", e)
            engine = direct_read.ENGINE_FALLBACK

    # Step3(REFACTOR-WA-OCRPERF)· 仅图片上传:Layer1 Vision 用压缩版(最长边 cap)·
    # image_bytes 传原图全分辨率 → L3 兜底用原图。PDF 路径(run_on_pdf_bytes)不经此。
    _l1_img = downscale_image_bytes(image_bytes, OCR_IMG_MAX_LONG_EDGE)
    pr = _process_one_page_resilient(
        image_bytes,
        page_number=1,
        api_key=api_key,
        enable_layer3=enable_layer3,
        fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
        pattern_memory=pattern_memory,
        document_type=document_type,
        layer1_image_bytes_override=_l1_img,
    )
    elapsed_ms = int((time.time() - t0) * 1000)
    cost_thb = _compute_total_cost([pr])
    return PipelineResult(
        pages=[pr],
        page_count=1,
        elapsed_ms=elapsed_ms,
        engine=engine,
        estimated_cost_thb=cost_thb,
    )


def run_on_table_bytes(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str] = None,
    pattern_memory: Optional[InvoicePatternMemory] = None,
    document_type: BusinessDocumentType = "auto",
) -> PipelineResult:
    """Run pipeline on a table-shaped file (Excel/CSV/Word). NO OCR.

    2026-05-21 multi-format refactor: per request "Excel/CSV/Word 不要走
    OCR, 直接读取". table_path reads the file structurally and returns
    Layer1Result-shaped pages where Page.table_rows + Page.table_headers
    carry the grid. Layer 2 then serializes (header|cell|cell...) into text
    for the LLM so it can still pick out columns by name.

    Layer 1 Vision and Layer 3 visual fallback are BOTH skipped — there's
    no image to look at. If Layer 2 confidence is low, the result is
    marked needs_review rather than escalated.
    """
    if not file_bytes:
        raise ValueError("pipeline: empty table file bytes")

    t0 = time.time()
    layer1_result = _table_extract(file_bytes, filename=filename)

    page_results: List[PipelinePageResult] = []
    for l1_page in layer1_result.pages:
        # No image — pass image_bytes=b"" and skip layer 3 entirely
        pr = _process_one_page(
            image_bytes=b"",
            page_number=l1_page.page_number,
            api_key=api_key,
            enable_layer3=False,  # no image, no visual fallback
            fallback_to_layer2_on_layer3_error=True,
            pattern_memory=pattern_memory,
            layer1_page_override=l1_page,
            document_type=document_type,
        )
        page_results.append(pr)

    elapsed_ms = int((time.time() - t0) * 1000)
    cost_thb = _compute_total_cost(page_results)
    return PipelineResult(
        pages=page_results,
        page_count=len(page_results),
        elapsed_ms=elapsed_ms,
        engine="pipeline_v1_table",
        estimated_cost_thb=cost_thb,
    )
