# -*- coding: utf-8 -*-
"""管家文案层的语言底座 + 跨 copy_* 共用的产物原语:支持语种 + 回落语言 + 取词。

九个 copy_* 模块此前各写一份一模一样的 DEFAULT_LANG 与 _t。收成一份的理由是「加第三种
语言 / 改回落语言」这件事该只发生在一处 —— 分散那九份里只要漏改一处,漏掉的那个模块会
在同一次对话里把回复掺成两种语言,而这种错测试很难看出来。

download_deeplink 也住这里:附件下载深链是 file_convert 与 table_generate 的产物里都会
出现的同一条 deeplink(copy_file / copy_table 各写一遍必漂)。

只放语言机制与这类原语,不放任何文案:文案表仍按语义分居在各 copy_* 模块里。
"""

from __future__ import annotations

from typing import Optional

# 管家只做 zh + th(照 adm-* 超管键先例),与前端 static/ai/ai-i18n-steward.js 同进同退。
LANGS = ("zh", "th")
DEFAULT_LANG = "zh"


def t(table: dict, lang: str) -> str:
    """按语言取词。缺该语种回落 DEFAULT_LANG,再缺给空串 —— 宁可少一句,不把 key 吐给会计。"""
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def download_deeplink(download: dict, label: dict, lang: str) -> Optional[dict]:
    """附件下载深链:产物带了 attachment_id 才给,否则 None(没有可下载的东西不摆按钮)。"""
    if not download.get("attachment_id"):
        return None
    return {
        "kind": "deeplink",
        "label": t(label, lang),
        "href": f"/api/ai/steward/attachments/{download['attachment_id']}/download",
    }
