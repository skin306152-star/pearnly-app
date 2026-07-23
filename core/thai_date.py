# -*- coding: utf-8 -*-
"""泰国佛历(พ.ศ.)与公历(ค.ศ.)的判定口径。

库里 invoice_date / doc_date / paid_date 全是公历 DATE —— 税期归属靠
to_char(doc_date,'YYYY-MM') 算,存佛历串会让跨月筛选、排序、账期比较全失效。
佛历只在【出口】按目标系统要求渲染(Express 2 位年、RD Prep 4 位年)。

所以入口必须挡住佛历年落库。2026-07-20 事故暴露的路径:识别抽屉的日期框收公历
却没有 ค.ศ. 标记(而全站默认显示佛历),用户按习惯填 2569-05-31 → strptime
照单全收 → DATE 列存成 2569 年 → 推 Express 时 (2569+543)%100 = 12,
送出 120531,比原本的错误更离谱。
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

BUDDHIST_ERA_OFFSET = 543

# 佛历年下界。2400 BE = 1857 AD,早于任何现行票据;公历年份不可能落进这个区间,
# 所以「年份 >= 2400」是判定"这是佛历"的可靠信号。
#
# ⚠️ 本模块目前【只是本次接线路径的口径】,不是全站权威 —— 仓库里另有十余处独立实现,
# 阈值分 >=2400 / >2400 / >=2500 三派,且 services/ocr/schemas_invoice.py 还带 2700 上界
# 与「换算结果须落 [2000, 今年+1] 才采信」的窗校验,本模块两者都没有。收编计划见交接文档;
# 在收编完成前,别假定 `from core import thai_date` 就等于全站一致。
BUDDHIST_YEAR_FLOOR = 2400

_ISO_DATE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$")


def looks_buddhist(year: int) -> bool:
    """该年份是否为佛历纪年。"""
    return year >= BUDDHIST_YEAR_FLOOR


def to_gregorian_year(year: int) -> int:
    """佛历年 → 公历年;已是公历则原样返回。"""
    return year - BUDDHIST_ERA_OFFSET if looks_buddhist(year) else year


def two_digit_year_to_gregorian(yy: int, anchor_year: Optional[int] = None) -> int:
    """两位年 → 公历年,取离锚点最近的解读。

    泰国票据的两位年有歧义:`69` 可能是公历 2069,也可能是佛历 2569 的缩写(=2026)。
    实务里近期单据占绝大多数,所以按"离锚点最近"消歧;锚点通常取该单据所属账期,
    缺省用今年。1957+yy 即 2500+yy-543。

    仓库里此前有四套互斥判据(一律佛历 / yy<70 当公历 / yy>=43 才当佛历 / 取最近),
    同一个 `69` 能解出 2026 或 2069 —— 后者还能通过 2000..2099 的窗校验落库。
    """
    anchor = anchor_year or date.today().year
    return min((2000 + yy, 1957 + yy), key=lambda y: abs(anchor - y))


_PRINTED_DATE = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\s*$")


def gregorian_from_printed(printed: object, anchor_year: Optional[int] = None) -> Optional[str]:
    """票面日期原文 → 公历 ISO(YYYY-MM-DD)。认不出返 None。

    人看到和填写的是票面那一串(泰国票面通常 DD/MM/พ.ศ.,如 31/5/2569),库里存的必须是
    公历 —— 换算只发生在这里,用户不需要知道它存在。年份三种形态都认:4 位佛历减 543、
    4 位公历原样、2 位按锚点消歧。日在前是泰式排法。
    """
    s = str(printed or "").strip()
    if not s:
        return None
    iso = _ISO_DATE.match(s)
    if iso:
        year, month, day = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
    else:
        m = _PRINTED_DATE.match(s)
        if not m:
            return None
        day, month, raw_year = int(m.group(1)), int(m.group(2)), m.group(3)
        year = (
            two_digit_year_to_gregorian(int(raw_year), anchor_year)
            if len(raw_year) == 2
            else int(raw_year)
        )
    year = to_gregorian_year(year)
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def buddhist_year_of(value: object) -> Optional[int]:
    """ISO 日期串(YYYY-MM-DD)的年份若是佛历,返回它;否则 None。

    只认 ISO —— 这是前端日期框与 API 契约的格式,别的形态不在本闸的职责内。
    """
    m = _ISO_DATE.match(str(value or ""))
    if not m:
        return None
    year = int(m.group(1))
    return year if looks_buddhist(year) else None


def gregorian_period(period: object) -> Optional[str]:
    """期间「YYYY-MM」→ 公历「YYYY-MM」;已是公历原样返回(幂等),解不出返 None。

    工单的 period 是佛历(2569-05),票面日期落库却是公历 —— 两者直接比会差 543 年,任何
    「距今几个月」的判据都会恒不触发(B-6 的可抵窗口就踩在这上面)。纪年换算只此一处。
    """
    try:
        year_s, month_s = str(period).split("-")
        month = int(month_s)
    except (ValueError, AttributeError, TypeError):
        return None
    if not 1 <= month <= 12:
        return None
    return f"{to_gregorian_year(int(year_s)):04d}-{month:02d}"
