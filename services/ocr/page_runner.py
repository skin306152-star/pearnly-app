# -*- coding: utf-8 -*-
"""
services/ocr/page_runner.py · REFACTOR-WB-modularize P-D(verbatim 搬家·0 逻辑改)

从 pipeline.py 抽出的 per-page L1→L2→(L3) 编排 + 多页调度:
  OCR_PDF_PAGE_WORKERS · _process_pages(多页并发/串行调度)· _process_one_page(单页编排)。
pipeline.py re-import 回原命名空间 → run_on_* 调用方 + Step2/Step3 单测 0 改动·对象身份不变。
"""

from __future__ import annotations

import contextvars
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from . import gemini_models, image_first
from .confidence import check_field_in_l1_text, find_field_min_word_conf
from .layer1_vision import extract_from_image_bytes as _l1_extract_image
from .layer2_structure import extract_from_page as _l2_extract_page
from .layer3_fallback import (
    Layer3AuthError,
    Layer3Error,
    Layer3FallbackError,
    Layer3QuotaError,
    Layer3TransientError,
    refine_page as _l3_refine_page,
)
from .pattern_memory import InvoicePatternMemory
from .schemas import BusinessDocumentType, Page, PipelinePageResult
from .triggers import (
    _aggregate_page_confidence,
    _bucket_confidence,
    _count_invoice_no_candidates,
    _evaluate_soft_flags,
    _evaluate_triggers,
)
from .validators import (
    validate_bank_document,
    validate_gl_document,
    validate_invoice,
)

logger = logging.getLogger(__name__)

# Step2(REFACTOR-WA-OCRPERF)· 多页 PDF 页面并行度 · 仅 pattern_memory is None(生产 web 路径)
# 时并发;并发 4 远低于 Vision 1800/min 配额 · 设 1 即退回串行。
OCR_PDF_PAGE_WORKERS = int(os.environ.get("OCR_PDF_PAGE_WORKERS", "4"))


def _process_pages(
    page_image_bytes_list: List[bytes],
    layer1_pages_override: Optional[list],
    *,
    api_key: Optional[str],
    enable_layer3: bool,
    fallback_to_layer2_on_layer3_error: bool,
    pattern_memory: Optional["InvoicePatternMemory"],
    document_type: "BusinessDocumentType",
) -> List[PipelinePageResult]:
    """Step2(REFACTOR-WA-OCRPERF)· 多页页面调度 · 【只改调度 · 单页 _process_one_page 调用一字不改】。

    pattern_memory is None(生产 web 路径)且多页 → ThreadPoolExecutor 并发(各页独立 ·
    无跨页 record 学习);pattern_memory 不为 None(跨页 pattern 学习有顺序依赖)或单页 →
    串行。并发分支结果按 page_number 排序还原页序(与串行输出逐项一致)。
    _process_one_page 内部自己 try/except 返回带 error 的 result(不抛)· 并发与串行错误语义一致。
    """

    def _run_page(i: int, image_bytes: bytes) -> PipelinePageResult:
        l1_override = layer1_pages_override[i - 1] if layer1_pages_override is not None else None
        return _process_one_page(
            image_bytes,
            page_number=i,
            api_key=api_key,
            enable_layer3=enable_layer3,
            fallback_to_layer2_on_layer3_error=fallback_to_layer2_on_layer3_error,
            pattern_memory=pattern_memory,
            layer1_page_override=l1_override,
            document_type=document_type,
        )

    n_pages = len(page_image_bytes_list)
    if pattern_memory is None and n_pages > 1 and OCR_PDF_PAGE_WORKERS > 1:
        workers = min(OCR_PDF_PAGE_WORKERS, n_pages)
        by_page: Dict[int, PipelinePageResult] = {}
        # 反馈闭环 ② · 把当前上下文(OCR 请求级 user/tenant)复制进 worker 线程,
        # 否则多页 PDF 的页工作线程读不到 contextvar → few-shot 注入漏掉多页场景。
        # 每个任务一份独立副本(Context 不可并发重入,不能跨 worker 复用同一个)。
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {
                ex.submit(contextvars.copy_context().run, _run_page, i, ib): i
                for i, ib in enumerate(page_image_bytes_list, start=1)
            }
            for fut in as_completed(futs):
                by_page[futs[fut]] = fut.result()
        return [by_page[i] for i in range(1, n_pages + 1)]
    # 串行(单页 / pattern_memory 学习路径)
    return [_run_page(i, ib) for i, ib in enumerate(page_image_bytes_list, start=1)]


