# -*- coding: utf-8 -*-
"""票面日期口径 —— 一张票按哪一天入账,规则写死在代码里,不交给模型。

单独成文件是因为场次票(Ocha 这类 POS)不印日期,只印 Time In / Time Out,判定要解析
票面**文本**;塞回 models.py 会把「输入契约」和「日期裁决」两件事搅在一起。

数据源只认上游真会给的字段:ThaiInvoice 的 `date` / `date_raw` / `notes`。这里曾经读
`time_in` / `time_out` 两个键,可全仓没有任何上游写它们 —— 规则看着生效,实际一次都没
跑到,只有测试喂得进去。宁可解析文本,也不留这种分支。

口径本身(2026-07 拍板):

1. 票面同时印了进/出两个时刻 → 以 **out** 为准。ABB 的纳税义务发生时点是结账收款,不是
   进店;而上游的 `date` 是模型从这两个时刻里挑的一个(金标那张 02000139 挑的是 in),
   模型挑哪个不受我们控制,所以两个时刻都在时不采信它。
2. 进/出跨月 → 该票进待判。跨月会把销项挪到上一期申报,这必须人拍板。
3. 没有场次时刻 → 用票面印的日期。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Mapping, Optional, Tuple

from services.knowledge.rules.validity import parse_invoice_date
from services.ledger.fields import pick_text

REASON_NO_DATE = "ไม่พบวันที่ในเอกสาร · ต้องระบุวันที่ก่อนลงบัญชี"
REASON_CROSS_MONTH = "เวลาเข้า-ออกคาบเกี่ยวข้ามเดือน · ต้องยืนยันวันที่ของใบกำกับ"

DATE_FROM_PRINTED = "printed"
DATE_FROM_TIME_OUT = "time_out"
DATE_FROM_TIME_IN = "time_in"

# 只认带 in/out 标签的场次时刻。故意不认 check-in / check-out:酒店票印的是入住退房,
# 它自己另有开票日期,拿退房日盖过开票日就是改了法定日期。
_SESSION_LABEL = re.compile(r"time\s*[-_]?\s*(?:in|out)|เวลาเข้า|เวลาออก", re.IGNORECASE)
_OUT_MARKS = ("out", "ออก")

# 票面文本进得来的两个口子:date_raw 是「日期原样」,notes 是模型倒剩余文本的地方。
_TEXT_FIELDS = ("date_raw", "notes")


@dataclass(frozen=True)
class DocDate:
    """票面日期裁决结果。source 说明这个日期是从哪一格读出来的,便于事后追。"""

    value: Optional[date]
    source: str
    pending_reason: str


def _segments(text: str) -> Mapping[str, str]:
    """票面文本 → {"in": 片段, "out": 片段};片段 = 标签之后到下一个标签之前的那截。

    必须切到下一个标签为止:「Time In 18:12 Time Out 28/05/2569」这种只在 out 印日期的
    写法,不切就会把 out 的日期当成 in 的,跨月判定跟着一起错。
    """
    marks = [(m.group(0), m.start(), m.end()) for m in _SESSION_LABEL.finditer(text or "")]
    out: dict = {}
    for i, (label, _start, end) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        low = label.lower()
        key = "out" if any(mark in low for mark in _OUT_MARKS) else "in"
        out.setdefault(key, text[end:stop])
    return out


def session_dates(fields: Mapping[str, object]) -> Tuple[Optional[date], Optional[date]]:
    """票面文本里的 (进场日, 离场日)。没印场次时刻就是 (None, None)。"""
    text = " ".join(t for t in (pick_text(fields, key) for key in _TEXT_FIELDS) if t)
    if not text:
        return None, None
    seg = _segments(text)
    return parse_invoice_date(seg.get("in", "")), parse_invoice_date(seg.get("out", ""))


def resolve_doc_date(fields: Mapping[str, object]) -> DocDate:
    """按上面的口径裁一张票的入账日期。"""
    time_in, time_out = session_dates(fields)
    if time_in and time_out:
        cross_month = (time_in.year, time_in.month) != (time_out.year, time_out.month)
        return DocDate(time_out, DATE_FROM_TIME_OUT, REASON_CROSS_MONTH if cross_month else "")
    printed = parse_invoice_date(pick_text(fields, "date", "invoice_date", "doc_date"))
    if printed:
        return DocDate(printed, DATE_FROM_PRINTED, "")
    if time_out:
        return DocDate(time_out, DATE_FROM_TIME_OUT, "")
    if time_in:
        # 只有入场时刻:它是唯一的 datum,用它但标明来源,不假装是开票时刻。
        return DocDate(time_in, DATE_FROM_TIME_IN, "")
    return DocDate(None, "", REASON_NO_DATE)
