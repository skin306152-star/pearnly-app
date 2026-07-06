# -*- coding: utf-8 -*-
"""身份证字段级打分器:泰国身份证 OCR「读得对不对」编码成确定性数字。

与 invoice_scorer 对等的一把尺,给 DMS 建档路(task=id_card)一个可回归的裁判。
输入两个 dict(真值、prod `/api/dms/id-card/recognize` 响应里的 id_card 面板字段),
输出逐字段命中 + 加权分 + 关键字段漏判清单。纯函数,不连模型、不读 IO。

为什么按权重而非平均:公民号(people_id)读错 = 建到别人名下,和 soi 少一个字的
代价天差地别。身份证建客户的三根命门 people_id/first_name/last_name 权重最高。

刻意不打分(prod 侧无输出可比):phone 面板恒空占位,非 OCR 字段。
issue_date/expiry_date 自 2026-07-06 起 prod 已抽取(_ID_CARD_PROMPT 补·治 #14),纳入打分。

两处格式必须归一(否则真值/抽取全判 miss):
- 生日:真值 YYYY-MM-DD(BE),prod _normalize_be_date 出 dd/mm/yyyy(BE)→ canonical。
- 公民号:两边只比 13 位数字(去空格/破折号)。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.ocr.money import normalize_id  # 13 位号只比数字,与 sanity/发票 scorer 共用

# 字段 → (比对类型, 权重)。权重反映读错的业务代价。
#   id13  : 13 位公民号,只比数字
#   text  : 姓名/地址名,去空白小写折叠后比
#   date  : 生日,跨格式归一到 BE canonical 后比
#   zip   : 5 位邮编,只比数字
_FIELD_SPEC: Dict[str, tuple] = {
    "people_id": ("id13", 5),
    "first_name": ("text", 3),
    "last_name": ("text", 3),
    "birthday_be": ("date", 2),
    "issue_date_be": ("date", 1),
    "expiry_date_be": ("date", 2),
    "prefix_name": ("text", 1),
    "address.house_no": ("text", 1),
    "address.subdistrict": ("text", 1),
    "address.district": ("text", 1),
    "address.province": ("text", 1),
    "address.zipcode": ("zip", 1),
}

# 权重 >= 此值未命中 → critical_misses(建错客户级)。
_CRITICAL_WEIGHT = 3


def normalize_text(v: Any) -> str:
    """姓名/地址名:折叠空白 + 小写 + 去首尾(NBSP 一并清,泰文渲染常掺)。"""
    return re.sub(r"\s+", " ", str(v or "").replace("\xa0", " ")).strip().lower()


def normalize_zip(v: Any) -> str:
    return re.sub(r"\D", "", str(v or ""))


def normalize_be_date(v: Any) -> str:
    """生日归一到 BE canonical `YYYY-MM-DD`。吃两种输入:
    - `2530-05-12`(真值·年-月-日)
    - `12/05/2530`(prod·日/月/年)
    公元年(< 2200)+543 转 BE。认不出返回 ''。"""
    s = str(v or "").strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4})\D+(\d{1,2})\D+(\d{1,2})$", s)  # YYYY-MM-DD
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})\D+(\d{1,2})\D+(\d{4})$", s)  # dd/mm/yyyy
        if not m:
            return ""
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 2200:  # Gregorian → Buddhist era
        year += 543
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return ""
    return f"{year:04d}-{month:02d}-{day:02d}"


def thai_citizen_id_checkdigit_ok(pid: Any) -> bool:
    """泰国身份证 13 位校验位(加权 mod-11,取模 10)——与发票税号 mod-11 不同算法。
    前 12 位分别乘 13..2,和对 11 取模,(11 - 余) % 10 == 第 13 位即合法。
    用途:自检语料真值号是否合法 + 抓 prod 读出结构不可能的号。"""
    digits = re.sub(r"\D", "", str(pid or ""))
    if len(digits) != 13:
        return False
    total = sum(int(digits[i]) * (13 - i) for i in range(12))
    return (11 - (total % 11)) % 10 == int(digits[12])


def _both_blank(a: str, b: str) -> Optional[bool]:
    """两边都空 → True(一致);仅一边空 → False;都非空 → None(交给值比对)。"""
    if not a and not b:
        return True
    if not a or not b:
        return False
    return None


def _match_field(kind: str, expected: Any, actual: Any) -> bool:
    norm = {
        "id13": normalize_id,
        "text": normalize_text,
        "zip": normalize_zip,
        "date": normalize_be_date,
    }[kind]
    e, a = norm(expected), norm(actual)
    blank = _both_blank(e, a)
    if blank is not None:
        return blank
    return e == a


def _nested_get(d: Dict[str, Any], dotted: str) -> Any:
    """`address.zipcode` → d['address']['zipcode'];缺任一层返回 None。"""
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def score_id_card(expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
    """对一张身份证打分。

    Args:
        expected: 真值 dict(顶层字段 + 嵌套 address)。只比对其中**出现的**字段。
        actual:   prod 响应的 id_card 面板 dict(editable_id_card 形状,含嵌套 address)。

    Returns:
        {
          "fields": {name: {expected, actual, match, weight, kind}},
          "weighted_score": 0.0..1.0,
          "id_valid": bool | None,       # 真值公民号是否过校验位(None=真值无号)
          "critical_misses": [field],    # 权重>=3 且未命中
          "scored_fields": n,
        }
    """
    fields_out: Dict[str, Any] = {}
    w_total = w_hit = 0
    critical_misses: List[str] = []

    for field, (kind, weight) in _FIELD_SPEC.items():
        exp_val = _nested_get(expected, field) if "." in field else expected.get(field)
        if exp_val in (None, ""):  # 真值没这字段就不比(最小真值也能用)
            continue
        act_val = _nested_get(actual, field) if "." in field else actual.get(field)
        match = _match_field(kind, exp_val, act_val)

        fields_out[field] = {
            "expected": exp_val,
            "actual": act_val,
            "match": match,
            "weight": weight,
            "kind": kind,
        }
        w_total += weight
        if match:
            w_hit += weight
        elif weight >= _CRITICAL_WEIGHT:
            critical_misses.append(field)

    exp_pid = expected.get("people_id")
    return {
        "fields": fields_out,
        "weighted_score": round(w_hit / w_total, 4) if w_total else None,
        "id_valid": thai_citizen_id_checkdigit_ok(exp_pid) if exp_pid else None,
        "critical_misses": critical_misses,
        "scored_fields": len(fields_out),
    }


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """多张身份证汇总:平均加权分 + 关键漏判计数 + 真值非法号计数(语料自检)。"""
    scored = [r for r in results if r and r.get("weighted_score") is not None]
    if not scored:
        return {"n": 0, "avg_weighted_score": None, "critical_miss_total": 0, "invalid_id_gt": 0}
    return {
        "n": len(scored),
        "avg_weighted_score": round(sum(r["weighted_score"] for r in scored) / len(scored), 4),
        "critical_miss_total": sum(len(r.get("critical_misses") or []) for r in scored),
        "invalid_id_gt": sum(1 for r in scored if r.get("id_valid") is False),
    }
