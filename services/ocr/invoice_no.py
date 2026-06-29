# -*- coding: utf-8 -*-
"""发票号格式一致性(确定性·纯函数)。

同一卖家、同一批(常见:一个 PDF 多张)的发票号本应同一格式;若多数派是
`IV69100179` 这种无分隔符、却混进一张 `IV69/00199`,那张大概率读错。

只揪异常、**不改写值** —— 我们无法确定真值到底带不带分隔符,瞎补会把对的票改错。
揪出后交调用方罚置信度 + 转人工(让人去改,改动再经持久化落库),不静默满分放过。

诚实边界:只在存在**严格过半的多数派**时裁定少数派为异常;平票/各不相同时一律
不判(宁可漏报,绝不误杀)。缺号(空值)不参与格式裁定 —— 缺号是另一类问题。
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import List, Optional

_LETTER = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")


def format_signature(raw) -> str:
    """抽象成格式签名:字母→A、数字→9、其余(分隔符)原样保留。

    `IV69/00199` → `AA99/99999`;`IV69100179` → `AA99999999`。签名不同 = 格式不同。
    """
    out: List[str] = []
    for ch in str(raw or "").strip():
        if _LETTER.match(ch):
            out.append("A")
        elif _DIGIT.match(ch):
            out.append("9")
        else:
            out.append(ch)
    return "".join(out)


def inconsistent_indices(numbers: List[str]) -> List[int]:
    """返回格式偏离多数派的下标(升序)。空列表 = 一致 / 无法裁定。

    保守裁定:多数派签名须**唯一且严格过半**,否则返回 []。空号跳过。
    """
    sigs = {i: format_signature(n) for i, n in enumerate(numbers) if str(n or "").strip()}
    if len(sigs) < 2:
        return []

    counts = Counter(sigs.values())
    top_sig, top_n = counts.most_common(1)[0]
    if list(counts.values()).count(top_n) > 1:
        return []  # 多个签名并列最多 → 无明确多数派,不裁
    if top_n * 2 <= len(sigs):
        return []  # 多数派没过半 → 不裁

    return sorted(i for i, s in sigs.items() if s != top_sig)


def inconsistent_in_batch(numbers: List[str], sellers: Optional[List] = None) -> List[int]:
    """按卖家分组后组内查一致性,返回全局异常下标(升序)。

    sellers=None → 视作同一卖家,全批一起比;给定 → 按税号(仅数字)分组,无税号的票
    各自成组(永不被裁),避免跨卖家不同格式被误杀。
    """
    if not sellers:
        return inconsistent_indices(numbers)

    groups = defaultdict(list)  # seller_key -> [global_idx]
    for i in range(len(numbers)):
        s = sellers[i] if i < len(sellers) else None
        key = re.sub(r"\D", "", str(s or "")) or f"__none_{i}"
        groups[key].append(i)

    flagged: List[int] = []
    for idxs in groups.values():
        sub = [numbers[i] for i in idxs]
        flagged.extend(idxs[local] for local in inconsistent_indices(sub))
    return sorted(flagged)


def format_warnings_for_groups(invoice_groups) -> List[dict]:
    """从 invoice_groups(每个含 invoice_fields)挑出格式偏离同卖家多数派的票。

    返回 [{invoice_index(1基), invoice_number, reason}],供识别路由置 needs_review +
    回前端提示人工核对。空 = 无异常。
    """
    fields = [(g or {}).get("invoice_fields") or {} for g in (invoice_groups or [])]
    numbers = [f.get("invoice_number") for f in fields]
    sellers = [f.get("seller_tax") for f in fields]
    return [
        {
            "invoice_index": idx + 1,
            "invoice_number": numbers[idx],
            "reason": "invoice_number_format_inconsistent",
        }
        for idx in inconsistent_in_batch(numbers, sellers)
    ]
