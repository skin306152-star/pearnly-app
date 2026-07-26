# -*- coding: utf-8 -*-
"""管家答复 / 步骤 / 产物的文案层(zh + th · 纯函数,零 I/O)。

为什么答复由这里确定性渲染,而不是让模型写:硬约束「模型只理解不算账」——所有数字必须
来自工具返回的确定性结果。模板只做取值和填空,不做任何计算,模型碰不到数字,物理上编不出
一个假数。模型的措辞只在两处用得上:听不懂时的解释(out_of_scope 的 message,已过
reply_guard 出口护栏)。

只写 zh + th:与前端 static/ai/ai-i18n-steward.js 同一决定(管家是事务所内部工作台入口,
照 adm-* 超管键先例先做两语,en/ja 回落 zh),对外开放再补两语——两侧同进同退,不各走各的。
"""

from __future__ import annotations

from typing import Optional

from services.steward import registry

DEFAULT_LANG = "zh"
_LANGS = ("zh", "th")

_THAI_RANGE = ("฀", "๿")

# 工单五态(services/workorder/engine.STATUS_*)的人话。机器词只在这里翻一次。
_ORDER_STATUS = {
    "collecting": {"zh": "收料中", "th": "กำลังรับเอกสาร"},
    "running": {"zh": "执行中", "th": "กำลังประมวลผล"},
    "stuck": {"zh": "卡住等人", "th": "ติดขัดรอคน"},
    "review": {"zh": "待审", "th": "รอตรวจ"},
    "archive": {"zh": "已冻结", "th": "ปิดงวดแล้ว"},
}

_TOOL_TITLE = {
    registry.MATRIX_OVERVIEW: {"zh": "查本期矩阵", "th": "ดูภาพรวมงวด"},
    registry.CLIENT_STATUS: {"zh": "查客户进度", "th": "ดูความคืบหน้าลูกค้า"},
    registry.WORKORDER_LIST: {"zh": "列工单", "th": "รายการงาน"},
    registry.PUSH_LOG_QUERY: {"zh": "查推送成败", "th": "ดูผลส่งเข้า ERP"},
    registry.HISTORY_QUERY: {"zh": "找识别记录", "th": "ค้นเอกสารที่สแกน"},
    registry.CLIENT_LOOKUP: {"zh": "查客户名录", "th": "ค้นรายชื่อลูกค้า"},
}

_STEP_UNDERSTAND = {"zh": "听懂你要什么", "th": "ทำความเข้าใจคำสั่ง"}
_STEP_SUMMARIZE = {"zh": "整理答复", "th": "เรียบเรียงคำตอบ"}

_ASK = {
    "client_name": {
        "zh": "哪一家客户?把名字说给我。",
        "th": "ลูกค้ารายไหนคะ พิมพ์ชื่อมาได้เลย",
    },
    "keyword": {
        "zh": "找哪一张?给我店名或单号。",
        "th": "หาใบไหนคะ บอกชื่อร้านหรือเลขใบเสร็จมาได้เลย",
    },
    "period": {
        "zh": "哪一期?说「上个月」或「2569-06」这样的都行。",
        "th": "งวดไหนคะ พิมพ์ว่า「เดือนที่แล้ว」หรือ「2569-06」ก็ได้",
    },
}

_OUT_OF_SCOPE = {
    "zh": "这个我还做不了。这一版我只能查:本期矩阵、某家客户进度、工单清单、推送成败、识别记录、客户名录。",
    "th": (
        "เรื่องนี้ยังทำให้ไม่ได้ค่ะ รุ่นนี้ค้นได้แค่: ภาพรวมงวด · ความคืบหน้าลูกค้า · "
        "รายการงาน · ผลส่งเข้า ERP · เอกสารที่สแกน · รายชื่อลูกค้า"
    ),
}
_DEGRADED = {
    "zh": "管家的理解服务暂时连不上,这句先没查成。你可以直接点上面的矩阵自己看,或者稍后再说一次。",
    "th": "ตอนนี้ระบบเข้าใจคำสั่งขัดข้อง ยังค้นให้ไม่ได้ค่ะ ลองกดดูที่ตารางงวดเองก่อน หรือพิมพ์ใหม่อีกครั้ง",
}
_ERROR = {
    "steward.client_not_found": {
        "zh": "名录里没有叫「{keyword}」的客户。换个说法,或者先让我列一下客户名录?",
        "th": 'ไม่พบลูกค้าชื่อ "{keyword}" ในรายชื่อ ลองพิมพ์ชื่ออื่น หรือให้ค้นรายชื่อลูกค้าให้ก่อนไหมคะ',
    },
    "steward.client_ambiguous": {
        "zh": "叫「{keyword}」的有 {n} 家:{names}。你说的是哪家?",
        "th": 'ชื่อ "{keyword}" มี {n} ราย: {names} หมายถึงรายไหนคะ',
    },
    "steward.history_forbidden": {
        "zh": "你的套餐看不了识别记录,这条查不了。",
        "th": "แพ็กเกจของคุณดูประวัติเอกสารไม่ได้ค่ะ",
    },
}
_ERROR_FALLBACK = {
    "zh": "这条没查成(错误码 {code})。再说一次,或者直接点上面的页面自己看。",
    "th": "ค้นไม่สำเร็จค่ะ (รหัส {code}) ลองพิมพ์ใหม่ หรือกดดูในหน้าจอเองก็ได้",
}

