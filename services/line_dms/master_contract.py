# -*- coding: utf-8 -*-
"""LINE 订车所用 DMS 主档的会话快照与提交前复核。"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from services.erp.mrerp_dms_company_banks import company_bank_label
from services.line_dms.qa_util import car_label, find_row, row_name

SNAPSHOT_KEYS = (
    "place_books",
    "cars",
    "term_sales",
    "regis_behalfs",
    "company_banks",
)
REQUIRED_NONEMPTY_KEYS = frozenset(SNAPSHOT_KEYS[:-1])
_ROW_WIDTHS = {"company_banks": 5}

_ANSWER_SPECS = (
    ("place", "place_books", "place", "name", row_name),
    ("car", "cars", "car_search", "label", car_label),
    ("term", "term_sales", "term", "name", row_name),
    ("regis", "regis_behalfs", "regis", "name", row_name),
)
_ANSWER_ORDER = ("place", "car", "paint", "delivery_date_be", "term", "regis", "regis_name")


class MasterSyncError(RuntimeError):
    def __init__(self, code: str, key: str = ""):
        super().__init__(f"{code}:{key}" if key else code)
        self.code = code
        self.key = key


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _compact(rows: Iterable[list], width: int = 3) -> List[list]:
    compact = []
    for row in rows or []:
        if not row or row[0] is None:
            continue
        compact.append(
            [
                str(row[index]) if len(row) > index and row[index] is not None else ""
                for index in range(width)
            ]
        )
    return compact


def _version(rows: Dict[str, List[list]]) -> str:
    canonical = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]


def build_snapshot(
    masters: Dict[str, Any],
    captured_at: Optional[str] = None,
    *,
    require_nonempty: bool = True,
) -> Dict[str, Any]:
    rows: Dict[str, List[list]] = {}
    for key in SNAPSHOT_KEYS:
        source = masters.get(key)
        if not isinstance(source, list):
            raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", key)
        rows[key] = _compact(source, _ROW_WIDTHS.get(key, 3))
        if require_nonempty and key in REQUIRED_NONEMPTY_KEYS and not rows[key]:
            raise MasterSyncError("ERR_DMS_MASTER_EMPTY", key)
    return {
        "version": _version(rows),
        "captured_at": captured_at or _now(),
        "counts": {key: len(value) for key, value in rows.items()},
        "rows": rows,
    }


def snapshot_rows(snapshot: Dict[str, Any], key: str) -> List[list]:
    rows = (snapshot or {}).get("rows") or {}
    value = rows.get(key)
    if not isinstance(value, list):
        raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", key)
    if key in REQUIRED_NONEMPTY_KEYS and not value:
        raise MasterSyncError("ERR_DMS_MASTER_EMPTY", key)
    return value


def build_paint_snapshot(car_id: str, rows: List[list]) -> Dict[str, Any]:
    compact = _compact(rows)
    if not compact:
        raise MasterSyncError("ERR_DMS_MASTER_EMPTY", "paints")
    payload = {"car_id": str(car_id), "rows": compact}
    return {
        **payload,
        "version": _version({"paints": compact}),
        "captured_at": _now(),
        "count": len(compact),
    }


def _change(changes: List[dict], field: str, before: str, after: str) -> None:
    if before != after:
        changes.append({"field": field, "before": before, "after": after})


def _missing_result(qa: dict, field: str, snapshot: dict, paints: List[list]) -> Dict[str, Any]:
    updated = copy.deepcopy(qa)
    updated["master_snapshot"] = snapshot
    updated.pop("masters_synced", None)
    updated.pop("paint_snapshots", None)
    answers = updated.setdefault("answers", {})

    if field == "advisor":
        return {
            "status": "unmatched",
            "field": field,
            "qa": updated,
            "code": "ERR_DMS_ADVISOR_UNMATCHED",
        }
    if field == "bank":
        transfers = [p for p in updated.get("payments") or [] if p.get("channel") == "transfer"]
        missing = transfers[0] if transfers else {"channel": "transfer", "amount": ""}
        updated["payments"] = [p for p in updated.get("payments") or [] if p is not missing]
        updated["pending_channel"] = missing
        updated["step"] = "pay_dst"
        return {
            "status": "unmatched",
            "field": field,
            "qa": updated,
            "code": "ERR_DMS_MASTER_UNMATCHED",
        }

    start = _ANSWER_ORDER.index(field)
    for answer_key in _ANSWER_ORDER[start:]:
        answers.pop(answer_key, None)
    updated["payments"] = []
    updated["pending_channel"] = {}
    updated["step"] = {
        "place": "place",
        "car": "car_search",
        "paint": "paint",
        "term": "term",
        "regis": "regis",
    }[field]
    if field == "paint" and paints:
        updated["paint_snapshots"] = {
            str((answers.get("car") or {}).get("id") or ""): build_paint_snapshot(
                str((answers.get("car") or {}).get("id") or ""), paints
            )
        }
    return {
        "status": "unmatched",
        "field": field,
        "qa": updated,
        "code": "ERR_DMS_MASTER_UNMATCHED",
    }


def reconcile(qa: dict, masters: Dict[str, Any], paints: Optional[List[list]]) -> Dict[str, Any]:
    """用确认瞬间的 DMS 主档复核选择；不创建单据。"""
    updated = copy.deepcopy(qa)
    snapshot = build_snapshot(masters, require_nonempty=False)
    answers = updated.setdefault("answers", {})
    changes: List[dict] = []

    advisor = updated.get("advisor") or {}
    advisor_row = find_row(masters.get("advisors"), str(advisor.get("id") or ""))
    if advisor_row is None:
        return _missing_result(updated, "advisor", snapshot, paints or [])
    advisor_name = row_name(advisor_row)
    _change(changes, "advisor", str(advisor.get("name") or ""), advisor_name)
    updated["advisor"] = {**advisor, "name": advisor_name}

    for answer_key, master_key, _, label_key, label_fn in _ANSWER_SPECS:
        selected = answers.get(answer_key) or {}
        row = find_row(masters.get(master_key), str(selected.get("id") or ""))
        if row is None:
            return _missing_result(updated, answer_key, snapshot, paints or [])
        current_label = label_fn(row)
        _change(changes, answer_key, str(selected.get(label_key) or ""), current_label)
        answers[answer_key] = {**selected, label_key: current_label}

    paint_selected = answers.get("paint") or {}
    paint_row = find_row(paints, str(paint_selected.get("id") or ""))
    if paint_row is None:
        return _missing_result(updated, "paint", snapshot, paints or [])
    paint_name = row_name(paint_row)
    _change(changes, "paint", str(paint_selected.get("name") or ""), paint_name)
    answers["paint"] = {**paint_selected, "name": paint_name}

    banks = masters.get("company_banks") or []
    for payment in updated.get("payments") or []:
        if payment.get("channel") != "transfer":
            continue
        extra = payment.setdefault("extra", {})
        bank = find_row(banks, str(extra.get("dst_id") or ""))
        if bank is None:
            return _missing_result(updated, "bank", snapshot, paints or [])
        label = company_bank_label(bank)
        _change(changes, "bank", str(extra.get("dst") or ""), label)
        extra["dst"] = label

    car_id = str((answers.get("car") or {}).get("id") or "")
    paint_snapshot = build_paint_snapshot(car_id, paints or [])
    updated["master_snapshot"] = snapshot
    updated["paint_snapshots"] = {car_id: paint_snapshot}
    updated.pop("masters_synced", None)
    updated["master_validation"] = {
        "validated_at": _now(),
        "version": snapshot["version"],
        "paint_version": paint_snapshot["version"],
        "changes": changes,
    }
    return {"status": "changed" if changes else "ok", "qa": updated, "changes": changes}
