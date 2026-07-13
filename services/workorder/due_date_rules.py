# -*- coding: utf-8 -*-
"""税历截止日顺延(MC2-B 件2 · G3 法定日历引擎)。

defer_due_date 是单一事实源纯函数:截止日遇周末或泰国法定假日,逐日顺延到下一个工作日
(连续假日/紧邻周末的假日自然逐日前推,不需要额外的"连假"分支)。obligation_engine 与
tax_profile_routes 的读侧(义务清单/事务所矩阵)统一 import 本函数,不许各自另起一份
假日判据(照 obligation_engine.current_be_period 的"单一权威源"先例)。

假日口径 = 泰国「政府假日」(วันหยุดราชการ),不是「银行假日」(วันหยุดธนาคาร)——两者常有
1-2 天出入(如 2026-01-02 只是内阁特批的政府加假,不进银行假日表)。下方两张年表逐条列
官方/半官方出处(内阁秘书处页面反爬无法程序化抓取,人工核对交叉校验)。

存量口径(读侧"两个事实"):client_period_obligations.due_paper/due_efiling 只存原始
未顺延日期(裸日历日,历史 snapshot 不因假日表更新而改写);顺延后的日期永远在读侧现算
(本模块零 I/O、零副作用),不落库、不加列——避免存量快照与假日表未来增补脱节。

不做(方案「不做」清单):e-Filing 延长期维度(纸质基准 +N 天,归 obligation_engine 的
sso_epayment_extra_workdays 走独立字段,不进本函数);假日表后台管理 UI(本表是人工按年
维护的 seed 常量,维护成本记入 runbook——每年初须核对内阁最新决议重新核验,过期年份只按
周末顺延、不假装认识未录入年份的假日)。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

# 2026(佛历 2569)泰国政府假日(วันหยุดราชการ,非银行假日口径)。交叉核对来源:
#   · Thai PBS 新闻(明确区分「ราชการ/พิเศษ/ธนาคาร」三类,引述 2025-12-02 内阁会议纪要)
#     https://www.thaipbs.or.th/news/content/500481
#   · Kapook 官方假日年历(页面标注「วันหยุดราชการและวันหยุดธนาคารประจำปี」并列两栏)
#     https://calendar.kapook.com/2569/holiday
#   · 内阁秘书处(สำนักเลขาธิการคณะรัฐมนตรี)官方公告页(权威源,列作交叉校验基准)
#     https://www.soc.go.th/?p=33672
THAI_HOLIDAYS_2026 = frozenset(
    {
        date(2026, 1, 1),  # 元旦
        date(2026, 1, 2),  # 内阁特批加假(衔接元旦周末)
        date(2026, 3, 3),  # 万佛节 Makha Bucha
        date(2026, 4, 6),  # 却克里王朝纪念日
        date(2026, 4, 13),  # 宋干节(泼水节)
        date(2026, 4, 14),
        date(2026, 4, 15),
        date(2026, 5, 1),  # 劳动节
        date(2026, 5, 4),  # 加冕纪念日
        date(2026, 5, 31),  # 卫塞节 Visakha Bucha(适逢周日)
        date(2026, 6, 1),  # 卫塞节顺延假(政府补假)
        date(2026, 6, 3),  # 苏提达王后诞辰
        date(2026, 7, 28),  # 现任国王诞辰
        date(2026, 7, 29),  # 三宝节 Asarnha Bucha
        date(2026, 7, 30),  # 佛诞守夏节 Khao Phansa
        date(2026, 8, 12),  # 诗丽吉王太后诞辰(母亲节)
        date(2026, 10, 13),  # 拉玛九世逝世纪念日
        date(2026, 10, 23),  # 五世王纪念日 Chulalongkorn Day
        date(2026, 12, 5),  # 拉玛九世诞辰 · 父亲节(适逢周六)
        date(2026, 12, 7),  # 父亲节顺延假(政府补假)
        date(2026, 12, 10),  # 宪法纪念日
        date(2026, 12, 31),  # 除夕
    }
)

# 2027(佛历 2570)—— 部分佛历浮动日截至本表录入时(2026-07)尚未经内阁最终公报确认,
# 引自公开年历交叉数据,标「暂定」;下一年度正式申报季前须重新核对内阁公告更新本表
# (维护成本见模块顶注)。来源:myhora.com 泰历年历(页面自述「当年数据随内阁公告更新」)
# https://myhora.com/calendar/holiday-2570.aspx
THAI_HOLIDAYS_2027 = frozenset(
    {
        date(2027, 1, 1),  # 元旦
        date(2027, 2, 21),  # 万佛节(暂定,适逢周日)
        date(2027, 2, 22),  # 万佛节顺延假(暂定)
        date(2027, 4, 6),  # 却克里王朝纪念日
        date(2027, 4, 13),  # 宋干节
        date(2027, 4, 14),
        date(2027, 4, 15),
        date(2027, 5, 1),  # 劳动节(适逢周六)
        date(2027, 5, 4),  # 加冕纪念日
        date(2027, 5, 20),  # 卫塞节(暂定)
        date(2027, 6, 3),  # 苏提达王后诞辰
        date(2027, 7, 18),  # 三宝节(暂定,适逢周日)
        date(2027, 7, 19),  # 佛诞守夏节(暂定)
        date(2027, 7, 28),  # 现任国王诞辰
        date(2027, 8, 12),  # 母亲节
        date(2027, 10, 13),  # 拉玛九世逝世纪念日
        date(2027, 10, 23),  # 五世王纪念日(适逢周六)
        date(2027, 10, 25),  # 五世王纪念日顺延假
        date(2027, 12, 5),  # 父亲节(适逢周日)
        date(2027, 12, 6),  # 父亲节顺延假
        date(2027, 12, 10),  # 宪法纪念日
        date(2027, 12, 31),  # 除夕
    }
)

_THAI_HOLIDAYS = THAI_HOLIDAYS_2026 | THAI_HOLIDAYS_2027

_SATURDAY = 5
_SUNDAY = 6


def defer_due_date(due: date) -> date:
    """周末/泰国政府假日顺延到下一工作日(纯函数,零 I/O)。

    逐日前推直至落在非周末且非假日——天然处理连续假日(宋干节三连休)与假日紧邻周末
    (卫塞节补假)两种情形,不需要单独的"连假"分支。未录入年份(表外)只按周末顺延,
    不假装认识没数据的年份(诚实降级,不拍脑袋猜)。
    """
    d = due
    while d.weekday() in (_SATURDAY, _SUNDAY) or d in _THAI_HOLIDAYS:
        d += timedelta(days=1)
    return d


def defer_optional(due: Optional[date]) -> Optional[date]:
    """None 直通版(供读侧序列化 due_paper/due_efiling 可能为空的场景直接调用)。"""
    return defer_due_date(due) if due is not None else None
