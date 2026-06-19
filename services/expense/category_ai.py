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
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

_TARGETS = {
    "food_drink": (
        ("ค่าอาหารและรับรอง", "餐饮", "อาหาร", "food", "meal", "entertainment"),
        ("ค่าอาหาร/เครื่องดื่ม", "餐费", "饮料", "อาหาร", "เครื่องดื่ม", "food", "drink"),
    ),
    "goods": (
        ("ซื้อสินค้า/วัตถุดิบ", "采购", "商品", "วัตถุดิบ", "goods", "purchase"),
        ("สินค้าสำเร็จรูป", "成品", "商品", "merchandise", "finished goods"),
    ),
    "fuel": (
        ("ค่าเดินทางและขนส่ง", "交通", "เดินทาง", "transport", "travel"),
        ("ค่าน้ำมันเชื้อเพลิง", "燃油", "น้ำมัน", "fuel", "petrol"),
    ),
    "taxi": (
        ("ค่าเดินทางและขนส่ง", "交通", "เดินทาง", "transport", "travel"),
        ("ค่าแท็กซี่/แกร็บ", "打车", "แท็กซี่", "grab", "taxi"),
    ),
    "hotel": (
        ("ค่าเดินทางและขนส่ง", "交通", "เดินทาง", "transport", "travel"),
        ("ค่าที่พัก/โรงแรม", "酒店", "ที่พัก", "โรงแรม", "hotel"),
    ),
    "parking_toll": (
        ("ค่าเดินทางและขนส่ง", "交通", "เดินทาง", "transport", "travel"),
        ("ค่าทางด่วน/ที่จอดรถ", "停车", "ทางด่วน", "ที่จอดรถ", "parking", "toll"),
    ),
    "shipping": (
        ("ค่าเดินทางและขนส่ง", "ขนส่ง", "transport", "logistics"),
        ("ค่าขนส่ง/พัสดุ", "快递", "พัสดุ", "ขนส่ง", "shipping", "parcel"),
    ),
    "electric": (("ค่าสาธารณูปโภค", "水电", "utility"), ("ค่าไฟฟ้า", "电费", "ไฟฟ้า")),
    "water": (("ค่าสาธารณูปโภค", "水电", "utility"), ("ค่าน้ำประปา", "水费", "น้ำประปา")),
    "phone_net": (
        ("ค่าสาธารณูปโภค", "通讯", "utility"),
        ("ค่าโทรศัพท์/อินเทอร์เน็ต", "电话", "网络", "internet", "phone"),
    ),
    "office_supplies": (
        ("ค่าใช้จ่ายสำนักงาน", "办公", "office"),
        ("เครื่องเขียน/วัสดุสิ้นเปลือง", "文具", "เครื่องเขียน", "stationery"),
    ),
    "office_equipment": (
        ("ค่าใช้จ่ายสำนักงาน", "办公", "office"),
        ("อุปกรณ์สำนักงาน", "办公用品", "office equipment"),
    ),
    "software": (
        ("ค่าใช้จ่ายสำนักงาน", "办公", "office"),
        ("ซอฟต์แวร์/บริการออนไลน์", "软件", "software", "online"),
    ),
    "cleaning": (
        ("ค่าใช้จ่ายสำนักงาน", "办公", "office"),
        ("ของใช้/ทำความสะอาดสำนักงาน", "清洁", "ทำความสะอาด", "cleaning"),
    ),
    "bank_fee": (
        ("ค่าธรรมเนียมและการเงิน", "财务", "finance", "bank"),
        ("ค่าธรรมเนียมธนาคาร", "银行手续费", "bank fee"),
    ),
    "rent": (("ค่าเช่า", "租金", "rent"), ("ค่าเช่าสำนักงาน/อาคาร", "办公室租金", "office rent")),
    "marketing": (
        ("ค่าการตลาดและโฆษณา", "营销", "marketing"),
        ("ค่าโฆษณาออนไลน์", "广告", "advertising"),
    ),
    "repair_vehicle": (
        ("ค่าซ่อมแซมและบำรุงรักษา", "维修", "repair"),
        ("ค่าซ่อม/บำรุงยานพาหนะ", "车辆维修", "vehicle"),
    ),
    "medicine": (
        ("ค่าสุขภาพและการแพทย์", "医疗", "health"),
        ("ค่ายา/เวชภัณฑ์", "药品", "ยา", "medicine"),
    ),
    "insurance_vehicle": (
        ("ค่าประกันภัย", "保险", "insurance"),
        ("ประกันยานพาหนะ", "车辆保险", "vehicle"),
    ),
}

