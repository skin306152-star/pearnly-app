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
from contextvars import ContextVar, Token
from typing import Optional

_VALID = ("aistudio", "vertex", "selfhost", "anthropic")

# 请求级后端覆盖:某处需为本请求固定某家 provider 时用(通用能力)。
# 现无生产调用方——economy 曾用它钉 aistudio(Vertex 无 2.5),已改由 vertex provider
# 按模型路由到 global 替代。显式传入 transport 的 backend 参数 > 本覆盖 > 全局 env。
_OVERRIDE: ContextVar[Optional[str]] = ContextVar("llm_backend_override", default=None)


def set_backend_override(backend: Optional[str]) -> Token:
    """设本请求上下文的后端覆盖;调用方负责用返回 token reset。非法值当无覆盖。"""
    b = (backend or "").strip().lower()
    return _OVERRIDE.set(b if b in _VALID else None)


def reset_backend_override(token: Token) -> None:
    _OVERRIDE.reset(token)


def override_backend() -> Optional[str]:
    """当前请求的后端覆盖(无 = None)。transport 在调用方未显式指定 backend 时消费。"""
    return _OVERRIDE.get()


def active_backend() -> str:
    """全局后端(env OCR_LLM_BACKEND·小写·未知值回落 aistudio 不抛)。"""
    raw = (os.environ.get("OCR_LLM_BACKEND") or "aistudio").strip().lower()
    return raw if raw in _VALID else "aistudio"


def effective_backend() -> str:
    """本请求实际后端:请求级覆盖(engine_policy 按档钉)> 全局 env。
    所有"走哪家 provider"的决策单点同源(is_aistudio / get_provider),不劈叉。"""
    return override_backend() or active_backend()


def is_aistudio() -> bool:
    """是否默认后端(老路径)。OCR 核心据此走"原样旧代码"分支——认请求级覆盖:
    selfhost 档钉了 override 时即便全局 env=aistudio 也返回 False,回落 Vision 路一并切自托管。"""
    return effective_backend() == "aistudio"


def get_provider(name: Optional[str] = None):
    """取 provider 模块(懒加载·避免顶层 import 重链路 / 可选依赖)。

    未显式指定后端时消费请求级覆盖(override_backend),再回落全局 env——这样
    engine_policy 按档钉的后端(如 selfhost 档)对直调 get_provider() 的热路(直读/
    gemini shim)也生效,不止 transport。transport 已自算 effective 后显式传入,不双取。"""
    backend = (name or effective_backend()).strip().lower()
    if backend == "vertex":
        from services.ai_gateway.providers import vertex

        return vertex
    if backend == "selfhost":
        from services.ai_gateway.providers import selfhost

        return selfhost
    if backend == "anthropic":
        from services.ai_gateway.providers import anthropic

        return anthropic
    from services.ai_gateway.providers import aistudio

    return aistudio
