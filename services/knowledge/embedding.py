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

MODEL = "gemini-embedding-001"
DIM = 768
_TASK_QUERY = "RETRIEVAL_QUERY"
_TASK_DOCUMENT = "RETRIEVAL_DOCUMENT"
_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents"


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
    """Embed a batch of texts. Returns one 768-float vector per input, in order."""
    if not texts:
        return []
    import httpx

    task = _TASK_QUERY if is_query else _TASK_DOCUMENT
    payload = {
        "requests": [
            {
                "model": f"models/{MODEL}",
                "content": {"parts": [{"text": text}]},
                "taskType": task,
                "outputDimensionality": DIM,
            }
            for text in texts
        ]
    }
    try:
        resp = httpx.post(_URL, params={"key": _api_key()}, json=payload, timeout=120)
        resp.raise_for_status()
        return [row["values"] for row in resp.json()["embeddings"]]
    except httpx.HTTPError as exc:
        raise EmbeddingError(f"gemini embedding request failed: {exc}") from exc


def to_pgvector(vector: Sequence[float]) -> str:
    """Render a vector as the text literal pgvector accepts after a ::vector cast."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"
