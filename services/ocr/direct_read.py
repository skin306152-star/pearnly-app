# -*- coding: utf-8 -*-
"""image-direct 直读主路(2026-07-05 Vision 消融定案·S2 分流)。

图片/扫描短文档(≤3 页,非多页对账件)不再过 L1 Vision:原图直喂档位多模态模型
(tier=flash_lite → economy=3.1-lite / direct35=3.5),用与 L2 相同的 doc-type
提示词出同一套 schema。六轮 411 样本实测:钱字段零损失、越糊越稳、省约一半。

Vision 路(page_runner)整建制保留,承担两件事:
  1. 长表/多页对账件的主路(路由器直接分给它——B 吐几百行 JSON 会顶爆 token);
  2. 直读的回落兜底:parse 失败/勾稽穿底/结构硬伤 → 抛 DirectReadFallback,
     调用方(pipeline)整件转回 Vision 路重跑。路由阈值判错也不丢件。

确定性闸替代 Vision 词级置信(实测该信号在真图上基本沉睡:L3 仅触发 2/32):
  硬闸(回落)= 金额勾稽(_check_amount_math)· 总额缺失 · sanity 结构硬伤
  (sanity 自带税号 mod-11 校验——校验位不符即回落,与实测"A 读税号微好"对齐);
  软闸(标注)= 单号缺失(实测 B 单号反而比 Vision 路更准,回落救不了,不回落)。

秒级回退:env OCR_IMAGE_DIRECT=0 → 全量走原 Vision 链,零迁移。
"""

from __future__ import annotations

import logging
import os
import time
from typing import List, Optional

from pydantic import ValidationError

from .cost import _compute_total_cost
from .layer2_prompts import _SYSTEM_PROMPT
from .layer2_structure import _DOC_PROMPTS, _DOC_SCHEMAS
from .sanity import credit_note_review_reason, evaluate_sanity, infer_missing_discount
from .schemas import BusinessDocumentType, PipelinePageResult, PipelineResult, ThaiInvoice
from .triggers import _bucket_confidence, _check_amount_math

logger = logging.getLogger(__name__)

ENGINE_DIRECT = "image_direct"
# 回落后走的仍是 pipeline_v1,engine 打上标记 → ocr_cost_log 可直接量回落率
ENGINE_FALLBACK = "pipeline_v1_id_fb"

# 路由阈值:实测 TTB(368/109 行)坐实长表是 B 唯一崩点;对账件哪怕 2 页也可能几十行,
# 门槛比普通文档更严。阈值保守 + 回落兜底,判错不丢件。
MAX_DIRECT_PAGES = int(os.environ.get("OCR_IMAGE_DIRECT_MAX_PAGES", "3"))
_TABLE_DOC_TYPES = ("bank_statement", "general_ledger")

_TIMEOUT_S = 60
_MAX_RETRIES = 1

_IMAGE_INPUT_NOTE = (
    "\n\nINPUT CHANGE: the input is the document IMAGE attached to this request, "
    "not pre-extracted OCR text. Read every character directly from the image "
    "and fill the exact same JSON schema. Same rules apply."
)


class DirectReadFallback(Exception):
    """直读不可信/失败 → 调用方整件回落 Vision 路。"""


def enabled() -> bool:
    return os.environ.get("OCR_IMAGE_DIRECT", "1").strip().lower() not in ("0", "false", "no", "off")


def route_direct(page_count: int, document_type: BusinessDocumentType) -> bool:
    """确定性路由:短文档 → 直读;长表/多页对账件 → Vision 路。"""
    if page_count > MAX_DIRECT_PAGES:
        return False
    if document_type in _TABLE_DOC_TYPES and page_count >= 2:
        return False
    return True


def _sniff_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/png"  # PDF 渲染页就是 PNG;未知类型按 PNG 送,模型端自会报错


def _call_model(image_bytes: bytes, document_type: BusinessDocumentType, api_key: Optional[str]):
    from services.ai_gateway import backends

    sys_prompt = (
        _SYSTEM_PROMPT if document_type in ("auto", "invoice") else _DOC_PROMPTS[document_type]
    )
    # 与 L2 同口径兜 env:aistudio provider 只认显式 key(vertex 走 SA 忽略此参)
    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    return backends.get_provider().multimodal_to_json(
        sys_prompt + _IMAGE_INPUT_NOTE,
        [(image_bytes, _sniff_mime(image_bytes))],
        tier="flash_lite",
        api_key=key,
        timeout_s=_TIMEOUT_S,
        max_retries=_MAX_RETRIES,
    )