# 复核屏「需复核高亮」的关键字段(与触发 Rule 4 同集)。
# 日期不入逐字段置信:存的是已转公历(2026-06-13)而 L1 文本是泰国原始格式(13/06/26·佛历
# 31.12.69)→ 恒不匹配 → 恒标「请核对」。佛历转换是确定性可靠的,日期不该靠像素置信复核
# (迎合泰国票据日期格式 · Zihao 2026-06-16)。
_FIELD_CONF_ATTRS = ("invoice_number", "total_amount", "seller_tax")


def _field_confidences(l1_page: Page, invoice) -> Dict[str, float]:
    """关键字段词级最低置信(0-1),喂复核屏字段三态着色。不在 OCR 文本(幻觉/缺)→ 0.0;
    在全文但无词级匹配(短值)→ 省略(不误标低)。"""
    out: Dict[str, float] = {}
    for attr in _FIELD_CONF_ATTRS:
        val = str(getattr(invoice, attr, "") or "").strip()
        if not val:
            continue
        if not check_field_in_l1_text(l1_page, val):
            out[attr] = 0.0
            continue
        conf = find_field_min_word_conf(l1_page, val)
        if conf is not None:
            out[attr] = round(float(conf), 4)
    return out


# ============================================================
# Internal: per-page orchestration
# ============================================================
def _process_one_page(
    image_bytes: bytes,
    page_number: int,
    api_key: Optional[str],
    enable_layer3: bool,
    fallback_to_layer2_on_layer3_error: bool,
    pattern_memory: Optional[InvoicePatternMemory] = None,
    layer1_page_override: Optional[Page] = None,
    document_type: BusinessDocumentType = "auto",
    layer1_image_bytes_override: Optional[bytes] = None,
) -> PipelinePageResult:
    """L1 -> L2 -> (maybe L3) for ONE page. Captures cost / latency / errors.

    If layer1_page_override is given (typically from text_path layer 0),
    Layer 1 Vision API is skipped — the supplied Page is used directly.
    image_bytes is still kept for potential Layer 3 visual fallback.

    Step3(REFACTOR-WA-OCRPERF)· layer1_image_bytes_override:给定时 Layer1 Vision 用它
    (图片上传压缩版)· image_bytes 仍是原图全分辨率 → L3 视觉兜底用原图(疑难票全清晰度)。
    """
    t_total = time.time()

    # --- Layer 1 (skipped if layer1_page_override provided) ---
    if layer1_page_override is None:
        t_l1 = time.time()
        _l1_input = (
            layer1_image_bytes_override if layer1_image_bytes_override is not None else image_bytes
        )
        l1_result = _l1_extract_image(_l1_input, page_number=page_number)
        l1_ms = int((time.time() - t_l1) * 1000)
        l1_page = l1_result.pages[0]
        l1_layer_name = "L1"
    else:
        l1_ms = 0  # text_path is essentially free per-page after PDF-level extract
        l1_page = layer1_page_override
        l1_layer_name = "text"

    # --- Layer 2 ---
    t_l2 = time.time()
    l2_result = _l2_extract_page(l1_page, api_key=api_key, document_type=document_type)
    l2_ms = int((time.time() - t_l2) * 1000)
    l2_invoice = l2_result.invoice
    l2_document = l2_result.document

    # --- Validators (2026-05-21 multi-schema refactor) ---
    # Run doc-type-specific validation: GL must not parse description numbers
    # as amounts, bank statement must source amounts from deposit/withdrawal,
    # invoice fields must come from total/subtotal/vat columns.
    validation_warnings: List[str] = list(l2_result.validation_warnings)
    if document_type == "general_ledger" and l2_document is not None:
        validation_warnings.extend(validate_gl_document(l2_document, l1_page))
    elif document_type == "bank_statement" and l2_document is not None:
        validation_warnings.extend(validate_bank_document(l2_document, l1_page))
    elif document_type in ("auto", "invoice"):
        validation_warnings.extend(validate_invoice(l2_invoice, l1_page))

    # --- Trigger evaluation (invoice path only — non-invoice docs use validators) ---
    # triggers gate the slow L3 visual re-read; soft_flags only lower confidence
    # to yellow_confirm (low word-conf on values that are present in L1 text).
    soft_flags: List[str] = []
    if document_type in ("auto", "invoice"):
        triggers = _evaluate_triggers(l1_page, l2_invoice, pattern_memory)
        soft_flags = _evaluate_soft_flags(l1_page, l2_invoice)
    else:
        # For non-invoice doc types, Layer 3 visual fallback is not yet
        # implemented. Triggers come from validators only.
        triggers = list(validation_warnings)

    # --- Layer 3 (conditional) ---
    invoice = l2_invoice
    document = l2_document
    layer_chain = [l1_layer_name, "L2"]
    l3_in_tokens = 0
    l3_out_tokens = 0
    l3_ms = 0
    needs_manual_review = False
    error_msg: Optional[str] = None

    # 2026-05-21 multi-schema refactor: L3 visual fallback only for invoice/auto.
    # Non-invoice docs route to needs_review when validators flag issues.
    l3_eligible = (
        triggers
        and enable_layer3
        and document_type in ("auto", "invoice")
        and image_bytes  # no image (table_path) → no visual fallback
    )

    if validation_warnings and document_type not in ("auto", "invoice"):
        needs_manual_review = True

    # image-first(OCR_IMAGE_FIRST 灰度 · 默认关):图直喂 2.5-flash 为主 → 低置信/关键
    # 字段缺升 3.5-flash · 替代触发式 L3(二选一)。默认关 → 走下方原 L3 路径不变。
    image_first_on = (
        image_first.is_enabled()
        and enable_layer3
        and document_type in ("auto", "invoice")
        and image_bytes
    )

    if image_first_on:
        try:
            res = image_first.run(
                image_bytes=image_bytes,
                l1_page=l1_page,
                l2_invoice=l2_invoice,
                trigger_reasons=triggers,
                api_key=api_key,
                document_type=document_type,
                refine=_l3_refine_page,
                field_conf_fn=_field_confidences,
                primary_model=gemini_models.flash(),
                escalate_model=gemini_models.escalate(),
            )
            invoice = res["invoice"]
            layer_chain = [l1_layer_name, "L2", *res["layers"]]
            l3_in_tokens = res["in_tokens"]
            l3_out_tokens = res["out_tokens"]
            l3_ms = res["ms"]
        except Layer3AuthError:
            raise
        except (
            Layer3FallbackError,
            Layer3QuotaError,
            Layer3TransientError,
            Layer3Error,
        ) as e:
            error_msg = f"image-first error: {e}"
            logger.warning("pipeline: image-first error on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = [l1_layer_name, "L2", "IF_failed"]
                needs_manual_review = True
            else:
                raise
    elif l3_eligible:
        try:
            l3_result = _l3_refine_page(
                image_bytes=image_bytes,
                layer1_page=l1_page,
                layer2_invoice=l2_invoice,
                trigger_reasons=triggers,
                api_key=api_key,
                document_type=document_type,
            )
            invoice = l3_result.invoice
            layer_chain = [l1_layer_name, "L2", "L3"]
            l3_in_tokens = l3_result.input_tokens
            l3_out_tokens = l3_result.output_tokens
            l3_ms = l3_result.elapsed_ms
        except Layer3AuthError:
            # Auth is never retryable / never fall-back-able — propagate
            raise
        except Layer3FallbackError as e:
            error_msg = f"L3 fallback error: {e}"
            logger.warning("pipeline: L3 fallback error on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = [l1_layer_name, "L2", "L3_failed"]
                needs_manual_review = True
            else:
                raise
        except Layer3QuotaError as e:
            error_msg = f"L3 quota: {e}"
            logger.warning("pipeline: L3 quota on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = [l1_layer_name, "L2", "L3_quota"]
                needs_manual_review = True
            else:
                raise
        except Layer3TransientError as e:
            error_msg = f"L3 transient: {e}"
            logger.warning("pipeline: L3 transient on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = [l1_layer_name, "L2", "L3_transient"]
                needs_manual_review = True
            else:
                raise
        except Layer3Error as e:
            # Other L3 errors — log + recover (same as fallback) to keep pipeline going
            error_msg = f"L3 error: {e}"
            logger.warning("pipeline: L3 error on page %d: %s", page_number, e)
            if fallback_to_layer2_on_layer3_error:
                layer_chain = [l1_layer_name, "L2", "L3_failed"]
                needs_manual_review = True
            else:
                raise

    total_ms = int((time.time() - t_total) * 1000)
    # 分段耗时(一行可 grep · 自带 request_id):定位 OCR 慢在哪层(L1 vision / L2 structure /
    # L3 fallback)。不记 OCR 文本(只记毫秒 + 层链),避免日志泄露票据内容。
    # P1G-Perf:加 l3_called + l3_skip,印证「触发收紧后多数票不进 L3」(spec §2 日志要求)。
    l3_called = any(c.startswith("L3") or c.startswith("IF") for c in layer_chain)
    if l3_called:
        l3_skip = "-"
    elif not (enable_layer3 and document_type in ("auto", "invoice")):
        l3_skip = "disabled"
    elif not image_bytes:
        l3_skip = "no_image"
    elif not triggers:
        l3_skip = "no_trigger"
    else:
        l3_skip = "not_eligible"
    logger.info(
        "pipeline: page %d timing l1=%dms l2=%dms l3=%dms total=%dms chain=%s "
        "l3_called=%s l3_skip=%s",
        page_number,
        l1_ms,
        l2_ms,
        l3_ms,
        total_ms,
        "/".join(layer_chain),
        l3_called,
        l3_skip,
    )

    # P0 修 (2026-05-26) · 同页多票 · 人工兜底(最后手段)。
    # 顺序:① L2 文本提取(含 additional_invoices)→ ② 若候选>提取 · Rule 7 已让
    # L3 视觉复读再补一次(加强自身 OCR)→ ③ 这里基于 L3 复读后的【最终】invoice
    # 再数一次:仍然候选>提取,说明 OCR 已尽力(残缺/涂抹/印刷异常等票据本身问题)
    # 才标人工核对 + 警告。绝不静默成功,但也不在 OCR 还能补救前就丢给人工。
    if (
        document_type in ("auto", "invoice")
        and not invoice.is_not_invoice
        and invoice.invoice_number
    ):
        extracted_n = 1 + len(invoice.additional_invoices or [])
        candidate_n = _count_invoice_no_candidates(l1_page.full_text, invoice.invoice_number)
        if candidate_n > extracted_n:
            reason = (
                f"possible_missed_invoice: page shows {candidate_n} invoice-number "
                f"candidates matching the pattern of {invoice.invoice_number!r} but only "
                f"{extracted_n} invoice(s) extracted after visual re-read — manual review needed"
            )
            validation_warnings.append(reason)
            needs_manual_review = True

    # Record final invoice pattern in pattern memory (after possible L3
    # correction). Subsequent pages benefit from this learned baseline.
    if (
        pattern_memory is not None
        and document_type in ("auto", "invoice")
        and not invoice.is_not_invoice
    ):
        pattern_memory.record(invoice.seller_tax, invoice.invoice_number)

    # 2026-05-21 confidence routing — derive a single page confidence and
    # route into one of three buckets per the spec.
    final_confidence = _aggregate_page_confidence(
        l1_page=l1_page,
        invoice=invoice,
        document=document,
        triggers=triggers,
        needs_manual_review=needs_manual_review,
        document_type=document_type,
        soft_flags=soft_flags,
    )
    confidence_band = _bucket_confidence(final_confidence, needs_manual_review)
    if confidence_band == "needs_review":
        needs_manual_review = True

    field_confidence = (
        _field_confidences(l1_page, invoice) if document_type in ("auto", "invoice") else {}
    )

    return PipelinePageResult(
        page_number=page_number,
        invoice=invoice,
        document_type=document_type,
        document=document,
        layer_chain=layer_chain,
        trigger_reasons=triggers + soft_flags,
        layer1_avg_confidence=l1_page.avg_confidence,
        layer2_input_tokens=l2_result.input_tokens,
        layer2_output_tokens=l2_result.output_tokens,
        layer3_input_tokens=l3_in_tokens,
        layer3_output_tokens=l3_out_tokens,
        layer1_ms=l1_ms,
        layer2_ms=l2_ms,
        layer3_ms=l3_ms,
        total_ms=total_ms,
        needs_manual_review=needs_manual_review,
        confidence_band=confidence_band,
        final_confidence=final_confidence,
        field_confidence=field_confidence,
        validation_warnings=validation_warnings,
        error=error_msg,
    )
