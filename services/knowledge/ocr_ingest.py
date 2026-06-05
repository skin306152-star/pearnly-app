"""全格式入库编排:文本走纯核心(按字符),图片 / 扫描件走 OCR(按页)。

确定性纯核心(ingest.py / processing.py · 无网络)保持不变。本层加网络路径:
图片与图片型(扫描)PDF 经既有 OCR Layer-1(Google Vision · 整页 full_text)转写成
纯文字,再喂回同一套 normalize + chunk。返回 ProcessOutcome,其中 ocr_pages>0 标识
走了 OCR(供按页计费),=0 为文本抽取(按字符计费)。
"""

from __future__ import annotations

from pathlib import Path

from services.knowledge.ingest import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    chunk_text,
    normalize_text,
)
from services.knowledge.processing import ProcessOutcome, process_uploaded
from services.knowledge.schema import DOC_FAILED, DOC_READY, ERROR_PROCESSING

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _ocr_text_and_pages(filename: str, data: bytes) -> tuple[str, int]:
    """图片 / PDF → (整页纯文字, 页数)· 经 OCR Layer-1 Vision。"""
    from services.ocr import layer1_vision

    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        result = layer1_vision.extract_from_pdf_bytes(data)
    else:
        result = layer1_vision.extract_from_image_bytes(data)
    text = "\n\n".join(p.full_text for p in result.pages if getattr(p, "full_text", "").strip())
    return text, int(getattr(result, "page_count", len(result.pages)) or len(result.pages))


def process_uploaded_any(
    filename: str,
    data: bytes,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> ProcessOutcome:
    """全格式入库。文本/文字型 → 纯核心(ocr_pages=0);图片/扫描 PDF → OCR(ocr_pages=页数)。"""
    suffix = Path(filename).suffix.lower()
    is_image = suffix in IMAGE_SUFFIXES

    if not is_image:
        # 损坏/加密文件会让文本抽取抛异常(非 UnsupportedDocument)· 不能逃逸成 500:
        # PDF 仍给 OCR 一次机会,其余直接落 failed。
        try:
            outcome = process_uploaded(filename, data, max_chars=max_chars, overlap=overlap)
        except Exception:
            if suffix != ".pdf":
                return ProcessOutcome(status=DOC_FAILED, error_code=ERROR_PROCESSING)
            outcome = ProcessOutcome(status=DOC_FAILED, error_code=ERROR_PROCESSING)
        if outcome.status == DOC_READY:
            return outcome  # 文字层抽到 → 按字符
        # 文字型 PDF 抽不到文本(扫描件)→ 落 OCR;其它 unsupported 仍失败。
        if suffix != ".pdf":
            return outcome

    try:
        text, pages = _ocr_text_and_pages(filename, data)
    except Exception:
        return ProcessOutcome(status=DOC_FAILED, error_code=ERROR_PROCESSING)

    text = normalize_text(text)
    if not text.strip():
        # 支持的类型但 OCR 抽不到任何文字(损坏 / 加密 / 空白扫描)→ 处理失败,
        # 不是"不支持的类型"(那类在 process_uploaded 已按 UnsupportedDocument 落)。
        return ProcessOutcome(status=DOC_FAILED, error_code=ERROR_PROCESSING)
    chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
    return ProcessOutcome(status=DOC_READY, chunks=chunks, ocr_pages=max(1, pages))