_REPLY = {
    registry.MATRIX_OVERVIEW: {
        "zh": "{period}:{client_count} 家客户 · 缺料 {missing_materials} · 待审 {pending_review} · 进行中 {in_progress} · 还没开单 {missing_order}。",
        "th": "งวด {period}: ลูกค้า {client_count} ราย · เอกสารไม่ครบ {missing_materials} · รอตรวจ {pending_review} · กำลังทำ {in_progress} · ยังไม่เปิดงาน {missing_order}",
    },
    registry.WORKORDER_LIST: {
        "zh": "{period}:{total} 张工单{breakdown}。",
        "th": "งวด {period}: {total} งาน{breakdown}",
    },
    registry.PUSH_LOG_QUERY: {
        "zh": "近 {days} 天 {total} 条推送:成功 {success} · 失败 {failed}。{note}",
        "th": "{days} วันล่าสุด ส่งไป {total} รายการ: สำเร็จ {success} · ล้มเหลว {failed} {note}",
    },
    registry.HISTORY_QUERY: {
        "zh": "「{keyword}」找到 {total} 条识别记录{shown}。",
        "th": 'ค้น "{keyword}" เจอ {total} รายการ{shown}',
    },
    registry.CLIENT_LOOKUP: {
        "zh": "「{keyword}」名录里有 {total} 家{names}。",
        "th": 'ชื่อ "{keyword}" มี {total} ราย{names}',
    },
}

_CLIENT_STATUS_WITH_ORDER = {
    "zh": "{client_name} · {period}:{status}(当前 {step}),已收 {material_count} 件料,{needs}。",
    "th": "{client_name} · งวด {period}: {status} (ขั้น {step}) รับเอกสารแล้ว {material_count} ชิ้น · {needs}",
}
_CLIENT_STATUS_NO_ORDER = {
    "zh": "{client_name} · {period}:还没开工单。",
    "th": "{client_name} · งวด {period}: ยังไม่ได้เปิดงาน",
}
_NEEDS_NONE = {"zh": "没记着缺什么", "th": "ไม่มีรายการที่ค้าง"}
_NEEDS_SOME = {"zh": "还缺 {n} 项", "th": "ยังขาด {n} รายการ"}
_TRUNCATED = {"zh": "(条数多,只统计了最近一批)", "th": "(รายการเยอะ นับเฉพาะชุดล่าสุด)"}
_SHOWN = {"zh": ",列出前 {n} 条", "th": " แสดง {n} รายการแรก"}

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


def pick_lang(text: str, hint: Optional[str] = None) -> str:
    """回复语言:前端给了 hint 就听它;没给就看这句话里有没有泰文字符(默认 zh)。

    前端目前只发 {text}(见 static/ai/ai-api-steward.js),所以必须能自己判——判据是文字
    本身,不是浏览器语言(会计在中文界面里用泰文打字是常态)。
    """
    if hint in _LANGS:
        return hint
    for ch in text or "":
        if _THAI_RANGE[0] <= ch <= _THAI_RANGE[1]:
            return "th"
    return DEFAULT_LANG


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def tool_title(tool: str, lang: str) -> str:
    return _t(_TOOL_TITLE.get(tool, {}), lang) or tool


def step_understand(lang: str) -> str:
    return _t(_STEP_UNDERSTAND, lang)


def step_summarize(lang: str) -> str:
    return _t(_STEP_SUMMARIZE, lang)


def ask(field: str, lang: str) -> str:
    return _t(_ASK.get(field, _ASK["keyword"]), lang)


def out_of_scope(lang: str) -> str:
    return _t(_OUT_OF_SCOPE, lang)


def degraded(lang: str) -> str:
    return _t(_DEGRADED, lang)


