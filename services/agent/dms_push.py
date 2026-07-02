# -*- coding: utf-8 -*-
"""LINE 拍身份证 → 建 DMS 客户(LINE-DMS-PUSH-DESIGN · 2026-07-02)。

三段:handle_id_card(意图=dms 的图到 → 专用身份证 OCR → 必填校验 → 存检查点 + 复述)、
execute_confirmed(用户回"确认" → 网页同一函数建客户 → erp_push_logs trigger=line_dms)、
cancel(回"取消" → 一句回执)。确认判定在 confirm_machine(确定性词表,大脑不参与)。
v1 只 create:重复证号 DMS 侧会拒,人话引导去网页处理;不建订车单(与网页范围对齐)。
"""

from __future__ import annotations

import json
import logging

from core import db
from services.erp import dms_id_ocr

logger = logging.getLogger("mr-pilot")

TOOL = "dms_push"

_NO_ENDPOINT = {
    "th": "ยังไม่ได้เชื่อมต่อ MR.ERP DMS ค่ะ ไปที่เว็บ Pearnly > การเชื่อมต่อ เพื่อเพิ่มปลายทาง DMS ก่อนนะคะ",
    "zh": "还没有连接 MR.ERP DMS,请先到网页「集成」里添加 DMS 端点。",
    "en": "MR.ERP DMS isn't connected yet — add a DMS endpoint under Integrations on the web first.",
    "ja": "MR.ERP DMS がまだ接続されていません。ウェブの「連携」から DMS を追加してください。",
}
_NO_BALANCE = {
    "th": "ยอดเงินคงเหลือไม่พอสำหรับสแกนบัตรค่ะ เติมเงินบนเว็บก่อนนะคะ",
    "zh": "余额不足,暂时无法识别身份证,请先到网页充值。",
    "en": "Insufficient balance for the ID scan — please top up on the web first.",
    "ja": "残高不足のためスキャンできません。ウェブでチャージしてください。",
}
_UNREADABLE = {
    "th": "อ่านบัตรไม่ชัดค่ะ (ขาด: {fields}) ถ่ายด้านหน้าบัตรให้ชัด ๆ แล้วส่งใหม่นะคะ",
    "zh": "身份证读不清(缺:{fields}),请拍清晰的正面照再发一次。",
    "en": "Couldn't read the ID card (missing: {fields}) — retake a clear photo of the front and resend.",
    "ja": "カードが読み取れません(不足:{fields})。表面を鮮明に撮り直して再送してください。",
}
_FAILED = {
    "th": "ระบบอ่านบัตรมีปัญหาชั่วคราวค่ะ ลองใหม่อีกครั้งนะคะ",
    "zh": "身份证识别暂时出了点问题,请稍后再试。",
    "en": "The ID scan hit a temporary problem — please try again.",
    "ja": "スキャンに一時的な問題が発生しました。もう一度お試しください。",
}
_RESTATE = {
    "th": "จะสร้างลูกค้า DMS: {name} · เลขบัตรลงท้าย {tail}\nพิมพ์ 'ยืนยัน' เพื่อดำเนินการ หรือ 'ยกเลิก' (ภายใน 15 นาที)",
    "zh": "将建 DMS 客户:{name}·证号尾4 {tail}\n回「确认」执行,回「取消」放弃(15 分钟内有效)。",
    "en": "About to create DMS customer: {name} · ID ending {tail}\nReply 'confirm' to proceed or 'cancel' (valid 15 min).",
    "ja": "DMS 顧客を作成します:{name} · 番号末尾 {tail}\n「確認」で実行、「キャンセル」で中止(15分以内)。",
}
_RUNNING = {
    "th": "⏳ กำลังสร้างลูกค้า DMS...",
    "zh": "⏳ 正在建 DMS 客户…",
    "en": "⏳ Creating the DMS customer…",
    "ja": "⏳ DMS 顧客を作成しています…",
}
_DONE_OK = {
    "th": "✅ สร้างลูกค้า DMS แล้ว: {name}",
    "zh": "✅ DMS 客户已建好:{name}",
    "en": "✅ DMS customer created: {name}",
    "ja": "✅ DMS 顧客を作成しました:{name}",
}
_DONE_FAIL = {
    "th": "❌ สร้างลูกค้า DMS ไม่สำเร็จ: {reason} · จัดการต่อได้บนเว็บ Pearnly นะคะ",
    "zh": "❌ DMS 客户没建成:{reason}·可到网页 Pearnly 继续处理。",
    "en": "❌ Couldn't create the DMS customer: {reason} · you can finish it on the Pearnly web.",
    "ja": "❌ DMS 顧客を作成できませんでした:{reason} · ウェブで続きを処理できます。",
}
_CANCELLED = {
    "th": "ยกเลิกแล้วค่ะ ไม่ได้สร้างลูกค้า DMS นะคะ",
    "zh": "已取消,没有建 DMS 客户。",
    "en": "Cancelled — no DMS customer was created.",
    "ja": "キャンセルしました。DMS 顧客は作成していません。",
}
# 必填字段的人话名(与网页面板同两项:证号+姓名)。
_FIELD_NAMES = {
    "people_id": {"th": "เลขบัตร", "zh": "证号", "en": "ID number", "ja": "番号"},
    "name": {"th": "ชื่อ-นามสกุล", "zh": "姓名", "en": "name", "ja": "氏名"},
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def _notify(line_user_id, tid, text, quote_token=None) -> None:
    from services.line_binding import line_reply

    line_reply.push_text_context(line_user_id, text, quote_token=quote_token or "", tenant_id=tid)


def _note(line_user_id, tid, bot_text) -> None:
    from services.line_binding import line_chat_memory

    line_chat_memory.note(
        line_user_id=line_user_id, tenant_id=tid, role="user", content="[ส่งรูปบัตรประชาชน]"
    )
    line_chat_memory.note(line_user_id=line_user_id, tenant_id=tid, role="bot", content=bot_text)


def wants_dms(intent) -> bool:
    """待决意图是不是"下一张进 DMS"。"""
    return isinstance(intent, dict) and "dms" in (intent.get("goals") or [])


def handle_id_card(user, tid, line_user_id, lang, file_bytes, filename, quote_token) -> bool:
    """意图=dms 的图到:专用身份证 OCR(绕过费用管线,按 1 页计)→ 必填校验 →
    存检查点 + 复述。恒返 True=本图已处理(含所有失败分支的人话回执)。
    同步重活——调用方 asyncio.to_thread。"""
    try:
        ep, ocr, _ = dms_id_ocr.recognize_id_card(user, file_bytes, filename)
    except dms_id_ocr.DmsOcrError as e:
        if e.code == "dms.no_endpoint":
            msg = _t(_NO_ENDPOINT, lang)
        elif e.code == "insufficient_balance":
            msg = _t(_NO_BALANCE, lang)
        elif e.code == "ocr.id_card_unreadable":
            msg = _t(_UNREADABLE, lang).format(fields=_field_names(["people_id", "name"], lang))
        else:
            msg = _t(_FAILED, lang)
        _notify(line_user_id, tid, msg, quote_token)
        _note(line_user_id, tid, f"DMS 身份证:失败({e.code})")
        return True

    fields = dms_id_ocr.editable_id_card(ocr.get("id_card") or {})
    missing = [k for k in ("people_id", "name") if not str(fields.get(k) or "").strip()]
    if missing:
        # 必填读不出 → 不出确认,直接说缺哪个字段(设计 §1:请拍清晰正面照重试)。
        _notify(
            line_user_id,
            tid,
            _t(_UNREADABLE, lang).format(fields=_field_names(missing, lang)),
            quote_token,
        )
        _note(line_user_id, tid, f"DMS 身份证:必填缺失 {missing}")
        return True

    from services.line_binding import line_pending_actions

    line_pending_actions.set_action(
        tid,
        line_user_id,
        {"tool": TOOL, "fields": fields, "endpoint_id": str(ep["id"]), "mode": "create"},
    )
    tail = str(fields.get("people_id") or "")[-4:]
    _notify(
        line_user_id,
        tid,
        _t(_RESTATE, lang).format(name=fields.get("name") or "", tail=tail),
        quote_token,
    )
    _note(line_user_id, tid, f"DMS 身份证:已复述等确认(尾4 {tail})")
    return True


def _field_names(keys, lang) -> str:
    return " + ".join(_t(_FIELD_NAMES.get(k, {"en": k}), lang) for k in keys)


def execute_confirmed(user, tid, line_user_id, lang, action) -> None:
    """检查点被"确认"消费:建 DMS 客户(网页同一函数)+ 写 erp_push_logs(trigger=line_dms)。
    调用方(confirm_machine)已 fail-open 兜底,这里只管把结果如实说给用户。"""
    _notify(line_user_id, tid, _t(_RUNNING, lang))
    fields = action.get("fields") or {}
    ep = dms_id_ocr.resolve_dms_endpoint(str(user["id"]), action.get("endpoint_id"))
    if not ep:
        _notify(line_user_id, tid, _t(_NO_ENDPOINT, lang))
        return
    from services.erp import erp_dms_intake

    result = erp_dms_intake.push_idcard_fields_mrerp_dms(
        ep, fields=fields, mode="create", customer_id=None, addresses=None
    )
    status = "success" if result.get("success") else "failed"
    try:
        db.insert_push_log(
            str(user["id"]),
            str(ep["id"]),
            None,
            result.get("customer_id") or "",
            str(fields.get("name") or "").strip(),
            None,
            status,
            200 if result.get("success") else 0,
            {
                "adapter": "mrerp_dms",
                "trigger": "line_dms",
                "mode": "create",
                "people_id_tail": (str(fields.get("people_id") or ""))[-4:],
            },
            json.dumps(result.get("response_body") or {}, ensure_ascii=False),
            result.get("error_code"),
            1,
            result.get("elapsed_ms", 0),
            "line_dms",
        )
    except Exception:
        logger.warning("[line_dms] push log failed (result already final)", exc_info=True)
    if result.get("success"):
        msg = _t(_DONE_OK, lang).format(name=fields.get("name") or "")
    else:
        msg = _t(_DONE_FAIL, lang).format(reason=_friendly_reason(result, lang))
    _notify(line_user_id, tid, msg)
    _note(line_user_id, tid, f"DMS 建客户:{status}")


def _friendly_reason(result, lang) -> str:
    """错误人话:ERR_DMS_* 目录(push_log_friendly)优先,兜底 error_friendly/裸码。"""
    code = str(result.get("error_code") or "")
    fallback = str(result.get("error_friendly") or code or "unknown")
    try:
        from services.erp.push_log_friendly import friendly_text

        return friendly_text(code, lang, fallback)
    except Exception:
        return fallback


def cancel(user, tid, line_user_id, lang) -> None:
    _notify(line_user_id, tid, _t(_CANCELLED, lang))
    _note(line_user_id, tid, "DMS 建客户:用户取消")
