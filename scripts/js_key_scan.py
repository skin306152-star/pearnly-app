#!/usr/bin/env python3
"""JS 静态扫描的公共底座 —— 三道闸共用,分两层。

下层(read_string / skip_comment / in_comment / line_of)是纯词法:转义、未闭合、注释里
的撇号、模板串的 ${}。这些条目每一条都是踩过才补上的,谁抄一份谁就得把同样的坑再踩一遍。
check_e2e_stub_contracts 扫的是桩的回包对象,跟词典半点关系没有,用的也是这一层。

上层(call_keys / first_arg_literals / neighbor)只服务 /ai 与 /home 两道词典引用闸:
两棵树的取词函数名、键的字符集、词典结构都不同(见各自的闸),但"从一个调用点里挑出哪些
字面量是键"这件事逐字相同 —— 按括号深度和引号扫过去,只认第一个实参、只认深度 0 的字面量,
再用左右邻居判它站没站在键位上。这段是全闸最容易写错的部分(正则版会把
`at(x ? 'a' : 'b')` 和 `at('pre_' + s)` 一起认错)。

上层调用方需要提供的只有一样:键的字符集正则(/ai 是 `[A-Za-z_]\\w*`,/home 的键带连字符
和点,如 `dxb-up-title` / `agent.ok.notifications`)。
"""

import re

_QUOTES = "'\"`"
_SCAN_LIMIT = 2000

# 字面量得站在「键位」上才算键:左邻是 ( ? : || &&,右邻是 ) , : ? || &&。
# 这条邻居规则排掉两类同样是字面量、却不是键的东西 ——
#   t(role === 'user' ? 'stw_you' : 'stw_agent') 里的 'user'(比较值,左邻 =)
#   t('bill_st_' + status) 里的前缀(右邻 +),半截前缀当键查必然落空,报出来只是噪声。
_LEFT_OK = "(?:|&"
_RIGHT_OK = "),:?|&"

_QUOTED_SPAN = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def read_string(text, i):
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


def skip_comment(text, i):
    """i 指向 / → 注释结束后的下标;不是注释返 i。注释里的撇号不能算字符串起点。"""
    nxt = text[i + 1 : i + 2]
    if nxt == "/":
        end = text.find("\n", i)
        return len(text) if end < 0 else end
    if nxt == "*":
        end = text.find("*/", i)
        return len(text) if end < 0 else end + 2
    return i


def in_comment(text, pos):
    """pos 是否落在注释里 —— 只看本行前缀,不做整文件分词。

    整文件分词要能认出正则字面量(ai-api.js 里就有 /filename="?([^";]+)"?/ 这种带引号的),
    认错一个就把后面整片代码当字符串吞掉。逐行判够用:注释里提一句 t('old_key') 不该把闸
    弄红(改名后注释常留旧键),而取词调用永远不会跨行接在同一行的注释后面。
    """
    line_start = text.rfind("\n", 0, pos) + 1
    prefix = _QUOTED_SPAN.sub("", text[line_start:pos])
    return "//" in prefix or prefix.lstrip().startswith(("*", "/*"))


def neighbor(text, i, step):
    """从 i 出发按 step 方向跳过空白,返回第一个实字符(越界返空串)。"""
    while 0 <= i < len(text):
        if not text[i].isspace():
            return text[i]
        i += step
    return ""


def first_arg_literals(text, start):
    """start = 左括号后一位。返回第一个实参里、括号深度为 0 的字面量 [(下标, 内容)]。

    只取第一个实参:t('k', {name: 'x'}) 的 'x' 是插值参数的值,不是键。
    只取深度 0:t(el.getAttribute('data-i18n')) 的 'data-i18n' 是内层调用的参数。
    """
    out = []
    depth = 0
    i = start
    end = min(len(text), start + _SCAN_LIMIT)
    while i < end:
        c = text[i]
        if c == "/":
            j = skip_comment(text, i)
            if j != i:
                i = j
                continue
        if c in _QUOTES:
            body, j = read_string(text, i)
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


def call_keys(text, arg_start, key_re):
    """一个取词调用点 → 它引用的键 [(下标, 键)]。

    arg_start = 左括号后一位(通常是 head.end())。key_re = 调用方那棵树的键字符集。
    二选一写法 t(x ? 'a' : 'b') 两个分支都算引用。
    """
    keys = []
    for pos, body in first_arg_literals(text, arg_start):
        if not key_re.match(body):
            continue
        left = neighbor(text, pos - 1, -1)
        right = neighbor(text, pos + len(body) + 2, 1)
        if left in _LEFT_OK and right in _RIGHT_OK:
            keys.append((pos, body))
    return keys
