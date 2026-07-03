# -*- coding: utf-8 -*-
"""task → 免费优先路径 / 首读档 tier 名 的静态声明(单一事实源)。

本模块只管「这个 task 用哪一档」;「这一档此刻映射到哪个具体模型」由
gemini_models 解析(env 默认 + engine_policy 按 OCR_MODE 的请求级覆写)——
换模型改 env/后台策略即可,业务代码零改动。free_first 描述该 task 的
零成本确定性路径(有文字层的 PDF / Excel / regex),命中即不叫模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from services.ocr import gemini_models


@dataclass(frozen=True)
class TaskPolicy:
    task: str
    primary_tier: str  # "flash" | "flash_lite" · 需要模型时的首读档
    free_first: Optional[str]  # 零成本路径描述 · None=无(直喂模型)


POLICIES: Dict[str, TaskPolicy] = {
    "invoice": TaskPolicy("invoice", "flash", "pdf_text_layer/table"),
    "id_card": TaskPolicy("id_card", "flash_lite", None),
    "bank_statement": TaskPolicy("bank_statement", "flash_lite", "excel/pdfplumber/coords"),
    "gl_ledger": TaskPolicy("gl_ledger", "flash", "excel/pdfplumber/mrerp_table"),
    "vat_report": TaskPolicy("vat_report", "flash", "excel/pdf_text/regex"),
}


def policy_for(task: str) -> TaskPolicy:
    """未知 task 直接 KeyError——编排入口的第一道防线。"""
    return POLICIES[task]


def primary_model(task: str) -> str:
    tier = POLICIES[task].primary_tier
    return gemini_models.flash_lite() if tier == "flash_lite" else gemini_models.flash()
