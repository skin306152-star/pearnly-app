# -*- coding: utf-8 -*-
"""RD Prep 中央格式(FORMAT กลาง v2.0)txt 装配 —— 纯函数零 I/O，两产品共享单一实现。

RD e-filing 上传前需先过官方 RD Prep 程序,输入为 pipe 分隔 UTF-8 .txt(逐字段规约见
官方 PDF FormatPND3V2_0 / FormatPND53V2_0,ปรับปรุง 16/06/2568)。本模块把 header/detail
的值字典渲染成合规记录串,不查库不算钱:钱由上游(aggregate.pnd)算好传入,这里只负责
格式契约(分隔符/头尾无 pipe/CR-LF/空数值补 0.00/禁用字符/佛历/字段序)。

字段序 = 单一事实源:HEADER_FIELDS(25)/DETAIL_FIELDS(38)照官方 PDF 逐字段落表,渲染
只按表走,不散写魔法下标。PND3 与 PND53 共用同一套字段序,唯 DETAIL 字段 4 语义分流:
PND3=PIN(个人 13 位身份证)、PND53=NID(法人 13 位税号),据 form 取对应键值。
"""

from __future__ import annotations

import datetime as _dt
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping

PND3 = "PND3"
PND53 = "PND53"
FORMS = (PND3, PND53)

# 记录内字段类型(表驱动渲染):
#   C   = 字符,空→留空(相邻 pipe),校验禁用字符
#   N   = 数值 N(_,2),空→"0.00",四舍五入进第三位(官方 §9)
#   INT = 整数计数(TOT_NUM N/7、SEQ_NO N/10),空→"0"
FIELD_C = "C"
FIELD_N = "N"
FIELD_INT = "INT"

_RECORD_SEP = "\r\n"  # 官方 §7:record 间以 CR/LF 换行
_FIELD_SEP = "|"  # 官方 §7:字段间 pipe,头尾不加
_BUDDHIST_OFFSET = 543  # 公历 → 佛历 พ.ศ.
_TWO_DP = Decimal("0.01")

# 官方 §10 禁用字符 + 单/双引号 + 逗号;pipe 为分隔符本身,值内出现会破坏字段边界,一并拦。
# 「保留字」§10 亦禁,但官方 PDF 未在本节列举具体词表,故只机械拦可枚举字符(见汇报待核项)。
_FORBIDDEN_CHARS = frozenset("*+/\\!$%#&@,'\"|")


# HEADER 25 字段(官方 §1.4)。字段 10-12 的税法条款 PND3/PND53 名称不同(ม.48ทวิ/ม.50 vs
# ม.65จัตวา/ม.69ทวิ),值语义等价故用与表无关的中性键 SECTION_B/SECTION_C,由调用方按 form 供值。
HEADER_FIELDS: tuple[tuple[str, str], ...] = (
    ("HEADER", FIELD_C),  # 1  固定 "H"
    ("SENDER_ID", FIELD_C),  # 2  报媒介填 "0000"
    ("SENDER_NID", FIELD_C),  # 3  报送人 13 位税号
    ("SENDER_BRANCH", FIELD_C),  # 4  总公司 "000000"
    ("SENDER_ROLE", FIELD_C),  # 5  1=扣缴人
    ("TAX_TYPE", FIELD_C),  # 6  PND3 / PND53
    ("NID", FIELD_C),  # 7  扣缴义务人(纳税人)13 位税号
    ("BRANCH_NO", FIELD_C),  # 8  纳税人分支
    ("DEPT_NAME", FIELD_C),  # 9  สำนักงานใหญ่
    ("SECTION3", FIELD_C),  # 10 ม.3 เตรส 0/1
    ("SECTION_B", FIELD_C),  # 11 PND3:ม.48ทวิ / PND53:ม.65จัตวา
    ("SECTION_C", FIELD_C),  # 12 PND3:ม.50 / PND53:ม.69ทวิ
    ("LTO", FIELD_C),  # 13 大企业局 0/1
    ("TAX_MONTH", FIELD_C),  # 14 01-12,00=3ก
    ("TAX_YEAR", FIELD_C),  # 15 佛历 4 位
    ("BRANCH_TYPE", FIELD_C),  # 16 V=VAT分支 / 空
    ("FORM_TYPE", FIELD_C),  # 17 00=正常
    ("TOT_NUM", FIELD_INT),  # 18 明细行数
    ("TOT_AMT", FIELD_N),  # 19 支付总额
    ("TOT_TAX", FIELD_N),  # 20 扣缴税总额
    ("SUR_AMT", FIELD_N),  # 21 加算金
    ("GTOT_TAX", FIELD_N),  # 22 税+加算金
    ("TRANS_AMT", FIELD_N),  # 23 银行转账额
    ("USER_ID", FIELD_C),  # 24 登记参考号/登录码
    ("FORM_FLAG", FIELD_C),  # 25 1=媒介寄档
)

