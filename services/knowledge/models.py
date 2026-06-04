"""Domain models for knowledge-base ingest.

These are plain dataclasses with no database coupling. The persisted row models
(documents / ingest_jobs) arrive with the DAL in the schema window; this file
holds only what the parse -> normalize -> chunk pipeline produces.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    ordinal: int  # 0-based position within the document
    text: str
    char_count: int


@dataclass
class ParsedDocument:
    filename: str
    text: str  # normalized full text
    chunks: list[Chunk]
