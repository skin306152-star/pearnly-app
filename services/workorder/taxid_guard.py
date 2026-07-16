# -*- coding: utf-8 -*-
"""客户税号错录守护闸(纯判断,无 I/O)。

病:客户账套登记的税号敲错一两位(换位/单字错/漏多一位),judge 方向锚定
(sort.bin_ocr_fields 精确比对 own_tax_id)对不上任何票 → 整批票退化成
direction_ambiguous,系统静默甩一堆 unknown 给人工,却不提示"税号可能录错了"。

守护:分类完跨料聚合——若登记税号锚不上任何票,而票上反复出现同一个税号、且它跟
登记税号只差一两位(Damerau-Levenshtein ≤2,含相邻换位),就判「疑似录错」,交上层
弹一句"票上都是 X,登记的是 Y,要改成 X 吗?"一键修正。

确定性、零 LLM。宁缺勿滥:登记税号只要还能锚上若干张就不触发(不打扰正常账套);
候选必须在够多张票上一致出现(coincidence 防线),两条一起把误报压到近乎不可能。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Optional

# 触发门槛:候选税号至少在这么多张票上一致出现,才敢说"录错"(单张巧合不算)。
_MIN_DOC_SUPPORT = 3
# 登记税号锚上的票数 ≤ 此值才算"锚不上"(留 1-2 张容错:偶有票税号 OCR 读花仍能命中,
# 不该因个别命中就闭嘴)。
_REGISTERED_HIT_TOLERANCE = 1
# 编辑距离上限:1=单字错/单漏多位,2=相邻换位(本案 203↔230)或两处小错。>2 视作两个不同税号。
_MAX_EDIT_DISTANCE = 2

_TAXID_LEN = 13


def _clean(tax_id: Optional[str]) -> str:
    """只留数字(剥空格/横线/杂字),保留任意长度。
    ⚠️ 不用 recon.field_clean.clean_tax_id:那个剥完必须恰好 13 位否则返 ''——本闸要拿
    「漏一位/多一位」的错长候选去算编辑距离,压成 '' 会让笔误直接消失,闸就废了。"""
    return "".join(ch for ch in str(tax_id or "") if ch.isdigit())


def _is_taxid(s: str) -> bool:
    return len(s) == _TAXID_LEN and s.isdigit()


def _damerau_levenshtein(a: str, b: str) -> int:
    """含相邻换位的编辑距离(换位算 1 步,故 203↔230 距离=1)。13 位串,O(n²) 够快。"""
    la, lb = len(a), len(b)
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[la][lb]


def _distance_label(registered: str, suspected: str) -> str:
    """给上层拼人话文案用的距离类型(仅粗分,精确措辞由 i18n 层定)。"""
    if len(registered) == len(suspected):
        diff = [i for i in range(len(registered)) if registered[i] != suspected[i]]
        if len(diff) == 1:
            return "substitution"  # 单字错
        if (
            len(diff) == 2
            and diff[1] == diff[0] + 1
            and registered[diff[0]] == suspected[diff[1]]
            and registered[diff[1]] == suspected[diff[0]]
        ):
            return "transposition"  # 相邻换位(本案)
    return "edit"  # 漏位/多位/两处小错


@dataclass(frozen=True)
class TaxIdTypoSuspicion:
    registered: str  # 登记的(疑似错的)税号
    suspected: str  # 票上反复出现的(疑似对的)税号
    doc_count: int  # 票上出现 suspected 的张数(支持度)
    distance: int  # 与登记税号的编辑距离
    kind: str  # transposition | substitution | edit


def suspect_registered_typo(
    registered_tax_id: Optional[str], doc_tax_ids: Iterable[Optional[str]]
) -> Optional[TaxIdTypoSuspicion]:
    """跨料聚合判「登记税号疑似录错」。

    registered_tax_id: 客户账套登记的税号(可脏)。
    doc_tax_ids: 全部料票上出现过的税号(买方+卖方各算一次,可含 None/脏值/重复)——
                 重复正是支持度信号,调用方原样喂,不要先去重。

    返回 TaxIdTypoSuspicion 或 None(无嫌疑/证据不足)。
    """
    reg = _clean(registered_tax_id)
    if not _is_taxid(reg):
        return None  # 登记税号本身就不是合法 13 位,另有问题,不在本闸管辖

    counts = Counter(c for c in (_clean(t) for t in doc_tax_ids) if _is_taxid(c))
    if not counts:
        return None

    registered_hits = counts.get(reg, 0)
    if registered_hits > _REGISTERED_HIT_TOLERANCE:
        return None  # 登记税号锚得上足够多票 = 没录错,别打扰

    cands = [
        (cand, n, dist)
        for cand, n in counts.items()
        if cand != reg
        and n >= _MIN_DOC_SUPPORT
        and 1 <= (dist := _damerau_levenshtein(reg, cand)) <= _MAX_EDIT_DISTANCE
    ]
    if not cands:
        return None
    # 择优:支持度高者先;并列取距离近者(更像笔误)。只给赢家建对象。
    cand, n, dist = max(cands, key=lambda c: (c[1], -c[2]))
    return TaxIdTypoSuspicion(
        registered=reg, suspected=cand, doc_count=n, distance=dist, kind=_distance_label(reg, cand)
    )
