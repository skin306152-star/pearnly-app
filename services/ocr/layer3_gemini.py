"""
services/ocr/layer3_gemini.py · Layer 3 Gemini 传输层(异常 + JSON 解析 + 异常分类 + 模型构造)

从 layer3_fallback.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改 · 同 L2-A layer2_gemini 范式)。
layer3_fallback re-import 全部名字回去(refine_page/refine_with_image 用 + 对外 re-export)。
"""

import json
import logging

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
# ai_gateway 路由(全后端统一经 model_client · 2026-07-03 收口)
# ============================================================
# B2 fix: 重试时追加 JSON 卫生提示,降低长泰文序列化时的截断/坏 JSON 概率。
_RETRY_HINT_BASE = (
    "\n\nIMPORTANT — your previous response was invalid JSON. Common "
    "failure modes:\n"
    "  1. Unterminated string (missing closing double-quote)\n"
    "  2. Unescaped newline inside a string value\n"
    "  3. Missing comma between fields\n"
    "  4. Trailing comma after last field\n"
    "Output exactly ONE complete JSON object. Close every string with a "
    "double-quote. Replace any literal newlines inside string values with "
    "spaces. Do NOT use markdown code fences. Do NOT add commentary "
    "before or after the JSON."
)


def _l3_error_for_kind(kind: str, model_name: str) -> Exception:
    msg = f"layer3: gateway ({kind}) model={model_name}"
    if kind == "auth":
        return Layer3AuthError(msg)
    if kind == "quota":
        return Layer3QuotaError(msg)
    return Layer3TransientError(msg)


def _call_l3_via_gateway(
    image_bytes: bytes,
    mime: str,
    system_prompt: str,
    base_user_prompt: str,
    api_key: str,
    model_name: str,
    max_retries: int,
    timeout: int,
):
    """L3 多模态→JSON 经 model_client(全后端统一)。保留 (data, meta) 元组契约
    + 重试追加 JSON 卫生提示;auth/quota/transient 映射回 Layer3 异常,
    parse/empty 在重试预算内重试。"""
    from services.ocr import model_client

    last_kind = "parse"
    for attempt in range(max_retries + 1):
        user_prompt = (
            base_user_prompt
            if attempt == 0
            else base_user_prompt + _RETRY_HINT_BASE + f"\n\nPrevious parse error: {last_kind}"
        )
        out = model_client.json_from_images(
            system_prompt + "\n\n" + user_prompt,
            [(image_bytes, mime)],
            model_name=model_name,
            task="ocr.layer3",
            api_key=api_key,
            timeout_s=timeout,
            max_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        )
        if out.ok:
            return out.data, {
                "input_tokens": out.input_tokens,
                "output_tokens": out.output_tokens,
                "retries": attempt,
            }
        last_kind = out.error_kind or "parse"
        if last_kind in ("auth", "quota", "timeout"):
            raise _l3_error_for_kind(last_kind, model_name)
        # parse/empty:落入下一轮重试(预算用尽则退出循环抛下方错误)
    raise Layer3FallbackError(
        f"layer3: gateway returned no valid JSON after {max_retries + 1} attempts ({last_kind})"
    )
