# -*- coding: utf-8 -*-
"""OCR 统一模型客户端:业务代码取模型输出只经此门面,内部只调 ai_gateway.transport。

调用方持有具体模型名(try_with_fallback 逐档传入),这里统一做模型名→tier 反解;
重试策略由调用方自持(一律 max_retries=0),抽取任务一律 temperature=0。
SDK(google.generativeai / vertex / httpx)只活在 ai_gateway/providers,
业务文件出现 import google.generativeai 即违规。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from services.ai_gateway import transport
from services.ai_gateway.tasks import ProviderOutcome
from services.ocr.gemini_models import tier_for_model


def json_from_text(
    prompt: str,
    *,
    model_name: str,
    task: str,
    api_key: Optional[str] = None,
    timeout_s: int = 30,
    max_tokens: int = 16384,
) -> ProviderOutcome:
    return transport.text_to_json(
        prompt,
        tier=tier_for_model(model_name),
        api_key=api_key,
        temperature=0.0,
        response_mime=True,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=0,
        task=task,
    )


def json_from_images(
    prompt: str,
    images: List[Tuple[bytes, str]],
    *,
    model_name: str,
    task: str,
    api_key: Optional[str] = None,
    timeout_s: int = 60,
    max_tokens: int = 8192,
    response_mime: bool = True,
) -> ProviderOutcome:
    """images = [(bytes, mime_type), ...];PDF 也走这里(mime=application/pdf)。"""
    return transport.multimodal_to_json(
        prompt,
        images,
        tier=tier_for_model(model_name),
        api_key=api_key,
        temperature=0.0,
        response_mime=response_mime,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=0,
        task=task,
    )


def json_from_pdf(model_name: str, pdf_bytes: bytes, prompt: str, task: str) -> dict:
    """银行 PDF→JSON(GL/对账单共用,原 bank_recon_utils.gateway_pdf_to_json)。
    失败抛 RuntimeError 让 try_with_fallback 升档。"""
    out = json_from_images(
        prompt,
        [(pdf_bytes, "application/pdf")],
        model_name=model_name,
        task=task,
        max_tokens=32768,
        response_mime=False,
    )
    if not out.ok:
        raise RuntimeError(f"gateway {out.error_kind}")
    return out.data
