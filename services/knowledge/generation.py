"""Gemini text generation client (gemini-2.5-flash).

Used by the cited-answer path (P4). The key comes from the environment, the same
as embedding.py; both failure modes (no key, request error) surface as one
GenerationError. An optional system instruction steers the model; generation is
deterministic-leaning (low temperature) since this is grounded Q&A, not creative
text.
"""

from __future__ import annotations

import os
from typing import Optional

MODEL = "gemini-2.5-flash"  # 参考默认;实际模型由网关 tier=flash 解析(可随后端切换)


class GenerationError(RuntimeError):
    """No key, or the generation request failed."""


def api_key_present() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise GenerationError("no Gemini API key (set GEMINI_API_KEY)")
    return key


def generate(prompt: str, *, system: Optional[str] = None, temperature: float = 0.2) -> str:
    """Generate a single text completion for the prompt(经网关 · 后端可切)。"""
    from services.ai_gateway import transport

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    out = transport.text_to_text(
        prompt,
        system=system,
        tier="flash",
        api_key=key,
        temperature=temperature,
        timeout_s=120,
        task="knowledge.generate",
    )
    if not out.ok or not out.data:
        if out.error_kind == "auth":
            raise GenerationError("no Gemini API key (set GEMINI_API_KEY)")
        raise GenerationError(f"gemini generation failed: {out.error_kind or 'empty'}")
    return out.data
