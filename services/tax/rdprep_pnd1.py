# -*- coding: utf-8 -*-
"""官方 FORMAT กลาง ภ.ง.ด.1 中央格式 txt 装配(FormatPND1V2_0 · 16/06/2568 · 方案 §4.3)。

字段序逐字段落官方 PDF(HEADER 22 / DETAIL 26),表驱动渲染只按表走,不散写魔法下标 ——
与 services/tax/rdprep.py(PND3/53)同范式,复用其 C/N/INT 渲染机与佛历/禁用字符契约。

与 ใบแนบ 扁平件(services/tax/pnd1_attach.py)的口径差异(施工必守):
  - 金额 N(15,2) 补 `.00`(官方 §9),ใบแนบ 是整数元;
  - 收入码用数字码 1-5(`40(1)`→`1`),ใบแนบ 写 `40(1)`;
  - DETAIL 含地址 12 项(AMPHUR/PROVINCE/POSTAL 官方标 M);我们无地址数据源 → 作为调用方
    可选入参,缺则留空(诚实降级,不臆造 —— 事务所走网页 ใบแนบ 从不用 RD Prep,此件为备件)。

优先级次要:T1 实锤事务所走网页 ใบแนบ 上传、从不用 RD Prep(与 D1-5 同结论),故 ใบแนบ
扁平件是主线,本中央格式作为对接 RD Prep 的备件。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping, Optional

from services.tax import rdprep
from services.tax.rdprep import FIELD_C, FIELD_INT, FIELD_N, RdPrepFormatError

PND1 = "PND1"  # ภ.ง.ด.1(月报)
PND1A = "PND1A"  # ภ.ง.ด.1ก(年报)
PND1AS = "PND1AS"  # ภ.ง.ด.1ก พิเศษ
TAX_TYPES = (PND1, PND1A, PND1AS)

# 收入码文字 → 官方数字码(§DETAIL 字段 13)。只映确定项;40(2) 子类型(离职/居民/非居民)
# 无判据不臆造,遇未知码抛错交人审。
_INCOME_CODE_MAP = {"40(1)": "1"}
_VALID_NUMERIC_CODES = {"1", "2", "3", "4", "5"}

_TWO_DP = Decimal("0.01")

# HEADER 22 字段(官方 §1 · Version 2.0)。
HEADER_FIELDS: tuple[tuple[str, str], ...] = (
    ("HEADER", FIELD_C),  # 1  固定 "H"
    ("SENDER_ID", FIELD_C),  # 2  ฝากไฟล์→"0000"
    ("SENDER_NID", FIELD_C),  # 3  报送人 13 位税号
    ("SENDER_BRANCH", FIELD_C),  # 4  报送人分支 "000000"
    ("SENDER_ROLE", FIELD_C),  # 5  1=ผู้หักภาษี
    ("TAX_TYPE", FIELD_C),  # 6  PND1/PND1A/PND1AS
    ("NID", FIELD_C),  # 7  扣缴义务人(付款方)税号
    ("BRANCH_NO", FIELD_C),  # 8  付款方分支
    ("DEPT_NAME", FIELD_C),  # 9  "สำนักงานใหญ่"
    ("LTO", FIELD_C),  # 10 大企业局 0/1
    ("TAX_MONTH", FIELD_C),  # 11 01-12,00=1ก
    ("TAX_YEAR", FIELD_C),  # 12 佛历 4 位
    ("BRANCH_TYPE", FIELD_C),  # 13 V/S/空
    ("FORM_TYPE", FIELD_C),  # 14 00=正常
    ("TOT_NUM", FIELD_INT),  # 15 明细行数
    ("TOT_AMT", FIELD_N),  # 16 总支付
    ("TOT_TAX", FIELD_N),  # 17 总扣税
    ("SUR_AMT", FIELD_N),  # 18 加算金 0.00
    ("GTOT_TAX", FIELD_N),  # 19 税+加算
    ("TRANS_AMT", FIELD_N),  # 20 银行转账额
    ("USER_ID", FIELD_C),  # 21 UserID/登记号
    ("FORM_FLAG", FIELD_C),  # 22 1=媒介 2=互联网
)

# DETAIL 26 字段(官方 §2)。字段 15-26 = 收款人地址(无数据源→留空,诚实降级)。
DETAIL_FIELDS: tuple[tuple[str, str], ...] = (
    ("DETAIL", FIELD_C),  # 1  固定 "D"
    ("SEQ_NO", FIELD_INT),  # 2  序号
    ("BRANCH_NO", FIELD_C),  # 3  付款方分支(与 header 一致)
    ("PIN", FIELD_C),  # 4  收入人身份证
    ("TIN", FIELD_C),  # 5  旧 10 位税号,无→"0000000000"
    ("TITLE_NAME", FIELD_C),  # 6  称谓,无→"-"
    ("FNAME", FIELD_C),  # 7  名
    ("SNAME", FIELD_C),  # 8  姓
    ("PAID_DATE", FIELD_C),  # 9  ddmmyyyy 佛历
    ("TAX_RATE", FIELD_N),  # 10 税率 N(4,2)
    ("PAID_AMT", FIELD_N),  # 11 支付额
    ("TAX_AMT", FIELD_N),  # 12 扣税额
    ("INC_TYPE_PND", FIELD_C),  # 13 收入码 1-5
    ("PAY_CON", FIELD_C),  # 14 1=หัก ณ ที่จ่าย
    ("BUILD_NAME", FIELD_C),  # 15 地址 12 项起(全 Optional)
    ("ROOM_NO", FIELD_C),  # 16
    ("FLOOR_NO", FIELD_C),  # 17
    ("VILLAGE_NAME", FIELD_C),  # 18
    ("ADD_NO", FIELD_C),  # 19
    ("MOO_NO", FIELD_C),  # 20
    ("SOI", FIELD_C),  # 21
    ("STREET_NAME", FIELD_C),  # 22
    ("TAMBON", FIELD_C),  # 23
    ("AMPHUR", FIELD_C),  # 24 官方标 M(无源留空,见模块注)
    ("PROVINCE", FIELD_C),  # 25 官方标 M
    ("POSTAL_CODE", FIELD_C),  # 26 官方标 M
)

HEADER_FIELD_COUNT = len(HEADER_FIELDS)  # = 22
DETAIL_FIELD_COUNT = len(DETAIL_FIELDS)  # = 26

_ADDRESS_KEYS = (
    "BUILD_NAME",
    "ROOM_NO",
    "FLOOR_NO",
    "VILLAGE_NAME",
    "ADD_NO",
    "MOO_NO",
    "SOI",
    "STREET_NAME",
    "TAMBON",
    "AMPHUR",
    "PROVINCE",
    "POSTAL_CODE",
)


def income_code_to_official(code: str) -> str:
    """收入码文字/数字码 → 官方数字码(1-5)。未知码抛错(不臆造 40(2) 子类型)。"""
    text = str(code or "").strip()
    if text in _VALID_NUMERIC_CODES:
        return text
    if text in _INCOME_CODE_MAP:
        return _INCOME_CODE_MAP[text]
    raise RdPrepFormatError(f"未知收入码 {text!r},官方码仅 1-5(40(1)=1),不臆造子类型")


def effective_rate(paid_amount, wht_amount) -> Decimal:
    """有效税率 = 扣税/支付×100(N(4,2))。支付为 0 → 0.00。采信事务所扣税额,只重构不重算。"""
    paid = _dec(paid_amount)
    if paid <= 0:
        return Decimal("0.00")
    return (_dec(wht_amount) / paid * 100).quantize(_TWO_DP, rounding=ROUND_HALF_UP)


def build_header(values: Mapping) -> str:
    """HEADER(22 字段)→ pipe 串。字段 1 恒 'H';TAX_TYPE 缺省 PND1。"""
    row = {"HEADER": "H", "TAX_TYPE": values.get("TAX_TYPE", PND1), **values}
    _require_tax_type(row["TAX_TYPE"])
    return rdprep._render_record(HEADER_FIELDS, row)


def build_detail(row, *, branch_no: str, address: Optional[Mapping] = None) -> str:
    """单员工 PayrollRow → DETAIL(26 字段)pipe 串。address 缺则地址项留空(诚实降级)。"""
    if row.paid_date is None:
        raise RdPrepFormatError(f"序号 {row.seq} 缺支付日,无法装配官方 DETAIL")
    addr = {k: (address or {}).get(k, "") for k in _ADDRESS_KEYS}
    values = {
        "DETAIL": "D",
        "SEQ_NO": row.seq,
        "BRANCH_NO": branch_no,
        "PIN": row.employee_id,
        "TIN": "0000000000",
        "TITLE_NAME": row.title or "-",
        "FNAME": row.first_name,
        "SNAME": row.last_name or ".",
        "PAID_DATE": rdprep.to_buddhist_paid_date(row.paid_date),
        "TAX_RATE": effective_rate(row.paid_amount, row.wht_amount),
        "PAID_AMT": row.paid_amount,
        "TAX_AMT": row.wht_amount,
        "INC_TYPE_PND": income_code_to_official(row.income_code),
        "PAY_CON": row.condition or "1",
        **addr,
    }
    return rdprep._render_record(DETAIL_FIELDS, values)


def build_file(
    header_values: Mapping,
    rows: Iterable,
    *,
    branch_no: str,
    address_by_seq: Optional[Mapping] = None,
) -> str:
    """HEADER + 逐员工 DETAIL → 完整中央格式文本(CR/LF 分行,末行无换行)。

    header_values 里 TOT_NUM/TOT_AMT/TOT_TAX 未给则按 rows 现算(守恒同源,Decimal 精确)。
    """
    rows = list(rows)
    address_by_seq = address_by_seq or {}
    tot_amt = sum((_dec(r.paid_amount) for r in rows), Decimal("0"))
    tot_tax = sum((_dec(r.wht_amount) for r in rows), Decimal("0"))
    header = {
        "TOT_NUM": len(rows),
        "TOT_AMT": tot_amt,
        "TOT_TAX": tot_tax,
        "SUR_AMT": Decimal("0"),
        "GTOT_TAX": tot_tax,
        "TRANS_AMT": Decimal("0"),
        **header_values,
    }
    details = [
        build_detail(r, branch_no=branch_no, address=address_by_seq.get(r.seq)) for r in rows
    ]
    return rdprep.assemble(build_header(header), details)


def build_filename(
    *,
    nid: str,
    branch_no: str,
    tax_year_be,
    tax_month: str,
    form_type: str = "00",
    submission_seq: str = "00",
    tax_type: str = PND1,
) -> str:
    """官方 §3 文件名:TAX_TYPE_NID_BRANCH_TAX_YEAR_TAX_MONTH_FORM_TYPE_ครั้งที่ส่ง.txt。"""
    _require_tax_type(tax_type)
    parts = [
        tax_type,
        str(nid),
        str(branch_no),
        str(tax_year_be),
        str(tax_month),
        str(form_type),
        str(submission_seq),
    ]
    return "_".join(parts) + ".txt"


def _require_tax_type(tax_type: str) -> None:
    if tax_type not in TAX_TYPES:
        raise RdPrepFormatError(f"未知 TAX_TYPE {tax_type!r},仅 {TAX_TYPES}")


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))
