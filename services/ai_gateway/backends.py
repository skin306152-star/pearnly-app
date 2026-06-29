# -*- coding: utf-8 -*-
"""LLM 后端选择(单一开关)。

OCR_LLM_BACKEND = aistudio(默认) | vertex | selfhost
  - aistudio:google-generativeai + API key(现状·行为零变化)
  - vertex  :google-genai + Vertex AI(服务账号 · 企业配额/数据驻留)
  - selfhost:OpenAI 兼容端点(自托管 Qwen2.5-VL 等)

唯一一处读环境变量决定后端;全产品 OCR/VAT/银行/知识的 LLM 调用都经此取 provider。
默认 aistudio → 老代码路径原样执行,不引入任何行为变化。
"""

from __future__ import annotations

import os
from typing import Optional

_VALID = ("aistudio", "vertex", "selfhost")


def active_backend() -> str:
    """当前后端(env OCR_LLM_BACKEND·小写·未知值回落 aistudio 不抛)。"""
    raw = (os.environ.get("OCR_LLM_BACKEND") or "aistudio").strip().lower()
    return raw if raw in _VALID else "aistudio"


def is_aistudio() -> bool:
    """是否默认后端(老路径)。OCR 核心据此走"原样旧代码"分支。"""
    return active_backend() == "aistudio"


def get_provider(name: Optional[str] = None):
    """取 provider 模块(懒加载·避免顶层 import 重链路 / 可选依赖)。"""
    backend = (name or active_backend()).strip().lower()
    if backend == "vertex":
        from services.ai_gateway.providers import vertex

        return vertex
    if backend == "selfhost":
        from services.ai_gateway.providers import selfhost

        return selfhost
    from services.ai_gateway.providers import aistudio

    return aistudio
