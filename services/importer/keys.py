# -*- coding: utf-8 -*-
"""
Pearnly · 通用导入器 · 共享字段键 + 表头指纹(REFACTOR-WA-B1 · 2026-05-29 从 template_learning 抽出)

纯搬家 0 逻辑改 · 叶子模块(只依赖 stdlib + coerce 叶子 · 不 import template_learning · 防循环)。
解 template_learning ↔ ai_mapping 循环:两者都从这里拿 _STMT_KEYS/_GL_KEYS + build_header_signature。
  · _STMT_KEYS / _GL_KEYS   银行对账 / GL 标准字段键(列推断 + AI 校验共用)
  · build_header_signature  表头指纹(归一化后 sha1 前 16 · 非安全用途 · 缓存键 / 学习键)
"""

from __future__ import annotations

import hashlib
from typing import Any, List

from services.importer.coerce import _norm

# ── statement 列推断标准键 ──
_STMT_KEYS = ("date", "description", "withdrawal", "deposit", "balance", "amount")
# ── GL 列推断标准键 ──
_GL_KEYS = ("date", "doc_no", "account", "description", "debit", "credit", "balance", "amount")


def build_header_signature(headers: List[Any]) -> str:
    normalized = [_norm(h) for h in headers if _norm(h)]
    # 表头指纹(非安全用途)· usedforsecurity=False 消除 bandit B324(摘要值不变 · 不影响已存映射键)
    return hashlib.sha1("|".join(normalized).encode("utf-8"), usedforsecurity=False).hexdigest()[
        :16
    ]
