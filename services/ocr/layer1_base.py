# -*- coding: utf-8 -*-
"""Layer1 OCR · 常量 + 异常类层级(leaf · pipeline 按异常类别分流)。"""

from __future__ import annotations

import os
from typing import List

DEFAULT_DPI = 200
DEFAULT_MAX_PAGES = 50
DEFAULT_LANGUAGE_HINTS: List[str] = ["th", "en"]
# 60s 一刀切太死:长表/大批量生成侧耗时高(2026-08-13 bench qwen csv 支路 2/2 撞超时),
# 运维现场 OCR_L1_TIMEOUT_SECONDS 可单独调,默认仍 60。
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("OCR_L1_TIMEOUT_SECONDS") or "60")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp", ".gif"}
PDF_EXTENSIONS = {".pdf"}


# ============================================================
# Exception hierarchy
# ============================================================
class Layer1Error(Exception):
    """Base exception for layer 1 OCR errors. Catch this to handle any
    layer-1 failure generically; use subclasses for targeted dispatch."""


class Layer1AuthError(Layer1Error):
    """Credentials / authentication / billing / permission failure.

    NOT retryable — usually means GOOGLE_APPLICATION_CREDENTIALS is wrong,
    the project has billing disabled, or the Service Account lacks the
    Cloud Vision AI Service Agent role.
    """


class Layer1QuotaError(Layer1Error):
    """Quota or rate-limit exceeded. Retry after backoff."""


class Layer1TransientError(Layer1Error):
    """Network / timeout / 5xx error. Potentially retryable."""


class Layer1PDFError(Layer1Error):
    """PDF cannot be opened or rendered (corrupted, password-protected, etc.)."""


class Layer1InvalidImageError(Layer1Error):
    """Image bytes are not a decodable image (Vision API code 3 / INVALID_ARGUMENT):
    truncated upload, wrong-extension payload (e.g. PDF bytes named .jpg), 0-byte body.
    User's file problem, not an engine fault — callers map this to a 4xx."""
