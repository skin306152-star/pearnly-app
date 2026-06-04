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

MODEL = "gemini-2.5-flash"
_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


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
    """Generate a single text completion for the prompt."""
    import httpx

    payload: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    try:
        resp = httpx.post(_URL, params={"key": _api_key()}, json=payload, timeout=120)
        resp.raise_for_status()
        candidates = resp.json().get("candidates", [])
        if not candidates:
            raise GenerationError("gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts).strip()
    except httpx.HTTPError as exc:
        raise GenerationError(f"gemini generation request failed: {exc}") from exc
