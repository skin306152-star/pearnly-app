# -*- coding: utf-8 -*-
"""PDF 文字层读取。带文字层 → 逐页文本;无文字层(扫描件)→ 诚实拒绝。

本引擎只接带文字层的 PDF。扫描件的 OCR 归 K1c,这里返回 no_text_layer,
不喂给下游假装转换。
"""

import io
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# 平均每页文字少于此阈值 = 视为扫描件/图片 PDF。电子台账每页数千字符,远超此值。
MIN_CHARS_PER_PAGE = 40


def extract_pages(pdf_bytes: bytes, *, layout: bool = False) -> Optional[List[str]]:
    """逐页抽文字层。解析失败返回 None(交调用方判 no_text_layer)。

    layout=True 保留字符的横向位置(列间空白不被压成单空格),给要按列切表的调用方用
    (services/summary_import/pdf_table.py)。默认 False = 现状,取数/关键词扫描不受影响。
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber 未安装 · 无法抽文字层")
        return None

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return [(page.extract_text(layout=layout) or "") for page in pdf.pages]
    except Exception as e:
        logger.info("PDF 文字层抽取失败 · %s: %s", type(e).__name__, e)
        return None


def has_text_layer(pages: Optional[List[str]]) -> bool:
    """页面文本是否够密 = 判定带文字层。空/过稀 → False。"""
    if not pages:
        return False
    total = sum(len(p) for p in pages)
    return total / len(pages) >= MIN_CHARS_PER_PAGE
