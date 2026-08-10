# -*- coding: utf-8 -*-
"""
services/erp/mrerp_business_friendly.py

Friendly-message catalog for MR.ERP business failures.

Maps the patterns that show up in the report.php xlsx's `หมายเหตุ` column
(or in our own ERR_* codes coming out of validate_history_for_sales_credit)
to friendly, localized messages.

The catalog has two layers:
- ERR_* codes  : exact-string keys; cover everything our adapter can
                 emit before reaching MR.ERP (length checks, missing
                 customer mapping, etc.).
- Thai reasons : substring-match keys (case-insensitive). Lets us catch
                 the actual server-side rejections from MR.ERP even when
                 the report wording drifts a bit between releases.

P1-A §3.9 (Zihao 2026-05-18 拍板) — 4-language coverage:
    th     Thai      (primary; matches MR.ERP UI language)
    en     English   (international)
    zh     Simplified Chinese (mainland)
    zh_TW  Traditional Chinese (Taiwan/HK)

Deviation note: CLAUDE.md's standard 4-lang set is `zh/en/th/ja`. Zihao
explicitly substituted ja → zh_TW for this catalog because the failure-
message UI surface lives close to MR.ERP-side accountants where Taiwan
locale is more common than Japanese.

Lookup contract (`get_friendly(reason, lang='zh')`):
    - returns the lang string when found
    - falls back to English, then to the input reason
    - never returns None

Use `translate_reasons(reasons, lang)` for the common case of a whole
FailedRow.reasons list.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from services.erp.mrerp_business_friendly_catalog import (
    _ERR_CATALOG,
    _THAI_REASON_CATALOG,
)

SUPPORTED_LANGS = ("th", "en", "zh", "zh_TW")
DEFAULT_LANG = "zh"


def get_friendly(
    reason: Optional[str],
    lang: str = DEFAULT_LANG,
) -> Dict[str, str]:
    """Translate one rejection reason into all 4 supported languages.

    Returns a dict containing every supported language. If no catalog
    entry matches, returns a dict where every language falls back to
    the raw `reason` string (so callers always get a printable value).

    `lang` selects which key is treated as primary (used by callers that
    want a single-string fallback), but the full dict is returned either
    way so the UI can offer "show original" toggles.
    """
    if not reason:
        return {k: "" for k in SUPPORTED_LANGS}

    # Exact match on ERR_* codes first (cheap, deterministic).
    if reason in _ERR_CATALOG:
        return dict(_ERR_CATALOG[reason])

    # Substring match for Thai reasons coming from report.php.
    low = reason.strip().lower()
    for pattern, translations in _THAI_REASON_CATALOG:
        if pattern.lower() in low:
            return dict(translations)

    # Unknown — echo the raw reason in every language. The UI can render
    # it verbatim; the user at least sees something honest.
    return {k: reason for k in SUPPORTED_LANGS}


def translate_reasons(
    reasons: List[str],
    lang: str = DEFAULT_LANG,
) -> List[Dict[str, str]]:
    """Apply get_friendly to a whole list (typically FailedRow.reasons).

    Returns a parallel list of {lang -> text} dicts.
    """
    return [get_friendly(r, lang=lang) for r in (reasons or [])]


def primary_friendly(
    reason: Optional[str],
    lang: str = DEFAULT_LANG,
) -> str:
    """Convenience: one string in the caller's chosen language, falling
    back gracefully to English then to the raw text."""
    translations = get_friendly(reason, lang=lang)
    if lang in translations and translations[lang]:
        return translations[lang]
    return translations.get("en") or (reason or "")


# Pearnly 前端主 UI 的 4 语集(home.js currentLang)· 注意是 ja 不是 zh_TW。
# catalog 历史按 th/en/zh/zh_TW 编(失败信息界面靠近台湾会计师 · 见模块头注释),
# 这里把它映射到主 UI 的 zh/th/en/ja:ja 无目录条目 → 退英文(国际兜底)。
APP_UI_LANGS = ("zh", "th", "en", "ja")


def _match_catalog(reason: str) -> Optional[Dict[str, str]]:
    """命中则返回 catalog 原始 dict(th/en/zh/zh_TW),否则 None。

    精确匹配 miss 后,再用正则从 reason 开头抠 ERR_ 码 token
    (生产的 error_msg 常带后缀,如 "ERR_AUTH: login failed" —— 整串精确匹配永远 miss),
    抠到且在 _ERR_CATALOG 里 → 直接返回该条;仍 miss 才走泰文子串层。"""
    if reason in _ERR_CATALOG:
        return _ERR_CATALOG[reason]
    m = re.match(r"^(ERR_[A-Z0-9_]+)", reason)
    if m and m.group(1) in _ERR_CATALOG:
        return _ERR_CATALOG[m.group(1)]
    low = reason.strip().lower()
    for pattern, translations in _THAI_REASON_CATALOG:
        if pattern.lower() in low:
            return translations
    return None


def friendly_for_ui(reason: Optional[str]) -> Optional[Dict[str, str]]:
    """P2-C (Zihao 2026-05-27) · 给前端日志/异常渲染用的友好文案 4 语 dict。

    返回 {zh, th, en, ja}(主 UI 语言集),**仅当 reason 命中 catalog 时**;
    未命中返回 None → 调用方(前端)回退自己的 humanizeError(处理网络错误)/ 原文,
    避免把 raw 泰文/ERR 码直接展示给中日英用户(B7「不裸透泰文」)。

    ja 无 catalog 条目 → 退 en(国际兜底);任何语言缺失 → 退 en → 退 raw reason。
    """
    if not reason:
        return None
    matched = _match_catalog(reason)
    if matched is None:
        return None
    en = matched.get("en") or reason
    return {
        "zh": matched.get("zh") or en,
        "th": matched.get("th") or en,
        "en": en,
        "ja": en,  # 无日语目录 → 英文兜底(文档化偏差)
    }
