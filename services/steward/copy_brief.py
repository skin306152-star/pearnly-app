# -*- coding: utf-8 -*-
"""开工简报 / 签批闸 / 交付物清单的文案(zh + th · 纯函数,零 I/O)。

从 copy.py 分出来的原因与 copy_close 同一条:体积闸(单文件 <500 行),不是语义分家 ——
copy.py 仍是唯一入口,tool_title / reply / artifacts 按工具委派到这里。

三条在这三句上尤其容易破的线:
  ① 模型不算账:所有数字取自工具返回的 data,模板只填空;
  ② 「没有」与「零」分开说:某一路没查出来(partial)绝不渲染成 0 —— 会计会据此判"今天
     没这类活";没开工单也不能说成"交付物 0 份"(前者是没开工,后者是开了工没出包);
  ③ 判据逐条给理由:签批闸每一项都要说清楚为什么没过,不出"看着差不多了"这种综合评价。
"""

from __future__ import annotations

from services.steward import copy_close, registry, tools_brief, tools_signoff

DEFAULT_LANG = "zh"

# 待办类型(tools_brief.KIND_*)的人话。
_KIND = {
    tools_brief.KIND_OVERDUE: {"zh": "逾期", "th": "เลยกำหนด"},
    tools_brief.KIND_DUE_SOON: {"zh": "快到期", "th": "ใกล้ครบกำหนด"},
    tools_brief.KIND_PUSH_FAILED: {"zh": "推失败", "th": "ส่งไม่สำเร็จ"},
    tools_brief.KIND_REVIEW: {"zh": "等你审", "th": "รอคุณตรวจ"},
}

# 三路取数各自的人话名(某一路挂了要说得出是哪一路,不含糊说"部分数据缺失")。
_LANE = {
    "due_soon": {"zh": "到期义务", "th": "รายการใกล้ครบกำหนด"},
    "review_queue": {"zh": "待审队列", "th": "คิวรอตรวจ"},
    "push_log_query": {"zh": "推送日志", "th": "ประวัติการส่ง"},
}

# 签批五项(tools_signoff.CHECK_*)的人话。
_CHECK = {
    tools_signoff.CHECK_NUMBERS: {"zh": "税额", "th": "ยอดภาษี"},
    tools_signoff.CHECK_BANK: {"zh": "银行对账", "th": "กระทบยอดธนาคาร"},
    tools_signoff.CHECK_FLAGGED: {"zh": "待判件", "th": "รายการที่ต้องตัดสิน"},
    tools_signoff.CHECK_DELIVERABLES: {"zh": "交付包", "th": "ชุดส่งมอบ"},
    tools_signoff.CHECK_SIGNOFF: {"zh": "签批", "th": "การอนุมัติ"},
}
_STATE = {
    tools_signoff.STATE_OK: {"zh": "过", "th": "ผ่าน"},
    tools_signoff.STATE_BLOCKED: {"zh": "没过", "th": "ไม่ผ่าน"},
    # 「不知道」是第三态而不是"没过":没收到银行流水的客户不该被判成不合格。
    tools_signoff.STATE_UNKNOWN: {"zh": "不知道", "th": "ยังไม่ทราบ"},
}
_REASON = {
    "computed": {"zh": "已算出应交税额", "th": "คำนวณภาษีที่ต้องชำระแล้ว"},
    "not_computed": {"zh": "引擎还没算到税额", "th": "ระบบยังคำนวณภาษีไม่ถึง"},
    "balanced": {"zh": "没有待清的笔", "th": "ไม่มีรายการค้าง"},
    "outstanding": {
        "zh": "还有 {n} 笔缺票或待人审",
        "th": "ยังมี {n} รายการที่ขาดใบกำกับหรือรอตรวจ",
    },
    "no_recon": {
        "zh": "还没有对账结果(没收到流水,或引擎还没跑到这一步)",
        "th": "ยังไม่มีผลกระทบยอด (ยังไม่ได้รับรายการเดินบัญชี หรือระบบยังทำไม่ถึงขั้นนี้)",
    },
    "clear": {"zh": "没有待判件", "th": "ไม่มีรายการที่ต้องตัดสิน"},
    "pending": {"zh": "还有 {n} 件等人判", "th": "ยังมี {n} รายการรอตัดสิน"},
    "packaged": {"zh": "已出 {n} 份", "th": "ออกแล้ว {n} รายการ"},
    "not_packaged": {"zh": "交付包还没出", "th": "ยังไม่ได้ออกชุดส่งมอบ"},
    "signed": {"zh": "已签批", "th": "อนุมัติแล้ว"},
    "unsigned": {"zh": "还没人签", "th": "ยังไม่มีใครอนุมัติ"},
    "stale": {
        "zh": "签过之后引擎又重跑了,要重签",
        "th": "อนุมัติแล้วแต่ระบบรันใหม่อีกครั้ง ต้องอนุมัติซ้ำ",
    },
}

