# -*- coding: utf-8 -*-
"""DMS 银行目录读取与订车转账校验；银行不等于公司收款账户。"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_payments import MANUAL_BANK_FLAG

PAYMENT_BANK_MASTERS = {
    "company_banks": "txtbanknametfmon",
    "source_banks": "txtbanknametffrom",
    "cheque_banks": "txtbanknamecheque",
    "cashier_banks": "txtbanknamecashiercq",
    "card_banks": "txtbanknamecddbc",
}
# 目录权威为空时允许用户手工填银行名称的四类付款银行目录。
# company_banks(公司收款账户)永不入列:它是钱真正落进去的账户,必须实时目录选择 + 提交前校验。
MANUAL_BANK_KEYS = ("source_banks", "cheque_banks", "cashier_banks", "card_banks")
PAYMENT_CHANNEL_BANKS = {
    "cheque": "cheque_banks",
    "cashier_cheque": "cashier_banks",
    "card": "card_banks",
}


def bank_row_name(row: list) -> str:
    """目录行 [id, code, name, ...] 的银行名称;缺名回退代码(与 qa_util.row_name 同口径)。"""
    if len(row) > 2 and str(row[2] or "").strip():
        return str(row[2]).strip()
    return str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""


def manual_bank_allowed_for_rows(key: str, rows: Any) -> bool:
    """rows 是权威读取结果时判「该目录确实为空」:空 list 才算空目录。

    None / 缺 key(这次没读到)一律不算 —— 读取失败由上层 fail closed,不许被当成
    「DMS 里就是没配」再退回手工填写。"""
    return key in MANUAL_BANK_KEYS and isinstance(rows, list) and not rows


def resolve_bank_identity(
    rows: Any, key: str, bank_id: Any = "", bank_name: Any = ""
) -> Dict[str, Any] | None:
    """目录行 + 本次载荷 → 银行身份 {"id", "name", "manual"};判不出来回 None(不许放行)。

    目录有行:必须命中 —— 给了 id 就按 id 精确命中(目录里已删除的旧 id 不拿名称兜底),
    只给名称时要求目录内唯一精确同名(手工敲的名称能被唯一认领才放行)。
    目录权威为空(合法空表):只有 MANUAL_BANK_KEYS 里的四类允许手工名称,id 必须留空;
    公司收款账户 company_banks 一律 None。rows=None(没读到)→ None,失败关闭。"""
    if rows is None:
        return None
    empty_directory = manual_bank_allowed_for_rows(key, rows)
    rows = [row for row in rows if row and row[0] is not None]
    wanted_id = str(bank_id or "").strip()
    wanted_name = str(bank_name or "").strip()
    if rows:
        if wanted_id:
            row = next((item for item in rows if str(item[0]).strip() == wanted_id), None)
        else:
            hits = (
                [item for item in rows if bank_row_name(item).casefold() == wanted_name.casefold()]
                if wanted_name
                else []
            )
            row = hits[0] if len(hits) == 1 else None
        if row is None:
            return None
        return {"id": str(row[0]).strip(), "name": bank_row_name(row), "manual": False}
    if not empty_directory or not wanted_name:
        return None
    return {"id": "", "name": wanted_name, "manual": True}


def apply_bank_identity(extra: dict, key: str, rows: Any, *, id_key: str, name_key: str) -> None:
    """按实时目录落这笔付款的银行身份;命中不了(含已删除的旧选项)→ ERR_DMS_MASTER_UNMATCHED。

    目录权威为空 → 保留用户手工填的名称、清掉 id,并挂 MANUAL_BANK_FLAG(提交校验据此只
    豁免 id 槽位,名称与其它原生字段照旧必填 —— 名称缺失由完整性校验报缺字段,不在这里被
    当成「选项不在目录里」)。"""
    if manual_bank_allowed_for_rows(key, rows):
        extra[id_key] = ""
        extra[MANUAL_BANK_FLAG] = "1"
        return
    identity = resolve_bank_identity(rows, key, extra.get(id_key), extra.get(name_key))
    if identity is None:
        raise DMSClientError(
            "selected bank is not in the current DMS list", "ERR_DMS_MASTER_UNMATCHED"
        )
    assign_bank_identity(extra, identity, id_key=id_key, name_key=name_key)


def assign_bank_identity(extra: dict, identity: dict, *, id_key: str, name_key: str) -> None:
    """把 resolve_bank_identity 的结论落进 extra:命中目录写回目录 id/名称并清手工标记,
    手工条目保留用户名称、id 留空(不伪造目录 id)。"""
    extra[id_key] = identity["id"]
    extra[name_key] = identity["name"]
    if identity["manual"]:
        extra[MANUAL_BANK_FLAG] = "1"
    else:
        extra.pop(MANUAL_BANK_FLAG, None)


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


def fetch_company_banks(adapter: Any, *, client: Any = None, timeout_ms: int = 10000) -> List[list]:
    """读取收款银行目录；不能假设银行行含公司收款账户。"""
    return _fetch_banks(adapter, "txtbanknametfmon", client=client)


def fetch_source_banks(adapter: Any, *, client: Any = None, timeout_ms: int = 10000) -> List[list]:
    """汇款银行使用独立原生目录，其 ID 和范围可能不同于收款银行。"""
    return _fetch_banks(adapter, "txtbanknametffrom", client=client)


def fetch_payment_bank_masters(adapter: Any, *, client: Any = None) -> dict:
    """五类付款银行目录。给了权威只读 client 就走它 —— 销售账号常看不到银行全表,
    少这一次分叉就等于少一次按字段的重复登录。"""
    return {
        key: _fetch_banks(adapter, elem, client=client)
        for key, elem in PAYMENT_BANK_MASTERS.items()
    }


def _fetch_banks(adapter: Any, elemname: str, *, client: Any = None) -> List[list]:
    failure = None
    for _ in range(2):
        try:
            reader = client or adapter._client()
            rows = reader._bshsd_all(elemname, page_size=200)
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


def validate_company_bank_payments(
    adapter: Any, payments: Iterable[dict], *, client: Any = None
) -> List[dict]:
    """提交前核对银行身份和完整转账资料，不把银行编号当作公司账号。

    client 为权威只读会话上的 DMSClient 时,银行目录也读权威视图。
    收款账户(company_banks)永远按实时目录 id 校验;其余四类目录权威为空时允许这一笔用手工
    银行名称(目录非空则仍要求命中,已删除的旧选项必被 ERR_DMS_MASTER_UNMATCHED 拦下)。"""
    from services.erp.mrerp_dms_payments import validate_payment_completeness

    payments = list(payments or [])
    by_key = {}

    def bank_rows(key):
        if key not in by_key:
            by_key[key] = _fetch_banks(adapter, PAYMENT_BANK_MASTERS[key], client=client)
        return by_key[key]

    def current_bank(key, bank_id):
        row = next(
            (item for item in bank_rows(key) if str(item[0]).strip() == str(bank_id or "").strip()),
            None,
        )
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
            apply_bank_identity(
                extra,
                "source_banks",
                bank_rows("source_banks"),
                id_key="src_bank_id",
                name_key="src_bank_name",
            )
        elif channel in PAYMENT_CHANNEL_BANKS:
            key = PAYMENT_CHANNEL_BANKS[channel]
            apply_bank_identity(extra, key, bank_rows(key), id_key="bank_id", name_key="bank_name")
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
