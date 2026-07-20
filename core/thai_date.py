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
from typing import Optional

BUDDHIST_ERA_OFFSET = 543

# 佛历年下界。2400 BE = 1857 AD,早于任何现行票据;公历年份不可能落进这个区间,
# 所以「年份 >= 2400」是判定"这是佛历"的可靠信号(与 OCR 层同口径)。
BUDDHIST_YEAR_FLOOR = 2400

_ISO_DATE = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$")


def looks_buddhist(year: int) -> bool:
    """该年份是否为佛历纪年。"""
    return year >= BUDDHIST_YEAR_FLOOR


def to_gregorian_year(year: int) -> int:
    """佛历年 → 公历年;已是公历则原样返回。"""
    return year - BUDDHIST_ERA_OFFSET if looks_buddhist(year) else year


def buddhist_year_of(value: object) -> Optional[int]:
    """ISO 日期串(YYYY-MM-DD)的年份若是佛历,返回它;否则 None。

    只认 ISO —— 这是前端日期框与 API 契约的格式,别的形态不在本闸的职责内。
    """
    m = _ISO_DATE.match(str(value or ""))
    if not m:
        return None
    year = int(m.group(1))
    return year if looks_buddhist(year) else None
