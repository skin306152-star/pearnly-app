# -*- coding: utf-8 -*-
"""管家文案层的语言底座:支持语种 + 回落语言 + 取词。

九个 copy_* 模块此前各写一份一模一样的 DEFAULT_LANG 与 _t。收成一份的理由是「加第三种
语言 / 改回落语言」这件事该只发生在一处 —— 分散那九份里只要漏改一处,漏掉的那个模块会
在同一次对话里把回复掺成两种语言,而这种错测试很难看出来。

只放语言机制,不放任何文案:文案表仍按语义分居在各 copy_* 模块里。
"""

from __future__ import annotations

# 管家只做 zh + th(照 adm-* 超管键先例),与前端 static/ai/ai-i18n-steward.js 同进同退。
LANGS = ("zh", "th")
DEFAULT_LANG = "zh"


def t(table: dict, lang: str) -> str:
    """按语言取词。缺该语种回落 DEFAULT_LANG,再缺给空串 —— 宁可少一句,不把 key 吐给会计。"""
    return table.get(lang) or table.get(DEFAULT_LANG) or ""
