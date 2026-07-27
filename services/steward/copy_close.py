# -*- coding: utf-8 -*-
"""月结产线四问 + 单票体检的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因只有一个:体积闸(单文件 <500 行),不是语义分家 —— copy.py 仍是
唯一入口,tool_title / reply 按工具委派到这里,调用方一律只 import copy。

三条与只读答复共通的硬要求,在这五句里尤其容易破:
  ① 模型不算账:所有数字取自工具返回的 data,模板只填空;
  ② 「没有」和「零」要分开说:还没开工单 / 引擎还没算 / 没收到银行流水,都不能渲染成
     「应交 0 บาท」「已对平」—— 会计据此签字,假零比说不知道危险得多;
  ③ 倒计时必须明说逾期:剩 -3 天要说成「已逾期 3 天」,不能印一个负数让人自己换算。
"""

from __future__ import annotations

from typing import Optional

from services.steward import registry

DEFAULT_LANG = "zh"

# 工单五态(services.workorder.engine.STATUS_*)的人话。答复层与产物层都要翻它,词表住在
# 叶子模块,两边各自 import —— 放在 facade(copy)里会让产物层为了一个词反向依赖入口。
_ORDER_STATUS = {
    "collecting": {"zh": "收料中", "th": "กำลังรับเอกสาร"},
    "running": {"zh": "执行中", "th": "กำลังประมวลผล"},
    "stuck": {"zh": "卡住等人", "th": "ติดขัดรอคน"},
    "review": {"zh": "待审", "th": "รอตรวจ"},
    "archive": {"zh": "已冻结", "th": "ปิดงวดแล้ว"},
}

# 矩阵徽章(services.workorder.matrix.BADGE_*)的人话。机器词只在这里翻一次。
_BADGE = {
    "missing_materials": {"zh": "缺料", "th": "เอกสารไม่ครบ"},
    "in_progress": {"zh": "进行中", "th": "กำลังทำ"},
    "pending_review": {"zh": "待审", "th": "รอตรวจ"},
    "pending_order": {"zh": "还没开单", "th": "ยังไม่เปิดงาน"},
    "not_evaluated": {"zh": "未评估", "th": "ยังไม่ประเมิน"},
}

# flagged 件严重度(services.workorder.verdict.SEV_*)。
_SEVERITY = {
    "crit": {"zh": "严重", "th": "ร้ายแรง"},
    "warn": {"zh": "提醒", "th": "เตือน"},
}

# 上传时声明的过账去向(services.erp.express_push.posting_kind)。空 = 没人声明过,
# 那正是推送被转人工的头号原因,必须说成「没声明」而不是留白。
_POSTING_KIND = {
    "service": {"zh": "服务", "th": "บริการ"},
    "stock": {"zh": "库存", "th": "สต๊อก"},
    "": {"zh": "没声明", "th": "ยังไม่ได้ระบุ"},
}

_DUE_SOON = {
    "zh": "{period}:还有 {total} 项没交完 · 已逾期 {overdue} 项 · {window} 天内到期 {soon} 项。{next}",
    "th": "งวด {period}: ยังไม่ได้ยื่น {total} รายการ · เลยกำหนด {overdue} รายการ · ครบกำหนดใน {window} วัน อีก {soon} รายการ {next}",
}
_DUE_SOON_CLEAR = {
    "zh": "{period}:没有还没交完的义务。",
    "th": "งวด {period}: ไม่มีรายการที่ค้างยื่น",
}
_DUE_NEXT = {
    "zh": "最近一项:{client} {code},{due}({left}){paper}。",
    "th": "ใกล้ที่สุด: {client} {code} วันที่ {due} ({left}){paper}",
}
# 倒计时锚的是 e-Filing 日(与矩阵页同一把尺)。纸质日已过而电子日还没到的那一周(ภ.พ.30
# 每月 16–23 号),只报电子日会让还在纸质申报的客户漏了真截止日,得点出来。
_DUE_PAPER_PASSED = {
    "zh": "(这是电子申报的日子;纸质 {paper} 已经过了)",
    "th": " (นี่คือกำหนดยื่นออนไลน์ ส่วนกำหนดยื่นกระดาษ {paper} เลยมาแล้ว)",
}
_DUE_LEFT = {
    "overdue": {"zh": "已逾期 {n} 天", "th": "เลยกำหนด {n} วัน"},
    "today": {"zh": "就是今天", "th": "ครบกำหนดวันนี้"},
    "left": {"zh": "还剩 {n} 天", "th": "เหลืออีก {n} วัน"},
    "none": {"zh": "没有截止日", "th": "ไม่มีวันครบกำหนด"},
}