def read_page(
    image_bytes: bytes,
    page_number: int,
    document_type: BusinessDocumentType = "auto",
    api_key: Optional[str] = None,
) -> PipelinePageResult:
    """单页直读 → PipelinePageResult(layer_chain=["ID"])。不可信即抛 DirectReadFallback。"""
    t0 = time.time()
    try:
        outcome = _call_model(image_bytes, document_type, api_key)
    except Exception as e:  # noqa: BLE001 — 直读任何炸法都回落 Vision 路,不让用户看 500
        raise DirectReadFallback(f"provider raise: {type(e).__name__}: {e}") from e
    if not outcome.ok or not isinstance(outcome.data, dict):
        raise DirectReadFallback(f"page {page_number}: {outcome.error_kind or 'empty output'}")

    invoice = ThaiInvoice(is_not_invoice=True)
    document = None
    warnings: List[str] = []
    if document_type in ("auto", "invoice"):
        try:
            invoice = ThaiInvoice(**outcome.data)
        except ValidationError as e:
            raise DirectReadFallback(f"page {page_number}: invoice schema: {e}") from e
        warnings.extend(_invoice_hard_gates(invoice, page_number))
        warnings.extend(_invoice_soft_flags(invoice))
    else:
        try:
            document = _DOC_SCHEMAS[document_type](**outcome.data)
        except ValidationError as e:
            raise DirectReadFallback(f"page {page_number}: {document_type} schema: {e}") from e

    # 贷记单方向性单据强制人工(两链共判 · sanity.credit_note_review_reason)
    force_review = False
    cn_reason = credit_note_review_reason(invoice)
    if cn_reason:
        warnings.append(cn_reason)
        force_review = True

    # 与 triggers 同口径:0.95 起步、每条软标注 -0.05;≥0.98 才 auto(直读永达不到,
    # 维持发票 confirm-first 现状),0.90-0.98 = yellow_confirm,再低转人工。
    final_confidence = round(max(0.0, 0.95 - 0.05 * len(warnings)), 4)
    band = _bucket_confidence(final_confidence, force_review)
    return PipelinePageResult(
        page_number=page_number,
        invoice=invoice,
        document_type=document_type,
        document=document,
        layer_chain=["ID"],
        trigger_reasons=[],
        layer1_avg_confidence=0.0,
        layer2_input_tokens=outcome.input_tokens,
        layer2_output_tokens=outcome.output_tokens,
        layer2_model=outcome.model,
        layer2_ms=int((time.time() - t0) * 1000),
        total_ms=int((time.time() - t0) * 1000),
        needs_manual_review=band == "needs_review",
        confidence_band=band,
        final_confidence=final_confidence,
        field_confidence={},
        validation_warnings=warnings,
    )


def _invoice_hard_gates(invoice: ThaiInvoice, page_number: int) -> List[str]:
    """钱面硬闸:不过 → 回落 Vision 路对质。通过 → 返回留痕(折扣回填说明)。"""
    if invoice.is_not_invoice:
        return []
    notes: List[str] = []
    repaired = infer_missing_discount(invoice)
    if repaired:
        notes.append(repaired)
    if not str(invoice.total_amount or "").strip():
        raise DirectReadFallback(f"page {page_number}: total_amount missing")
    math_issue = _check_amount_math(invoice)
    if math_issue:
        raise DirectReadFallback(f"page {page_number}: {math_issue}")
    sanity_issues = evaluate_sanity(invoice)
    if sanity_issues:
        raise DirectReadFallback(f"page {page_number}: sanity: {'; '.join(sanity_issues)}")
    return notes


def _invoice_soft_flags(invoice: ThaiInvoice) -> List[str]:
    """软标注(降置信不回落):实测 B 读单号反而比 Vision 路准,回落救不了这些。"""
    if invoice.is_not_invoice:
        return []
    if not str(invoice.invoice_number or "").strip():
        return ["direct_read: invoice_number missing"]
    return []


def run_file(
    page_image_bytes_list: List[bytes],
    document_type: BusinessDocumentType = "auto",
    api_key: Optional[str] = None,
) -> PipelineResult:
    """整件直读(调用方已过 enabled()+route_direct())。任一页不可信 → 整件回落。"""
    t0 = time.time()
    pages = [
        read_page(ib, page_number=i, document_type=document_type, api_key=api_key)
        for i, ib in enumerate(page_image_bytes_list, start=1)
    ]
    return PipelineResult(
        pages=pages,
        page_count=len(pages),
        elapsed_ms=int((time.time() - t0) * 1000),
        engine=ENGINE_DIRECT,
        estimated_cost_thb=_compute_total_cost(pages),
    )
