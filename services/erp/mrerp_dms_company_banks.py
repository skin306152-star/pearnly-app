# -*- coding: utf-8 -*-
"""DMS 公司银行主档的浏览器读取与订车支付校验。"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urljoin

from services.erp.mrerp_dms_client_base import DMSClientError

_BANK_PAGE = "bank/view.php"
_READY_SELECTOR = "#showdata"
_ROW_SELECTOR = "#showdatact > div[data-val]"


def company_bank_label(row: list) -> str:
    """公司银行行 [id, code, name] 的稳定展示值，重复的 code/name 只显示一次。"""
    code = str(row[1]).strip() if len(row) > 1 else ""
    name = str(row[2]).strip() if len(row) > 2 else ""
    if code and name and code.casefold() != name.casefold():
        return f"{code} · {name}"
    return name or code or str(row[0])


def normalize_company_bank_rows(rows: Iterable[Dict[str, Any]]) -> List[list]:
    """把页面 DOM 结果归一成通用主档行，丢弃没有 DMS id 的脏行。"""
    out = []
    for item in rows:
        bank_id = str(item.get("id") or "").strip()
        if not bank_id:
            continue
        details = [str(value or "").strip() for value in item.get("details") or []]
        out.append([bank_id, details[0] if details else "", details[1] if len(details) > 1 else ""])
    return out


def fetch_company_banks(adapter: Any, *, timeout_ms: int = 10000) -> List[list]:
    """从已登录 DMS 页面读取公司银行；首轮失败 reload 一次，仍失败留截图并报错。"""
    page = adapter._page
    failure = None
    for attempt in range(2):
        try:
            with page.expect_response(_is_bank_list_response, timeout=timeout_ms):
                if attempt == 0:
                    page.goto(
                        urljoin(adapter.base_url, _BANK_PAGE),
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                else:
                    page.reload(wait_until="domcontentloaded", timeout=timeout_ms)
            page.locator(_READY_SELECTOR).wait_for(state="visible", timeout=timeout_ms)
            page.wait_for_timeout(100)
            raw = page.locator(_ROW_SELECTOR).evaluate_all("""rows => rows.map(row => ({
                    id: row.getAttribute('data-val') || '',
                    details: Array.from(row.querySelectorAll('.detaildata > div'))
                        .map(cell => (cell.textContent || '').trim())
                }))""")
            return normalize_company_bank_rows(raw)
        except Exception as exc:
            failure = exc
    screenshot = _failure_screenshot(adapter)
    raise DMSClientError(
        "company bank master did not become ready"
        f"; screenshot={screenshot}; cause={type(failure).__name__}"
    )


def _is_bank_list_response(response: Any) -> bool:
    request = response.request
    return (
        response.status == 200
        and response.url.endswith("/bank/component/showdata.php")
        and "sdtpage=" in (request.post_data or "")
    )


def validate_company_bank_payments(adapter: Any, payments: Iterable[dict]) -> List[dict]:
    """提交前确认每笔转账仍指向现存公司银行，并用主档当前名称覆盖会话旧值。"""
    payments = list(payments or [])
    if not any(payment.get("channel") == "transfer" for payment in payments):
        return [dict(payment) for payment in payments]
    rows = fetch_company_banks(adapter)
    by_id = {str(row[0]): row for row in rows}
    validated = []
    for payment in payments:
        current = dict(payment)
        if current.get("channel") == "transfer":
            extra = dict(current.get("extra") or {})
            row = by_id.get(str(extra.get("dst_id") or ""))
            if row is None:
                # 已选公司银行不在当前 live 主档:主档已变更,不许拿会话旧值提交。
                raise DMSClientError(
                    "selected company bank is no longer available",
                    "ERR_DMS_MASTER_UNMATCHED",
                )
            extra["dst"] = company_bank_label(row)
            current["extra"] = extra
        validated.append(current)
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