_REVIEW_QUEUE = {
    "zh": "{scope}等人审的有 {orders} 张工单({clients} 家)· 要判的件 {flagged} 条{sev}。",
    "th": "{scope}รอตรวจอยู่ {orders} งาน ({clients} ราย) · รายการที่ต้องตัดสิน {flagged} รายการ{sev}",
}
_REVIEW_EMPTY = {
    "zh": "{scope}没有等人审的工单。",
    "th": "{scope}ไม่มีงานที่รอตรวจ",
}
_REVIEW_SCOPE = {"zh": "{name} · ", "th": "{name} · "}
_REVIEW_SEV = {"zh": "(只看{sev}的)", "th": " (เฉพาะระดับ{sev})"}

_TAX_NUMBERS = {
    "zh": "{client} · {period}:销项 ฿{sales} (销项税 ฿{output}) · 进项 ฿{purchase} (进项税 ฿{input}) · 应交 ฿{due}。",
    "th": "{client} · งวด {period}: ขาย ฿{sales} (ภาษีขาย ฿{output}) · ซื้อ ฿{purchase} (ภาษีซื้อ ฿{input}) · ต้องชำระ ฿{due}",
}
_TAX_NO_ORDER = {
    "zh": "{client} · {period}:还没开工单,税额还没算。",
    "th": "{client} · งวด {period}: ยังไม่ได้เปิดงาน จึงยังไม่มีตัวเลขภาษี",
}
_TAX_NO_NUMBERS = {
    "zh": "{client} · {period}:还没算到税额(工单在{status},当前 {step})。等这一步跑完再问我。",
    "th": "{client} · งวด {period}: ยังคำนวณภาษีไม่ถึง (งานอยู่ในสถานะ{status} ขั้น {step}) รอขั้นนี้เสร็จแล้วถามใหม่นะคะ",
}

_RECON = {
    "zh": "{client} · {period}:对上 {matched} 笔 · 待人审 {review} 笔 · 缺票 {missing} 笔 · 有票无流水 {unmatched} 笔 · 净差 ฿{net}。",
    "th": "{client} · งวด {period}: จับคู่ได้ {matched} · รอตรวจ {review} · ขาดใบกำกับ {missing} · มีใบแต่ไม่มีรายการเดินบัญชี {unmatched} · ผลต่างสุทธิ ฿{net}",
}
_RECON_NO_ORDER = {
    "zh": "{client} · {period}:还没开工单,银行对账还没跑。",
    "th": "{client} · งวด {period}: ยังไม่ได้เปิดงาน จึงยังไม่ได้กระทบยอดธนาคาร",
}
_RECON_NO_DATA = {
    "zh": "{client} · {period}:还没有银行对账结果 —— 没收到银行流水,或者引擎还没跑到对账这一步。",
    "th": "{client} · งวด {period}: ยังไม่มีผลกระทบยอดธนาคาร — ยังไม่ได้รับรายการเดินบัญชี หรือระบบยังทำไม่ถึงขั้นนี้",
}

