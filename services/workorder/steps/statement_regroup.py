# -*- coding: utf-8 -*-
"""Recover continuation pages that belong to one photographed bank statement."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from services.workorder import kinds, storage
from services.workorder.steps import checkpoint
from services.workorder.steps import sort as sort_step

_FILE_NUMBER = re.compile(r"^(.*?)(\d{3,})([^0-9]*)$")
_MAX_ANCHOR_GAP = 4
_TRAIL_EXTEND = _MAX_ANCHOR_GAP
_MIN_ANCHORS = 3


@dataclass(frozen=True)
class _Record:
    item: dict
    fields: dict
    kind: str
    status: str


class Collector:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.records: list[_Record] = []

    def add(self, item: dict, ocr, outcome: dict) -> None:
        if self.enabled and isinstance(ocr, dict):
            self.records.append(
                _Record(
                    item=item,
                    fields=ocr,
                    kind=outcome["kind"],
                    status=outcome["update"]["status"],
                )
            )

    def apply(self, ctx, bins: dict[str, int]) -> int:
        rescued = _rescued_records(self.records)
        flagged_reduced = 0
        for record in rescued:
            with checkpoint.item_scope(ctx):
                ctx.store.update_item(
                    ctx.cur,
                    tenant_id=ctx.tenant_id,
                    item_id=record.item["id"],
                    kind=kinds.BANK_STATEMENT,
                    status="ok",
                    clear_flag_reason=True,
                )
                ctx.store.append_event(
                    ctx.cur,
                    tenant_id=ctx.tenant_id,
                    work_order_id=ctx.work_order_id,
                    step="classify",
                    event_type="item_regrouped",
                    payload={
                        "item_id": record.item["id"],
                        "from_kind": record.kind,
                        "to_kind": kinds.BANK_STATEMENT,
                        "reason": "statement_sequence",
                    },
                    dedupe_key=f"stmt_regroup:{record.item['id']}",
                )
            _move_bin(bins, record.kind)
            flagged_reduced += int(record.status == "flagged")
        return flagged_reduced


def _rescued_records(records: list[_Record]) -> list[_Record]:
    """救回锚区间内续页，并向两端加严扩展，补掉最后一页落在锚范围外的结构性漏洞。"""
    ranges = _statement_ranges(records)
    rescued = []
    for record in records:
        identity = _file_identity(record.item.get("file_ref"))
        if not identity or record.kind == kinds.BANK_STATEMENT:
            continue
        group, number = identity
        if sort_step._has_vat(record.fields):
            continue
        bank_evidence = sort_step._mentions_bank(record.fields) or sort_step._category_is_bank(
            record.fields
        )
        if not bank_evidence:
            continue
        for start, end in ranges.get(group, ()):
            inside = start <= number <= end
            extended = (
                start - _TRAIL_EXTEND <= number < start or end < number <= end + _TRAIL_EXTEND
            )
            if inside or (extended and sort_step._is_statement_title(record.fields)):
                rescued.append(record)
                break
    return rescued


def _statement_ranges(records: list[_Record]) -> dict[tuple, list[tuple[int, int]]]:
    anchors: dict[tuple, list[int]] = {}
    for record in records:
        identity = _file_identity(record.item.get("file_ref"))
        if (
            identity
            and record.kind == kinds.BANK_STATEMENT
            and sort_step._is_statement_title(record.fields)
        ):
            group, number = identity
            anchors.setdefault(group, []).append(number)

    ranges: dict[tuple, list[tuple[int, int]]] = {}
    for group, numbers in anchors.items():
        component = []
        for number in sorted(set(numbers)):
            if component and number - component[-1] > _MAX_ANCHOR_GAP:
                _append_range(ranges, group, component)
                component = []
            component.append(number)
        _append_range(ranges, group, component)
    return ranges


def _append_range(ranges: dict, group: tuple, component: list[int]) -> None:
    if len(component) >= _MIN_ANCHORS:
        ranges.setdefault(group, []).append((component[0], component[-1]))


def _file_identity(file_ref: str | None) -> tuple[tuple, int] | None:
    name = storage.original_name_of(file_ref) or Path(file_ref or "").name
    path = Path(name)
    match = _FILE_NUMBER.match(path.stem)
    if not match:
        return None
    group = (match.group(1).lower(), match.group(3).lower(), path.suffix.lower())
    return group, int(match.group(2))


def _move_bin(bins: dict[str, int], old_kind: str) -> None:
    if old_kind in bins:
        bins[old_kind] -= 1
        if not bins[old_kind]:
            del bins[old_kind]
    bins[kinds.BANK_STATEMENT] = bins.get(kinds.BANK_STATEMENT, 0) + 1
