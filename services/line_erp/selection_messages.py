"""Quick-reply questions for the ERP LINE destination flow."""

from __future__ import annotations

import math

from services.line_erp import target_preflight
from services.line_platform.quick_replies import question, quick_reply_item

QR_LIMIT = 13
QR_PAGE_SIZE = 11
_ADAPTERS = (("mrerp", "MR.ERP"), ("express", "Express"))


def _status(targets: list[dict]) -> str:
    return target_preflight.status_text({"targets": targets})


def erp_picker_message(targets: list[dict], mode: str) -> dict:
    items = [
        quick_reply_item(label, "erp-type", erp=adapter, mode=mode)
        for adapter, label in _ADAPTERS
        if any(
            str(target.get("adapter") or "").lower() == adapter and target.get("selectable")
            for target in targets
        )
    ]
    return question(
        "เลือก ERP",
        f"เลือกปลายทางสำหรับเอกสารชุดนี้\n{_status(targets)}",
        items,
    )


def account_picker_message(targets: list[dict], adapter: str, mode: str, *, page: int = 0) -> dict:
    adapter = str(adapter or "").lower()
    adapter_targets = [
        target for target in targets if str(target.get("adapter") or "").lower() == adapter
    ]
    ready_targets = [target for target in adapter_targets if target.get("selectable")]
    page_count = max(1, math.ceil(len(ready_targets) / QR_PAGE_SIZE))
    page = max(0, min(int(page or 0), page_count - 1))
    start = page * QR_PAGE_SIZE
    items = [
        quick_reply_item(
            str(target.get("label") or target.get("workspace_name") or adapter),
            "target",
            mode=mode,
            endpoint=target.get("endpoint_id"),
            workspace=target.get("workspace_client_id"),
        )
        for target in ready_targets[start : start + QR_PAGE_SIZE]
    ]
    if page > 0:
        items.insert(
            0,
            quick_reply_item(
                "ก่อนหน้า",
                "erp-type",
                erp=adapter,
                mode=mode,
                page=page - 1,
            ),
        )
    if page + 1 < page_count:
        items.append(
            quick_reply_item(
                "เพิ่มเติม",
                "erp-type",
                erp=adapter,
                mode=mode,
                page=page + 1,
            )
        )
    return question(
        "เลือกชุดบัญชี",
        f"ระบบตรวจสอบการเชื่อมต่อก่อนให้เลือก\n{_status(adapter_targets)}",
        items,
    )


def posting_mode_message(mode: str, target: dict) -> dict:
    if str(target.get("adapter") or "").lower() == "express":
        options = (("stock", "สินค้า / สต๊อก"), ("service", "บริการ / ไม่ลงสต๊อก"))
    else:
        options = (("credit", "เครดิต"),)
        if mode == "sales":
            options = (("cash", "เงินสด"), *options)
    target_name = " · ".join(
        value
        for value in (
            str(target.get("workspace_name") or "").strip(),
            str(target.get("label") or "").strip(),
        )
        if value
    )
    return question(
        "เลือกวิธีลงบัญชี",
        "\n".join(value for value in ("เลือกวิธีบันทึกเอกสารชุดนี้", target_name) if value),
        [quick_reply_item(label, f"posting:{value}") for value, label in options],
    )


__all__ = [
    "QR_LIMIT",
    "QR_PAGE_SIZE",
    "account_picker_message",
    "erp_picker_message",
    "posting_mode_message",
]
