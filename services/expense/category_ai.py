# -*- coding: utf-8 -*-
"""图片路自动分类 LLM 兜底(PO-9 · docs/smart-intake/16)。

关键词匹配(intake._match_category)命中不了泰文供应商/品名时,用 Gemini flash-lite 在
【本套账真实科目树】里选一个子科目编号 → 映射回 (category_id, subcategory_id)。只让模型在
真实选项里挑编号,绝不臆造科目;无 key/无选项/越界/失败 → (None, None)。文本路已够用,
仅图片路在关键词落空时调用(省成本)。结果仍可人工改(卡/详情/复核屏)。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_PROMPT = (
    "You categorize a Thai SMB business expense into ONE existing account category.\n"
    "You get the vendor name, line items, and a NUMBERED list of allowed categories.\n"
    "Reason from BOTH the vendor type AND the items together:\n"
    "- convenience store (7-Eleven/CP ALL/Lotus/FamilyMart) / restaurant / cafe / food delivery, "
    "or food & drink items → food & entertainment\n"
    "- fuel / petrol station (Bangchak/PTT/Shell/Caltex) or fuel items → travel & transport / fuel\n"
    "- water/electric/internet/phone bill → utilities\n"
    "- stationery / IT / software / office supplies → office expense\n"
    "- taxi/Grab/flight/hotel/toll → travel & transport\n"
    "- raw materials / goods for resale → cost of goods\n"
    "ALWAYS pick the single closest-matching number — make a reasonable best guess. Choose 0 ONLY "
    "when the receipt is truly unrelated to EVERY listed category (never pick 0 just because it is "
    "a mix).\n"
    'Never invent a category. Output ONLY JSON: {"choice": <number>} and nothing else.'
)


def _options(categories: list) -> list:
    """科目树 → [(category_id, subcategory_id, '大类 > 子类')] 扁平选项(仅含真实子科目)。"""
    out = []
    for parent in categories or []:
        for child in parent.get("children") or []:
            out.append((parent["id"], child["id"], f'{parent["name"]} > {child["name"]}'))
    return out


def suggest_category(
    vendor: str,
    descriptions: str,
    categories: list,
    *,
    api_key: Optional[str],
    timeout: int = 12,
) -> tuple[Optional[str], Optional[str]]:
    """LLM 兜底归类。返回 (category_id, subcategory_id);任何不确定 → (None, None)。"""
    if not api_key:
        return None, None
    options = _options(categories)
    if not options:
        return None, None
    listing = "\n".join(f"{i + 1}. {label}" for i, (_, _, label) in enumerate(options))
    payload = f"Vendor: {vendor or '-'}\nItems: {descriptions or '-'}\nCategories:\n{listing}"
    try:
        from services.ocr import gemini_models
        from services.ocr.layer2_gemini import _call_gemini_with_retry

        data, _meta = _call_gemini_with_retry(
            payload,
            api_key=api_key,
            model_name=gemini_models.flash_lite(),
            max_retries=1,
            timeout=timeout,
            system_prompt_override=_PROMPT,
        )
        choice = int((data or {}).get("choice") or 0)
    except (ValueError, TypeError):
        return None, None
    except Exception as e:  # noqa: BLE001
        logger.warning("[category_ai] suggest failed: %s", str(e)[:160])
        return None, None
    if 1 <= choice <= len(options):
        cat_id, sub_id, _ = options[choice - 1]
        return cat_id, sub_id
    return None, None
