# -*- coding: utf-8 -*-
"""
Mr.Pilot · Typhoon OCR 引擎(v0.12.0)
泰国本土 SCB 10X 出品的 Typhoon OCR · 泰语场景辅助识别

定位:
  - 不做主 OCR(主走 Gemini)
  - 仅在 Gemini 识别质量差时被调用作为"原始文字提取器"
  - 提取结果送回 Gemini 做二次结构化 · 实现 1+1>2

API 文档:https://docs.opentyphoon.ai/

环境变量:
  - TYPHOON_API_KEY · 必需(typhoon-* 格式 · opentyphoon.ai 注册)
  - TYPHOON_BASE_URL · 默认 https://api.opentyphoon.ai/v1

调用流程:
  1) 把 PDF 单页转 PNG → base64
  2) 送 typhoon-ocr 模型 → 返回 markdown 格式的文字提取
  3) 调用方拿到文字后,可以喂给 Gemini 重新结构化
"""
import os
import io
import time
import base64
import logging
import threading
from typing import Optional, Dict, Any, List
from collections import deque

logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
TYPHOON_BASE_URL = os.environ.get("TYPHOON_BASE_URL", "https://api.opentyphoon.ai/v1")
TYPHOON_API_KEY = os.environ.get("TYPHOON_API_KEY", "")

# Typhoon 主力 OCR 模型 · 输出 markdown
MODEL_OCR = os.environ.get("TYPHOON_MODEL_OCR", "typhoon-ocr-preview")

# 速率控制(opentyphoon.ai 免费层约 10 RPM)
RATE_LIMIT_RPM = int(os.environ.get("TYPHOON_RATE_LIMIT_RPM", "8"))
DEFAULT_TIMEOUT = int(os.environ.get("TYPHOON_TIMEOUT", "45"))

# ============================================================
# 全局速率限制 + 客户端
# ============================================================
_request_times: deque = deque()
_rate_lock = threading.Lock()
_client = None
_client_lock = threading.Lock()


def _rate_check() -> bool:
    now = time.time()
    with _rate_lock:
        while _request_times and now - _request_times[0] > 60:
            _request_times.popleft()
        if len(_request_times) >= RATE_LIMIT_RPM:
            return False
        _request_times.append(now)
        return True


def _get_client():
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("openai 库未安装")
            return None
        if not TYPHOON_API_KEY:
            logger.warning("TYPHOON_API_KEY 未配置 · Typhoon 增援将禁用")
            return None
        _client = OpenAI(base_url=TYPHOON_BASE_URL, api_key=TYPHOON_API_KEY, timeout=DEFAULT_TIMEOUT)
        logger.info(f"✅ Typhoon 客户端初始化完成")
        return _client


def is_available() -> bool:
    return bool(TYPHOON_API_KEY) and _get_client() is not None


# ============================================================
# 主接口:从 PIL 图片提取泰文文字
# ============================================================
def extract_text_from_image(pil_image, language_hint: str = "thai") -> Optional[str]:
    """
    送一张 PIL 图片给 Typhoon · 返回提取的文字(markdown 格式)
    失败返回 None
    """
    client = _get_client()
    if client is None:
        return None
    if not _rate_check():
        logger.warning("[Typhoon] 速率限制 · 跳过")
        return None

    try:
        # PIL → PNG bytes → base64
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"

        prompt = (
            "Extract ALL text from this invoice/receipt image. "
            "Preserve the original layout (use newlines for line breaks). "
            "Pay special attention to numbers (amounts, dates, invoice numbers, tax IDs). "
            "If there are tables, output them as markdown tables. "
            f"The text is primarily in {language_hint}."
        )

        t0 = time.time()
        resp = client.chat.completions.create(
            model=MODEL_OCR,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            temperature=0.0,
            max_tokens=2048,
        )
        elapsed = int((time.time() - t0) * 1000)
        text = resp.choices[0].message.content if resp.choices else ""
        logger.info(f"[Typhoon] OCR · {elapsed}ms · {len(text)} chars")
        return text or ""
    except Exception as e:
        logger.warning(f"[Typhoon] OCR 失败: {type(e).__name__}: {str(e)[:200]}")
        return None


def extract_text_from_pdf_bytes(pdf_bytes: bytes, page_indices: Optional[List[int]] = None) -> Dict[int, str]:
    """
    从 PDF 提取多页文字
    page_indices · 指定要提取的页码(0-based)· None 则提取所有页
    返回 {page_index: text}
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF 未安装")
        return {}

    out = {}
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total = len(doc)
        targets = page_indices if page_indices is not None else list(range(total))

        for idx in targets:
            if idx < 0 or idx >= total:
                continue
            page = doc.load_page(idx)
            # 渲染为 PIL 图片(180 dpi 平衡速度/精度)
            pix = page.get_pixmap(dpi=180)
            from PIL import Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            text = extract_text_from_image(img)
            if text:
                out[idx] = text
        doc.close()
    except Exception as e:
        logger.warning(f"[Typhoon] PDF 处理失败: {type(e).__name__}: {e}")
    return out


def health_check() -> Dict[str, Any]:
    return {
        "available": is_available(),
        "has_api_key": bool(TYPHOON_API_KEY),
        "base_url": TYPHOON_BASE_URL,
        "model": MODEL_OCR,
        "rate_limit_rpm": RATE_LIMIT_RPM,
    }
