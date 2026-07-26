# -*- coding: utf-8 -*-
"""管家答复 / 步骤 / 产物的文案层(zh + th · 纯函数,零 I/O)。

为什么答复由这里确定性渲染,而不是让模型写:硬约束「模型只理解不算账」——所有数字必须
来自工具返回的确定性结果。模板只做取值和填空,不做任何计算,模型碰不到数字,物理上编不出
一个假数。模型的措辞只在两处用得上:听不懂时的解释(out_of_scope 的 message,已过
reply_guard 出口护栏)。

只写 zh + th:与前端 static/ai/ai-i18n-steward.js 同一决定(管家是事务所内部工作台入口,
照 adm-* 超管键先例先做两语,en/ja 回落 zh),对外开放再补两语——两侧同进同退,不各走各的。

体积闸(<500 行)下的三块分居:产物层在 copy_artifacts,月结产线四问 + 单票体检的文案在
copy_close,写工具 erp_push 的文案在 copy_erp_push。语义边界不变 —— 调用方一律只 import
copy,本模块按工具/错误码委派过去。
"""

from __future__ import annotations

from typing import Optional

from services.steward import copy_artifacts, copy_close, copy_erp_push, registry, store

DEFAULT_LANG = "zh"
_LANGS = ("zh", "th")

_THAI_RANGE = ("฀", "๿")

# 状态语义组(engine.STATUS_GROUPS 的组名)的人话。工单清单的答复要自证口径:
# 「2569-07:0 张工单」看不出筛没筛,与同屏矩阵的「待审 2」对不上时无从判断谁错。
_STATUS_GROUP = {
    "missing_materials": {"zh": "缺料", "th": "เอกสารไม่ครบ"},
    "in_progress": {"zh": "进行中", "th": "กำลังทำ"},
    "pending_review": {"zh": "待审", "th": "รอตรวจ"},
    "frozen": {"zh": "已冻结", "th": "ปิดงวดแล้ว"},
}

