# -*- coding: utf-8 -*-
"""管家左窗产物层:工具结果 → 表格 + 已验证过的 /ai 深链(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因是体积闸(单文件 <500 行);语义边界仍是 copy —— 调用方一律走
copy.artifacts / copy.artifact_links,不直接 import 本模块。

只给真实存在的路由:查不到落点的(推送日志/识别记录在主站不在 /ai)就只给表格不编深链,
不摆一个点开是 404 的按钮(深链落空的老坑)。
"""

from __future__ import annotations

from services.steward import copy_close, registry

DEFAULT_LANG = "zh"

_ARTIFACT_LABEL = {
    "matrix_link": {"zh": "打开本期矩阵", "th": "เปิดตารางงวดนี้"},
    "client_link": {"zh": "打开这家的工单", "th": "เปิดงานของลูกค้ารายนี้"},
    "attention": {"zh": "要盯的格子", "th": "ช่องที่ต้องตาม"},
    "orders": {"zh": "工单", "th": "รายการงาน"},
    "push_rows": {"zh": "推送记录", "th": "รายการที่ส่ง"},
    "history_rows": {"zh": "识别记录", "th": "เอกสารที่สแกน"},
    "clients": {"zh": "客户", "th": "ลูกค้า"},
    "due_rows": {"zh": "还没交完的", "th": "ที่ยังไม่ได้ยื่น"},
    "queue_rows": {"zh": "等人审的工单", "th": "งานที่รอตรวจ"},
    "missing_invoice": {"zh": "缺票的流水", "th": "รายการเดินบัญชีที่ขาดใบกำกับ"},
    "push_attempts": {"zh": "这张票的推送尝试", "th": "ประวัติการส่งใบนี้"},
    "board_link": {"zh": "打开看板 · 等你审", "th": "เปิดบอร์ด · รอคุณตรวจ"},
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
    "period": {"zh": "账期", "th": "งวด"},
    "due": {"zh": "截止日", "th": "วันครบกำหนด"},
    "days_left": {"zh": "还剩", "th": "เหลือ"},
    "flagged": {"zh": "待判件", "th": "รายการที่ต้องตัดสิน"},
    "severity": {"zh": "严重度", "th": "ระดับ"},
    "tx_date": {"zh": "日期", "th": "วันที่"},
    "amount": {"zh": "金额", "th": "จำนวนเงิน"},
    "description": {"zh": "摘要", "th": "รายละเอียด"},
    "category": {"zh": "失败类型", "th": "ประเภทข้อผิดพลาด"},
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
    if tool == registry.DUE_SOON:
        rows = [_due_row(r, lang) for r in (data.get("rows") or [])]
        cols = ("client_name", "obligation_code", "due", "days_left", "badge")
        out = [_link("matrix_link", "/ai#/", lang)]
        return out + ([_table("due_rows", rows, cols, lang)] if rows else [])
    if tool == registry.REVIEW_QUEUE:
        rows = [_queue_row(r, lang) for r in (data.get("rows") or [])]
        cols = ("client_name", "period", "status", "flagged", "severity", "due")
        # 待审队列在 SPA 里的落点是看板(#/board 消费 /api/workorder/review-queue),
        # 不是另起一个 #/review —— 那个路由不存在,摆出来就是点开 404 的按钮。
        out = [_link("board_link", "/ai#/board", lang)]
        return out + ([_table("queue_rows", rows, cols, lang)] if rows else [])
    if tool == registry.TAX_NUMBERS:
        return _client_link(data, lang)
    if tool == registry.BANK_RECON_STATUS:
        rows = data.get("rows") or []
        cols = ("tx_date", "amount", "description")
        return _client_link(data, lang) + (
            [_table("missing_invoice", rows, cols, lang)] if rows else []
        )
    if tool == registry.INVOICE_DETAIL:
        rows = data.get("push_rows") or []
        cols = ("created_at", "status", "error_code", "category")
        return [_table("push_attempts", rows, cols, lang)] if rows else []
    return []


def _due_row(row: dict, lang: str) -> dict:
    """倒计时与徽章在这里就翻成人话:表格里印 -3 / missing_materials 等于让人自己解码。"""
    return {
        **row,
        "days_left": copy_close.days_left(row.get("days_left"), lang),
        "badge": copy_close.badge(row.get("badge"), lang),
    }


def _queue_row(row: dict, lang: str) -> dict:
    return {
        **row,
        "status": copy_close.order_status(row.get("status"), lang),
        "severity": copy_close.severity(row.get("severity"), lang),
    }


def _client_link(data: dict, lang: str) -> list[dict]:
    """按客户查的工具共用的落点:这家这期的工单页(没定位到客户就不摆按钮)。"""
    if not data.get("client_id"):
        return []
    href = f"/ai#/client/{data['client_id']}/wo?period={data.get('period', '')}"
    return [_link("client_link", href, lang)]


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
