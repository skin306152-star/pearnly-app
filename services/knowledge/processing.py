"""Turn an uploaded file into a terminal ingest outcome.

This wraps the deterministic ingest core (extract -> normalize -> chunk) and maps
its result onto the document lifecycle: a parseable file yields its chunks (which
P2 then embeds and stores), a file we cannot turn into text (unknown type,
image-only PDF) is FAILED with a stable error code rather than a silent success.

Kept as a pure function over bytes so it is unit-testable without a database or
the network; the route embeds the returned chunks and persists them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.knowledge.ingest import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    UnsupportedDocument,
    ingest_document,
)
from services.knowledge.models import Chunk
from services.knowledge.schema import DOC_FAILED, DOC_READY, ERROR_UNSUPPORTED


@dataclass(frozen=True)
class ProcessOutcome:
    status: str  # DOC_READY | DOC_FAILED
    chunks: list[Chunk] = field(default_factory=list)
    error_code: str | None = None
    # >0 表示走了 OCR(图片 / 扫描件)· 按页计费;=0 表示文本抽取 · 按字符计费。
    ocr_pages: int = 0

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def char_count(self) -> int:
        return sum(c.char_count for c in self.chunks)


def process_uploaded(
    filename: str,
    data: bytes,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> ProcessOutcome:
    try:
        parsed = ingest_document(filename, data, max_chars=max_chars, overlap=overlap)
    except UnsupportedDocument:
        return ProcessOutcome(status=DOC_FAILED, error_code=ERROR_UNSUPPORTED)
    return ProcessOutcome(status=DOC_READY, chunks=parsed.chunks)
