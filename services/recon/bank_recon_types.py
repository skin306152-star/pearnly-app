# -*- coding: utf-8 -*-
"""bank_recon_types.py · Pearnly · bank reconciliation dataclasses.

Split verbatim from bank_recon_v2.py (facade re-exports these). Leaf module:
no dependency on any bank_recon_v2 function, only stdlib.
"""

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class StatementRow:
    date: Optional[date]
    description: str
    withdrawal: float  # money out (≥ 0)
    deposit: float  # money in (≥ 0)
    balance: float
    source_file: str = ""
    account_no: str = ""  # v118.35.0.61 · 所属账户(多账户文件分账户对账/校验用)
    row_hash: str = ""  # for deduplication
    # v118.33.13.0 · accuracy verification fields
    confidence: str = "high"  # 'high'|'medium'|'low' (set by OCR engine)
    balance_ok: Optional[bool] = None  # True/False (arithmetic verified)/None (cannot verify)
    # v118.35.0.50 · 系统按余额涨跌自动校正了借贷方向(OCR 把提款/存款列读反)· 让 UI/Excel 透明标注
    direction_autocorrected: bool = False
    # v118.35.0.62 · 系统按前后余额反推 · 自动修正了读错的金额(差异小 + 前后余额都对得上才动)
    amount_autocorrected: bool = False

    def __post_init__(self):
        if not self.row_hash:
            # v118.35.0.49 · 哈希含余额 · 防同日/同额/同描述的两笔合法交易被误判重复删掉
            # (真实案例 KKP 30/12 两笔一样的 SWD 65,573.75 · 余额不同 = 不同笔)
            key = (
                f"{self.account_no}|{self.date}|{self.withdrawal:.2f}|{self.deposit:.2f}"
                f"|{self.balance:.2f}|{self.description[:40]}"
            )
            # 行指纹去重用 · 非安全用途(故 usedforsecurity=False)
            self.row_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()[:12]


@dataclass
class GlRow:
    date: Optional[date]
    doc_no: str
    account_code: str
    description: str
    debit: float  # money out (≥ 0)
    credit: float  # money in (≥ 0)
    source_file: str = ""
    balance: float = 0.0  # 行运行余额(期初+累计借−贷)· 仅展示/导出 · 不参与匹配 · 不入 row_hash
    row_hash: str = ""

    def __post_init__(self):
        if not self.row_hash:
            key = (
                f"{self.date}|{self.doc_no}|{self.account_code}|{self.debit:.2f}|{self.credit:.2f}"
            )
            # 行指纹去重用 · 非安全用途(故 usedforsecurity=False)
            self.row_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()[:12]


@dataclass
class BankReconRow:
    match_status: str  # matched|gl_debit_only|gl_credit_only|stmt_withdrawal_only|stmt_deposit_only
    match_layer: Optional[int]  # 1=exact, 2=date_tol, 3=amount_only, None=unmatched
    # Statement side
    stmt_date: Optional[date] = None
    stmt_desc: str = ""
    stmt_withdrawal: float = 0.0
    stmt_deposit: float = 0.0
    stmt_balance: float = 0.0
    # GL side
    gl_date: Optional[date] = None
    gl_doc_no: str = ""
    gl_account_code: str = ""
    gl_desc: str = ""
    gl_debit: float = 0.0
    gl_credit: float = 0.0
    gl_balance: float = 0.0  # GL 行运行余额(透传自 GlRow.balance)· 仅展示
    # Meta
    date_diff_days: Optional[int] = None
    source_stmt_file: str = ""
    source_gl_file: str = ""
    # v118.33.13.0 · OCR accuracy verification (from StatementRow)
    stmt_confidence: str = "high"  # 'high'|'medium'|'low'
    stmt_balance_ok: Optional[bool] = None  # True/False/None
    # v118.35.0.62 · 系统按余额自动修正过本行(金额或方向)· 透明标注让用户知情可复核
    stmt_autocorrected: bool = False


@dataclass
class BankReconSummary:
    bank_code: str = ""
    gl_account_code: str = ""
    # Balance figures
    stmt_opening: float = 0.0
    stmt_closing: float = 0.0
    gl_opening: float = 0.0
    gl_closing: float = 0.0
    # Totals
    stmt_total_deposit: float = 0.0
    stmt_total_withdrawal: float = 0.0
    gl_total_credit: float = 0.0
    gl_total_debit: float = 0.0
    # Counts
    matched_count: int = 0
    gl_debit_only_count: int = 0
    gl_credit_only_count: int = 0
    stmt_withdrawal_only_count: int = 0
    stmt_deposit_only_count: int = 0
    # Unmatched amounts
    gl_debit_only_amount: float = 0.0
    gl_credit_only_amount: float = 0.0
    stmt_withdrawal_only_amount: float = 0.0
    stmt_deposit_only_amount: float = 0.0
    # Reconciliation check
    opening_diff: float = 0.0  # stmt_opening - gl_opening
    formula_stmt_closing: float = 0.0  # calculated from formula
    formula_diff: float = 0.0  # stmt_closing - formula_stmt_closing (ideally 0)
