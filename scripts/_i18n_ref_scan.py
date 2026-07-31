#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端源码里「取词调用引到了哪个字面量键」的扫描器 —— 两道词典引用闸共用这一份。

check_ai_i18n_refs.py(/ai 那套独立词典)和 check_i18n_refs.py(主 SPA + POS)判的是
同一件事:引用得到定义。差别只在「取词入口叫什么、词典在哪」。判据本身抄成两份必然漂 ——
一边补了「注释里的旧键不算」另一边没补,漏网的就从没补的那边过。

扫描只认【字面量键】。at('bill_st_' + status) 这类拼出来的键静态查不了,喂进闸只会变成
噪声;闸一旦开始误报就会被人 skip 掉,还不如不装。所以宁可少认,不可错认。
"""

from __future__ import annotations

import re

_QUOTES = "'\"`"
# 字面量得站在「键位」上才算键:左邻是 ( ? : || &&,右邻是 ) , : ? || &&。
# 这条邻居规则排掉两类同样是字面量、却不是键的东西 ——
#   at(role === 'user' ? 'stw_you' : 'stw_agent') 里的 'user'(比较值,左邻 =)
#   at('bill_st_' + status) 里的前缀(右邻 +),半截前缀当键查必然落空
_LEFT_OK = "(?:|&"
_RIGHT_OK = "),:?|&"
# 一个取词调用的实参扫描窗口:够长的模板串参数不至于把后面的调用点吞掉
_SCAN_LIMIT = 2000

_QUOTED_SPAN = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _read_string(text: str, i: int):
    """i 指向开引号 → (字面量内容, 引号后一位的下标);带 ${} 的模板串返 None。"""
    quote = text[i]
    j = i + 1
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == quote:
            body = text[i + 1 : j]
            if quote == "`" and "${" in body:
                return None, j + 1
            return body, j + 1
        j += 1
    return None, len(text)


def _skip_comment(text: str, i: int) -> int:
    """i 指向 / → 注释结束后的下标;不是注释返 i。注释里的撇号不能算字符串起点。"""
    nxt = text[i + 1 : i + 2]
    if nxt == "/":
        end = text.find("\n", i)
        return len(text) if end < 0 else end
    if nxt == "*":
        end = text.find("*/", i)
        return len(text) if end < 0 else end + 2
    return i


def in_comment(text: str, pos: int) -> bool:
    """pos 是否落在注释里 —— 只看本行前缀,不做整文件分词。

    整文件分词要能认出正则字面量(ai-api.js 里就有 /filename="?([^";]+)"?/ 这种带引号的),
    认错一个就把后面整片代码当字符串吞掉。逐行判够用:注释里提一句 t('old_key') 不该把闸
    弄红(改名后注释常留旧键),而取词调用永远不会跨行接在同一行的注释后面。
    """
    line_start = text.rfind("\n", 0, pos) + 1
    prefix = _QUOTED_SPAN.sub("", text[line_start:pos])
    return "//" in prefix or prefix.lstrip().startswith(("*", "/*"))


def _neighbor(text: str, i: int, step: int) -> str:
    """从 i 出发按 step 方向跳过空白,返回第一个实字符(越界返空串)。"""
    while 0 <= i < len(text):
        if not text[i].isspace():
            return text[i]
        i += step
    return ""


def first_arg_literals(text: str, start: int) -> list[tuple[int, str]]:
    """start = 左括号后一位。返回第一个实参里、括号深度为 0 的字面量 [(下标, 内容)]。

    只取第一个实参:t('k', {name: 'x'}) 的 'x' 是插值参数的值,不是键。
    只取深度 0:t(el.getAttribute('data-i18n')) 的 'data-i18n' 是内层调用的参数。
    """
    out: list[tuple[int, str]] = []
    depth = 0
    i = start
    end = min(len(text), start + _SCAN_LIMIT)
    while i < end:
        c = text[i]
        if c == "/":
            j = _skip_comment(text, i)
            if j != i:
                i = j
                continue
        if c in _QUOTES:
            body, j = _read_string(text, i)
            if depth == 0 and body is not None:
                out.append((i, body))
            i = j
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if c == ")" and depth == 0:
                break
            depth -= 1
        elif c == "," and depth == 0:
            break
        i += 1
    return out


def call_keys(text: str, head: re.Match, key_re: re.Pattern) -> list[tuple[int, str]]:
    """一个取词调用点 → 它引用的键。二选一写法 t(x ? 'a' : 'b') 两个分支都算引用。"""
    keys: list[tuple[int, str]] = []
    for pos, body in first_arg_literals(text, head.end()):
        if not key_re.match(body):
            continue
        left = _neighbor(text, pos - 1, -1)
        right = _neighbor(text, pos + len(body) + 2, 1)
        if left in _LEFT_OK and right in _RIGHT_OK:
            keys.append((pos, body))
    return keys


def scan_calls(text: str, heads: list[re.Match], key_re: re.Pattern) -> list[tuple[int, str]]:
    """[(行号, 键)] · heads 是各取词入口正则在本文件里的全部命中。"""
    refs: list[tuple[int, str]] = []
    for head in heads:
        if in_comment(text, head.start()):
            continue
        for pos, key in call_keys(text, head, key_re):
            refs.append((line_of(text, pos), key))
    return refs


def scan_attrs(text: str, attr_re: re.Pattern, key_re: re.Pattern) -> list[tuple[int, str]]:
    """HTML 属性写法(data-i18n="key")· 键写在标记里,只扫 JS 会漏掉同一种翻车。

    属性值现拼的(data-i18n="' + from + '")按 key_re 一律不认:静态查不了。
    """
    refs: list[tuple[int, str]] = []
    for m in attr_re.finditer(text):
        key = m.group(1)
        if key_re.match(key):
            refs.append((line_of(text, m.start(1)), key))
    return refs
