# -*- coding: utf-8 -*-
"""ใบแนบ ภ.ง.ด.1 扁平上传串装配(网页 ใบแนบ 逐员工 pipe · 纯函数零 I/O · 方案 §4.2)。

这是事务所真实提交件(RD e-Filing 网页 ใบแนบ 上传),与官方 FORMAT กลาง(见
services/tax/rdprep_pnd1.py:HEADER/DETAIL)是**两种不同格式**:此件 10 段、金额整数元、
收入码写 `40(1)`;官方中央件 22+26 段、金额 N(15,2) 补 .00、收入码用数字码 1-5。金标末列
逐字节对齐此格式(不含付款方税号 —— 付款方在 e-Filing 表头填一次)。

字段序(10 段):收入码|序号|员工身份证|称谓|名|姓|支付日ddmmyyyy佛历|金额|扣税|条件
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from services.tax import rdprep
from services.tax.rdprep import RdPrepFormatError

_FIELD_SEP = "|"
_RECORD_SEP = "\r\n"  # 官方 §8:record 间 CR/LF


def build_line(row) -> str:
    """单员工 PayrollRow → 扁平 pipe 串(金标末列格式)。

    金额输出整数元形态(金标事实:`13000` 非 `13000.00`);扣税同理 `0`。姓名/称谓过 RD Prep
    禁用字符校验(含 `|`/`,`/引号即拦,防破坏字段边界)。支付日复用 to_buddhist_paid_date。
    """
    if row.paid_date is None:
        raise RdPrepFormatError(f"序号 {row.seq} 缺支付日,无法装配 ใบแนบ 上传串")
    cells = [
        _text(row.income_code),
        str(row.seq),
        _text(row.employee_id),
        _text(row.title),
        _text(row.first_name),
        _text(row.last_name),
        rdprep.to_buddhist_paid_date(row.paid_date),
        _amount(row.paid_amount),
        _amount(row.wht_amount),
        _text(row.condition),
    ]
    return _FIELD_SEP.join(cells)


def build_attachment(rows: Iterable) -> str:
    """全员工 → ใบแนบ 上传件文本(CR/LF 分行,末行无换行,UTF-8)。"""
    return _RECORD_SEP.join(build_line(row) for row in rows)


def _text(value) -> str:
    """字符字段:去空格 + RD Prep 禁用字符校验(复用官方 §11 字符集)。"""
    s = "" if value is None else str(value).strip()
    bad = rdprep._FORBIDDEN_CHARS.intersection(s)
    if bad:
        raise RdPrepFormatError(f"ใบแนบ 字段含禁用字符 {sorted(bad)!r}: {s!r}")
    return s


def _amount(value) -> str:
    """金额 → 整数元串(金标事实)。含 satang 的小数行为无金标样本(U1 待核)→ 保留两位
    诚实输出,不静默丢分;整数元走整数形态与金标逐字节一致。"""
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    if amount == amount.to_integral_value():
        return str(int(amount))
    return f"{amount:.2f}"
