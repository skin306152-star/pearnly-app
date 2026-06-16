# -*- coding: utf-8 -*-
"""图片路自动分类 LLM 兜底(PO-9 · docs/smart-intake/16)。

关键词匹配(intake._match_category)命中不了泰文供应商/品名时,用 Gemini flash-lite 在
【本套账真实科目树】里选一个子科目编号 → 映射回 (category_id, subcategory_id)。只让模型在
真实选项里挑编号,绝不臆造科目;无 key/无选项/越界/失败 → (None, None)。文本路已够用,
仅图片路在关键词落空时调用(省成本)。结果仍可人工改(卡/详情/复核屏)。
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# 无歧义高频商户/品名 → (大类名, 子类名)的确定性规则:瞬时、零 LLM、永远一致、不可能判错。
# 只放无歧义的(加油站=燃油、Grab=交通、水电费=水电、电信=通讯);便利店/餐厅这种「看品名
# 才知道是商品还是餐饮」的有歧义项不进规则,留给 LLM 看品名判。名称对齐 categories._PRESET;
# 老树没这些名 → _resolve 不命中 → 退 LLM(优雅降级)。英文 token 用 \b 防误配。
_RULES: tuple = (
    (
        r"ไฮดีเซล|ดีเซล|เบนซิน|แก๊สโซฮอล|น้ำมันเชื้อเพลิง|gasohol|diesel|benzin|"
        r"บางจาก|bangchak|ปตท|\bptt\b|เชลล์|\bshell\b|คาลเท็กซ์|caltex|เอสโซ่|\besso\b|ซัสโก้|susco",
        "ค่าเดินทางและขนส่ง",
        "ค่าน้ำมันเชื้อเพลิง",
    ),
    (
        r"\bgrab\b|แกร็บ|\bbolt\b|โบลท์|lineman|ไลน์แมน|แท็กซี่|\btaxi\b|วินมอเตอร์ไซค์|ตุ๊กตุ๊ก",
        "ค่าเดินทางและขนส่ง",
        "ค่าแท็กซี่/แกร็บ",
    ),
    (r"การไฟฟ้า|กฟภ|กฟน|\bmea\b|\bpea\b|ค่าไฟฟ้า|ค่าไฟ", "ค่าสาธารณูปโภค", "ค่าไฟฟ้า"),
    (r"การประปา|กปน|กปภ|ค่าน้ำประปา", "ค่าสาธารณูปโภค", "ค่าน้ำประปา"),
    (
        r"\bais\b|เอไอเอส|ทรูมูฟ|\btrue\b|\bdtac\b|ดีแทค|3bb|อินเทอร์เน็ต|internet|ค่าโทรศัพท์",
        "ค่าสาธารณูปโภค",
        "ค่าโทรศัพท์/อินเทอร์เน็ต",
    ),
)


def _resolve(categories: list, parent_name: str, child_name: str):
    """(大类名, 子类名) → 树里的 (cat_id, sub_id);名不在树里返 (None, None)。"""
    for p in categories or []:
        if p.get("name") == parent_name:
            for c in p.get("children") or []:
                if c.get("name") == child_name:
                    return p["id"], c["id"]
            return p["id"], None
    return None, None


def rule_category(vendor: str, descs: str, categories: list):
    """无歧义高频商户/品名 → 确定性归类(瞬时·永远一致·零 LLM)。不命中 → (None, None) 交 LLM。"""
    text = f"{vendor or ''} {descs or ''}"
    for pattern, pname, cname in _RULES:
        if re.search(pattern, text, re.IGNORECASE):
            cid, sid = _resolve(categories, pname, cname)
            if cid:
                return cid, sid
    return None, None


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
    "CRITICAL: coffee / drinks / snacks / meals / any food item (even bought at a convenience "
    "store) → food & entertainment, NEVER travel. Travel/transport is ONLY taxi/Grab/fuel/flight/"
    "hotel/toll — never food.\n"
    "ALWAYS pick the single closest-matching number — make a reasonable best guess. Choose 0 ONLY "
    "when the receipt is truly unrelated to EVERY listed category (never pick 0 just because it is "
    "a mix).\n"
    'Never invent a category. Output ONLY JSON: {"choice": <number>} and nothing else.'
)


_BATCH_PROMPT = (
    "Categorize EACH Thai SMB expense item into ONE category number from the numbered list.\n"
    "Rules: coffee/drinks/snacks/meals/groceries/any food → food & entertainment (NEVER travel);\n"
    "taxi/Grab/fuel/flight/hotel/toll → travel & transport;\n"
    "water/electric/internet/phone bill → utilities;\n"
    "stationery/IT/software/office supplies → office; raw materials/goods for resale → cost of goods.\n"
    "Pick the single closest number for EACH item; never invent. "
    'Output ONLY JSON {"choices": [n1, n2, ...]} — same length and order as the items.'
)


def categorize_items(items: list, categories: list, *, api_key: Optional[str], timeout: int = 15):
    """批量归类多项(确定性规则先行 → 剩余项一次 LLM 调用)。返回与 items 等长的 [(cat_id, sub_id)]。

    多项一句话(电费/买菜/吃饭…)逐项归类:省成本(规则免 LLM·剩余批量一次)、避免 N 次串行调用。
    """
    out = [rule_category(it.get("name", ""), "", categories) for it in items]
    options = _options(categories)
    todo = [i for i, (c, _s) in enumerate(out) if not c]
    if not (todo and api_key and options):
        return out
    listing = "\n".join(f"{i + 1}. {label}" for i, (_, _, label) in enumerate(options))
    names = "\n".join(f"{j + 1}) {items[i].get('name', '')}" for j, i in enumerate(todo))
    payload = f"Items:\n{names}\n\nCategories:\n{listing}"
    try:
        from services.ocr import gemini_models
        from services.ocr.layer2_gemini import _call_gemini_with_retry

        data, _meta = _call_gemini_with_retry(
            payload,
            api_key=api_key,
            model_name=gemini_models.flash(),
            max_retries=1,
            timeout=timeout,
            system_prompt_override=_BATCH_PROMPT,
        )
        choices = (data or {}).get("choices") or []
    except Exception as e:  # noqa: BLE001
        logger.warning("[category_ai] batch suggest failed: %s", str(e)[:160])
        return out
    for j, i in enumerate(todo):
        if j >= len(choices):
            break
        try:
            ch = int(choices[j])
        except (ValueError, TypeError):
            continue
        if 1 <= ch <= len(options):
            out[i] = (options[ch - 1][0], options[ch - 1][1])
    return out


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

        # 用主力 flash(2.5-flash),非最强 3.5-flash:分类是「在选项里挑编号」的小任务,2.5-flash
        # ~3s 且准(prod 实测咖啡→餐饮、加油→燃油、电费→水电全对);3.5-flash 慢、常超 12s →
        # DeadlineExceeded 返空 → 分类全丢(这才是「分类一直空」的真因)。
        data, _meta = _call_gemini_with_retry(
            payload,
            api_key=api_key,
            model_name=gemini_models.flash(),
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
