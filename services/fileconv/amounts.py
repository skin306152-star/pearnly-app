# -*- coding: utf-8 -*-
"""泰式金额解析。钱一律 Decimal,不碰 float(精度守恒校验的前提)。

处理:泰数字 ๐-๙、千分位、括号负数、前导负号,以及 pdfplumber 抽文字层时
偶发的"数字内插空格"退化(例:'4 3.25' 实为 '43.25','1 ,727.46' 实为 '1,727.46')。
"""

import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

# 金额 token:可选括号/负号 + 千分位整数 + 两位小数。要求 .dd 结尾以排除税号/日期/代码。
# 用 ASCII [0-9] 而非 \d:\d 在 Python 是 Unicode,会把泰数字边框(๓=Thai-3)误当数字。
MONEY_RE = re.compile(r"\(?-?[0-9][0-9,]*\.[0-9]{2}\)?")


def normalize_thai_digits(s: str) -> str:
    return s.translate(_THAI_DIGITS)


def parse_amount(token: Optional[str]) -> Optional[Decimal]:
    """单个金额 token → Decimal。解析不了返回 None(不返 0,避免污染守恒校验)。"""
    if token is None:
        return None
    s = normalize_thai_digits(str(token)).strip()
    if not s:
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.startswith("-"):
        negative = True
        s = s[1:]
    s = s.replace(",", "").replace(" ", "")
    try:
        value = Decimal(s)
    except InvalidOperation:
        return None
    return -value if negative else value


def repair_number_spaces(line: str) -> str:
    """修复 pdfplumber 在数字内插入的杂散空格。

    只做保守修复,不合并会改变数值语义的空格:
      · 数字与其后逗号间的空格('1 ,727' → '1,727')
      · 逗号与其后数字间的空格(',   727' → ',727')
      · 孤立单数字与其后 ≤2 位小数金额间的空格('4 3.25' → '43.25')
    末条限定右侧 ≤2 位整数,故不会把科目代码 '10003' 并进金额,也不会误合 '5 100.00'。
    合不成整数的边界情形宁可留给守恒校验点名,不静默改写。
    """
    line = re.sub(r"(?<=[0-9])\s+(?=,)", "", line)
    line = re.sub(r"(?<=,)\s+(?=[0-9])", "", line)
    line = re.sub(r"(?<= [0-9]) (?=[0-9]{1,2}\.[0-9]{2})", "", line)
    return line


def money_tokens(text: str) -> List[Decimal]:
    """抽出一段文本里全部金额 token(按出现顺序)。

    不在此处做泰数字归一:泰数字 ๐-๙ 在老式表单里当边框(例:๓ 是 Thai-3),
    若整行归一会把边框并进相邻金额。真实财务金额一律 Arabic 数字,MONEY_RE 直配。
    """
    out: List[Decimal] = []
    for m in MONEY_RE.finditer(text):
        value = parse_amount(m.group(0))
        if value is not None:
            out.append(value)
    return out


def trailing_money_block(line: str) -> List[Decimal]:
    """取行尾"连续"金额块(token 之间只隔空白)。

    台账数据行的借/贷/余额是行尾连续的金额,描述里偶发的金额(少见)不应并入。
    从最后一个金额 token 起向左收,遇非空白间隔即停。
    """
    matches = list(MONEY_RE.finditer(line))
    if not matches:
        return []
    kept = [matches[-1]]
    for prev in reversed(matches[:-1]):
        gap = line[prev.end() : kept[0].start()]
        if gap.strip():
            break
        kept.insert(0, prev)
    values = [parse_amount(m.group(0)) for m in kept]
    return [v for v in values if v is not None]
