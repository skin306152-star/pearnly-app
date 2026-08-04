# -*- coding: utf-8 -*-
"""开票日期与历法(docs/16 §G)。纯逻辑叶子,不连库。

- bangkok_today: 票面日历日必须按曼谷本地推导,不能直接取 UTC 的 date——临近午夜会差
  一天,连带连号 period_key 分桶错配。泰国固定 UTC+7、无夏令时,所以直接 +7 小时取日期。
- validate_issue_date: 禁未来日(税点未到);倒填不得跨出当前 VAT 申报期(自然月),否则
  连号与 ภ.พ.30 申报错位(§G2)。
- to_thai_date: PDF 日期按佛历 พ.ศ. = 公历 + 543 展示(数据仍存公历 · §G3)。
- BANGKOK / iso_bangkok: 曼谷时区常量与「时刻→曼谷本地 ISO」单一出口(POS 报表面共用,
  此前各模块自拷常量+注释指认此处,漂移过一次)。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

BANGKOK = timezone(timedelta(hours=7))
_BE_OFFSET = 543


def bangkok_today() -> date:
    return datetime.now(BANGKOK).date()


def bangkok_now() -> datetime:
    """当前曼谷本地时间(UTC+7·无夏令时)。答「现在几点」用,绝不让模型编时间。"""
    return datetime.now(BANGKOK)


def iso_bangkok(v) -> Optional[str]:
    """时刻按曼谷本地 ISO 输出(消费端直接切串显示/入 CSV,UTC 串会与曼谷日切窗口自相矛盾)。
    tz-aware 转曼谷;naive 视为已是本地值原样输出,不按机器时区猜(CI 是 UTC 机)。空值给 None。"""
    if not v:
        return None
    return (v.astimezone(BANGKOK) if v.tzinfo else v).isoformat()


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
