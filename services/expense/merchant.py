# -*- coding: utf-8 -*-
"""商户身份归一(学习键 + 匹配)· P2A。

分类规则在 category_ai;本模块只回答「这是哪个商户」:把「CP ALL / 7-ELEVEN / 7-11」、
「บริษัท X จำกัด (มหาชน) / X」收敛成同一商户键 —— 用户学习与读取用同一键,同商户不同写法学一次
即命中。税号→规范别名仅做身份解析(填错只影响身份识别,分类仍由 category_ai 品名优先决定)。
"""

from __future__ import annotations

import re

# 公司后缀(归一后形态)— 剥掉使「บริษัท X จำกัด (มหาชน)」与「X」同键。长后缀在前避免被短后缀
# 先吃掉(จำกัดมหาชน 先于 จำกัด/มหาชน)。
_SUFFIXES = (
    "บริษัทมหาชนจำกัด",
    "บริษัทจำกัดมหาชน",
    "จำกัดมหาชน",
    "บริษัท",
    "จำกัด",
    "มหาชน",
    "หจก",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "publiccompanylimited",
    "companylimited",
    "company",
    "limited",
    "coltd",
    "ltd",
    "plc",
    "inc",
    "股份有限公司",
    "有限公司",
    "公司",
)

# 大连锁不同写法 → 规范品牌键。让 7-ELEVEN/7-11/CP ALL/เซเว่น 学到同一条(要求 §2)。
_BRAND_ALIASES = (
    (r"7-?eleven|seven ?eleven|เซเว่น|7-?11|cp all|ซีพี ?ออลล์", "7-eleven"),
    (r"familymart|family mart|แฟมิลี่มาร์ท", "familymart"),
    (r"makro|แม็คโคร|แม็กโคร", "makro"),
    (r"\btops\b|ท็อปส์", "tops"),
    (r"lotus|โลตัส|tesco|เทสโก้", "lotus"),
    (r"big ?c|บิ๊กซี", "bigc"),
    (r"cafe amazon|amazon coffee|กาแฟอเมซอน|กาแฟพันธุ์ไทย", "cafe-amazon"),
    (r"starbucks|สตาร์บัคส์", "starbucks"),
    (r"bangchak|บางจาก", "bangchak"),
    (r"\bptt\b|ปตท", "ptt"),
    (r"\bshell\b|เชลล์", "shell"),
    (r"caltex|คาลเท็กซ์", "caltex"),
    (r"\besso\b|เอสโซ่", "esso"),
)

# 大连锁税号 → 规范商户别名(仅身份解析)。只放确信的极少数:填错只影响身份识别,品名仍主导
# 分类。待真票核验后再扩。
_TAX_ALIASES = {
    "0107542000011": "7-eleven cp all",  # บริษัท ซีพี ออลล์ จำกัด (มหาชน) · 7-Eleven 运营商
}


def _norm(name: str) -> str:
    # 去全部非词字符(空格/标点/逗号点括号)· 保留泰/拉丁/数字(Unicode \w 含泰文)。
    return re.sub(r"[\W_]+", "", (name or "").casefold())


def normalize_merchant(name: str) -> str:
    """归一商户名:小写、去空格/标点、剥公司后缀。空 → ''。"""
    n = _norm(name)
    for suf in _SUFFIXES:
        s = _norm(suf)
        if s and len(n) > len(s):  # 不把整名吃空
            n = n.replace(s, "")
    return n


def merchant_alias_by_tax(tax_id: str) -> str:
    """已知大连锁税号 → 规范商户别名(身份解析);未知 → ''。"""
    return _TAX_ALIASES.get((tax_id or "").strip(), "")


def is_known_brand(name: str) -> bool:
    """名字归一命中已知大连锁(含纯数字店号 711/7-11)→ True。供 field_clean 守卫:像金额的纯数字
    若实为店号则当店名保留、不当金额清空。"""
    return any(re.search(pattern, name or "", re.IGNORECASE) for pattern, _key in _BRAND_ALIASES)


def canonical_merchant(name: str, tax_id: str = "") -> str:
    """商户唯一键(学习键用):识别已知大连锁 → 规范品牌键(各写法归一);否则归一名。空 → ''。"""
    blob = f"{name or ''} {merchant_alias_by_tax(tax_id)}"
    for pattern, key in _BRAND_ALIASES:
        if re.search(pattern, blob, re.IGNORECASE):
            return key
    return normalize_merchant(name)