_INVOICE = {
    "zh": "{invoice_no} · {seller} · ฿{amount}({date})· 过账去向 {kind}。{push}",
    "th": "{invoice_no} · {seller} · ฿{amount} ({date}) · ปลายทางการลงบัญชี {kind} {push}",
}
_PUSH_NEVER = {
    "zh": "还没推过 ERP。",
    "th": "ยังไม่เคยส่งเข้า ERP",
}
_PUSH_OK = {
    "zh": "已经推进 ERP 了({at})。",
    "th": "ส่งเข้า ERP แล้ว ({at})",
}
_PUSH_BAD = {
    "zh": "推过 {n} 次,最后一次没成({status}{code})。去「集成 · 推送日志」看这条的详情。",
    "th": "ส่งไปแล้ว {n} ครั้ง ครั้งล่าสุดไม่สำเร็จ ({status}{code}) ดูรายละเอียดที่「การเชื่อมต่อ · ประวัติการส่ง」",
}
_PUSH_KIND_HINT = {
    "zh": "上传时没选过账去向,推送多半会被转人工 —— 这张只能重新上传时选好服务/库存。",
    "th": "ตอนอัปโหลดไม่ได้เลือกปลายทางการลงบัญชี การส่งมักถูกโอนให้คนตรวจ — ใบนี้ต้องอัปโหลดใหม่แล้วเลือกบริการ/สต๊อกให้เรียบร้อย",
}

