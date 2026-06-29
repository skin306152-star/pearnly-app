# -*- coding: utf-8 -*-
"""Gemini provider 适配器:包住现有 OCR 传输层(layer2_gemini._call_gemini_with_retry +
gemini_models 档位),把各家原始异常收敛到标准 error_kind。默认行为与现状完全一致。

懒加载传输/模型:既保留现有 mock 点(测试 patch layer2_gemini._call_gemini_with_retry /
gemini_models.flash 仍透明生效),也避免 import OCR 重链路进 gateway 顶层。
"""

from __future__ import annotations

from services.ai_gateway.tasks import ProviderOutcome

NAME = "gemini"


def _resolve_model(model_tier: str) -> str:
    """抽象档位 → 具体模型(集中在 gemini_models·业务/文档不出现具体模型名)。"""
    from services.ocr import gemini_models

    return {
        "flash": gemini_models.flash,
        "flash_lite": gemini_models.flash_lite,
        "best": gemini_models.best,
        "fallback": gemini_models.fallback,
    }.get(model_tier, gemini_models.flash)()


def generate_json(
    *, prompt: str, text: str, api_key, model_tier: str, timeout_s: int, max_retries: int
) -> ProviderOutcome:
    """结构化 JSON 调用。无 key/失败 → ok=False + 标准 error_kind(不抛,业务层据此走 fallback)。

    非 aistudio 后端(vertex/selfhost)经统一 backends 开关转对应 provider —— LINE 记账大脑
    (line_text_understand / expense_category_choose / line_chat_reply)随 OCR_LLM_BACKEND 一起
    切到 Vertex。默认 aistudio 走下方原直连路径,行为零变化。system+text 合并为单 prompt(JSON
    形态无独立 system_instruction,与 transport.multimodal 同口径)。
    """
    from services.ai_gateway import backends

    if not backends.is_aistudio():
        provider = backends.get_provider()
        combined = (prompt + "\n\n" + text) if prompt else (text or "")
        return provider.text_to_json(
            combined,
            tier=model_tier,
            api_key=api_key,
            response_mime=True,
            timeout_s=timeout_s,
            max_retries=max_retries,
        )
    if not api_key:
        return ProviderOutcome(ok=False, error_kind="auth")
    model = _resolve_model(model_tier)
    from services.ocr.layer2_gemini import (
        Layer2AuthError,
        Layer2Error,
        Layer2QuotaError,
        Layer2TransientError,
        _call_gemini_with_retry,
    )

    try:
        data, meta = _call_gemini_with_retry(
            text,
            api_key=api_key,
            model_name=model,
            max_retries=max_retries,
            timeout=timeout_s,
            system_prompt_override=prompt,
        )
    except Layer2AuthError:
        return ProviderOutcome(ok=False, error_kind="auth", model=model)
    except Layer2QuotaError:
        return ProviderOutcome(ok=False, error_kind="quota", model=model)
    except Layer2TransientError:
        return ProviderOutcome(ok=False, error_kind="timeout", model=model)
    except ValueError:  # 空响应 / 非法 JSON(传输层超重试后抛 ValueError)→ parse
        return ProviderOutcome(ok=False, error_kind="parse", model=model)
    except (Layer2Error, Exception):  # noqa: BLE001 — 兜底统一收敛为 provider,不外泄细节
        return ProviderOutcome(ok=False, error_kind="provider", model=model)
    meta = meta or {}
    return ProviderOutcome(
        ok=True,
        data=data,
        model=model,
        input_tokens=int(meta.get("input_tokens") or 0),
        output_tokens=int(meta.get("output_tokens") or 0),
    )