_TOOL_TITLE = {
    registry.MATRIX_OVERVIEW: {"zh": "查本期矩阵", "th": "ดูภาพรวมงวด"},
    registry.CLIENT_STATUS: {"zh": "查客户进度", "th": "ดูความคืบหน้าลูกค้า"},
    registry.WORKORDER_LIST: {"zh": "列工单", "th": "รายการงาน"},
    registry.PUSH_LOG_QUERY: {"zh": "查推送成败", "th": "ดูผลส่งเข้า ERP"},
    registry.HISTORY_QUERY: {"zh": "找识别记录", "th": "ค้นเอกสารที่สแกน"},
    registry.CLIENT_LOOKUP: {"zh": "查客户名录", "th": "ค้นรายชื่อลูกค้า"},
    registry.ERP_PUSH: {"zh": "推票进 Express", "th": "ส่งใบเข้า Express"},
    **copy_close.TITLES,
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

_TASK_ACK = {
    "zh": "收到,「{title}」开跑了。左边看得到进度,跑完我会在这里回你。",
    "th": "รับทราบค่ะ กำลังทำ「{title}」ให้อยู่ ดูความคืบหน้าได้ทางซ้าย เสร็จแล้วจะตอบในแชทนี้ค่ะ",
}

# 写工具入队的应承(confirm-first):活没开跑,先出授权卡等人批 —— 措辞不冒领「开跑了」。
_AUTHZ_ACK = {
    "zh": "「{title}」会改数,先给你出了授权卡。左边批准后我才动手,拒绝就一步都不执行。",
    "th": "「{title}」จะแก้ข้อมูล ออกการ์ดขออนุมัติให้แล้วค่ะ กดอนุมัติทางซ้ายก่อนถึงจะทำ ถ้าปฏิเสธจะไม่ทำอะไรเลย",
}
_AUTHZ_WAIT = {"zh": "等你批准", "th": "รอคุณอนุมัติ"}

# 任务级失败原因(error_code → 人话)。与工具级 _ERROR 分开:这里是"任务没跑成"
# (超时/失联/取消),那边是"工具跑了但查不出"(查无客户/多义)。
_FAIL_REASON = {
    "steward.timeout": {
        "zh": "跑了超过 {seconds} 秒还没有结果,先停了。稍后再说一次让我重跑。",
        "th": "ทำงานเกิน {seconds} วินาทีแล้วยังไม่เสร็จ ระบบหยุดให้ก่อน ลองสั่งใหม่อีกครั้งนะคะ",
    },
    "steward.worker_lost": {
        "zh": "执行中断(服务重启或异常),这条没跑完。再说一次让我重跑。",
        "th": "งานถูกขัดจังหวะ (ระบบรีสตาร์ต) ยังทำไม่เสร็จ ลองสั่งใหม่อีกครั้งนะคะ",
    },
    "steward.queue_stalled": {
        "zh": "排了很久也没开始跑(后台执行不在线),先标记失败。再说一次让我重跑。",
        "th": "รอคิวนานแต่ยังไม่ได้เริ่มทำ (ระบบประมวลผลไม่ออนไลน์) ขอบันทึกว่าล้มเหลวก่อน ลองสั่งใหม่นะคะ",
    },
    "steward.cancelled": {
        "zh": "你取消了这条任务,后面的步骤没有跑。",
        "th": "คุณยกเลิกงานนี้แล้ว ขั้นตอนที่เหลือไม่ได้ทำต่อค่ะ",
    },
    "steward.task_crashed": {
        "zh": "执行时出了意外错误,这条没跑完。再说一次让我重跑。",
        "th": "เกิดข้อผิดพลาดระหว่างทำงาน ยังทำไม่เสร็จ ลองสั่งใหม่อีกครั้งนะคะ",
    },
    "steward.context_lost": {
        "zh": "派活时的账号或权限已变更,这条没法继续跑。重新说一次即可。",
        "th": "บัญชีหรือสิทธิ์ที่ใช้สั่งงานเปลี่ยนไปแล้ว งานนี้ทำต่อไม่ได้ สั่งใหม่อีกครั้งนะคะ",
    },
    "steward.authz_rejected": {
        "zh": "这个操作被拒绝了,一步都没有执行。要做的话重新说一次、批准后才会动手。",
        "th": "คำขอนี้ถูกปฏิเสธ ยังไม่ได้ทำอะไรเลยค่ะ ถ้าต้องการทำจริง สั่งใหม่แล้วกดอนุมัติก่อนนะคะ",
    },
    "steward.budget_task_exceeded": {
        "zh": "这条任务的 AI 花费到上限了(฿{cap}),先停在这里。改小范围再试,或让管理员调高上限。",
        "th": "งานนี้ใช้ค่า AI ถึงเพดานแล้ว (฿{cap}) ขอหยุดก่อนค่ะ ลองสั่งให้แคบลง หรือให้ผู้ดูแลปรับเพดาน",
    },
    "steward.budget_session_exceeded": {
        "zh": "这个会话的 AI 花费到上限了(฿{cap}),先停在这里。开个新会话继续,或让管理员调高上限。",
        "th": "แชตนี้ใช้ค่า AI ถึงเพดานแล้ว (฿{cap}) ขอหยุดก่อนค่ะ เปิดแชตใหม่เพื่อทำต่อ หรือให้ผู้ดูแลปรับเพดาน",
    },
    "steward.budget_tenant_exceeded": {
        "zh": "整个事务所 24 小时内的 AI 花费到上限了(฿{cap}),先停在这里。稍后自动恢复,或让管理员调高上限。",
        "th": "สำนักงานใช้ค่า AI ใน 24 ชม. ถึงเพดานแล้ว (฿{cap}) ขอหยุดก่อนค่ะ รอสักพักจะใช้ได้อีก หรือให้ผู้ดูแลปรับเพดาน",
    },
}

_OUT_OF_SCOPE = {
    "zh": (
        "这个我还做不了。我能查:本期矩阵、到期义务、待审队列、某家客户进度、工单清单、应交税额、"
        "银行对账、推送成败、识别记录与单票详情、客户名录;"
        "能改的只有一件 —— 把一张已识别的票推进 Express(要你先批准)。"
    ),
    "th": (
        "เรื่องนี้ยังทำให้ไม่ได้ค่ะ ที่ค้นได้: ภาพรวมงวด · รายการใกล้ครบกำหนด · คิวรอตรวจ · "
        "ความคืบหน้าลูกค้า · รายการงาน · ยอดภาษีที่ต้องชำระ · ผลกระทบยอดธนาคาร · "
        "ผลส่งเข้า ERP · เอกสารที่สแกนและรายละเอียดใบเดี่ยว · รายชื่อลูกค้า; "
        "ที่แก้ข้อมูลได้มีอย่างเดียว — ส่งใบที่สแกนแล้วเข้า Express (ต้องให้คุณอนุมัติก่อน)"
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
        "zh": "{period}{status_filter}:{total} 张工单{breakdown}。",
        "th": "งวด {period}{status_filter}: {total} งาน{breakdown}",
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


def task_ack(title: str, lang: str) -> str:
    """入队即回的应承话:告诉会计活真派出去了、去哪看进度、结果会回到对话里。"""
    return _t(_TASK_ACK, lang).format(title=title)


def authz_ack(title: str, lang: str) -> str:
    """写工具入队的应承话:说清「卡已出、批了才动手」,不说「开跑了」(状态诚实)。"""
    return _t(_AUTHZ_ACK, lang).format(title=title)


def authz_wait(lang: str) -> str:
    """waiting_auth 步骤的 detail(左窗那行「等你批准」)。"""
    return _t(_AUTHZ_WAIT, lang)


def authz_title(tool: str, facts: dict, lang: str) -> str:
    """授权卡标题。写工具按接地事实现渲染(对哪个账套做什么、影响几条),其余回落工具名。"""
    if tool == registry.ERP_PUSH:
        return copy_erp_push.card_title(facts or {}, lang)
    return tool_title(tool, lang)


def fail_reason(
    code: str,
    lang: str,
    *,
    seconds: Optional[int] = None,
    cap: Optional[str] = None,
    tool: str = "",
) -> str:
    """任务级失败原因(超时/失联/取消/拒批/超预算)。没配文案的码走兜底句,原样带码 —— 诚实。

    tool 给了写工具时优先取写工具版:同一个「超时」,只读工具可以说"再说一次让我重跑",
    写工具说这句就是在教人双写(桥可能已经落账),必须改口成"别重推、先去查"。
    """
    spec = registry.get(tool) if tool else None
    table = copy_erp_push.FAIL_REASON.get(code) if spec and not spec.readonly else None
    table = table or _FAIL_REASON.get(code)
    if not table:
        return _t(_ERROR_FALLBACK, lang).format(code=code)
    text = _t(table, lang)
    if "{seconds}" in text:
        return text.format(seconds=seconds)
    if "{cap}" in text:
        return text.format(cap=cap)
    return text


def error(code: str, data: Optional[dict], lang: str) -> str:
    data = data or {}
    if code in copy_erp_push.ERRORS:
        return copy_erp_push.error(code, data, lang)
    table = _ERROR.get(code)
    if not table:
        return _t(_ERROR_FALLBACK, lang).format(code=code)
    names = ", ".join(c.get("name", "") for c in (data.get("candidates") or [])[:5])
    return _t(table, lang).format(
        keyword=data.get("keyword", ""), n=len(data.get("candidates") or []), names=names
    )


def reply(tool: str, data: dict, lang: str) -> str:
    """工具结果 → 一句人话。数字全部取自 data,模板不做任何计算。"""
    renderer = copy_close.REPLIES.get(tool)
    if renderer:
        return renderer(data, lang)
    if tool == registry.ERP_PUSH:
        return copy_erp_push.reply(data, lang)
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
            status_filter=status_filter(data.get("status_filter"), lang),
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


def status_filter(group: Optional[str], lang: str) -> str:
    """筛选口径 → 答复里的「 · 待审」片段。没筛返回空串,不认识的组名原样吐(诚实)。"""
    if not group:
        return ""
    table = _STATUS_GROUP.get(group)
    return " · " + (_t(table, lang) if table else group)


def order_status(status: Optional[str], lang: str) -> str:
    """工单机器态 → 人话(词表在 copy_close,产物层与答复层共用一份)。"""
    return copy_close.order_status(status, lang)


def _breakdown(counts: dict, lang: str) -> str:
    parts = [f"{order_status(k, lang)} {v}" for k, v in sorted(counts.items()) if v]
    return "(" + " · ".join(parts) + ")" if parts else ""


def artifacts(tool: str, data: dict, lang: str) -> list[dict]:
    """左窗产物(表格 + /ai 深链)· 实现在 copy_artifacts,入口留在 copy 不变。"""
    return copy_artifacts.build(tool, data, lang)


def build_steps(
    tool: str,
    lang: str,
    *,
    tool_state: str,
    detail: str = "",
    links: Optional[list] = None,
    summarize: Optional[str] = None,
) -> list[dict]:
    """三步流水:听懂 → 跑工具 → 整理答复。state 值与前端 B1 状态语言一一对应。
    请求侧(入队/追问)与 worker 侧(执行/收尾)共用同一个装配,两边不各写各的。

    summarize 缺省跟随工具步:工具还在跑 → 排队;跑完(成功或失败)→ 已完成,因为失败
    也是要组织成一句人话说出去的,那一步真做了。入队时两步都还没跑,显式传 queued。
    """
    return [
        {
            "id": "understand",
            "label": step_understand(lang),
            "state": store.STEP_DONE,
            "detail": tool_title(tool, lang),
            "links": [],
        },
        {
            "id": tool,
            "label": tool_title(tool, lang),
            "state": tool_state,
            "detail": detail,
            "links": links or [],
        },
        {
            "id": "summarize",
            "label": step_summarize(lang),
            "state": summarize
            or (store.STEP_QUEUED if tool_state == store.STEP_RUNNING else store.STEP_DONE),
            "detail": "",
            "links": [],
        },
    ]


def artifact_links(artifacts: list) -> list[dict]:
    """产物里的深链投到步骤行上(左窗步骤直接可点,不用翻产物区)。"""
    return copy_artifacts.links(artifacts)
