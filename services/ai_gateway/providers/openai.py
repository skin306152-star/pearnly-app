# -*- coding: utf-8 -*-
"""openai provider:OpenAI Chat Completions 适配器(与 aistudio/vertex/selfhost/anthropic 同契约)。

接口与其它 provider 一致 → transport 无感切换。默认直连官方;base 可覆写以走代理/OpenRouter。
env:
  OPENAI_API_KEY      API key(缺 → auth 类·上层 fallback,不抛)
  OPENAI_BASE_URL     可选自定义 base(默认 https://api.openai.com/v1)
  OPENAI_FLASH_MODEL  flash 档模型名(不在代码里写死·未配置 → 当后端不可用)
  OPENAI_BEST_MODEL   best 档模型名(未配置回落 flash 档)
  OPENAI_EMBED_MODEL  embedding 模型名(chat 模型不能 embed·未配置 → 当不可用)
  TAXOPS_BRAIN_MODEL  taxops_verdict 档模型名(工单大脑影子车道·有内置默认,见下)
  TAXOPS_INTENT_MODEL taxops_intent 档模型名(前门意图解析车道·独立旋钮·默认同 verdict,见下)

请求一律带 store:false:数据边界——不让 OpenAI 侧留存请求/响应用于其产品功能。
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from services.ai_gateway.providers.http_common import error_kind_for_status, image_content_parts
from services.ai_gateway.tasks import ProviderOutcome

NAME = "openai"

# 参数支持按模型代际走,与命名形状无关 → 不猜:发一次,被拒(400)就记下该模型、调整重发。
# 运行时自适配,零型号清单维护;命中后进程内记忆,不重复试错(同 anthropic._NO_TEMP 先例)。
_NO_TEMP: set[str] = set()  # reasoning 代际拒 temperature(只认默认值)
_LEGACY_MAX: set[str] = set()  # 老 OpenAI 兼容端点只认 max_tokens,不认 max_completion_tokens


def _base() -> str:
    return (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")


def _key() -> str:
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


# 工单大脑影子车道(routing_matrix 的 taxops.verdict · brain_shadow 裁决预判):独立 env,
# 不与通用 flash/best 档互相牵动(改 OCR/对话档不许连坐工单大脑,契约测试锁死)。
# gpt-5.6-luna=2026-07-14 三臂摸底考钉死(66 题同卷方向 96.8%,完胜 nano/gemini-3.5),
# OpenRouter 命名带 openai/ 前缀;换模型同 PR 改 routing_matrix 与 cost 价表。
TAXOPS_VERDICT_TIER = "taxops_verdict"
_TAXOPS_DEFAULT_MODEL = "openai/gpt-5.6-luna"


def taxops_verdict_model() -> str:
    """taxops.verdict 车道模型名(env 覆写 > 内置默认)。routing_matrix 引用此函数解析车道。"""
    return (os.environ.get("TAXOPS_BRAIN_MODEL") or "").strip() or _TAXOPS_DEFAULT_MODEL


# 前门意图解析车道(routing_matrix 的 taxops.intent · front_desk.interpret 把用户目标归成闭集
# 意图/客户/期间建议):独立 env 旋钮,与 verdict/OCR/对话档互不牵动(契约测试锁死)。默认同
# verdict(luna)——同一 OpenRouter 模型,换任一车道只改各自旋钮 + 同 PR 改 routing_matrix/cost。
TAXOPS_INTENT_TIER = "taxops_intent"


def taxops_intent_model() -> str:
    """taxops.intent 车道模型名(env 覆写 > 内置默认·默认同 verdict)。routing_matrix 引用此函数。"""
    return (os.environ.get("TAXOPS_INTENT_MODEL") or "").strip() or _TAXOPS_DEFAULT_MODEL


def _model(tier: str) -> str:
    """抽象档位 → 具体模型(集中此处·业务/文档不出现型号名·通用档无内置默认)。"""
    if tier == TAXOPS_VERDICT_TIER:
        return taxops_verdict_model()
    if tier == TAXOPS_INTENT_TIER:
        return taxops_intent_model()
    flash = os.environ.get("OPENAI_FLASH_MODEL", "").strip()
    best = os.environ.get("OPENAI_BEST_MODEL", "").strip() or flash
    return best if tier in ("best", "fallback") else flash


def _embed_model() -> str:
    return os.environ.get("OPENAI_EMBED_MODEL", "").strip()


def _payload(model: str, messages: list, *, temperature, max_tokens, json_mode: bool) -> dict:
    payload: dict = {"model": model, "messages": messages, "store": False}
    if temperature is not None and model not in _NO_TEMP:
        payload["temperature"] = temperature
    if max_tokens:
        # 官方现行参数是 max_completion_tokens(reasoning 代际拒收老名);老兼容端点被拒后
        # 由 _chat 改回 max_tokens 重发(见 _LEGACY_MAX)。
        key = "max_tokens" if model in _LEGACY_MAX else "max_completion_tokens"
        payload[key] = max_tokens
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _adapt_param_rejection(payload: dict, model: str, err_text: str) -> bool:
    """400 因参数不被该代际支持 → 记忆 + 调整 payload,返回是否值得重发。"""
    low = err_text.lower()
    if "temperature" in payload and "temperature" in low:
        _NO_TEMP.add(model)
        payload.pop("temperature")
        return True
    if "max_completion_tokens" in payload and "max_completion_tokens" in low:
        _LEGACY_MAX.add(model)
        payload["max_tokens"] = payload.pop("max_completion_tokens")
        return True
    return False


def _chat(payload: dict, model: str, timeout_s: int):
    """POST /chat/completions → (text, error_kind, (in_tokens, out_tokens))。

    截断(finish_reason=length)与空 choices 收敛为 parse 且不再重试:截断是确定性的,
    重试是白烧钱——aistudio 曾因空 candidates 裸取 resp.text 抛异常穿透网关,此处从第一天堵死。
    """
    import httpx

    key = _key()
    if not key:
        return None, "auth", (0, 0)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for _ in range(3):  # 首发 + 至多两类参数被拒各重发一次
        try:
            resp = httpx.post(
                f"{_base()}/chat/completions", headers=headers, json=payload, timeout=timeout_s
            )
        except httpx.TimeoutException:
            return None, "timeout", (0, 0)
        except httpx.HTTPError:
            return None, "provider", (0, 0)
        if resp.status_code == 400 and _adapt_param_rejection(payload, model, resp.text):
            continue
        if resp.status_code >= 400:
            return None, error_kind_for_status(resp.status_code), (0, 0)
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            return None, "parse", (0, 0)
        choices = body.get("choices") or []
        usage = body.get("usage") or {}
        toks = (
            int(usage.get("prompt_tokens", 0) or 0),
            int(usage.get("completion_tokens", 0) or 0),
        )
        if not choices:
            return None, "parse", toks
        if (choices[0].get("finish_reason") or "") == "length":
            return None, "parse", toks
        text = (choices[0].get("message") or {}).get("content") or ""
        return text.strip(), None, toks
    return None, "provider", (0, 0)  # 理论不可达(每类参数只调整一次,第三发必走到返回)


def _chat_json(
    prompt, images, *, tier, temperature, response_mime, max_tokens, timeout_s, max_retries
):
    from services.ocr.layer2_gemini import _parse_json

    model = _model(tier)
    if not model:
        return ProviderOutcome(ok=False, error_kind="auth", model=NAME)  # 未配置 → 上层 fallback
    content = image_content_parts(prompt, images) if images else prompt
    payload = _payload(
        model,
        [{"role": "user", "content": content}],
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=bool(response_mime),
    )
    last_raw = ""
    for _ in range(max_retries + 1):
        text, kind, toks = _chat(payload, model, timeout_s)
        if kind:
            return ProviderOutcome(ok=False, error_kind=kind, model=model)
        if text:
            last_raw = text
            try:
                return ProviderOutcome(
                    ok=True,
                    data=_parse_json(text),
                    model=model,
                    input_tokens=toks[0],
                    output_tokens=toks[1],
                )
            except Exception:  # noqa: BLE001 — 坏 JSON → 重试;用尽落 parse
                pass
    # 解析失败带回原文(上层可把散文当回复救援)· raw 绝不进日志(_observe 只记 error_kind/token)
    return ProviderOutcome(ok=False, error_kind="parse", model=model, raw=last_raw)


def text_to_action(prompt, *, tools, **kw) -> ProviderOutcome:
    """原生 function-calling 另案(照 selfhost/anthropic 先例)→ 调用方回落 JSON 协议。"""
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
        tier=tier,
        temperature=temperature,
        response_mime=response_mime,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
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
        tier=tier,
        temperature=temperature,
        response_mime=response_mime,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        max_retries=max_retries,
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
    model = _model(tier)
    if not model:
        return ProviderOutcome(ok=False, error_kind="auth", model=NAME)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = _payload(model, messages, temperature=temperature, max_tokens=None, json_mode=False)
    text, kind, toks = _chat(payload, model, timeout_s)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind, model=model)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model)
    return ProviderOutcome(
        ok=True, data=text, model=model, input_tokens=toks[0], output_tokens=toks[1]
    )


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
) -> ProviderOutcome:
    import httpx

    model = _embed_model()
    key = _key()
    if not model or not key:
        return ProviderOutcome(ok=False, error_kind="auth", model=NAME)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        resp = httpx.post(
            f"{_base()}/embeddings",
            headers=headers,
            json={"model": model, "input": texts},
            timeout=timeout_s,
        )
    except httpx.TimeoutException:
        return ProviderOutcome(ok=False, error_kind="timeout", model=model)
    except httpx.HTTPError:
        return ProviderOutcome(ok=False, error_kind="provider", model=model)
    if resp.status_code >= 400:
        return ProviderOutcome(
            ok=False, error_kind=error_kind_for_status(resp.status_code), model=model
        )
    try:
        rows = sorted(resp.json()["data"], key=lambda d: d.get("index", 0))
        out = [list(r["embedding"]) for r in rows]
    except Exception:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind="parse", model=model)
    return ProviderOutcome(ok=True, data=out, model=model)