# DETAIL 38 字段(官方 §1.5),一行一 payee。字段 9-26 = 3 组收入类型(每组 6 字段);
# 字段 27-38 = 收款人地址 12 项。字段 4 键 "PAYEE_ID" 由 form 决定填 PIN 还是 NID。
DETAIL_FIELDS: tuple[tuple[str, str], ...] = (
    ("DETAIL", FIELD_C),  # 1  固定 "D"
    ("SEQ_NO", FIELD_INT),  # 2  明细序号(一序≤3 收入类型)
    ("BRANCH_NO", FIELD_C),  # 3  付款方分支
    ("PAYEE_ID", FIELD_C),  # 4  PND3=PIN / PND53=NID(均 13 位)
    ("TIN", FIELD_C),  # 5  10 位旧税号,无="0000000000"
    ("TITLE_NAME", FIELD_C),  # 6  抬头(นาย/บริษัท),个人无="-"
    ("FNAME", FIELD_C),  # 7  名/单位名
    ("SNAME", FIELD_C),  # 8  姓(个人),单位空
    ("PAID_DATE1", FIELD_C),  # 9  ddmmyyyy 佛历
    ("TAX_RATE1", FIELD_N),  # 10 税率 N(4,2)
    ("PAID_AMT1", FIELD_N),  # 11 支付基数
    ("TAX_AMT1", FIELD_N),  # 12 扣缴税额
    ("INC_TYPE_PND1", FIELD_C),  # 13 收入类型文字
    ("PAY_CON1", FIELD_C),  # 14 1=扣缴
    ("PAID_DATE2", FIELD_C),  # 15 收入组 2
    ("TAX_RATE2", FIELD_N),  # 16
    ("PAID_AMT2", FIELD_N),  # 17
    ("TAX_AMT2", FIELD_N),  # 18
    ("INC_TYPE_PND2", FIELD_C),  # 19
    ("PAY_CON2", FIELD_C),  # 20
    ("PAID_DATE3", FIELD_C),  # 21 收入组 3
    ("TAX_RATE3", FIELD_N),  # 22
    ("PAID_AMT3", FIELD_N),  # 23
    ("TAX_AMT3", FIELD_N),  # 24
    ("INC_TYPE_PND3", FIELD_C),  # 25
    ("PAY_CON3", FIELD_C),  # 26
    ("BUILD_NAME", FIELD_C),  # 27 地址 12 项起
    ("ROOM_NO", FIELD_C),  # 28
    ("FLOOR_NO", FIELD_C),  # 29
    ("VILLAGE_NAME", FIELD_C),  # 30
    ("ADD_NO", FIELD_C),  # 31
    ("MOO_NO", FIELD_C),  # 32
    ("SOI", FIELD_C),  # 33
    ("STREET_NAME", FIELD_C),  # 34
    ("TAMBON", FIELD_C),  # 35
    ("AMPHUR", FIELD_C),  # 36 PND3 必填
    ("PROVINCE", FIELD_C),  # 37 PND3 必填
    ("POSTAL_CODE", FIELD_C),  # 38 PND3 必填
)

HEADER_FIELD_COUNT = len(HEADER_FIELDS)  # = 25
DETAIL_FIELD_COUNT = len(DETAIL_FIELDS)  # = 38


