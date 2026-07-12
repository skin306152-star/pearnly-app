# -*- coding: utf-8 -*-
"""工资进料五校验(V1-V5 · 只验不算 · 纯函数 · 方案 §3)。

范围硬控制:验金额自洽 + 身份证/日期合法,**不算工资个税**(累进/减免/全年平均法是全 HR
范畴,事务所已算好,扣税列一律采信 —— 方案 §3.1)。逐行结构化点名,绝不静默;钱用 Decimal。

  V1 员工身份证 13 位 + mod-11 校验位(mod11_check 单一事实源,不另写一份算法)
  V2 支付日可解析 + 落在申报期月内(佛历口径复用 obligation_engine 权威)
  V3 Σ支付金额 == 申报总额(Decimal 精确,禁 float 回算)
  V4 0 ≤ 扣税 ≤ 支付额(越界点名,不校验「税该是多少」)
  V5 称谓/姓名/身份证等必填非空
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from services.recon.field_comparator import mod11_check
from services.payroll import model

_TAX_ID_LEN = 13


def validate_rows(rows: list, *, period: Optional[str] = None, declared_total=None) -> list:
    """跑 V1-V5,返回结构化 Issue 列表(空=全过)。

    period: 佛历「YYYY-MM」(给 V2 期内判定;None 则只验日期可解析不验出期)。
    declared_total: 申报总额(合计行/用户输入);None 则跳过 V3(无对比基准不臆断)。
    """
    issues: list = []
    for row in rows:
        issues.extend(_validate_row(row, period))
    total_issue = _validate_total(rows, declared_total)
    if total_issue:
        issues.append(total_issue)
    return issues


def total_paid(rows: list) -> Decimal:
    """Σ可解析支付金额(Decimal 精确 · 供 V3 与产出守恒断言同源)。"""
    return sum((r.paid_amount for r in rows if r.paid_amount is not None), Decimal("0"))


def _validate_row(row, period: Optional[str]) -> list:
    out: list = []
    out.extend(_check_required(row))
    out.extend(_check_employee_id(row))
    out.extend(_check_paid_date(row, period))
    out.extend(_check_amount_and_wht(row))
    return out


def _check_required(row) -> list:
    out = []
    values = {
        model.F_EMPLOYEE_ID: row.employee_id,
        model.F_TITLE: row.title,
        model.F_FIRST_NAME: row.first_name,
        model.F_LAST_NAME: row.last_name,
    }
    for field_key in model.REQUIRED_FIELDS:
        if field_key == model.F_PAID_AMOUNT:
            continue  # 金额缺失由 _check_amount_and_wht 专管(区分「缺」与「非法」)
        if not str(values.get(field_key, "")).strip():
            out.append(
                model.Issue(
                    kind=model.ISSUE_MISSING_FIELD,
                    field=field_key,
                    message=f"必填字段缺失:{field_key}",
                    row_no=row.seq,
                )
            )
    return out


def _check_employee_id(row) -> list:
    tid = row.employee_id
    if not tid:
        return []  # 缺失已由 _check_required 点名,不重复
    if len(tid) != _TAX_ID_LEN or not tid.isdigit() or not mod11_check(tid):
        return [
            model.Issue(
                kind=model.ISSUE_INVALID_ID,
                field=model.F_EMPLOYEE_ID,
                message="身份证非 13 位数字或 mod-11 校验位不符",
                row_no=row.seq,
                value=tid,
            )
        ]
    return []


def _check_paid_date(row, period: Optional[str]) -> list:
    if row.paid_date is None:
        raw = row.raw.get("paid_date")
        if raw in (None, ""):
            return []  # 无支付日:非硬必填(可整表赋值),不点名
        return [
            model.Issue(
                kind=model.ISSUE_BAD_DATE,
                field=model.F_PAID_DATE,
                message="支付日无法解析",
                row_no=row.seq,
                value=str(raw),
            )
        ]
    if period and _to_be_period(row.paid_date) != period:
        return [
            model.Issue(
                kind=model.ISSUE_DATE_OUT_OF_PERIOD,
                field=model.F_PAID_DATE,
                message=f"支付日不在申报期 {period} 内",
                row_no=row.seq,
                value=row.paid_date.isoformat(),
            )
        ]
    return []


def _check_amount_and_wht(row) -> list:
    out = []
    amount = row.paid_amount
    if amount is None:
        out.append(
            model.Issue(
                kind=model.ISSUE_BAD_AMOUNT,
                field=model.F_PAID_AMOUNT,
                message="支付金额缺失或无法解析",
                row_no=row.seq,
                value=str(row.raw.get("paid_amount", "")),
            )
        )
        return out
    wht = row.wht_amount or Decimal("0")
    if wht < 0 or wht > amount:
        out.append(
            model.Issue(
                kind=model.ISSUE_WHT_OUT_OF_RANGE,
                field=model.F_WHT_AMOUNT,
                message="扣税额须 0 ≤ 扣税 ≤ 支付额",
                row_no=row.seq,
                value=f"wht={wht} amount={amount}",
            )
        )
    return out


def _validate_total(rows: list, declared_total) -> Optional[model.Issue]:
    if declared_total is None:
        return None
    declared = (
        declared_total if isinstance(declared_total, Decimal) else Decimal(str(declared_total))
    )
    actual = total_paid(rows)
    if abs(actual - declared) > Decimal("0.01"):
        return model.Issue(
            kind=model.ISSUE_SUM_MISMATCH,
            field=model.F_PAID_AMOUNT,
            message="Σ支付金额与申报总额不符",
            row_no=None,
            value=f"Σ={actual} 申报={declared} 差={actual - declared}",
        )
    return None


def _to_be_period(d) -> str:
    return f"{d.year + 543:04d}-{d.month:02d}"
