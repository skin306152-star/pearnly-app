# -*- coding: utf-8 -*-
"""泰国身份证 13 位 mod-11 校验位纯函数。

DMS 建档前给 OCR 出的身份证号做自检:模型认得出 13 位不代表数字组合合法,
校验位对不上多半是某一位读错(热敏/糊图易错一位)。校验只用来降信心
(needs_review),不阻断——真号也可能因罕见 OCR 误判,最终由人复核定夺。
"""

from __future__ import annotations

# 泰文数字 ๐-๙ → ASCII,容忍卡面/OCR 偶带泰数字。
_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def is_valid_thai_id(s: str) -> bool:
    """13 位泰国公民号 mod-11 校验:前 12 位按权重 13..2 加权求和,
    check = (11 - (sum % 11)) % 10,须等于第 13 位。

    容忍空格/连字符/泰文数字;去噪后非「恰好 13 位纯数字」一律 False。
    """
    if not s:
        return False
    digits = str(s).translate(_THAI_DIGITS).replace(" ", "").replace("-", "")
    # isascii()+isdigit() 一起用才锁死 0-9(单 isdigit 会放行其它 Unicode 数字)。
    if len(digits) != 13 or not (digits.isascii() and digits.isdigit()):
        return False
    total = sum(int(digits[i]) * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == int(digits[12])
