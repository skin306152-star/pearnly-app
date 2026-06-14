# -*- coding: utf-8 -*-
"""按 source_id 反查做账分录(只读)· 喂外流 Sheet 的 借方/贷方/凭证号/入账状态列。

过账钩子是"业务 → 做账"单向(accounting/posting.generate_for_source enqueue),无反查接口。
本模块复用 accounting.vouchers.find_active_by_source + get_voucher 组合出导出向只读摘要。
未开做账模块 / 该单未过账 → 返回"未记账"占位(4 列留空标注),不报错(契约 04 §七E)。

隔离:vouchers 查询自带 WHERE tenant_id + workspace_client_id,套账边界由调用方传入。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from services.accounting import vouchers as jv

# 做账凭证状态 → 导出"入账状态"中文标签。
_STATUS_LABEL = {
    "posted": "已过账",
    "pending_review": "待复核",
    "void": "已作废",
}
_NOT_POSTED = "未记账"


def _acct_label(line: dict) -> str:
    """借/贷行 → "科目码 科目名"(缺名退码退 id)。"""
    code = (line.get("account_code") or "").strip()
    name = (line.get("account_name") or "").strip()
    if code and name:
        return f"{code} {name}"
    return code or name or str(line.get("account_id") or "")


def summarize_voucher(voucher: Optional[dict]) -> dict:
    """凭证(头+lines)或 None → 导出摘要。纯函数(不连库),便于单测。

    返回 {posted, voucher_no, status, status_label, debit, credit, debit_text, credit_text},
    其中 debit/credit = [{code,name,amount}],*_text = "码 名 ¤金额" 分号拼接(喂 Sheet 单元格)。
    """
    if not voucher:
        return {
            "posted": False,
            "voucher_no": "",
            "status": "",
            "status_label": _NOT_POSTED,
            "debit": [],
            "credit": [],
            "debit_text": "",
            "credit_text": "",
        }
    debit, credit = [], []
    for ln in voucher.get("lines") or []:
        item = {
            "code": ln.get("account_code"),
            "name": ln.get("account_name"),
            "amount": Decimal(str(ln.get("amount") or 0)),
            "label": _acct_label(ln),
        }
        (debit if ln.get("dr_cr") == "debit" else credit).append(item)
    status = voucher.get("status") or ""

    def _text(items):
        return "; ".join(f"{i['label']} {i['amount']}" for i in items)

    return {
        "posted": status == "posted",
        "voucher_no": voucher.get("voucher_no") or "",
        "status": status,
        "status_label": _STATUS_LABEL.get(status, status or _NOT_POSTED),
        "debit": debit,
        "credit": credit,
        "debit_text": _text(debit),
        "credit_text": _text(credit),
    }


def get_posting_for_source(cur, *, tenant_id, workspace_client_id, source_type, source_id) -> dict:
    """按 (source_type, source_id) 反查活跃凭证 → 导出摘要。无凭证 → "未记账"摘要。"""
    head = jv.find_active_by_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=source_type,
        source_id=source_id,
    )
    if not head:
        return summarize_voucher(None)
    full = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=head["id"]
    )
    return summarize_voucher(full)
