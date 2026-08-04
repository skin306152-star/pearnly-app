# -*- coding: utf-8 -*-
"""POS 报表面的业务日窗口(单一事实源)。

「业务日 = 曼谷日」是营业额报表(report)/ 交易明细(sales_log)/ 异常记录(audit_report)
三个报表面共享的契约:同一路由同一日期参数,窗口不同轴则各页同日数字对不上。此前该口径以
三份同构 SQL 片段散落各模块,漂移过一次(sales_query 曼谷、其余 UTC),故收口到此。

列是 timestamptz:日期参数先 ::timestamp 成 naive 午夜、再按 Asia/Bangkok 解释成绝对时刻。
裸比较 date 会按会话时区(UTC)切日,把曼谷凌晨 0–7 点的单划进前一天。表达式在参数侧且为
IMMUTABLE 链,计划期折常量,不影响 sold_at 复合索引的范围扫。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional


def bangkok_day_range(
    col: str, date_from: Optional[date], date_to: Optional[date]
) -> tuple[str, list]:
    """时间窗口 SQL 片段(半开 [from, to+1天)· 含 to 当天 · 曼谷日切)。无界则不加条件。"""
    clause, params = "", []
    if date_from:
        clause += f" AND {col} >= (%s::timestamp AT TIME ZONE 'Asia/Bangkok')"
        params.append(date_from)
    if date_to:
        clause += f" AND {col} < (%s::timestamp AT TIME ZONE 'Asia/Bangkok')"
        params.append(date_to + timedelta(days=1))
    return clause, params
