# -*- coding: utf-8 -*-
"""回复出口护栏(从 loop 抽出·零行为变化)。

闲聊/查询回复本就一两句,失控生成(复读循环/退化输出)绝不原样发给用户。
与后端无关(model-agnostic)——换任何大脑都可能偶发抽风,这是最后一道兜底。
"""

from __future__ import annotations

from typing import Optional

_REPLY_MAX_LEN = 1500  # 超长 = 大概率失控(正常回复远短于此)
_REPLY_MAX_RUN = 30  # 同一字符连续 30+ = 复读循环(如「1000…000」一屏零)
_REPLY_MIN_VARIETY_LEN = 60  # 达到此长度却只有极少种字符 = 退化输出


def sane(message: str) -> bool:
    """模型自撰回复是否合理(非失控生成)。空/超长/字符复读/极低多样性 → 不合理。"""
    t = (message or "").strip()
    if not t or len(t) > _REPLY_MAX_LEN:
        return False
    longest = run = 1
    for prev, cur in zip(t, t[1:]):
        run = run + 1 if cur == prev else 1
        if run > longest:
            longest = run
    if longest >= _REPLY_MAX_RUN:
        return False
    if len(t) >= _REPLY_MIN_VARIETY_LEN and len(set(t)) <= 4:
        return False
    return True


def salvage_prose(outcome) -> Optional[str]:
    """parse 失败但模型吐了干净散文(常是陪伴/查询的人话·忘了包 JSON)→ 当回复救回。
    含 { 的多半是坏/截断 JSON 残片(不给用户看)→ 不救,交 crash 走安全兜底。"""
    raw = (getattr(outcome, "raw", "") or "").strip()
    if not raw or len(raw) > 800 or "{" in raw or '"kind"' in raw:
        return None
    return raw