def error(code: str, data: Optional[dict], lang: str) -> str:
    data = data or {}
    table = _ERROR.get(code)
    if not table:
        return _t(_ERROR_FALLBACK, lang).format(code=code)
    names = ", ".join(c.get("name", "") for c in (data.get("candidates") or [])[:5])
    return _t(table, lang).format(
        keyword=data.get("keyword", ""), n=len(data.get("candidates") or []), names=names
    )


def reply(tool: str, data: dict, lang: str) -> str:
    """工具结果 → 一句人话。数字全部取自 data,模板不做任何计算。"""
    if tool == registry.CLIENT_STATUS:
        return _client_status_reply(data, lang)
    if tool == registry.MATRIX_OVERVIEW:
        badges = data.get("badges") or {}
        return _t(_REPLY[tool], lang).format(
            period=data.get("period", ""),
            client_count=data.get("client_count", 0),
            missing_materials=badges.get("missing_materials", 0),
            pending_review=badges.get("pending_review", 0),
            in_progress=badges.get("in_progress", 0),
            missing_order=data.get("missing_order", 0),
        )
    if tool == registry.WORKORDER_LIST:
        return _t(_REPLY[tool], lang).format(
            period=data.get("period", ""),
            total=data.get("total", 0),
            breakdown=_breakdown(data.get("counts") or {}, lang),
        )
    if tool == registry.PUSH_LOG_QUERY:
        return _t(_REPLY[tool], lang).format(
            days=data.get("days", 0),
            total=data.get("total", 0),
            success=data.get("success", 0),
            failed=data.get("failed", 0),
            note=_t(_TRUNCATED, lang) if data.get("truncated") else "",
        )
    if tool == registry.HISTORY_QUERY:
        rows = data.get("rows") or []
        shown = _t(_SHOWN, lang).format(n=len(rows)) if len(rows) < data.get("total", 0) else ""
        return _t(_REPLY[tool], lang).format(
            keyword=data.get("keyword", ""), total=data.get("total", 0), shown=shown
        )
    if tool == registry.CLIENT_LOOKUP:
        names = ", ".join(c.get("name", "") for c in (data.get("clients") or [])[:5])
        return _t(_REPLY[tool], lang).format(
            keyword=data.get("keyword", ""),
            total=data.get("total", 0),
            names=f":{names}" if names else "",
        )
    return ""


def _client_status_reply(data: dict, lang: str) -> str:
    if not data.get("has_order"):
        return _t(_CLIENT_STATUS_NO_ORDER, lang).format(
            client_name=data.get("client_name", ""), period=data.get("period", "")
        )
    needs = data.get("needs") or []
    needs_txt = _t(_NEEDS_SOME, lang).format(n=len(needs)) if needs else _t(_NEEDS_NONE, lang)
    return _t(_CLIENT_STATUS_WITH_ORDER, lang).format(
        client_name=data.get("client_name", ""),
        period=data.get("period", ""),
        status=order_status(data.get("status"), lang),
        step=data.get("current_step") or "-",
        material_count=data.get("material_count", 0),
        needs=needs_txt,
    )


def order_status(status: Optional[str], lang: str) -> str:
    """工单机器态 → 人话。不认识的未来态原样吐机器词(诚实,不冒充已知态)。"""
    table = _ORDER_STATUS.get(status or "")
    return _t(table, lang) if table else (status or "")


def _breakdown(counts: dict, lang: str) -> str:
    parts = [f"{order_status(k, lang)} {v}" for k, v in sorted(counts.items()) if v]
    return "(" + " · ".join(parts) + ")" if parts else ""


def artifacts(tool: str, data: dict, lang: str) -> list[dict]:
    """左窗产物:表格 + 已验证过的 /ai 深链(#/ 与 #/client/<id>/wo?period= 见 ai-router.js)。

    只给真实存在的路由,查不到落点的(推送日志/识别记录在主站不在 /ai)就只给表格不编深链。
    """
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


def _link(label_key: str, href: str, lang: str) -> dict:
    return {"kind": "deeplink", "label": _t(_ARTIFACT_LABEL[label_key], lang), "href": href}


def _table(label_key: str, rows: list, columns: tuple, lang: str) -> dict:
    return {
        "kind": "table",
        "label": _t(_ARTIFACT_LABEL[label_key], lang),
        "columns": [{"key": k, "label": _t(_COLUMN_LABEL.get(k, {}), lang) or k} for k in columns],
        "rows": [{k: r.get(k) for k in columns} for r in rows],
    }