# 交付物 kind → 人话。routes/workorder_financials_routes.py 另有一份泰文版,那份只管下载
# 文件名(泰文单语是那条路由的既定口径),两处刻意不合并:合并会把管家的两语需求压进一个
# 只需要一语的地方。表外的 kind 原样吐机器名(诚实,不冒充已知件)。
_DELIVERABLE = {
    "pp30_draft": {"zh": "ภ.พ.30 草稿", "th": "แบบร่าง ภ.พ.30"},
    "pnd3_prep_txt": {"zh": "ภ.ง.ด.3 申报文件", "th": "ไฟล์ยื่น ภ.ง.ด.3"},
    "pnd3_keying_xlsx": {"zh": "ภ.ง.ด.3 键入表", "th": "ตารางคีย์ ภ.ง.ด.3"},
    "pnd53_prep_txt": {"zh": "ภ.ง.ด.53 申报文件", "th": "ไฟล์ยื่น ภ.ง.ด.53"},
    "pnd53_keying_xlsx": {"zh": "ภ.ง.ด.53 键入表", "th": "ตารางคีย์ ภ.ง.ด.53"},
    "financials_report": {"zh": "月度报表", "th": "งบการเงิน"},
    "ledger_workpaper": {"zh": "进销底稿", "th": "ใบงานประกอบบัญชี"},
    "bank_workpaper": {"zh": "银行材料清单", "th": "เอกสารธนาคาร"},
    "shadow_workpaper": {"zh": "影子底稿", "th": "ใบงานร่างบัญชีคู่"},
    "missing_doc_memo": {"zh": "缺件备忘", "th": "บันทึกเอกสารที่ขาด"},
    "evidence_index": {"zh": "证据索引", "th": "ดัชนีหลักฐาน"},
    "entries_export": {"zh": "Express 分录", "th": "รายการบัญชี Express"},
}
_FILE_READY = {"zh": "可下载", "th": "ดาวน์โหลดได้"}
_FILE_PENDING = {"zh": "还没出文件", "th": "ยังไม่มีไฟล์"}

