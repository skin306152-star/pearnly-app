# -*- coding: utf-8 -*-
"""供应商历史量级基线(确定性·纯函数)。

抓 [[ocr-determinism-layer-root-cause]] 头号缺口 pur05-44.67:加油票真值 ~1780,被读成
总额 44.67(选错列),内部自洽 → sanity 在无明细佐证时抓不住。唯一确定性信号 = 这家供应商
历史总额一直是几千铢,这张低了 ~40 倍。

只揪、不改值。保守:有效历史不足 → 不判(无基线,绝不误杀新供应商);缺额/非正 → 不判
(缺额由别的闸管)。用中位数而非均值,抗历史脏值。

★接线说明(未在此提交):需一个"按 seller_tax 取近 N 张正 total_amount"的查询喂 history;
本地无 DB 不提交未验证查询。纯决策核心在此完成并单测,接线见证据夹说明。
"""

from __future__ import annotations

from statistics import median
from typing import List, Optional

# 偏离倍数阈值:保守取 20×(pur05 实差 ~40×)。只抓"量级错"(选错列/多读一位),不抓
# 正常的批量波动(同供应商 2~3 倍波动不少见)。
_RATIO = 20.0
# 最少历史张数:不足则无可靠基线,不判(新供应商免误杀)。
_MIN_HISTORY = 5


def magnitude_anomaly_reason(
    new_total: Optional[float],
    history_totals: List,
    *,
    min_history: int = _MIN_HISTORY,
    ratio: float = _RATIO,
) -> Optional[str]:
    """新票总额相对供应商历史中位数偏离 ratio 倍 → 返回原因串;否则 None。"""
    if not isinstance(new_total, (int, float)) or new_total <= 0:
        return None
    valid = [float(t) for t in (history_totals or []) if isinstance(t, (int, float)) and t > 0]
    if len(valid) < min_history:
        return None
    med = median(valid)
    if med <= 0:
        return None
    if new_total * ratio < med:
        return f"总额 {new_total} 比该供应商历史中位数 {med:.2f} 低 >{ratio:g}× — 疑选错列/读错位"
    if new_total > med * ratio:
        return f"总额 {new_total} 比该供应商历史中位数 {med:.2f} 高 >{ratio:g}× — 疑多读位/串列"
    return None
