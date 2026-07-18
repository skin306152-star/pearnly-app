# -*- coding: utf-8 -*-
"""vertex provider:google-genai + Vertex AI(服务账号 · 企业配额/数据驻留/不训练)。

同模型(gemini-*),只是换"门":认证走 GCP 服务账号(GOOGLE_APPLICATION_CREDENTIALS / ADC),
区域 VERTEX_LOCATION(默认 asia-southeast1·离泰国最近)。api_key 参数对 Vertex 无意义(忽略)。
4 形态接口与 aistudio 完全一致 → 上层 transport 无感切换。
"""

from __future__ import annotations

import os
import threading
from typing import List, Optional, Tuple

from services.ai_gateway.tasks import ProviderOutcome

NAME = "vertex"

_client_cache: dict = {}
_lock = threading.Lock()


def _location() -> str:
    return os.environ.get("VERTEX_LOCATION", "asia-southeast1").strip() or "asia-southeast1"


def _location_for_model(model: str) -> str:
    """按模型选区域:gemini-2.5-* 与 gemini-3.1-* 仅 Vertex global 端点提供(asia-se1 实测,
    2.5 返 404、3.1-lite 返空 JSON 均跑不通),走 global(真图 OCR 3.5~3.6s / 连打零错);
    3.5 与 embedding 留就近区域(默认 asia-se1)。VERTEX_LOCATION_25 覆写这批 global-only 档的区域。"""
    m = (model or "").lower()
    if m.startswith("gemini-2.5") or m.startswith("gemini-3.1"):
        return os.environ.get("VERTEX_LOCATION_25", "global").strip() or "global"
    return _location()


def _project() -> Optional[str]:
    return (
        os.environ.get("GCP_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("VERTEX_PROJECT")
        or None
    )


def _resolve_model(tier: str) -> str:
    from services.ocr import gemini_models

    return {
        "flash": gemini_models.flash,
        "flash_lite": gemini_models.flash_lite,
        "best": gemini_models.best,
        "fallback": gemini_models.fallback,
        "escalate": gemini_models.escalate,
        "brain": gemini_models.brain,
    }.get(tier, gemini_models.flash)()


def _embed_model() -> str:
    # 默认与 aistudio 同一向量空间(gemini-embedding-001)→ 知识库无需重建索引
    return (
        os.environ.get("VERTEX_EMBED_MODEL", "gemini-embedding-001").strip()
        or "gemini-embedding-001"
    )


def _client(loc: Optional[str] = None):
    loc = loc or _location()
    proj = _project()
    key = (proj, loc)
    if key in _client_cache:
        return _client_cache[key]
    with _lock:
        if key in _client_cache:
            return _client_cache[key]
        from google import genai

        kwargs = {"vertexai": True, "location": loc}
        if proj:
            kwargs["project"] = proj
        c = genai.Client(**kwargs)
        if len(_client_cache) >= 8:
            _client_cache.pop(next(iter(_client_cache)))
        _client_cache[key] = c
        return c


def _error_kind(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).lower()
    code = getattr(exc, "code", None)
    # 配额判定先于鉴权:配额耗尽偶尔以 403 + RESOURCE_EXHAUSTED 回(非 429),若先按 401/403
    # 归 auth 会把可重试错误当成 fail-fast 不重试。真正的权限错(403 permission denied)不含
    # quota 关键词,仍落到下面的 auth 分支,不受影响。
    if code == 429 or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg:
        return "quota"
    if code in (401, 403) or "permission" in msg or "unauthenticated" in msg or "api key" in msg:
        return "auth"
    if (
        code in (500, 502, 503, 504)
        or "timeout" in msg
        or "deadline" in msg
        or "unavailable" in msg
        or "DeadlineExceeded" in name
    ):
        return "timeout"
    return "provider"


def _config(temperature, max_tokens, response_mime, *, structured_vision_model=""):
    from google.genai import types

    kw = {"temperature": temperature, "max_output_tokens": max_tokens}
    if response_mime:
        kw["response_mime_type"] = "application/json"
    if structured_vision_model:
        if structured_vision_model.lower().startswith("gemini-2.5"):
            thinking = types.ThinkingConfig(thinking_budget=0)
        else:
            thinking = types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)
        kw["thinking_config"] = thinking
    return types.GenerateContentConfig(**kw)


def _usage(resp) -> Tuple[int, int]:
    try:
        u = getattr(resp, "usage_metadata", None)
        if u is not None:
            return (
                int(getattr(u, "prompt_token_count", 0) or 0),
                int(getattr(u, "candidates_token_count", 0) or 0),
            )
    except Exception:
        pass
    return (0, 0)