class RdPrepFormatError(ValueError):
    """字段值违反 RD Prep 格式契约(禁用字符/未知 form 等)。"""


def _money(value) -> str:
    """N(_,2) 渲染:空→'0.00',否则 Decimal 量化两位(四舍五入进第三位,官方 §9)。禁 float。"""
    if value is None or value == "":
        return "0.00"
    q = Decimal(str(value)).quantize(_TWO_DP, rounding=ROUND_HALF_UP)
    return f"{q:.2f}"


def _integer(value) -> str:
    if value is None or value == "":
        return "0"
    return str(int(Decimal(str(value))))


def _char(value) -> str:
    """字符字段:空→留空;校验禁用字符(官方 §10)。变长不补位(§15)。"""
    if value is None:
        return ""
    s = str(value)
    bad = _FORBIDDEN_CHARS.intersection(s)
    if bad:
        raise RdPrepFormatError(f"字段值含 RD Prep 禁用字符 {sorted(bad)!r}: {s!r}")
    return s


_RENDER = {FIELD_C: _char, FIELD_N: _money, FIELD_INT: _integer}


def _render_record(fields: tuple[tuple[str, str], ...], values: Mapping) -> str:
    cells = [_RENDER[ftype](values.get(key)) for key, ftype in fields]
    return _FIELD_SEP.join(cells)


def to_buddhist_year(year_ce: int) -> str:
    """公历年 → 佛历 พ.ศ. 4 位串(官方 §1.4 字段 15)。"""
    return str(year_ce + _BUDDHIST_OFFSET)


def to_buddhist_paid_date(d: _dt.date) -> str:
    """支付日 → ddmmyyyy(年为佛历,官方 §1.5 字段 9)。2026-07-01 → '01072569'。"""
    return f"{d.day:02d}{d.month:02d}{d.year + _BUDDHIST_OFFSET}"


def to_buddhist_date_slashes(d: _dt.date) -> str:
    """支付日 → dd/mm/พ.ศ.(键入底稿人读版式,同一佛历偏移,只是分隔符不同)。
    2026-07-01 → '01/07/2569'。"""
    return f"{d.day:02d}/{d.month:02d}/{d.year + _BUDDHIST_OFFSET}"


def build_header(form: str, values: Mapping) -> str:
    """HEADER(25 字段)→ pipe 分隔串。字段 1 恒 'H';TAX_TYPE 缺省取 form。"""
    _require_form(form)
    row = {"HEADER": "H", "TAX_TYPE": form, **values}
    return _render_record(HEADER_FIELDS, row)


def build_detail(form: str, values: Mapping) -> str:
    """DETAIL(38 字段)→ pipe 分隔串。字段 1 恒 'D';字段 4 按 form 取 PIN(PND3)/NID(PND53)。"""
    _require_form(form)
    payee_id = values.get("NID" if form == PND53 else "PIN")
    row = {"DETAIL": "D", "PAYEE_ID": payee_id, **values}
    return _render_record(DETAIL_FIELDS, row)


def assemble(header: str, details: Iterable[str]) -> str:
    """HEADER + DETAIL 行 → 完整文件文本(CR/LF 分隔,末行无换行,官方 §7)。"""
    return _RECORD_SEP.join([header, *details])


def build_filename(
    *,
    form: str,
    nid: str,
    branch_no: str,
    tax_year_be: str | int,
    tax_month: str,
    form_type: str = "00",
    submission_seq: str = "00",
) -> str:
    """官方 §3 文件名规约:TAX_TYPE_NID_BRANCH_TAX_YEAR_TAX_MONTH_FORM_TYPE_ครั้งที่ส่ง.txt。"""
    _require_form(form)
    parts = [
        form,
        str(nid),
        str(branch_no),
        str(tax_year_be),
        str(tax_month),
        str(form_type),
        str(submission_seq),
    ]
    return "_".join(parts) + ".txt"


def _require_form(form: str) -> None:
    if form not in FORMS:
        raise RdPrepFormatError(f"未知 form {form!r},仅支持 {FORMS}")