_ITEM_RULES: tuple[tuple[str, str]] = (
    (
        r"กาแฟ|คอฟฟี่|อเมริกาโน|ลาเต้|คาปู|มอคค่า|espresso|americano|latte|cappuccino|coffee|"
        r"ชา|เครื่องดื่ม|น้ำดื่ม|น้ำเปล่า|น้ำแข็ง|เบเกอรี่|เค้ก|ขนม|snack|drink|beverage|"
        r"อาหาร|ข้าว|ก๋วยเตี๋ยว|ไก่|หมู|ปลา|เนื้อ|ผัด|ทอด|ต้ม|ยำ|แกง|meal|food|"
        r"สลัด|salad|ผัก|veggie|vegetable|สเต็ก|สเต๊ก|steak|เบอร์เกอร์|burger|พิซซ่า|pizza|"
        r"พาสต้า|pasta|สปาเกตตี|spaghetti|เฟรนช์ฟราย|fries|ทรัฟเฟิล|truffle|วาซาบิ|wasabi|"
        r"บุฟเฟ่ต์|บุฟเฟต์|buffet|ซีฟู้ด|ทะเล|seafood",
        "food_drink",
    ),
    (r"ไฮดีเซล|ดีเซล|เบนซิน|แก๊สโซฮอล|น้ำมันเชื้อเพลิง|gasohol|diesel|benzin|petrol|fuel", "fuel"),
    (
        r"\bgrab\b|แกร็บ|\bbolt\b|โบลท์|lineman|ไลน์แมน|แท็กซี่|\btaxi\b|วินมอเตอร์ไซค์|ตุ๊กตุ๊ก",
        "taxi",
    ),
    (r"ทางด่วน|ค่าจอด|ที่จอดรถ|parking|toll", "parking_toll"),
    (r"โรงแรม|ที่พัก|hotel|accommodation", "hotel"),
    (r"ไปรษณีย์|ems|flash express|kerry|j&t|dhl|พัสดุ|shipping|parcel|delivery fee", "shipping"),
    (r"การไฟฟ้า|กฟภ|กฟน|\bmea\b|\bpea\b|ค่าไฟฟ้า|ค่าไฟ", "electric"),
    (r"การประปา|กปน|กปภ|ค่าน้ำประปา", "water"),
    (
        r"\bais\b|เอไอเอส|ทรูมูฟ|\btrue\b|\bdtac\b|ดีแทค|3bb|อินเทอร์เน็ต|internet|ค่าโทรศัพท์",
        "phone_net",
    ),
    (r"กระดาษ|ปากกา|ดินสอ|สมุด|เครื่องเขียน|stationery|toner|หมึกพิมพ์", "office_supplies"),
    (r"คีย์บอร์ด|เมาส์|printer|เครื่องพิมพ์|อุปกรณ์สำนักงาน|office equipment", "office_equipment"),
    (r"software|saas|hosting|domain|cloud|ซอฟต์แวร์|บริการออนไลน์", "software"),
    (r"ทำความสะอาด|น้ำยาล้าง|ถุงขยะ|cleaning", "cleaning"),
    (r"ค่าธรรมเนียมธนาคาร|bank fee|ค่าธรรมเนียมโอน|transfer fee", "bank_fee"),
    (r"ค่าเช่า|rent", "rent"),
    (r"facebook ads|google ads|โฆษณา|advertising|marketing", "marketing"),
    (r"ซ่อมรถ|บำรุงรถ|ยางรถ|vehicle repair|car repair", "repair_vehicle"),
    (r"ยา|เวชภัณฑ์|medicine|pharmacy|drugstore", "medicine"),
    (r"ประกันรถ|vehicle insurance|car insurance", "insurance_vehicle"),
)

