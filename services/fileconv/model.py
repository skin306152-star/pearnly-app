# -*- coding: utf-8 -*-
"""财务文件转换引擎 · 数据模型。

引擎产出的唯一事实源:ConvertResult。守恒校验不静默 —— 每条不平的行进 issues,
带行号 + 期望 + 实际,调用方(K1b HTTP/UI)照单点名。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Any, Dict

# doc_type 取值。识别不了一律 GENERIC_TABLE,不假装。
GL_LEDGER = "gl_ledger"
BANK_STATEMENT = "bank_statement"
VAT_REPORT = "vat_report"
GENERIC_TABLE = "generic_table"

# status 取值。无文字层的扫描件/图片走 OCR(K1c);OCR 读不全或读不到一律结构化拒绝,
# 绝不把截断的行集当成功出件(截断尾行会让余额链假自洽,比拒绝更危险)。
STATUS_OK = "ok"
STATUS_NO_TEXT_LAYER = "no_text_layer"
STATUS_OCR_INCOMPLETE = "ocr_incomplete"  # 模型读了但输出截断/不可解析 → 拒绝(K1c 命门)
STATUS_OCR_UNAVAILABLE = "ocr_unavailable"  # 够不到/授权不了模型 → 拒绝,不假装转出来
STATUS_UNSUPPORTED_FORMAT = "unsupported_format"  # K2:损坏/空/老式 .xls 缺解析库 → 拒绝

# 拒绝态分组:绝不出数据表(截断/读不到时半截行集会假自洽)——xlsx_out/cli 共用同一判据。
REJECT_STATUSES = frozenset(
    {STATUS_NO_TEXT_LAYER, STATUS_OCR_INCOMPLETE, STATUS_OCR_UNAVAILABLE, STATUS_UNSUPPORTED_FORMAT}
)

# issue.kind 取值。
ISSUE_GL_BALANCE_CHAIN = "gl_balance_chain"  # 期初±借贷 ≠ 本行余额
ISSUE_RUNNING_BALANCE = "running_balance"  # |余额变动| ≠ 本行金额(单金额列格式)
ISSUE_FOOTER_TOTAL = "footer_total"  # 明细列合计 ≠ 报表总计行
ISSUE_CLOSING_ANCHOR = "closing_anchor"  # 文档印刷期末余额 ≠ 解析末行余额(治截断假自洽的独立锚)


@dataclass
class LedgerRow:
    """一行台账/流水。借贷双列格式填 debit/credit;单金额列格式填 amount。"""

    line_no: int  # 源文本全局行号(1 基),用于 issues 定位
    account: str
    date: str  # 原样保留(可能是佛历 พ.ศ.)
    date_ce: str  # 归一后的公历 ISO(复用 field_comparator.parse_date),解析不了留空
    doc_no: str
    description: str
    balance: Decimal
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    amount: Optional[Decimal] = None


@dataclass
class Table:
    """转换产出的一张表。columns 为列头,rows 为单元格值(Decimal 保留原类型)。"""

    name: str
    columns: List[str]
    rows: List[List[Any]] = field(default_factory=list)


@dataclass
class Issue:
    """一条守恒校验不通过的记录。expected/actual 用字符串保留精确值。"""

    kind: str
    line_no: int
    message: str
    expected: str = ""
    actual: str = ""
    account: str = ""


@dataclass
class ConvertResult:
    doc_type: str
    status: str
    source_name: str
    tables: List[Table] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def conserved(self) -> bool:
        """守恒校验全过 = 无 issue。四态诚实:有 issue 时调用方不得显示"完成"。"""
        return not self.issues
