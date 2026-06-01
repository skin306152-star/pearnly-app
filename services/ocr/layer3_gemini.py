"""
services/ocr/layer3_gemini.py · Layer 3 Gemini 传输层(异常 + JSON 解析 + 异常分类 + 模型构造)

从 layer3_fallback.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改 · 同 L2-A layer2_gemini 范式)。
layer3_fallback re-import 全部名字回去(refine_page/refine_with_image 用 + 对外 re-export)。
"""

import json
import logging
import threading

logger = logging.getLogger(__name__)


DEFAULT_TEMPERATURE = 0.0
# B2 fix: bumped from 4096 to 8192. Real-world Thai invoices serialized
# to JSON with all line items can exceed 4096 output tokens, leading to
# truncated unterminated-string JSON errors. 8192 leaves headroom for
# 50+ line items + long Thai company names + full address.
DEFAULT_MAX_OUTPUT_TOKENS = 8192


# ============================================================
# Exception hierarchy
# ============================================================
class Layer3Error(Exception):
    """Base exception for layer 3 errors. Catch this for generic dispatch."""


class Layer3FallbackError(Layer3Error):
    """Layer 3 itself failed (JSON parse / empty response after retries).

    Per spec: do NOT crash pipeline.py. The caller decides whether to fall
    back to the (still imperfect) layer 2 ThaiInvoice, send to manual
    review queue, or hard-fail.
    """


class Layer3AuthError(Layer3Error):
    """Missing or invalid API key (NOT retryable)."""


class Layer3QuotaError(Layer3Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer3TransientError(Layer3Error):
    """Network / timeout / 5xx. Potentially retryable."""


def _parse_json(text: str) -> dict:
    """Parse Gemini's response as JSON, stripping markdown fences if present.

    Mirrors layer2_structure._parse_json; same defensive logic.
    """
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl > 0:
            s = s[first_nl + 1 :]
        else:
            s = s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3].rstrip()
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise json.JSONDecodeError(
            f"expected JSON object, got {type(obj).__name__}",
            s,
            0,
        )
    return obj


def _classify_gemini_exception(e: Exception) -> Exception:
    """Translate raw google-generativeai SDK exception into Layer3 hierarchy.

    Mirrors layer2_structure._classify_gemini_exception. We sniff message
    + type name because the SDK's exception classes vary across versions.
    """
    name = type(e).__name__
    msg = str(e)[:400]
    msg_lower = msg.lower()

    if (
        name in ("Unauthenticated", "PermissionDenied")
        or "permission denied" in msg_lower
        or "unauthenticated" in msg_lower
        or "api key not valid" in msg_lower
        or "invalid api key" in msg_lower
        or "403" in msg
        or "401" in msg
    ):
        return Layer3AuthError(f"layer3: auth ({name}): {msg}")

    if (
        name in ("ResourceExhausted",)
        or "429" in msg
        or "quota" in msg_lower
        or "resource_exhausted" in msg_lower
        or "rate limit" in msg_lower
    ):
        return Layer3QuotaError(f"layer3: quota ({name}): {msg}")

    if (
        name in ("DeadlineExceeded", "ServiceUnavailable", "InternalServerError", "Timeout")
        or "timeout" in msg_lower
        or "deadline" in msg_lower
        or "unavailable" in msg_lower
        or "503" in msg
        or "502" in msg
        or "504" in msg
        or "500" in msg
        or "connection" in msg_lower
    ):
        return Layer3TransientError(f"layer3: transient ({name}): {msg}")

    return Layer3Error(f"layer3: {name}: {msg}")


# ============================================================
# Model lazy singleton (keyed by api_key + model_name)
# ============================================================
_model_cache: dict = {}
_model_lock = threading.Lock()


def _get_model(api_key: str, model_name: str):
    """Return a GenerativeModel for the given (api_key, model_name).

    Cached up to 10 distinct combinations. Same pattern as layer 2.
    """
    cache_key = (api_key, model_name)

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]

        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "layer3: google-generativeai required. " "Install: pip install google-generativeai"
            ) from e

        # Direct endpoint (no Cloudflare proxy). If/when dev machine cannot
        # reach generativelanguage.googleapis.com, plumb a proxy via env var.
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
                "response_mime_type": "application/json",
            },
        )

        if len(_model_cache) >= 10:
            _model_cache.pop(next(iter(_model_cache)))
        _model_cache[cache_key] = model

        logger.info("layer3: GenerativeModel initialized: %s", model_name)
        return model
