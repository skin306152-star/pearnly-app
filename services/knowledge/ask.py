"""Cited question answering over retrieved chunks (P4).

Grounded generation only: the model is given numbered source chunks and told to
answer from them and cite [n], or to say it cannot. With no retrieved chunks the
question is refused outright (no_answer) — the product never answers without a
source. Retrieval and persistence live in the route; this module builds the
prompt, calls generation, and assembles citations, with `generate` injectable so
the assembly is testable without the network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from services.knowledge import generation
from services.knowledge.schema import SearchHit

# Token the model must emit when the sources don't answer the question. Kept
# distinctive so it can't collide with a legitimate cited answer.
NO_ANSWER_SENTINEL = "NO_ANSWER"

SYSTEM_PROMPT = (
    "You are a financial knowledge assistant for an accounting firm. "
    "Answer ONLY from the numbered sources provided. Cite the sources you use "
    f"as [1], [2], etc. If the sources do not contain the answer, reply with "
    f"exactly {NO_ANSWER_SENTINEL} and nothing else. Reply in the language of "
    "the question."
)

# Returned as the answer text when there is nothing to ground an answer on.
NO_SOURCE_MESSAGE_KEY = "ask.no_source"

# A grounded answer must reference at least one source as [n]; its absence (or
# the refusal sentinel) means the model did not answer from the sources.
_CITATION_MARK = re.compile(r"\[\d+\]")


@dataclass
class AnswerResult:
    answer: str
    no_answer: bool
    citations: list[dict] = field(default_factory=list)
    model: Optional[str] = None


def _citations(hits: list[SearchHit]) -> list[dict]:
    return [
        {
            "index": i + 1,
            "chunk_id": h.chunk_id,
            "document_id": h.document_id,
            "filename": h.filename,
            "score": round(h.score, 4),
        }
        for i, h in enumerate(hits)
    ]


def build_prompt(question: str, hits: list[SearchHit]) -> str:
    sources = "\n\n".join(f"[{i + 1}] ({h.filename}) {h.text}" for i, h in enumerate(hits))
    return f"Sources:\n{sources}\n\nQuestion: {question}\n\nAnswer with citations:"


def answer_question(
    question: str,
    hits: list[SearchHit],
    *,
    generate: Callable[..., str] = generation.generate,
) -> AnswerResult:
    if not hits:
        return AnswerResult(answer="", no_answer=True, citations=[])
    text = generate(build_prompt(question, hits), system=SYSTEM_PROMPT).strip()
    # Refusal: the model emitted the sentinel, or produced no [n] citation — in
    # either case it did not ground an answer, so refuse and do not bill.
    refused = text.upper().startswith(NO_ANSWER_SENTINEL) or not _CITATION_MARK.search(text)
    if refused:
        return AnswerResult(answer="", no_answer=True, citations=[])
    return AnswerResult(
        answer=text,
        no_answer=False,
        citations=_citations(hits),
        model=generation.MODEL,
    )
