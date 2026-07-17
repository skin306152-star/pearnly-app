# -*- coding: utf-8 -*-
"""客户档字段级 diff 引擎(纯函数)。

DMS 已有客户 vs 身份证识别出的新值:只报白名单里「真的变了」的字段,供前端
标红让操作员逐条确认覆盖。归一化吸收无意义差异(首尾/连续空格、泰文数字);
incoming 缺键或空值视为「没这条信息」——绝不拿空值去清 DMS 现值。
people_id 是主键身份,永不进 diff。
"""

from __future__ import annotations

from typing import Any, Dict, List

# 允许 diff 的字段:身份 + 户籍地址(地址比 id,不比显示标签)。people_id 不在内(主键)。
_DIFF_FIELDS = (
    "prefix_id",
    "name",
    "birthday_be",
    "phone",
    "house_no",
    "moo",
    "soi",
    "road",
    "province_id",
    "district_id",
    "subdistrict_id",
    "zipcode_id",
)

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def _norm(v: Any) -> str:
    """归一:泰文数字→ASCII、连续空白折一、首尾去空。"""
    s = str(v if v is not None else "").translate(_THAI_DIGITS)
    return " ".join(s.split())


def diff_customer_fields(current: Dict[str, Any], incoming: Dict[str, Any]) -> List[Dict[str, str]]:
    """比对白名单字段,返回变化项 [{'field','old','new'}](归一后对照值)。

    incoming 缺键、或值归一后为空 = 无信息,不产生 diff(绝不覆盖现值)。
    """
    out: List[Dict[str, str]] = []
    for field in _DIFF_FIELDS:
        if field not in incoming:
            continue
        new = _norm(incoming.get(field))
        if not new:  # 空值 = 无信息
            continue
        old = _norm(current.get(field))
        if new != old:
            out.append({"field": field, "old": old, "new": new})
    return out