# 左窗步骤行 / 任务标题(copy._TOOL_TITLE 摊平进去,不在两处各抄一份工具名)。
TITLES = {
    registry.DUE_SOON: {"zh": "查到期义务", "th": "ดูรายการใกล้ครบกำหนด"},
    registry.REVIEW_QUEUE: {"zh": "查待审队列", "th": "ดูคิวรอตรวจ"},
    registry.TAX_NUMBERS: {"zh": "查应交税额", "th": "ดูยอดภาษีที่ต้องชำระ"},
    registry.BANK_RECON_STATUS: {"zh": "查银行对账", "th": "ดูผลกระทบยอดธนาคาร"},
    registry.INVOICE_DETAIL: {"zh": "查单票详情", "th": "ดูรายละเอียดใบนี้"},
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def order_status(status: Optional[str], lang: str) -> str:
    """工单机器态 → 人话。不认识的未来态原样吐机器词(诚实,不冒充已知态)。"""
    table = _ORDER_STATUS.get(status or "")
    return _t(table, lang) if table else (status or "")


def badge(code: Optional[str], lang: str) -> str:
    """矩阵徽章 → 人话。不认识的未来态原样吐机器词(诚实,不冒充已知态)。"""
    table = _BADGE.get(code or "")
    return _t(table, lang) if table else (code or "")


def severity(code: Optional[str], lang: str) -> str:
    table = _SEVERITY.get(code or "")
    return _t(table, lang) if table else (code or "")


def posting_kind(code: Optional[str], lang: str) -> str:
    return _t(_POSTING_KIND.get(code or "", _POSTING_KIND[""]), lang)


def days_left(value, lang: str) -> str:
    """倒计时人话。负数说成「已逾期 N 天」—— 印一个 -3 等于让会计自己换算。"""
    if not isinstance(value, int):
        return _t(_DUE_LEFT["none"], lang)
    if value < 0:
        return _t(_DUE_LEFT["overdue"], lang).format(n=-value)
    if value == 0:
        return _t(_DUE_LEFT["today"], lang)
    return _t(_DUE_LEFT["left"], lang).format(n=value)


def due_soon(data: dict, lang: str) -> str:
    rows = data.get("rows") or []
    if not data.get("total"):
        return _t(_DUE_SOON_CLEAR, lang).format(period=data.get("period", ""))
    head = rows[0] if rows else {}
    nxt = (
        _t(_DUE_NEXT, lang).format(
            client=head.get("client_name", ""),
            code=head.get("obligation_code", ""),
            due=head.get("due") or "-",
            left=days_left(head.get("days_left"), lang),
            paper=_paper_note(head, lang),
        )
        if head
        else ""
    )
    return _t(_DUE_SOON, lang).format(
        period=data.get("period", ""),
        total=data.get("total", 0),
        overdue=data.get("overdue", 0),
        window=data.get("window_days", 0),
        soon=data.get("due_soon", 0),
        next=nxt,
    )


def _paper_note(row: dict, lang: str) -> str:
    """纸质截止日已过、电子日还没到时补一句。两个日子一致(或纸质也没过)就不啰嗦。"""
    paper_left, left = row.get("days_left_paper"), row.get("days_left")
    if not isinstance(paper_left, int) or paper_left >= 0:
        return ""
    if isinstance(left, int) and left < 0:
        return ""  # 两个都过了,「已逾期」那句已经说清楚
    return _t(_DUE_PAPER_PASSED, lang).format(paper=row.get("due_paper") or "-")


def review_queue(data: dict, lang: str) -> str:
    name = data.get("client_name") or ""
    scope = _t(_REVIEW_SCOPE, lang).format(name=name) if name else ""
    if not data.get("order_count"):
        return _t(_REVIEW_EMPTY, lang).format(scope=scope)
    sev = data.get("severity") or ""
    return _t(_REVIEW_QUEUE, lang).format(
        scope=scope,
        orders=data.get("order_count", 0),
        clients=data.get("client_count", 0),
        flagged=data.get("flagged_count", 0),
        sev=_t(_REVIEW_SEV, lang).format(sev=severity(sev, lang)) if sev else "",
    )


def tax_numbers(data: dict, lang: str) -> str:
    client, period = data.get("client_name", ""), data.get("period", "")
    if not data.get("has_order"):
        return _t(_TAX_NO_ORDER, lang).format(client=client, period=period)
    if not data.get("has_numbers"):
        return _t(_TAX_NO_NUMBERS, lang).format(
            client=client,
            period=period,
            status=order_status(data.get("status"), lang),
            step=data.get("current_step") or "-",
        )
    return _t(_TAX_NUMBERS, lang).format(
        client=client,
        period=period,
        sales=data.get("sales_amount", "-"),
        output=data.get("output_vat", "-"),
        purchase=data.get("purchase_amount", "-"),
        input=data.get("input_vat", "-"),
        due=data.get("tax_due", "-"),
    )


def bank_recon_status(data: dict, lang: str) -> str:
    client, period = data.get("client_name", ""), data.get("period", "")
    if not data.get("has_order"):
        return _t(_RECON_NO_ORDER, lang).format(client=client, period=period)
    if not data.get("has_recon"):
        return _t(_RECON_NO_DATA, lang).format(client=client, period=period)
    return _t(_RECON, lang).format(
        client=client,
        period=period,
        matched=data.get("auto_matched", 0),
        review=data.get("review", 0),
        missing=data.get("missing_invoice", 0),
        unmatched=data.get("unmatched_invoice", 0),
        net=data.get("net", "0.00"),
    )


def invoice_detail(data: dict, lang: str) -> str:
    return _t(_INVOICE, lang).format(
        invoice_no=data.get("invoice_no") or data.get("filename") or "-",
        seller=data.get("seller_name") or "-",
        amount=data.get("total_amount", "0.00"),
        date=data.get("invoice_date") or "-",
        kind=posting_kind(data.get("posting_kind"), lang),
        push=_push_line(data, lang),
    )


def _push_line(data: dict, lang: str) -> str:
    """推送那一段。没推过 / 推成了 / 推失败三态各说各的,失败时把去哪看一并给出来。

    没声明过账去向的票额外补一句:重试也带不上去向(产品里补不了),只能重传 —— 不说清楚
    会计会一直点重试。
    """
    hint = "" if data.get("posting_kind") else " " + _t(_PUSH_KIND_HINT, lang)
    count = data.get("push_count") or 0
    if not count:
        return _t(_PUSH_NEVER, lang) + hint
    if (data.get("push_status") or "") == "success":
        return _t(_PUSH_OK, lang).format(at=data.get("push_at") or "-")
    code = data.get("push_error_code") or ""
    return (
        _t(_PUSH_BAD, lang).format(
            n=count,
            status=data.get("push_status") or "-",
            code=f" · {code}" if code else "",
        )
        + hint
    )


# 工具名 → 答复渲染器。copy.reply 按本表委派,加一个工具不必再往 copy.py 的分支树上加一支。
REPLIES = {
    registry.DUE_SOON: due_soon,
    registry.REVIEW_QUEUE: review_queue,
    registry.TAX_NUMBERS: tax_numbers,
    registry.BANK_RECON_STATUS: bank_recon_status,
    registry.INVOICE_DETAIL: invoice_detail,
}