_BRIEF = {
    "zh": "{period} · 今天要盯的:逾期 {overdue} 项 · {window} 天内到期 {soon} 项 · 等你审 {orders} 张工单({flagged} 件待判) · 近 {pdays} 天{pscope}推失败 {failed} 条 · 缺料 {missing} 家。{top}{note}",
    "th": "งวด {period} · วันนี้ต้องตามอะไรบ้าง: เลยกำหนด {overdue} รายการ · ครบกำหนดใน {window} วัน {soon} รายการ · รอคุณตรวจ {orders} งาน ({flagged} รายการที่ต้องตัดสิน) · ส่งไม่สำเร็จ{pscope}ใน {pdays} วันล่าสุด {failed} รายการ · เอกสารไม่ครบ {missing} ราย {top}{note}",
}
# 推失败只数得到本人推的(tools_brief.PUSH_SCOPE_SELF),与另外三个数不同轴 —— 不加这半句,
# 同事替同一批客户推失败的票会被这句话说成"不存在"。
_BRIEF_PUSH_SELF = {"zh": "你自己", "th": "ของคุณเอง"}
_BRIEF_CLEAR = {
    "zh": "{period}:今天没有逾期的、没有等你审的、{pscope}也没有推失败的。{note}",
    "th": "งวด {period}: วันนี้ไม่มีรายการเลยกำหนด ไม่มีงานรอตรวจ และไม่มีรายการส่งไม่สำเร็จ{pscope} {note}",
}
# 有一路没查出来时,「今天没活」这句话是假的:那一路的活恰好被算成了 0,而会计读到的第一句
# 就是"今天没这类活"。清净日与降级同时成立时只说得起这一句。
_BRIEF_CLEAR_PARTIAL = {
    "zh": "{period}:查得到的这几路今天没活,「{lanes}」没查出来 —— 这部分有没有活我说不了。{note}",
    "th": "งวด {period}: เท่าที่ดึงข้อมูลได้ วันนี้ไม่มีงานค้าง แต่ดึง「{lanes}」ไม่สำเร็จ จึงยังบอกไม่ได้ว่าส่วนนี้มีงานหรือไม่ {note}",
}
_BRIEF_TOP = {"zh": "最紧的一条:{line}。", "th": "เร่งที่สุด: {line}"}
_BRIEF_PARTIAL = {
    "zh": "(「{lanes}」这一路没查出来,上面的数少了这部分。)",
    "th": "(ดึงข้อมูล「{lanes}」ไม่สำเร็จ ตัวเลขด้านบนจึงยังไม่รวมส่วนนี้)",
}
_BRIEF_TRUNCATED = {
    "zh": "(到期项多,只数了最紧的一批。)",
    "th": "(รายการครบกำหนดเยอะ นับเฉพาะชุดที่เร่งที่สุด)",
}
_BRIEF_LINE = {"zh": "{client} {detail}({when})", "th": "{client} {detail} ({when})"}
_BRIEF_LINE_PLAIN = {"zh": "{client} {detail}", "th": "{client} {detail}"}
_BRIEF_FLAGGED_N = {"zh": "{n} 件待判", "th": "{n} รายการรอตัดสิน"}

_READY = {
    "not_started": {
        "zh": "{client} · {period}:还没开工单,谈不上签批。",
        "th": "{client} · งวด {period}: ยังไม่ได้เปิดงาน จึงยังไม่ถึงขั้นอนุมัติ",
    },
    "signed": {
        "zh": "{client} · {period}:已经签批了({actor} · {at})。",
        "th": "{client} · งวด {period}: อนุมัติแล้ว ({actor} · {at})",
    },
    "resign_needed": {
        "zh": "{client} · {period}:签过了,但之后引擎又重跑过,数字已经重生成 —— 要再签一次。",
        "th": "{client} · งวด {period}: เคยอนุมัติแล้ว แต่ระบบรันใหม่อีกครั้ง ตัวเลขถูกสร้างใหม่ — ต้องอนุมัติซ้ำ",
    },
    "ready": {
        "zh": "{client} · {period}:四项前置都过了,可以签批。",
        "th": "{client} · งวด {period}: เงื่อนไขก่อนอนุมัติผ่านครบทั้ง 4 ข้อ อนุมัติได้เลย",
    },
    "blocked": {
        "zh": "{client} · {period}:还不能签,差 {n} 项 —— {items}。",
        "th": "{client} · งวด {period}: ยังอนุมัติไม่ได้ ขาดอยู่ {n} ข้อ — {items}",
    },
}

