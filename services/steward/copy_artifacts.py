# -*- coding: utf-8 -*-
"""管家左窗产物层:工具结果 → 表格 + 已验证过的 /ai 深链(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因是体积闸(单文件 <500 行);语义边界仍是 copy —— 调用方一律走
copy.artifacts / copy.artifact_links,不直接 import 本模块。

只给真实存在的路由:查不到落点的(推送日志/识别记录在主站不在 /ai)就只给表格不编深链,
不摆一个点开是 404 的按钮(深链落空的老坑)。
"""

from __future__ import annotations

from services.steward import (
    copy_brief,
    copy_calc,
    copy_close,
    copy_doc,
    copy_file,
    copy_period,
    copy_table,
    registry,
)
from services.steward.copy_lang import t as _t

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
    "vat_breakdown": {"zh": "拆解", "th": "รายละเอียดการคำนวณ"},
    "today_rows": {"zh": "最紧的几条", "th": "รายการที่เร่งที่สุด"},
    "checks": {"zh": "签批前五项", "th": "5 ข้อก่อนอนุมัติ"},
    "deliverables": {"zh": "交付物", "th": "ชุดส่งมอบ"},
    "tax_rows": {"zh": "全所税额表", "th": "ตารางภาษีทุกราย"},
    "invoice_rows": {"zh": "这期的进项票", "th": "ใบกำกับซื้อในงวดนี้"},
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
    "item": {"zh": "项目", "th": "รายการ"},
    "sales_amount": {"zh": "销项", "th": "ยอดขาย"},
    "output_vat": {"zh": "销项税", "th": "ภาษีขาย"},
    "purchase_amount": {"zh": "进项", "th": "ยอดซื้อ"},
    "input_vat": {"zh": "进项税", "th": "ภาษีซื้อ"},
    "tax_due": {"zh": "应交", "th": "ต้องชำระ"},
    "state": {"zh": "情况", "th": "สถานะ"},
    "vendor": {"zh": "卖方", "th": "ผู้ขาย"},
    "kind": {"zh": "类型", "th": "ประเภท"},
    "detail": {"zh": "事由", "th": "เรื่อง"},
    "when": {"zh": "期限", "th": "กำหนด"},
    "check": {"zh": "项目", "th": "รายการ"},
    "result": {"zh": "结果", "th": "ผล"},
    "reason": {"zh": "说明", "th": "รายละเอียด"},
    "deliverable": {"zh": "报表", "th": "รายงาน"},
    "file": {"zh": "文件", "th": "ไฟล์"},
}


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
    if tool == registry.TAX_MATRIX:
        rows = [_tax_row(r, lang) for r in (data.get("rows") or [])]
        cols = (
            "client_name",
            "sales_amount",
            "output_vat",
            "purchase_amount",
            "input_vat",
            "tax_due",
            "state",
        )
        out = [_link("matrix_link", "/ai#/", lang)]
        return out + ([_table("tax_rows", rows, cols, lang)] if rows else [])
    if tool == registry.PERIOD_INVOICES:
        rows = [_invoice_row(r, lang) for r in (data.get("rows") or [])]
        cols = ("invoice_no", "vendor", "invoice_date", "amount", "state")
        return _client_link(data, lang) + (
            [_table("invoice_rows", rows, cols, lang)] if rows else []
        )
    if tool == registry.VAT_CALC:
        # 算账没有可去的落点(数不在任何页面上),只给拆解表 —— 摆一个深链就是摆个 404。
        rows = copy_calc.breakdown_rows(data, lang)
        return [_table("vat_breakdown", rows, ("item", "amount"), lang)]
    if tool == registry.INVOICE_DETAIL:
        rows = data.get("push_rows") or []
        cols = ("created_at", "status", "error_code", "category")
        return [_table("push_attempts", rows, cols, lang)] if rows else []
    if tool == registry.TODAY_BRIEF:
        rows = [copy_brief.brief_row(r, lang) for r in (data.get("rows") or [])]
        cols = ("kind", "client_name", "detail", "when")
        # 两个落点各管一半:矩阵看到期,看板看等你审。简报的行动横跨两屏,给一个会指错路。
        out = [_link("matrix_link", "/ai#/", lang), _link("board_link", "/ai#/board", lang)]
        return out + ([_table("today_rows", rows, cols, lang)] if rows else [])
    if tool == registry.CLOSE_READINESS:
        rows = [copy_brief.check_row(r, lang) for r in (data.get("checks") or [])]
        cols = ("check", "result", "reason")
        return _client_link(data, lang) + ([_table("checks", rows, cols, lang)] if rows else [])
    if tool == registry.DELIVERABLES_LIST:
        return _deliverables(data, lang)
    # 两只 S2 工具各有自己的产物形状(引用表 / 预览表+下载链),必须在下面这条通用
    # ATTACHMENT_TOOLS 兜底之前拦下来——否则会被 copy_file.artifacts 接管,而那边只认
    # file_convert/vat_report_check 两个名字,对其余名字一律返回空产物(静默丢产物)。
    if tool == registry.DOC_READ_QA:
        return copy_doc.artifacts(data, lang)
    if tool == registry.TABLE_GENERATE:
        return copy_table.artifacts(data, lang)
    if tool in registry.ATTACHMENT_TOOLS:
        return copy_file.artifacts(tool, data, lang)
    return []


def _deliverables(data: dict, lang: str) -> list[dict]:
    """交付物:一张清单表 + 每份已出文件一个下载链。

    下载链只能各自成一条产物 —— 表格单元格是纯文本(ai-steward-render.js 的 tableHtml
    只 esc 值,不渲染链接),把 URL 塞进格子只会印出一串裸地址。
    """
    rows = data.get("rows") or []
    out = _client_link(data, lang)
    if rows:
        table_rows = [copy_brief.deliverable_row(r, lang) for r in rows]
        out.append(_table("deliverables", table_rows, ("deliverable", "file"), lang))
    out.extend(
        {
            "kind": "deeplink",
            "label": copy_brief.deliverable(r.get("kind") or "", lang),
            "href": r["href"],
        }
        for r in rows
        if r.get("has_file") and r.get("href")
    )
    return out


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


def _tax_row(row: dict, lang: str) -> dict:
    """机器态在这里就翻成人话:表格里印 no_numbers 等于让人自己解码。"""
    return {**row, "state": copy_period.tax_state(row.get("state"), lang)}


def _invoice_row(row: dict, lang: str) -> dict:
    return {**row, "state": copy_period.invoice_state(row.get("state"), lang)}


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
