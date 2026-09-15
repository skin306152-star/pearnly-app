# -*- coding: utf-8 -*-
"""LINE 一行资料按常见分隔符分段(订车付款资料共用)· 零 IO 纯函数。

用户在 LINE 里写同一行资料的分隔方式五花八门:竖线(半/全角)、逗号(英文/中文/顿号)、
斜杠(半/全角)、居中点。这里只做一件事 —— **一次只当一种规则**用,切完必须精确等于调用方
期望的段数;一种都切不出来就回 None 让调用方重问。宁可多问一次,也不把账号/金额猜着
拆成两段写进 DMS。

刻意不拆的:
  · 账号里的 `/`(19/09/2569 这种日期、123/456 这种账号):斜杠切出来的段数对不上就不认;
  · 时间 `14:36`:冒号不是分隔符;
  · 金额 `1,000.00`:点号两侧没有留白、「数字.数字」一律不当分隔符;逗号/斜杠紧夹在数字
    中间(千位逗号、账号里的斜杠)也不当分隔符。
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple

# 分隔符类:一次只用一类,顺序即优先级(越靠前越不容易误伤)。
SEPARATOR_CLASSES: Tuple[Tuple[str, ...], ...] = (
    ("|",),  # 竖线(全角 ｜ 先归一成 |)
    (",", "，", "、"),  # 英文逗号 / 中文逗号 / 顿号
    ("/", "／"),  # 斜杠(半角 / 全角)
    ("·", "・", "•", "∙"),  # 居中点类
)

# 数字/数字紧邻的**半角** , 与 / 不是分隔符,是千位逗号或账号/日期里的斜杠:
# 「1,000.00」「123/456」必须原样留在同一段里。全角 , / 从不这样写数字(它们是明确的分隔
# 写法),竖线与居中点同理,都不加这条。
_DIGIT_GUARDS: Dict[Tuple[str, ...], "re.Pattern[str]"] = {
    (",", "，", "、"): re.compile(r"\d,\d"),
    ("/", "／"): re.compile(r"\d/\d"),
}

# 点号最保守:两侧留白(「 . 」)才认;不加空白的点号另有严格计数规则,且绝不拆
# 「数字.数字」(1,000.00 / 19.09 这类金额与日期)、也不认「点号后跟空格」(Mr. Somchai)。
_SPACED_DOT_RE = re.compile(r"\s\.\s")
_DIGIT_DOT_RE = re.compile(r"\d\s*\.\s*\d")
_DOT_THEN_SPACE_RE = re.compile(r"\.\s")


def _by_chars(chars: Tuple[str, ...], value: str) -> Optional[List[str]]:
    if not any(ch in value for ch in chars):
        return None
    guard = _DIGIT_GUARDS.get(chars)
    if guard is not None and guard.search(value):
        return None
    parts = [value]
    for ch in chars:
        parts = [piece for part in parts for piece in part.split(ch)]
    return parts


def _by_spaced_dot(value: str) -> Optional[List[str]]:
    """a . b . c(点号两侧留白)。"""
    if not _SPACED_DOT_RE.search(value) or _DIGIT_DOT_RE.search(value):
        return None
    return _SPACED_DOT_RE.split(value)


def _by_dot(value: str) -> Optional[List[str]]:
    """点号兜底:严格按段数拆(KBank.VISA);小数与缩写一律不认。"""
    if "." not in value or _DIGIT_DOT_RE.search(value) or _DOT_THEN_SPACE_RE.search(value):
        return None
    return value.split(".")


_RULES: Tuple[Callable[[str], Optional[List[str]]], ...] = (
    *(lambda value, chars=chars: _by_chars(chars, value) for chars in SEPARATOR_CLASSES),
    _by_spaced_dot,
    _by_dot,
)


def split_fields(text: Optional[str], expected: int) -> Optional[List[str]]:
    """一行资料 → 恰好 `expected` 段(已去首尾空白);没有一种规则能给到这个段数就回 None。

    段里出现空串也算这条规则不成立(空段不是字段):「A |  | C」不会被当成三段。
    """
    if expected <= 0:
        return None
    value = str(text or "").replace("｜", "|").strip()
    if not value:
        return None
    for rule in _RULES:
        parts = rule(value)
        if parts is None or len(parts) != expected:
            continue
        cleaned = [part.strip() for part in parts]
        if any(not part for part in cleaned):
            continue
        return cleaned
    return None


__all__ = ["SEPARATOR_CLASSES", "split_fields"]
