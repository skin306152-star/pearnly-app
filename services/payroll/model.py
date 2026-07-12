# -*- coding: utf-8 -*-
"""工资进料的语义字段键 + 结构化行 + 校验 Issue(全域共享单一事实源)。

进料兼容层把「任意工资 Excel 的某一列」映射到这里的语义键;校验/三产出/持久化都只认
这些键,不散写魔法列下标。Issue 照 services/fileconv Issue 范式:结构化逐行点名,绝不
静默(方案 §3)。钱字段在结构化行里恒为 Decimal,不经 float。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

# 语义字段键(列映射 column_map 的值域 · 结构化行的键)。
F_INCOME_CODE = "income_code"  # 收入类型码,金标 "40(1)"
F_SEQ = "seq"  # 序号(缺则按行号自动补)
F_EMPLOYEE_ID = "employee_id"  # 员工 13 位身份证(必 · mod-11 强特征)
F_TITLE = "title"  # 称谓 นาย/นางสาว
F_FIRST_NAME = "first_name"
F_LAST_NAME = "last_name"
F_PAID_DATE = "paid_date"  # 支付日(结构化后为 date)
F_PAID_AMOUNT = "paid_amount"  # 支付金额(必 · Decimal)
F_WHT_AMOUNT = "wht_amount"  # 预扣税额(Decimal · 采信事务所,只验不算)
F_CONDITION = "condition"  # 条件 1=หัก ณ ที่จ่าย

# 付款方(扣缴义务人)13 位税号是表头级字段(全表同值 · 默认取客户档 workspace_clients.tax_id),
# 不在逐行语义键里 —— 金标虽逐行重复,但它是申报表头填一次的量,见方案 §2.2。
F_PAYER_ID = "payer_id"

# 自动猜列的目标字段(方案 §2.2)——付款方/序号不猜(表头级/行号派生)。
GUESSABLE_FIELDS = (
    F_EMPLOYEE_ID,
    F_PAID_AMOUNT,
    F_WHT_AMOUNT,
    F_TITLE,
    F_FIRST_NAME,
    F_LAST_NAME,
    F_PAID_DATE,
    F_INCOME_CODE,
)

# 结构化行必填(V5)——缺失点名,不臆造。
REQUIRED_FIELDS = (F_EMPLOYEE_ID, F_TITLE, F_FIRST_NAME, F_LAST_NAME, F_PAID_AMOUNT)

DEFAULT_INCOME_CODE = "40(1)"  # 工资薪金 ม.40(1);模板可改(方案 U3)
DEFAULT_CONDITION = "1"  # หัก ณ ที่จ่าย 代扣

# Issue.kind —— 校验失败类别(供 UI 分色/汇总计数),不是给机器分支的枚举魔术串。
ISSUE_INVALID_ID = "invalid_employee_id"  # V1 mod-11 / 长度不符
ISSUE_BAD_DATE = "bad_paid_date"  # V2 无法解析
ISSUE_DATE_OUT_OF_PERIOD = "paid_date_out_of_period"  # V2 出申报期
ISSUE_SUM_MISMATCH = "sum_mismatch"  # V3 Σ ≠ 申报总额
ISSUE_WHT_OUT_OF_RANGE = "wht_out_of_range"  # V4 wht<0 或 wht>amount
ISSUE_BAD_AMOUNT = "bad_amount"  # 金额无法解析
ISSUE_MISSING_FIELD = "missing_required_field"  # V5


@dataclass(frozen=True)
class Issue:
    """一条结构化校验问题(照 fileconv Issue:逐行点名 · row_no=None 表整表级)。"""

    kind: str
    field: str
    message: str
    row_no: Optional[int] = None  # 1-based 数据行号(表头不计)
    value: str = ""


@dataclass
class PayrollRow:
    """结构化工资行(进料/手工同构产出)。金额恒 Decimal;日期为公历 date。"""

    seq: int
    employee_id: str
    title: str
    first_name: str
    last_name: str
    paid_amount: Decimal
    wht_amount: Decimal
    paid_date: Optional[object] = None  # datetime.date | None(认不出留 None,由 V2 点名)
    income_code: str = DEFAULT_INCOME_CODE
    condition: str = DEFAULT_CONDITION
    # 原始未解析值:金额/日期解析失败时留证,供 Issue 点名与人审回看,不静默丢。
    raw: dict = field(default_factory=dict)
