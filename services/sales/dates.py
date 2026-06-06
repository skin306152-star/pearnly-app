# -*- coding: utf-8 -*-
"""开票日期与历法(docs/16 §G)。纯逻辑叶子,不连库。

- bangkok_today: 票面日历日必须按曼谷本地推导,不能直接取 UTC 的 date——临近午夜会差
  一天,连带连号 period_key 分桶错配。泰国固定 UTC+7、无夏令时,所以直接 +7 小时取日期。
- validate_issue_date: 禁未来日(税点未到);倒填不得跨出当前 VAT 申报期(自然月),否则
  连号与 ภ.พ.30 申报错位(§G2)。
- to_thai_date: PDF 日期按佛历 พ.ศ. = 公历 + 543 展示(数据仍存公历 · §G3)。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

_BANGKOK = timezone(timedelta(hours=7))
_BE_OFFSET = 543


def bangkok_today() -> date:
    return datetime.now(_BANGKOK).date()


def validate_issue_date(on: date, today: Optional[date] = None) -> Optional[str]:
    """开票日护栏。返回错误码或 None。today 默认曼谷当天(可注入便于测试)。"""
    ref = today or bangkok_today()
    if on > ref:
        return "future_issue_date"
    if (on.year, on.month) != (ref.year, ref.month):
        return "backdate_cross_period"
    return None


def to_thai_date(value) -> str:
    """公历 date / 'YYYY-MM-DD' → 'DD/MM/พ.ศ.'(佛历)。解析不了原样返回。"""
    d = _coerce(value)
    if d is None:
        return str(value) if value not in (None, "") else "-"
    return f"{d.day:02d}/{d.month:02d}/{d.year + _BE_OFFSET}"


def _coerce(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None
