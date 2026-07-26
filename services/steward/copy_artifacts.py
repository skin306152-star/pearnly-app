# -*- coding: utf-8 -*-
"""管家左窗产物层:工具结果 → 表格 + 已验证过的 /ai 深链(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因是体积闸(单文件 <500 行);语义边界仍是 copy —— 调用方一律走
copy.artifacts / copy.artifact_links,不直接 import 本模块。

只给真实存在的路由:查不到落点的(推送日志/识别记录在主站不在 /ai)就只给表格不编深链,
不摆一个点开是 404 的按钮(深链落空的老坑)。
"""

from __future__ import annotations

from services.steward import registry

DEFAULT_LANG = "zh"

_ARTIFACT_LABEL = {
    "matrix_link": {"zh": "打开本期矩阵", "th": "เปิดตารางงวดนี้"},
    "client_link": {"zh": "打开这家的工单", "th": "เปิดงานของลูกค้ารายนี้"},
    "attention": {"zh": "要盯的格子", "th": "ช่องที่ต้องตาม"},
    "orders": {"zh": "工单", "th": "รายการงาน"},
    "push_rows": {"zh": "推送记录", "th": "รายการที่ส่ง"},
    "history_rows": {"zh": "识别记录", "th": "เอกสารที่สแกน"},
    "clients": {"zh": "客户", "th": "ลูกค้า"},
}

_COLUMN_LABEL = {
    "name": {"zh": "客户", "th": "ลูกค้า"},
    "client_name": {"zh": "客户", "th": "ลูกค้า"},
    "obligation_code": {"zh": "义务", "th": "ภาระ"},
    "badge": {"zh": "状态", "th": "สถานะ"},
    "status": {"zh": "状态", "th": "สถานะ"},
    "current_step": {"zh": "当前步骤", "th": "ขั้นตอน"},
    "invoice_no": {"zh": "单号", "th": "เลขที่"},
    "subject": {"zh": "对象", "th": "เกี่ยวกับ"},
    "error_code": {"zh": "错误码", "th": "รหัสข้อผิดพลาด"},
    "created_at": {"zh": "时间", "th": "เวลา"},
    "filename": {"zh": "文件", "th": "ไฟล์"},
    "seller_name": {"zh": "卖方", "th": "ผู้ขาย"},
    "invoice_date": {"zh": "票面日期", "th": "วันที่ในเอกสาร"},
    "tax_id": {"zh": "税号", "th": "เลขผู้เสียภาษี"},
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def build(tool: str, data: dict, lang: str) -> list[dict]:
    """左窗产物(表格 + 深链)。写工具不产物:推完的凭证在 ERP 里,/ai 没有可去的落点。"""
    if tool == registry.MATRIX_OVERVIEW:
        out = [_link("matrix_link", "/ai#/", lang)]
        if data.get("attention"):
            out.append(
                _table("attention", data["attention"], ("name", "obligation_code", "badge"), lang)
            )
        return out
    if tool == registry.CLIENT_STATUS:
        if not data.get("client_id"):
            return []
        href = f"/ai#/client/{data['client_id']}/wo?period={data.get('period', '')}"
        return [_link("client_link", href, lang)]
    if tool == registry.WORKORDER_LIST:
        rows = data.get("orders") or []
        return (
            [_table("orders", rows, ("client_name", "status", "current_step"), lang)]
            if rows
            else []
        )
    if tool == registry.PUSH_LOG_QUERY:
        rows = data.get("rows") or []
        cols = ("created_at", "subject", "invoice_no", "status", "error_code")
        return [_table("push_rows", rows, cols, lang)] if rows else []
    if tool == registry.HISTORY_QUERY:
        rows = data.get("rows") or []
        cols = ("invoice_no", "seller_name", "invoice_date", "status")
        return [_table("history_rows", rows, cols, lang)] if rows else []
    if tool == registry.CLIENT_LOOKUP:
        rows = data.get("clients") or []
        return [_table("clients", rows, ("name", "tax_id"), lang)] if rows else []
    return []


def links(artifacts: list) -> list[dict]:
    """产物里的深链投到步骤行上(左窗步骤直接可点,不用翻产物区)。"""
    return [
        {"label": a["label"], "href": a["href"]}
        for a in artifacts
        if a.get("kind") == "deeplink" and a.get("href")
    ]


def _link(label_key: str, href: str, lang: str) -> dict:
    return {"kind": "deeplink", "label": _t(_ARTIFACT_LABEL[label_key], lang), "href": href}


def _table(label_key: str, rows: list, columns: tuple, lang: str) -> dict:
    return {
        "kind": "table",
        "label": _t(_ARTIFACT_LABEL[label_key], lang),
        "columns": [{"key": k, "label": _t(_COLUMN_LABEL.get(k, {}), lang) or k} for k in columns],
        "rows": [{k: r.get(k) for k in columns} for r in rows],
    }
