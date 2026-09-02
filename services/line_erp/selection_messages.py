"""Quick-reply questions for the ERP LINE destination flow."""

from __future__ import annotations

from services.line_erp import target_preflight
from services.line_platform.quick_replies import question, quick_reply_item

QR_LIMIT = 13
QR_PAGE_SIZE = 11


def _connection_name(target: dict) -> str:
    adapter = str(target.get("adapter") or "").lower()
    connection = str(
        target.get("connection_label")
        or ("MR.ERP" if adapter == "mrerp" else "Express" if adapter == "express" else "ERP")
    ).strip()
    workspace = str(target.get("workspace_name") or target.get("workspace_label") or "").strip()
    return " · ".join(value for value in (connection, workspace) if value)


def erp_connection_page(
    targets: list[dict], *, page: int = 0
) -> tuple[list[tuple[dict, str]], int, int]:
    """Return one LINE-safe page of selectable ERP connections."""
    ready = [target for target in targets if target.get("selectable")]
    names = [_connection_name(target)[:20] for target in ready]
    totals = {name: names.count(name) for name in set(names)}
    seen: dict[str, int] = {}
    options: list[tuple[dict, str]] = []
    for target, name in zip(ready, names, strict=True):
        seen[name] = seen.get(name, 0) + 1
        suffix = f" {seen[name]}" if totals[name] > 1 else ""
        options.append((target, name[: 20 - len(suffix)] + suffix))
    page_count = max(1, (len(options) + QR_PAGE_SIZE - 1) // QR_PAGE_SIZE)
    page = max(0, min(int(page or 0), page_count - 1))
    start = page * QR_PAGE_SIZE
    return options[start : start + QR_PAGE_SIZE], page, page_count


def _status(targets: list[dict]) -> str:
    return target_preflight.status_text({"targets": targets})


def erp_picker_message(targets: list[dict], mode: str, *, page: int = 0) -> dict:
    options, page, page_count = erp_connection_page(targets, page=page)
    items = [
        quick_reply_item(
            label,
            "target",
            mode=mode,
            endpoint=target.get("endpoint_id") or target.get("id"),
            workspace=target.get("workspace_client_id"),
        )
        for target, label in options
    ]
    if page > 0:
        items.insert(
            0,
            quick_reply_item("ก่อนหน้า", "erp-type", mode=mode, page=page - 1),
        )
    if page + 1 < page_count:
        items.append(quick_reply_item("เพิ่มเติม", "erp-type", mode=mode, page=page + 1))
    return question(
        "เลือก ERP",
        f"เลือกปลายทางสำหรับเอกสารชุดนี้\n{_status(targets)}",
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
    "erp_connection_page",
    "erp_picker_message",
    "posting_mode_message",
]
