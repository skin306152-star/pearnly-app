# -*- coding: utf-8 -*-
"""
services/ocr/pdf_backfill.py · REFACTOR-WA-OCRPERF Step1(PDF 留底后台化)

把「searchable PDF 生成 + 留底保存」从 OCR recognize 响应主路径挪到响应返回后的后台任务。
generate_and_save_pdf 是 app.py 原同步留底块(v114/v115)的【逐字搬家 · 0 逻辑改】:
  收集每页搜索文本(已识别字段)→ make_searchable_pdf(失败 fallback 原文件)→ save_pdf 落盘。
纯本地(pdf_searchable + pdf_storage · 不调 Gemini · 不碰扣费 · 不改任何识别字段)·
由 app.py 后台任务经 asyncio.to_thread 调度(sync CPU/disk 不堵 event loop · 铁律 #10)。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


def generate_and_save_pdf(
    content: bytes, pages: List[Any], user_id: str
) -> Tuple[Optional[str], Optional[int]]:
    """生成 searchable PDF 并留底 · 返回 (rel_path, size_bytes)· 失败返 (None, None)·绝不抛。

    与 app.py 原同步留底块语义逐字一致:
      - 收集每页搜索文本;有非空文本 → make_searchable_pdf 塞进不可见层;
      - 生成失败 → fallback 原始文件字节;
      - save_pdf 落盘返回相对路径 + 大小。
    任何异常吞掉(留底失败绝不影响识别 · 同原 try/except 行为)。
    """
    try:
        from services.ocr import pdf_storage
        from services.ocr import pdf_searchable

        _pdf_to_save = content
        try:
            pages_texts = pdf_searchable.extract_searchable_text_from_pages(pages or [])
            if any(t.strip() for t in pages_texts):
                searchable = pdf_searchable.make_searchable_pdf(content, pages_texts)
                if searchable:
                    _pdf_to_save = searchable
        except Exception as _se:
            logger.warning(f"v115 · searchable PDF 生成失败 · 用原始 PDF: {_se}")

        rel_path, size_bytes = pdf_storage.save_pdf(str(user_id), _pdf_to_save)
        return rel_path, size_bytes
    except Exception as _pdf_err:
        logger.warning(f"⚠️ PDF 留底失败(已忽略): {_pdf_err}")
        return None, None
