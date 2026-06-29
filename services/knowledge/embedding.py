"""Gemini embedding client (gemini-embedding-001 @768).

The model and dimension are the P0.5 spike's verdict (eval/thai_spike_result.md):
gemini-embedding-001 at 768 dims scored R@1=1.0 on the Thai financial corpus.
Documents and queries are encoded with different task types — Gemini is a
retrieval-tuned model, so a query vector and a document vector of the same text
are intentionally not identical.

The key comes from the environment (GEMINI_API_KEY / GOOGLE_API_KEY). The
sandbox loads it from the gitignored eval/.gemini_key at startup; in the main
project it arrives as a normal secret. All failure modes surface as a single
EmbeddingError so callers have one thing to catch.
"""

from __future__ import annotations

import os
from typing import Sequence

MODEL = "gemini-embedding-001"  # 经网关 embed;后端默认同模型(向量空间不漂)
DIM = 768


class EmbeddingError(RuntimeError):
    """No key, or the embedding request failed. The single failure surface."""


def api_key_present() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise EmbeddingError("no Gemini API key (set GEMINI_API_KEY)")
    return key


def embed_texts(texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
    """Embed a batch of texts. Returns one 768-float vector per input, in order(经网关 · 后端可切)。"""
    if not texts:
        return []
    from services.ai_gateway import transport

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    out = transport.embed(
        list(texts), is_query=is_query, dim=DIM, api_key=key, task="knowledge.embed"
    )
    if not out.ok:
        if out.error_kind == "auth":
            raise EmbeddingError("no Gemini API key (set GEMINI_API_KEY)")
        raise EmbeddingError(f"gemini embedding request failed: {out.error_kind}")
    return out.data


def to_pgvector(vector: Sequence[float]) -> str:
    """Render a vector as the text literal pgvector accepts after a ::vector cast."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"