def _safe_text(resp) -> str:
    """`.text` 访问器在混合 parts/空 candidates 时可能抛——统一收敛为空串,走各调用方
    既有的 empty/parse 路(同 aistudio._safe_raw 手法;vertex 不细分截断,刻意最小化)。"""
    try:
        return (getattr(resp, "text", "") or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def _gen_json(contents, *, model_name, config, max_retries):
    from services.ocr.layer2_gemini import _parse_json

    client = _client(_location_for_model(model_name))
    last_raw = ""
    last_it = last_ot = 0
    for attempt in range(max_retries + 1):
        try:
            resp = client.models.generate_content(
                model=model_name, contents=contents, config=config
            )
        except Exception as e:  # noqa: BLE001
            return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
        raw = _safe_text(resp)
        it, ot = _usage(resp)
        last_it, last_ot = it, ot
        if raw:
            last_raw = raw
            try:
                return ProviderOutcome(
                    ok=True,
                    data=_parse_json(raw),
                    model=model_name,
                    input_tokens=it,
                    output_tokens=ot,
                )
            except Exception:  # noqa: BLE001
                pass
        if attempt < max_retries:
            continue
    # 解析失败带回原文(Agent 可把散文当回复救援)· raw 绝不进日志(_observe 只记 error_kind/token)
    return ProviderOutcome(
        ok=False,
        error_kind="parse",
        model=model_name,
        input_tokens=last_it,
        output_tokens=last_ot,
        raw=last_raw,
    )


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
    model_name = _resolve_model(tier)
    return _gen_json(
        prompt,
        model_name=model_name,
        config=_config(temperature, max_tokens, response_mime),
        max_retries=max_retries,
    )


def _fc_schema(d: Optional[dict]):
    """通用 JSON-schema dict → SDK Schema(无参工具不带 parameters → None)。"""
    from google.genai import types

    if not d:
        return None
    t = str(d.get("type", "string")).upper()
    kw = {"type": getattr(types.Type, t, types.Type.STRING)}
    if d.get("description"):
        kw["description"] = d["description"]
    if d.get("enum"):
        kw["enum"] = [str(v) for v in d["enum"]]
    if t == "OBJECT":
        kw["properties"] = {k: _fc_schema(v) for k, v in (d.get("properties") or {}).items()}
        if d.get("required"):
            kw["required"] = list(d["required"])
    if t == "ARRAY" and d.get("items"):
        kw["items"] = _fc_schema(d["items"])
    return types.Schema(**kw)


def text_to_action(
    prompt: str,
    *,
    tools: List[dict],
    tier: str = "flash",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1200,
    timeout_s: int = 18,
    max_retries: int = 1,
) -> ProviderOutcome:
    """原生 function-calling 决策。返回归一动作 dict(与 agent JSON 协议同形):
    functionCall → {"kind":"tool","tool","args"} · 纯文本 → {"kind":"reply","message"}。"""
    from google.genai import types

    model_name = _resolve_model(tier)
    decls = [
        types.FunctionDeclaration(
            name=d["name"],
            description=d.get("description") or "",
            parameters=_fc_schema(d.get("parameters")),
        )
        for d in tools
    ]
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        tools=[types.Tool(function_declarations=decls)],
    )
    try:
        resp = _client(_location_for_model(model_name)).models.generate_content(
            model=model_name, contents=prompt, config=config
        )
    except Exception as e:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
    it, ot = _usage(resp)
    fcs = getattr(resp, "function_calls", None) or []
    if fcs:
        fc = fcs[0]
        return ProviderOutcome(
            ok=True,
            data={"kind": "tool", "tool": fc.name, "args": dict(fc.args or {})},
            model=model_name,
            input_tokens=it,
            output_tokens=ot,
        )
    text = _safe_text(resp)
    if text:
        return ProviderOutcome(
            ok=True,
            data={"kind": "reply", "message": text},
            model=model_name,
            input_tokens=it,
            output_tokens=ot,
        )
    return ProviderOutcome(ok=False, error_kind="parse", model=model_name)


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
    from google.genai import types

    model_name = _resolve_model(tier)
    contents: list = []
    for data, mime in images:
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))
    contents.append(prompt)
    return _gen_json(
        contents,
        model_name=model_name,
        config=_config(
            temperature,
            max_tokens,
            response_mime,
            structured_vision_model=model_name,
        ),
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
    from google.genai import types

    model_name = _resolve_model(tier)
    kw = {"temperature": temperature}
    if system:
        kw["system_instruction"] = system
    try:
        resp = _client(_location_for_model(model_name)).models.generate_content(
            model=model_name, contents=prompt, config=types.GenerateContentConfig(**kw)
        )
    except Exception as e:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
    text = _safe_text(resp)
    it, ot = _usage(resp)
    if not text:
        return ProviderOutcome(ok=False, error_kind="parse", model=model_name)
    return ProviderOutcome(ok=True, data=text, model=model_name, input_tokens=it, output_tokens=ot)


def embed(
    texts: List[str],
    *,
    is_query: bool = False,
    api_key: Optional[str] = None,
    dim: int = 768,
    timeout_s: int = 120,
) -> ProviderOutcome:
    from google.genai import types

    model_name = _embed_model()
    task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    try:
        resp = _client().models.embed_content(
            model=model_name,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=dim),
        )
        out = [list(e.values) for e in resp.embeddings]
    except Exception as e:  # noqa: BLE001
        return ProviderOutcome(ok=False, error_kind=_error_kind(e), model=model_name)
    return ProviderOutcome(ok=True, data=out, model=model_name)
