# -*- coding: utf-8 -*-
"""本期盘点两问的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因只有一个:体积闸(单文件 <500 行),不是语义分家 —— copy 仍是唯一
入口,tool_title / reply 按工具委派到这里。

这两句尤其容易破的两条:
  ① 模型不算账:句子里每个数都取自工具返回的 data,模板只填空,一次加法都不做;
  ② 「没有」和「零」分开说 —— 没算出税额的家数要单独报,不能混进合计里让人以为它们是 0;
     「还没推」也不能一句盖过去,失败 / 在途 / 从没推过 / 读不出票号要各说各的,因为四种的
     下一步动作完全不同(去看错误码 / 等 / 去推 / 去翻原件)。
"""

from __future__ import annotations

from services.steward import registry, tools_period
from services.workorder import push_coverage

DEFAULT_LANG = "zh"

# 税额表里一行的三态。
_TAX_STATE = {
    tools_period.TAX_READY: {"zh": "已算出", "th": "คำนวณแล้ว"},
    tools_period.TAX_NO_NUMBERS: {"zh": "还没算到", "th": "ยังคำนวณไม่ถึง"},
    tools_period.TAX_NO_ORDER: {"zh": "还没开单", "th": "ยังไม่เปิดงาน"},
}

# 一张票在这期的六态(tools_period.INVOICE_STATES)。
_INVOICE_STATE = {
    push_coverage.STATE_PUSHED: {"zh": "已推进", "th": "ส่งแล้ว"},
    push_coverage.STATE_FAILED: {"zh": "推失败", "th": "ส่งไม่สำเร็จ"},
    push_coverage.STATE_IN_FLIGHT: {"zh": "推送中", "th": "กำลังส่ง"},
    push_coverage.STATE_NEVER: {"zh": "还没推", "th": "ยังไม่ได้ส่ง"},
    tools_period.INVOICE_PENDING_REVIEW: {"zh": "待判", "th": "รอตัดสิน"},
    tools_period.INVOICE_NO_NUMBER: {"zh": "票号读不出", "th": "อ่านเลขที่ไม่ออก"},
}

_TAX_MATRIX = {
    "zh": "{period}:{ready}/{count} 家已算出税额 —— 销项税合计 ฿{output} · 进项税合计 ฿{input} · 应交合计 ฿{due}{credit}。{rest}",
    "th": "งวด {period}: คำนวณภาษีแล้ว {ready}/{count} ราย — ภาษีขายรวม ฿{output} · ภาษีซื้อรวม ฿{input} · ต้องชำระรวม ฿{due}{credit} {rest}",
}
_TAX_MATRIX_CREDIT = {
    "zh": "(留抵 {n} 家已冲抵在内)",
    "th": " (มีเครดิตยกไป {n} ราย หักรวมอยู่แล้ว)",
}
_TAX_MATRIX_REST = {
    "zh": "还没算到税额 {no_numbers} 家、还没开工单 {no_order} 家。",
    "th": "ยังคำนวณไม่ถึง {no_numbers} ราย · ยังไม่เปิดงาน {no_order} ราย",
}
_TAX_MATRIX_REST_CLEAR = {"zh": "全所都出数了。", "th": "ครบทุกรายแล้ว"}
_TAX_MATRIX_NONE_READY = {
    "zh": "{period}:{count} 家客户里还没有一家算出税额 —— 还没开工单 {no_order} 家、开了单但引擎还没跑到算税这步 {no_numbers} 家。",
    "th": "งวด {period}: ยังไม่มีรายไหนคำนวณภาษีเสร็จจาก {count} ราย — ยังไม่เปิดงาน {no_order} ราย · เปิดแล้วแต่ระบบยังทำไม่ถึงขั้นคำนวณ {no_numbers} ราย",
}
_TAX_MATRIX_EMPTY = {
    "zh": "{period}:你这边一家客户都没有。",
    "th": "งวด {period}: ยังไม่มีลูกค้าในความดูแลของคุณ",
}
_TAX_MATRIX_TRUNCATED = {
    "zh": "(表里只列了前 {n} 家,合计是全部的)",
    "th": " (ตารางแสดง {n} รายแรก ยอดรวมนับครบทุกราย)",
}

