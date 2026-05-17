"""
Mr.Pilot · v105 · Google Vision API 备份引擎

只在 Gemini 主引擎失败时调用 · 提取文字后用 Gemini 二次抽字段
1000 页/月免费 · 之后 $1.50/1000 页

设计原则:
- 跟主引擎(Gemini)走同一个 API key(Default Gemini Project 已启用 Vision API)
- 只做"文字提取" · 字段抽取仍交回 Gemini
- 失败时返回 None · 让上层报错给用户(罕见情况)
"""

import os
import logging
import base64
import io
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)

VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
TIMEOUT_SECONDS = 30


def is_available() -> bool:
    """是否启用了 Vision 备份(只要有 Gemini key 就算启用)"""
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_VISION_API_KEY"))


def _get_api_key() -> Optional[str]:
    return os.getenv("GOOGLE_VISION_API_KEY") or os.getenv("GEMINI_API_KEY")


def health_check() -> Dict[str, Any]:
    """简单可用性检查"""
    if not _get_api_key():
        return {"available": False, "error": "no_api_key"}
    return {"available": True}


def _pdf_to_images(pdf_bytes: bytes, max_pages: int = 50) -> List[bytes]:
    """PDF 转图片字节列表(Vision 不支持 PDF · 必须转图)"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed · vision fallback unavailable")
        return []
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        # 200 DPI 渲染 · 平衡精度和体积
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        images.append(pix.tobytes("png"))
    doc.close()
    return images


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 50) -> Optional[Dict[int, str]]:
    """
    PDF → 每页文字 dict
    返回 {page_index_0_based: text} · 失败返回 None
    """
    api_key = _get_api_key()
    if not api_key:
        return None
    
    try:
        images = _pdf_to_images(pdf_bytes, max_pages=max_pages)
        if not images:
            return None
        
        results = {}
        for idx, img_bytes in enumerate(images):
            text = _vision_extract_image(img_bytes, api_key)
            if text:
                results[idx] = text
        return results if results else None
    except Exception as e:
        logger.error(f"Vision PDF extract error: {e}")
        return None


def extract_text_from_image_bytes(img_bytes: bytes) -> Optional[str]:
    """单张图 → 文字 · 失败返回 None"""
    api_key = _get_api_key()
    if not api_key:
        return None
    return _vision_extract_image(img_bytes, api_key)


def _vision_extract_image(img_bytes: bytes, api_key: str) -> Optional[str]:
    """调 Vision API 提文字"""
    try:
        b64 = base64.b64encode(img_bytes).decode("ascii")
        payload = {
            "requests": [{
                "image": {"content": b64},
                "features": [{
                    "type": "DOCUMENT_TEXT_DETECTION",  # 比 TEXT_DETECTION 更适合发票(保留布局)
                }],
                "imageContext": {
                    "languageHints": ["th", "en", "zh"]  # 泰文 + 英文 + 中文
                }
            }]
        }
        url = f"{VISION_API_URL}?key={api_key}"
        resp = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        if resp.status_code != 200:
            logger.warning(f"Vision API HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        responses = data.get("responses", [])
        if not responses:
            return None
        full_annotation = responses[0].get("fullTextAnnotation", {})
        text = full_annotation.get("text", "")
        return text.strip() if text else None
    except requests.Timeout:
        logger.warning("Vision API timeout")
        return None
    except Exception as e:
        logger.error(f"Vision API error: {e}")
        return None
