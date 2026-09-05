"""Execute the pinned Enterprise + image schema contract through Vertex."""

from __future__ import annotations

import json
import time

from services.ai_gateway import attribution, logging as ai_log, costing
from services.ai_gateway.providers import vertex
from services.ai_gateway.tasks import AiResult, ProviderOutcome
from services.ocr.enterprise_contract import CONTRACT_VERSION
from services.ocr.enterprise_request import build_request


def extract(image: bytes, mime: str, category: str, transcript: str, *, timeout_s=180):
    from google.genai import types

    request = build_request(category, transcript)
    config = types.GenerateContentConfig(**request["config"])
    config.http_options = types.HttpOptions(
        timeout=int(timeout_s * 1000), retry_options=types.HttpRetryOptions(attempts=1)
    )
    started = time.monotonic()
    outcome = ProviderOutcome(ok=False, model=request["model"])
    try:
        response = vertex._client(request["location"]).models.generate_content(
            model=request["model"],
            contents=[types.Part.from_bytes(data=image, mime_type=mime), request["prompt"]],
            config=config,
        )
        outcome.input_tokens, outcome.output_tokens = vertex._usage(response)
        candidates = getattr(response, "candidates", None) or []
        finish = str(getattr(candidates[0], "finish_reason", "")) if candidates else ""
        if "MAX_TOKENS" in finish:
            outcome.error_kind = "parse"
        else:
            outcome.data = json.loads(vertex._safe_text(response))
            outcome.ok = isinstance(outcome.data, dict)
            outcome.error_kind = None if outcome.ok else "parse"
    except (ValueError, TypeError):
        outcome.error_kind = "parse"
    except Exception as exc:
        outcome.error_kind = vertex._error_kind(exc)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    attr = attribution.current() or {}
    ai_log.log_call(
        AiResult(
            ok=outcome.ok,
            task=attr.get("task") or "ocr.enterprise_schema",
            schema_version=CONTRACT_VERSION,
            provider="vertex",
            model=outcome.model,
            error_kind=outcome.error_kind,
            latency_ms=elapsed_ms,
            input_tokens=outcome.input_tokens,
            output_tokens=outcome.output_tokens,
            cost_thb=costing.estimate_thb(
                outcome.model, outcome.input_tokens, outcome.output_tokens
            ),
        ),
        tenant_id=attr.get("tenant_id"),
        user_id=attr.get("user_id"),
        trace_id=attr.get("trace_id"),
    )
    return outcome, elapsed_ms