_VENDOR_RULES: tuple[tuple[str, str]] = (
    (r"cafe amazon|amazon coffee|กาแฟพันธุ์ไทย|starbucks|คาเฟ่|cafe|coffee", "food_drink"),
    (
        r"ร้านอาหาร|restaurant|little betong|foodstory|ภัตตาคาร|ครัว|kitchen|"
        r"บุฟเฟ่ต์|บุฟเฟต์|buffet|ซีฟู้ด|seafood|cafe|คาเฟ่",
        "food_drink",
    ),
    # 批发/大卖场 → 采购商品默认(品名清楚时 _ITEM_RULES 已先归位:笔→办公、食品→餐饮;
    # 只有品名识别不清才落到这里 = 调用方记 vendor_default)。
    (
        r"makro|แม็คโคร|แม็กโคร|\btops\b|ท็อปส์|lotus|โลตัส|tesco|เทสโก้|big ?c|บิ๊กซี|"
        r"gourmet market|villa market|วิลล่า มาร์เก็ต|foodland|ฟู้ดแลนด์",
        "goods",
    ),
    # 便利店 → 餐饮/便利店默认(同上:品名优先;不清才落此默认 = vendor_default)。
    (
        r"7-?eleven|seven ?eleven|เซเว่น|เซเว่นอีเลฟเว่น|7-?11|cp all|ซีพี ?ออลล์|"
        r"familymart|แฟมิลี่มาร์ท|family mart|มินิ ?บิ๊กซี",
        "food_drink",
    ),
    (r"\bgrab\b|แกร็บ|\bbolt\b|โบลท์|lineman|ไลน์แมน|แท็กซี่|\btaxi\b", "taxi"),
    (
        r"บางจาก|bangchak|ปตท|\bptt\b|เชลล์|\bshell\b|คาลเท็กซ์|caltex|เอสโซ่|\besso\b|ซัสโก้|susco",
        "fuel",
    ),
    (r"การไฟฟ้า|กฟภ|กฟน|\bmea\b|\bpea\b", "electric"),
    (r"การประปา|กปน|กปภ", "water"),
    (r"\bais\b|เอไอเอส|ทรูมูฟ|\btrue\b|\bdtac\b|ดีแทค|3bb", "phone_net"),
    (r"ไปรษณีย์|flash express|kerry|j&t|dhl", "shipping"),
    (r"ธนาคาร|bank", "bank_fee"),
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


def _norm_name(name: str) -> str:
    return re.sub(r"[\s\-/()（）&·]+", "", (name or "").casefold())


def _alias_match(name: str, aliases: tuple[str, ...]) -> bool:
    n = _norm_name(name)
    return bool(n) and any((a := _norm_name(alias)) and (a in n or n in a) for alias in aliases)


def _resolve_target(categories: list, target: str):
    parent_aliases, child_aliases = _TARGETS[target]
    parent_hit = None
    for parent in categories or []:
        if _alias_match(parent.get("name"), parent_aliases):
            parent_hit = parent
            for child in parent.get("children") or []:
                if _alias_match(child.get("name"), child_aliases):
                    return parent["id"], child["id"]
    for parent in categories or []:
        for child in parent.get("children") or []:
            if _alias_match(child.get("name"), child_aliases):
                return parent["id"], child["id"]
    return (parent_hit["id"], None) if parent_hit else (None, None)


def _first_rule(text: str, rules: tuple[tuple[str, str]], categories: list):
    for pattern, target in rules:
        if re.search(pattern, text or "", re.IGNORECASE):
            cid, sid = _resolve_target(categories, target)
            if cid:
                return cid, sid
    return None, None


def classify_rules(vendor: str, descs: str, categories: list):
    """确定性归类,返回 (cat_id, sub_id, layer)。layer ∈ 'item'|'vendor'|''。

    品名优先(item)→ 商户(vendor)→ 商户+品名合并再过品名。品名优先避免 PTT/Cafe Amazon
    咖啡误分燃油;7-11/Makro 等便利店/大卖场只在品名识别不清时落到商户默认(layer='vendor',
    调用方据此记 category_source=vendor_default 便于观察)。
    """
    cid, sid = _first_rule(descs or "", _ITEM_RULES, categories)
    if cid:
        return cid, sid, "item"
    cid, sid = _first_rule(vendor or "", _VENDOR_RULES, categories)
    if cid:
        return cid, sid, "vendor"
    cid, sid = _first_rule(f"{vendor or ''} {descs or ''}", _ITEM_RULES, categories)
    return (cid, sid, "item") if cid else (None, None, "")


def rule_category(vendor: str, descs: str, categories: list):
    """确定性归类(2-tuple · 向后兼容多处调用)。命中层见 classify_rules。"""
    cid, sid, _layer = classify_rules(vendor, descs, categories)
    return cid, sid


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
    out = [rule_category("", it.get("name", ""), categories) for it in items]
    options = _options(categories)
    todo = [i for i, (c, _s) in enumerate(out) if not c]
    if not (todo and api_key and options):
        return out
    listing = _listing(options)
    names = "\n".join(f"{j + 1}) {items[i].get('name', '')}" for j, i in enumerate(todo))
    payload = f"Items:\n{names}\n\nCategories:\n{listing}"
    # 经 AI Gateway 跑 expense_category_choose(P2E·批量挑编号)。ok=False → 保留规则结果(out)。
    try:
        from services.ai_gateway import router as ai_gateway

        res = ai_gateway.run_task(
            "expense_category_choose",
            prompt=_BATCH_PROMPT,
            text=payload,
            api_key=api_key,
            timeout_s=timeout,
        )
        if not res.ok:
            return out
        choices = (res.data or {}).get("choices") or []
    except Exception as e:  # noqa: BLE001
        logger.warning("[category_ai] batch suggest failed: %s", str(e)[:160])
        return out
    for j, i in enumerate(todo):
        if j >= len(choices):
            break
        cid, sid = _decode_choice(choices[j], options)
        if cid:
            out[i] = (cid, sid)
    return out


_PARSE_PROMPT = (
    "Extract EACH expense from the user's casual Thai/Chinese sentence. For EACH expense:\n"
    "- name: the CLEAN item only (e.g. 'น้ำดื่ม', 'ทุเรียน', '榴莲', '咖啡') — DROP verbs (ซื้อ/买/"
    "ซื้อมา), the word price (ราคา/价/价格), store names (เซเว่น/7-Eleven/Lotus), connectors (และ/แ"
    "ละ/和/跟), and units (บาท/元/THB).\n"
    "- amount: the TOTAL THB for that item (qty×unit price), copied EXACTLY as digits from the "
    "text. For '买2杯咖啡共120' / '2 แก้ว 120' the amount is 120 (the total), NOT 60.\n"
    "- qty: the quantity if stated (2杯/2 แก้ว/x2/买2个/2 ชิ้น → 2), else 1. Keep the whole "
    "'qty units item total' as ONE item (do NOT split the qty number into a separate item).\n"
    "- choice: the category number from the list that best fits the item (food/drink/snack/groceries"
    " → food & entertainment; fuel → travel; water/electric/phone → utilities; goods → cost of goods"
    "; office supplies → office).\n"
    "Also extract document-level:\n"
    "- date: resolve relative dates against the given Today (yesterday/เมื่อวาน/昨天 → Today−1, "
    "etc.) → YYYY-MM-DD; empty if none stated.\n"
    "- vendor: the shop/seller name if stated (เซเว่น/7-Eleven/Starbucks/星巴克), else empty.\n"
    'Output ONLY JSON {"date":"...","vendor":"...","items":[{"name":"...","amount":"...","qty":N,'
    '"choice":N}]}.'
)


def parse_and_categorize(text: str, categories: list, *, api_key: Optional[str], timeout: int = 15):
    """口语多项 → 一次 LLM 拆干净 items(名+额+分类)+ 文档级 date/vendor。返回
    {"date": "YYYY-MM-DD"|"", "vendor": str, "items": [{name, amount(Decimal), category_id,
    subcategory_id}]} 或 None(无 key/失败/空)。

    治正则拆口语乱(「ฉันซื้อน้ำดื่มราคา」当项目名)。护栏:金额必须原文真出现的数字才采纳(不信
    LLM 编额);date 必须合法 YYYY-MM-DD 否则丢(用今天)。
    """
    if not api_key:
        return None
    options = _options(categories)
    if not options:
        return None
    from datetime import date as _date

    today = _date.today().isoformat()
    nums = {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text or "")}
    listing = _listing(options)
    try:
        from services.ocr import gemini_models
        from services.ocr.layer2_gemini import _call_gemini_with_retry

        data, _meta = _call_gemini_with_retry(
            f"Today: {today}\nText: {text}\n\nCategories:\n{listing}",
            api_key=api_key,
            model_name=gemini_models.flash(),
            max_retries=1,
            timeout=timeout,
            system_prompt_override=_PARSE_PROMPT,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[category_ai] multi-parse failed: %s", str(e)[:160])
        return None
    data = data or {}
    items = []
    for it in data.get("items") or []:
        name = str(it.get("name") or "").strip()
        amt_s = str(it.get("amount") or "").replace(",", "").strip()
        if not name or amt_s not in nums:  # 金额必须原文有(防 LLM 编造)
            continue
        try:
            amt = Decimal(amt_s)
        except (InvalidOperation, ValueError):
            continue
        cid, sid = _decode_choice(it.get("choice") or 0, options)
        qty = Decimal("1")  # 数量(#8):缺省 1;非法值回落 1(总额仍按 amount 权威)
        try:
            _q = Decimal(str(it.get("qty") or "1"))
            if _q > 0:
                qty = _q
        except (InvalidOperation, ValueError, TypeError):
            pass
        if amt > 0:
            items.append(
                {
                    "name": name,
                    "amount": amt,
                    "qty": qty,
                    "category_id": cid,
                    "subcategory_id": sid,
                }
            )
    if not items:
        return None
    d = str(data.get("date") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):  # 非法日期 → 用今天(不信 LLM 乱编)
        d = ""
    return {"date": d, "vendor": str(data.get("vendor") or "").strip(), "items": items}


def _options(categories: list) -> list:
    """科目树 → [(category_id, subcategory_id, '大类 > 子类')] 扁平选项(仅含真实子科目)。"""
    out = []
    for parent in categories or []:
        for child in parent.get("children") or []:
            out.append((parent["id"], child["id"], f'{parent["name"]} > {child["name"]}'))
    return out


def _listing(options: list) -> str:
    """扁平选项 → 编号清单文本(让 LLM 在真实编号里挑)。"""
    return "\n".join(f"{i + 1}. {label}" for i, (_, _, label) in enumerate(options))


def _decode_choice(choice, options: list) -> tuple:
    """LLM 返回编号 → (category_id, subcategory_id);非数字/越界 → (None, None)。"""
    try:
        ch = int(choice)
    except (ValueError, TypeError):
        return None, None
    if 1 <= ch <= len(options):
        return options[ch - 1][0], options[ch - 1][1]
    return None, None


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
    listing = _listing(options)
    payload = f"Vendor: {vendor or '-'}\nItems: {descriptions or '-'}\nCategories:\n{listing}"
    # 经 AI Gateway 跑 expense_category_choose(P2E):档位 flash·只在真实编号里挑;ok=False(无 key/
    # 超时/parse)→ (None, None) 让调用方走规则/留未分类。模型/超时由 task 规格定,与现状一致。
    try:
        from services.ai_gateway import router as ai_gateway

        res = ai_gateway.run_task(
            "expense_category_choose",
            prompt=_PROMPT,
            text=payload,
            api_key=api_key,
            timeout_s=timeout,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[category_ai] suggest failed: %s", str(e)[:160])
        return None, None
    if not res.ok:
        return None, None
    return _decode_choice((res.data or {}).get("choice"), options)
