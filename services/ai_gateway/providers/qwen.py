# -*- coding: utf-8 -*-
"""qwen provider:阿里云百炼(DashScope)OpenAI 兼容端点 · Qwen 全家桶。

HTTP 形状与 selfhost 同源(POST {base}/chat/completions),差别在档位映射:自托管是单模型,
全家桶按档分模型——读取臂 flash 与升级臂 max 单价差约 60 倍(见 services/ocr/cost 价表),
tier 必须真落到不同模型,不能像 selfhost 那样全档一个名字。

env:
  QWEN_OCR_URL         OpenAI 兼容 base(如 https://<ws>.<region>.maas.aliyuncs.com/compatible-mode/v1)
  QWEN_OCR_KEY         Bearer key(绝不入库/入日志)
  QWEN_MODEL_FLASH     读取臂(默认 qwen3.7-flash)
  QWEN_MODEL_ESCALATE  升级臂(默认 qwen3.8-max)
  QWEN_MODEL_VLOCR     整页转写(默认 qwen-vl-ocr-2025-11-20 · 只出文本不出字段)

两处与别家 provider 有意不同:
  · 每个 chat 请求显式 enable_thinking=false:千问默认开思考链,抽字段用不上,不关既慢又贵。
    转写路按 2026-08-11 实测编排不带这个参数(调用方按车道传,不从模型名反猜)。
  · 不发 response_format=json_object:DashScope 视觉模型对它不稳,JSON 由 prompt 约束,
    解析统一走 layer2_gemini._parse_json(与 selfhost 同一支解析,行为不劈叉)。
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Optional, Tuple

from services.ai_gateway.providers.http_common import (
    bearer_headers,
    chat_json_outcome,
    chat_text_and_usage,
    image_content_parts,
    post_json,
)
from services.ai_gateway.tasks import ProviderOutcome

NAME = "qwen"

DEFAULT_FLASH = "qwen3.7-flash"
DEFAULT_ESCALATE = "qwen3.8-max"
DEFAULT_VLOCR = "qwen-vl-ocr-2025-11-20"

# 整页转写档:不在 OCR 四档之列(它不出字段),由 multimodal_to_text 与 qwen_direct 显式点名。
TIER_VLOCR = "vlocr"
_ESCALATE_TIERS = ("fallback", "escalate", "best")


def _base() -> str:
    return (os.environ.get("QWEN_OCR_URL") or "").rstrip("/")


def _headers() -> dict:
    return bearer_headers(os.environ.get("QWEN_OCR_KEY"))


def model_for_tier(tier: str) -> str:
    """档位 → 模型名。flash/flash_lite 走读取臂,fallback/escalate 走升级臂,vlocr 走转写模型。

    routing_matrix 与 qwen_direct 都读这支,总表打印的就是真正会发出去的模型名。
    """
    t = (tier or "flash").strip().lower()
    if t in _ESCALATE_TIERS:
        return os.environ.get("QWEN_MODEL_ESCALATE", "").strip() or DEFAULT_ESCALATE
    if t == TIER_VLOCR:
        return os.environ.get("QWEN_MODEL_VLOCR", "").strip() or DEFAULT_VLOCR
    return os.environ.get("QWEN_MODEL_FLASH", "").strip() or DEFAULT_FLASH


def _payload(
    model: str,
    content,
    *,
    temperature: float,
    max_tokens: int,
    enable_thinking: Optional[bool],
) -> dict:
    """enable_thinking=None 则整个参数不发。带不带由调用方按车道定(chat 关思考链、转写路
    按实测编排不带),不从模型名反猜 —— env 换个模型名,猜法就默默失灵。"""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if enable_thinking is not None:
        body["enable_thinking"] = enable_thinking
    return body


def _chat_text(payload: dict, timeout_s: int):
    base = _base()
    if not base:
        return None, "auth", (0, 0)  # 未配置端点 = 不可用(auth 类·上层走 fallback)
    body, kind = post_json(f"{base}/chat/completions", _headers(), payload, timeout_s)
    if kind:
        return None, kind, (0, 0)
    return chat_text_and_usage(body)


_ARRAY_RE = re.compile(r"\[.*\]", re.S)


def _parse_object(text: str) -> dict:
    """响应 → 对象。主路复用 layer2_gemini._parse_json(与别家 provider 同一支解析)。

    数组另接一手:升级臂的提示词明写"同页多票 → 数组",而 _parse_json 只认对象 ——
    2026-08-11 真机冒烟就栽在这里(整页读对了却被判 parse 失败,白烧一次 max)。
    取第一个对象,与实测编排同口径;同页多票的其余张目前不进管线(qwen 档已知边界)。
    """
    from services.ocr.layer2_gemini import _parse_json

    try:
        return _parse_json(text)
    except Exception:  # noqa: BLE001
        pass
    match = _ARRAY_RE.search(text or "")
    if not match:
        raise ValueError("no JSON object in response")
    first = next((row for row in json.loads(match.group(0)) if isinstance(row, dict)), None)
    if first is None:
        raise ValueError("no JSON object in array response")
    return first


def _chat_json(prompt, images, *, temperature, max_tokens, timeout_s, max_retries, tier):
    model_name = model_for_tier(tier)
    content = image_content_parts(prompt, images) if images else prompt
    payload = _payload(
        model_name,
        content,
        temperature=temperature,
        max_tokens=max_tokens,
        enable_thinking=False,
    )
    return chat_json_outcome(
        lambda: _chat_text(payload, timeout_s), _parse_object, model_name, max_retries
    )


def text_to_action(prompt, *, tools, **kw) -> ProviderOutcome:
    """原生 function-calling 未接(qwen 只做 OCR 车道)→ 调用方回落 JSON 协议。"""
    return ProviderOutcome(ok=False, error_kind="unsupported", model=NAME)


def text_to_json(
    prompt: str,
    *,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    response_mime: bool = True,
    max_tokens: int = 16384,
    timeout_s: int = 30,
    max_retries: int = 1,
) -> ProviderOutcome:
    return _chat_json(
        prompt,
        None,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
        tier=tier,
    )


def multimodal_to_json(
    prompt: str,
    images: List[Tuple[bytes, str]],
    *,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    response_mime: bool = True,
    max_tokens: int = 8192,
    timeout_s: int = 60,
    max_retries: int = 1,
) -> ProviderOutcome:
    return _chat_json(
        prompt,
        images,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
        tier=tier,
    )


def multimodal_to_text(
    prompt: str,
    images: List[Tuple[bytes, str]],
    *,
    tier: str = TIER_VLOCR,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    timeout_s: int = 90,
) -> ProviderOutcome:
    """整页转写:图 → 纯文本(不解析 JSON)。qwen_direct 用它给字段做落地校验。"""
    model_name = model_for_tier(tier)
    payload = _payload(
        model_name,
        image_content_parts(prompt, images),
        temperature=temperature,
        max_tokens=max_tokens,
        enable_thinking=None,  # 转写路按 2026-08-11 实测编排不带这个参数
    )
    text, kind, toks = _chat_text(payload, timeout_s)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(
        ok=True, data=text, model=model_name, input_tokens=toks[0], output_tokens=toks[1]
    )


def text_to_text(
    prompt: str,
    *,
    system: Optional[str] = None,
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    timeout_s: int = 120,
) -> ProviderOutcome:
    model_name = model_for_tier(tier)
    content = f"{system}\n\n{prompt}" if system else prompt
    payload = _payload(
        model_name, content, temperature=temperature, max_tokens=4096, enable_thinking=False
    )
    text, kind, toks = _chat_text(payload, timeout_s)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model_name)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(
        ok=True, data=text, model=model_name, input_tokens=toks[0], output_tokens=toks[1]
    )


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
) -> ProviderOutcome:
    """知识库向量车道没走过千问,不声称支持(声称了就会有人把它当默认后端)。"""
    return ProviderOutcome(ok=False, error_kind="unsupported", model=NAME)