_DELIVERABLES = {
    "zh": "{client} · {period}:交付物 {total} 份,{ready} 份可以下载{pending}。",
    "th": "{client} · งวด {period}: ชุดส่งมอบ {total} รายการ ดาวน์โหลดได้ {ready} รายการ{pending}",
}
_DELIVERABLES_PENDING = {"zh": ",{n} 份还没出文件", "th": " ยังไม่มีไฟล์อีก {n} รายการ"}
_DELIVERABLES_NO_ORDER = {
    "zh": "{client} · {period}:还没开工单,交付物一份都没有。",
    "th": "{client} · งวด {period}: ยังไม่ได้เปิดงาน จึงยังไม่มีชุดส่งมอบ",
}
_DELIVERABLES_EMPTY = {
    "zh": "{client} · {period}:交付包还没出(引擎还没跑到出包这一步)。",
    "th": "{client} · งวด {period}: ยังไม่ได้ออกชุดส่งมอบ (ระบบยังทำไม่ถึงขั้นออกชุด)",
}

# 左窗步骤行 / 任务标题(copy._TOOL_TITLE 摊平进去,不在两处各抄一份工具名)。
TITLES = {
    registry.TODAY_BRIEF: {"zh": "整理今天的活", "th": "สรุปงานวันนี้"},
    registry.CLOSE_READINESS: {"zh": "查能不能签批", "th": "ตรวจว่าอนุมัติได้หรือยัง"},
    registry.DELIVERABLES_LIST: {"zh": "查交付物", "th": "ดูชุดส่งมอบ"},
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or ""


def kind(code: str, lang: str) -> str:
    table = _KIND.get(code or "")
    return _t(table, lang) if table else (code or "")


def check(code: str, lang: str) -> str:
    table = _CHECK.get(code or "")
    return _t(table, lang) if table else (code or "")


def state(code: str, lang: str) -> str:
    table = _STATE.get(code or "")
    return _t(table, lang) if table else (code or "")


def reason(code: str, n, lang: str) -> str:
    """未过原因。带 {n} 的模板才填数,数由工具算好带过来(模板不做任何计算)。"""
    table = _REASON.get(code or "")
    if not table:
        return code or ""
    text = _t(table, lang)
    return text.format(n=n) if "{n}" in text else text


def deliverable(code: str, lang: str) -> str:
    table = _DELIVERABLE.get(code or "")
    return _t(table, lang) if table else (code or "")


# ── today_brief ──────────────────────────────────────────────


def today_brief(data: dict, lang: str) -> str:
    counts = data.get("counts") or {}
    lanes = _lane_names(data, lang)
    truncated = _t(_BRIEF_TRUNCATED, lang) if data.get("truncated") else ""
    period = data.get("period", "")
    if not data.get("total") and not any(counts.values()):
        if lanes:
            return (
                _t(_BRIEF_CLEAR_PARTIAL, lang)
                .format(period=period, lanes="、".join(lanes), note=truncated)
                .strip()
            )
        return (
            _t(_BRIEF_CLEAR, lang)
            .format(period=period, pscope=_push_scope(data, lang), note=truncated)
            .strip()
        )
    partial = _t(_BRIEF_PARTIAL, lang).format(lanes="、".join(lanes)) if lanes else ""
    rows = data.get("rows") or []
    top = _t(_BRIEF_TOP, lang).format(line=_brief_line(rows[0], lang)) if rows else ""
    return _t(_BRIEF, lang).format(
        period=period,
        overdue=counts.get("overdue", 0),
        window=data.get("window_days", 0),
        soon=counts.get("due_soon", 0),
        orders=counts.get("review_orders", 0),
        flagged=counts.get("review_flagged", 0),
        pdays=data.get("push_days", 0),
        pscope=_push_scope(data, lang),
        failed=counts.get("push_failed", 0),
        missing=counts.get("missing_materials", 0),
        top=top,
        note=partial + truncated,
    )


def _lane_names(data: dict, lang: str) -> list[str]:
    """没查出来的那几路叫什么。缺了就点名,不含糊说"部分数据缺失"。"""
    return [_t(_LANE.get(k, {}), lang) or k for k in data.get("partial") or []]


def _push_scope(data: dict, lang: str) -> str:
    """推失败那个数的作用域限定语(本人推的 vs 全部)。别处的三个数按账套算,不带这半句。"""
    if data.get("push_scope") != tools_brief.PUSH_SCOPE_SELF:
        return ""
    return _t(_BRIEF_PUSH_SELF, lang)


def _brief_line(row: dict, lang: str) -> str:
    when = (
        copy_close.days_left(row.get("days_left"), lang) if row.get("days_left") is not None else ""
    )
    detail = brief_detail(row, lang)
    table = _BRIEF_LINE if when else _BRIEF_LINE_PLAIN
    return (
        _t(table, lang)
        .format(client=row.get("client_name") or "-", detail=detail, when=when)
        .strip()
    )


def brief_detail(row: dict, lang: str) -> str:
    """一条待办的「事由」格:义务码 / 票号 / 待判件数。都由工具给的机器字段现拼。"""
    if row.get("kind") == tools_brief.KIND_REVIEW:
        return _t(_BRIEF_FLAGGED_N, lang).format(n=row.get("n") or 0)
    return row.get("subject") or ""


def brief_row(row: dict, lang: str) -> dict:
    """左窗表格的一行(机器码全翻成人话,表里不印 overdue / -3 这种要人解码的东西)。"""
    return {
        "kind": kind(row.get("kind") or "", lang),
        "client_name": row.get("client_name") or "",
        "detail": brief_detail(row, lang),
        "when": (
            copy_close.days_left(row.get("days_left"), lang)
            if row.get("days_left") is not None
            else ""
        ),
    }


# ── close_readiness ──────────────────────────────────────────


def close_readiness(data: dict, lang: str) -> str:
    verdict = data.get("verdict") or "blocked"
    table = _READY.get(verdict) or _READY["blocked"]
    return _t(table, lang).format(
        client=data.get("client_name", ""),
        period=data.get("period", ""),
        actor=data.get("signoff_actor") or "-",
        at=data.get("signoff_at") or "-",
        n=data.get("blocking", 0),
        items="、".join(_blocking_items(data, lang)),
    )


def _blocking_items(data: dict, lang: str) -> list[str]:
    """没过那几项的短说明。逐项来自 checks 的 reason 码,不做归纳总结。"""
    return [
        reason(c.get("reason") or "", c.get("n"), lang)
        for c in data.get("checks") or []
        if c.get("check") != tools_signoff.CHECK_SIGNOFF
        and c.get("state") != tools_signoff.STATE_OK
    ]


def check_row(row: dict, lang: str) -> dict:
    """左窗表格的一行。列键 result 而非 state:产物层的列标签表是全工具共用的一张,
    state 已被本期盘点两问占着(那边是"情况"),同名会让两处的表头互相覆盖。"""
    return {
        "check": check(row.get("check") or "", lang),
        "result": state(row.get("state") or "", lang),
        "reason": reason(row.get("reason") or "", row.get("n"), lang),
    }


# ── deliverables_list ────────────────────────────────────────


def deliverables_list(data: dict, lang: str) -> str:
    client, period = data.get("client_name", ""), data.get("period", "")
    if not data.get("has_order"):
        return _t(_DELIVERABLES_NO_ORDER, lang).format(client=client, period=period)
    if not data.get("total"):
        return _t(_DELIVERABLES_EMPTY, lang).format(client=client, period=period)
    pending = data.get("pending") or 0
    return _t(_DELIVERABLES, lang).format(
        client=client,
        period=period,
        total=data.get("total", 0),
        ready=data.get("ready", 0),
        pending=_t(_DELIVERABLES_PENDING, lang).format(n=pending) if pending else "",
    )


def deliverable_row(row: dict, lang: str) -> dict:
    return {
        "deliverable": deliverable(row.get("kind") or "", lang),
        "file": _t(_FILE_READY if row.get("has_file") else _FILE_PENDING, lang),
    }


# 工具名 → 答复渲染器。copy.reply 按本表委派。
REPLIES = {
    registry.TODAY_BRIEF: today_brief,
    registry.CLOSE_READINESS: close_readiness,
    registry.DELIVERABLES_LIST: deliverables_list,
}