_INVOICES = {
    "zh": "{client} · {period}:进项票 {total} 张 —— 已推进 Express {pushed} 张,还差 {rest} 张{breakdown}。",
    "th": "{client} · งวด {period}: ใบกำกับซื้อ {total} ใบ — ส่งเข้า Express แล้ว {pushed} ใบ ยังเหลือ {rest} ใบ{breakdown}",
}
_INVOICES_ALL_PUSHED = {
    "zh": "{client} · {period}:进项票 {total} 张,全部推进 Express 了。",
    "th": "{client} · งวด {period}: ใบกำกับซื้อ {total} ใบ ส่งเข้า Express ครบแล้ว",
}
_INVOICES_NO_ORDER = {
    "zh": "{client} · {period}:还没开工单,这期一张票都还没收。",
    "th": "{client} · งวด {period}: ยังไม่ได้เปิดงาน จึงยังไม่มีเอกสารในงวดนี้",
}
_INVOICES_EMPTY = {
    "zh": "{client} · {period}:工单开了,但还没有一张认成进项票(资料还没到,或还没识别完)。",
    "th": "{client} · งวด {period}: เปิดงานแล้ว แต่ยังไม่มีใบไหนถูกจัดเป็นใบกำกับซื้อ (เอกสารยังไม่มา หรือยังสแกนไม่เสร็จ)",
}
_INVOICES_FILTERED_EMPTY = {
    "zh": "{client} · {period}:进项票 {total} 张,按「{filter}」筛下来一张都没有。",
    "th": "{client} · งวด {period}: ใบกำกับซื้อ {total} ใบ กรองด้วย「{filter}」แล้วไม่เหลือใบไหน",
}
_FILTER_LABEL = {
    tools_period.FILTER_NOT_PUSHED: {"zh": "还没推进去的", "th": "ที่ยังไม่ได้ส่ง"},
    tools_period.FILTER_PENDING_REVIEW: {"zh": "待判的", "th": "ที่รอตัดสิน"},
}

TITLES = {
    registry.TAX_MATRIX: {"zh": "列全所税额表", "th": "ทำตารางภาษีทุกราย"},
    registry.PERIOD_INVOICES: {"zh": "列这期的票", "th": "รายการใบกำกับในงวด"},
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def tax_state(code: str, lang: str) -> str:
    """税额行三态 → 人话。不认识的未来态原样吐机器词(诚实,不冒充已知态)。"""
    table = _TAX_STATE.get(code or "")
    return _t(table, lang) if table else (code or "")


def invoice_state(code: str, lang: str) -> str:
    table = _INVOICE_STATE.get(code or "")
    return _t(table, lang) if table else (code or "")


def tax_matrix(data: dict, lang: str) -> str:
    count = data.get("client_count", 0)
    if not count:
        return _t(_TAX_MATRIX_EMPTY, lang).format(period=data.get("period", ""))
    ready = data.get("ready", 0)
    if not ready:
        return _t(_TAX_MATRIX_NONE_READY, lang).format(
            period=data.get("period", ""),
            count=count,
            no_order=data.get("no_order", 0),
            no_numbers=data.get("no_numbers", 0),
        )
    totals = data.get("totals") or {}
    pending = data.get("no_numbers", 0) + data.get("no_order", 0)
    rest = (
        _t(_TAX_MATRIX_REST, lang).format(
            no_numbers=data.get("no_numbers", 0), no_order=data.get("no_order", 0)
        )
        if pending
        else _t(_TAX_MATRIX_REST_CLEAR, lang)
    )
    if data.get("truncated"):
        rest += _t(_TAX_MATRIX_TRUNCATED, lang).format(n=len(data.get("rows") or []))
    credit = data.get("credit", 0)
    return _t(_TAX_MATRIX, lang).format(
        period=data.get("period", ""),
        ready=ready,
        count=count,
        output=totals.get("output_vat", "-"),
        input=totals.get("input_vat", "-"),
        due=totals.get("tax_due", "-"),
        credit=_t(_TAX_MATRIX_CREDIT, lang).format(n=credit) if credit else "",
        rest=rest,
    )


def period_invoices(data: dict, lang: str) -> str:
    client, period = data.get("client_name", ""), data.get("period", "")
    if not data.get("has_order"):
        return _t(_INVOICES_NO_ORDER, lang).format(client=client, period=period)
    total = data.get("total", 0)
    if not total:
        return _t(_INVOICES_EMPTY, lang).format(client=client, period=period)
    counts = data.get("counts") or {}
    pushed = counts.get(push_coverage.STATE_PUSHED, 0)
    rest = data.get("not_pushed", 0)
    if not rest:
        return _t(_INVOICES_ALL_PUSHED, lang).format(client=client, period=period, total=total)
    if not data.get("shown"):
        return _t(_INVOICES_FILTERED_EMPTY, lang).format(
            client=client,
            period=period,
            total=total,
            filter=_t(_FILTER_LABEL.get(data.get("filter"), {}), lang) or data.get("filter", ""),
        )
    return _t(_INVOICES, lang).format(
        client=client,
        period=period,
        total=total,
        pushed=pushed,
        rest=rest,
        breakdown=_breakdown(counts, lang),
    )


def _breakdown(counts: dict, lang: str) -> str:
    """还没推的那几张各是什么情况。四种的下一步动作不同,不能合成一句「还差 N 张」。"""
    parts = [
        f"{invoice_state(state, lang)} {counts.get(state, 0)}"
        for state in tools_period.INVOICE_STATES
        if state != push_coverage.STATE_PUSHED and counts.get(state)
    ]
    return "(" + " · ".join(parts) + ")" if parts else ""


REPLIES = {
    registry.TAX_MATRIX: tax_matrix,
    registry.PERIOD_INVOICES: period_invoices,
}
