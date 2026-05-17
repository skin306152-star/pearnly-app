# -*- coding: utf-8 -*-
"""
Mr.Pilot · OCR 引擎模块
EasyOCR 懒加载 + 线程锁(免费 CPU 层不适合并发)
PDF 转图片 + EasyOCR 识别 + 简单字段抽取
"""

import os
import io
import re
import time
import logging
import tempfile
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# 全局 EasyOCR Reader(懒加载单例)
_reader = None
_reader_lock = threading.Lock()
_reader_loading = False

# OCR 识别串行锁(HF 免费层 CPU 弱,并行会崩)
_ocr_lock = threading.Lock()


def get_reader():
    """
    懒加载 EasyOCR Reader
    第一次调用会下载模型(5-10 分钟),之后秒开
    """
    global _reader, _reader_loading
    if _reader is not None:
        return _reader

    with _reader_lock:
        if _reader is not None:
            return _reader
        _reader_loading = True
        try:
            logger.info("🔄 EasyOCR 首次加载(下载模型 + 初始化,预计 3-10 分钟)...")
            t0 = time.time()
            import easyocr
            # 泰文 + 英文组合(EasyOCR 限制:'th' 必须和 'en' 一起)
            _reader = easyocr.Reader(
                ["th", "en"],
                gpu=False,
                verbose=False,
                download_enabled=True,
            )
            logger.info(f"✅ EasyOCR 就绪(耗时 {time.time()-t0:.1f}s)")
            return _reader
        finally:
            _reader_loading = False


def is_reader_loading() -> bool:
    return _reader_loading


def is_reader_ready() -> bool:
    return _reader is not None


# ============================================================
# PDF 处理
# ============================================================
def count_pdf_pages(pdf_bytes: bytes) -> int:
    """快速查 PDF 页数(不解压图片)"""
    import fitz
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        n = doc.page_count
        doc.close()
        return n
    except Exception as e:
        logger.error(f"读取 PDF 页数失败: {e}")
        return 0


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[bytes]:
    """PDF → PNG bytes 列表(每页一张)"""
    import fitz
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


# ============================================================
# 字段简易抽取(EasyOCR 纯文本 → 半结构化)
# ============================================================
_RE_TAX_ID = re.compile(r"(?<!\d)(\d{13})(?!\d)")
_RE_INVOICE_NO = re.compile(
    r"(?:INV|INVOICE|เลขที่|No\.?|NO\.?)[^\w]{0,3}([A-Z0-9\-/]{4,30})",
    re.IGNORECASE,
)
_RE_DATE = re.compile(
    r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})"
)
_RE_TOTAL = re.compile(
    r"(?:TOTAL|รวม|จำนวนเงิน|ยอดรวม|ยอดสุทธิ|รวมทั้งสิ้น)[^\d]{0,10}([\d,]+\.?\d*)",
    re.IGNORECASE,
)


def extract_fields(text: str) -> Dict[str, Any]:
    """从 OCR 文本抽取基础字段(Free 版简化解析)"""
    result = {
        "invoice_number": None,
        "date": None,
        "tax_ids": [],
        "total_amount": None,
    }

    # 发票号
    m = _RE_INVOICE_NO.search(text)
    if m:
        result["invoice_number"] = m.group(1).strip()

    # 日期
    m = _RE_DATE.search(text)
    if m:
        result["date"] = m.group(1).strip()

    # 税号(13 位数字,可能有多个)
    tax_ids = _RE_TAX_ID.findall(text)
    result["tax_ids"] = list(set(tax_ids))[:5]  # 最多 5 个

    # 总金额(找最大的一个)
    amounts = []
    for m in _RE_TOTAL.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            amounts.append(float(raw))
        except ValueError:
            pass
    if amounts:
        result["total_amount"] = max(amounts)

    return result


# ============================================================
# 识别主入口
# ============================================================
def recognize_pdf(pdf_bytes: bytes, max_pages: int = 20) -> Dict[str, Any]:
    """
    识别 PDF,返回结构化结果
    {
        "pages": [
            {
                "page_number": 1,
                "text": "...",
                "lines": ["..."],
                "fields": {...},
            }
        ],
        "page_count": N,
        "elapsed_ms": XXX,
        "engine": "easyocr"
    }
    """
    t0 = time.time()

    # 1. PDF → 图片
    try:
        images = pdf_to_images(pdf_bytes, dpi=200)
    except Exception as e:
        logger.error(f"PDF 转图片失败: {e}")
        raise ValueError("ocr.invalid_pdf")

    if not images:
        raise ValueError("ocr.empty_pdf")

    if len(images) > max_pages:
        raise ValueError("ocr.too_many_pages")

    # 2. 加载 Reader(首次耗时)
    reader = get_reader()

    # 3. 逐页识别(串行锁,防并发 OOM)
    pages_result = []
    with _ocr_lock:
        for idx, img_bytes in enumerate(images, start=1):
            t_page = time.time()
            try:
                # readtext 返回 [(bbox, text, conf), ...]
                rows = reader.readtext(
                    img_bytes,
                    detail=1,
                    paragraph=False,
                )
                lines = [r[1] for r in rows if r[1].strip()]
                full_text = "\n".join(lines)

                pages_result.append({
                    "page_number": idx,
                    "text": full_text,
                    "lines": lines,
                    "fields": extract_fields(full_text),
                    "elapsed_ms": int((time.time() - t_page) * 1000),
                })
                logger.info(
                    f"  第 {idx}/{len(images)} 页识别完 "
                    f"({len(lines)} 行, {int((time.time()-t_page)*1000)}ms)"
                )
            except Exception as e:
                logger.error(f"第 {idx} 页识别失败: {e}")
                pages_result.append({
                    "page_number": idx,
                    "text": "",
                    "lines": [],
                    "fields": extract_fields(""),
                    "error": str(e),
                    "elapsed_ms": int((time.time() - t_page) * 1000),
                })

    return {
        "pages": pages_result,
        "page_count": len(pages_result),
        "elapsed_ms": int((time.time() - t0) * 1000),
        "engine": "easyocr",
    }
