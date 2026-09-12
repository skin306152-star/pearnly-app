# -*- coding: utf-8 -*-
"""DMS 银行目录读取与订车转账校验；银行不等于公司收款账户。"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from services.erp.mrerp_dms_client_base import DMSClientError

PAYMENT_BANK_MASTERS = {
    "company_banks": "txtbanknametfmon",
    "source_banks": "txtbanknametffrom",
    "cheque_banks": "txtbanknamecheque",
    "cashier_banks": "txtbanknamecashiercq",
    "card_banks": "txtbanknamecddbc",
}
PAYMENT_CHANNEL_BANKS = {
    "cheque": "cheque_banks",
    "cashier_cheque": "cashier_banks",
    "card": "card_banks",
}


def company_bank_label(row: list) -> str:
    """银行行 [id, code, name, branch, account] 的展示值；后两列可能为空。"""
    code = str(row[1]).strip() if len(row) > 1 else ""
    name = str(row[2]).strip() if len(row) > 2 else ""
    branch = str(row[3]).strip() if len(row) > 3 else ""
    account = str(row[4]).strip() if len(row) > 4 else ""
    bank = (
        f"{code} · {name}" if code and name and code.casefold() != name.casefold() else name or code
    )
    return " · ".join(value for value in (bank, account, branch) if value) or str(row[0])


def normalize_company_bank_rows(rows: Iterable[Any]) -> List[list]:
    """归一 DMS typeahead 行；兼容旧 DOM 字典结果，丢弃没有 DMS id 的脏行。"""
    out = []
    for item in rows:
        if isinstance(item, dict):
            bank_id = str(item.get("id") or "").strip()
            details = [str(value or "").strip() for value in item.get("details") or []]
        else:
            values = list(item or [])
            bank_id = str(values[0] if values else "").strip()
            details = [str(value or "").strip() for value in values[1:]]
        if not bank_id:
            continue
        out.append([bank_id, *(details + ["", "", "", ""])[:4]])
    return out


def fetch_company_banks(adapter: Any, *, timeout_ms: int = 10000) -> List[list]:
    """读取收款银行目录；不能假设银行行含公司收款账户。"""
    return _fetch_banks(adapter, "txtbanknametfmon")


def fetch_source_banks(adapter: Any, *, timeout_ms: int = 10000) -> List[list]:
    """汇款银行使用独立原生目录，其 ID 和范围可能不同于收款银行。"""
    return _fetch_banks(adapter, "txtbanknametffrom")


def fetch_payment_bank_masters(adapter: Any) -> dict:
    return {key: _fetch_banks(adapter, elem) for key, elem in PAYMENT_BANK_MASTERS.items()}


def _fetch_banks(adapter: Any, elemname: str) -> List[list]:
    failure = None
    for _ in range(2):
        try:
            rows = adapter._client()._bshsd_all(elemname, page_size=200)
            if rows is not None:
                return normalize_company_bank_rows(rows)
            failure = RuntimeError("DMS bank typeahead returned no result")
        except Exception as exc:
            failure = exc
    screenshot = _failure_screenshot(adapter)
    raise DMSClientError(
        "company bank master did not become ready"
        f"; screenshot={screenshot}; cause={type(failure).__name__}",
        "ERR_DMS_MASTER_UNAVAILABLE",
    )


def company_bank_payment_extra(row: list, existing: dict | None = None) -> Dict[str, str]:
    """更新银行身份；目录缺少账户时保留已明确填写的收款资料。"""
    existing = existing or {}
    return {
        "dst_id": str(row[0]),
        "dst": company_bank_label(row),
        "dst_bank_id": str(row[0]),
        "dst_bank_name": str(row[2]).strip() if len(row) > 2 else "",
        "dst_branch_name": (str(row[3]).strip() if len(row) > 3 else "")
        or str(existing.get("dst_branch_name") or "").strip(),
        "dst_account_no": (str(row[4]).strip() if len(row) > 4 else "")
        or str(existing.get("dst_account_no") or "").strip(),
    }


def validate_company_bank_payments(adapter: Any, payments: Iterable[dict]) -> List[dict]:
    """提交前核对银行身份和完整转账资料，不把银行编号当作公司账号。"""
    from services.erp.mrerp_dms_payments import validate_payment_completeness

    payments = list(payments or [])
    by_key = {}

    def current_bank(key, bank_id):
        if key not in by_key:
            rows = _fetch_banks(adapter, PAYMENT_BANK_MASTERS[key])
            by_key[key] = {str(row[0]): row for row in rows}
        row = by_key[key].get(str(bank_id or ""))
        if row is None:
            raise DMSClientError(
                "selected bank is not in the current DMS list", "ERR_DMS_MASTER_UNMATCHED"
            )
        return row

    validated = []
    for payment in payments:
        current = dict(payment)
        channel = current.get("channel")
        extra = dict(current.get("extra") or {})
        if channel == "transfer":
            row = current_bank("company_banks", extra.get("dst_id"))
            extra.update(company_bank_payment_extra(row, extra))
            source = current_bank("source_banks", extra.get("src_bank_id"))
            extra["src_bank_name"] = str(source[2] or source[1]).strip()
        elif channel in PAYMENT_CHANNEL_BANKS:
            row = current_bank(PAYMENT_CHANNEL_BANKS[channel], extra.get("bank_id"))
            extra["bank_name"] = str(row[2] or row[1]).strip()
        current["extra"] = extra
        validated.append(current)
    validate_payment_completeness(validated)
    return validated


def _failure_screenshot(adapter: Any) -> str:
    session = getattr(adapter, "_session", None)
    path = (
        session.screenshot("company-bank-master-failed", scenario="company bank list not ready")
        if session is not None
        else None
    )
    if path:
        return str(path)
    folder = Path(tempfile.gettempdir()) / "pearnly-dms-failures"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"company-bank-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    try:
        adapter._page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        return "unavailable"
