# -*- coding: utf-8 -*-
"""LINE 图片意图接线层(LI-2)—— image_intent 决策核与真实管线之间的唯一桥。

decide():闸(agent_image_intent)+ 取走待决意图 → route_image 分流;default/闸关/
任何故障 → None,line_image_ocr 走现状代码逐字节不变(fail-safe 是这层的第一职责)。
execute():只落地 push / both / nothing 三个终端(record=覆盖套账后继续现状路;
archive_only=跳过记账段落回现状识别记录路,均由调用方按 route 微调,不在这里做):
  nothing  → 按现行口径计费 + 一句诚实回执,零落账
  push     → 写 ocr_history 载体行(推送机械只认 history)→ 计费 → 确认卡(push 消息)
  both     → 载体行 + 确认卡后返 None 继续现状记账路(计费在记账路,只收一次);
             记账闸关的租户退化为 push(载体行本身就是该租户的"记账"形态=识别记录)
推送永远止步于确认卡——真推送只发生在用户点按钮(services/agent/push_confirm)。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from core import db
from core.db import insert_ocr_history
from services.agent.image_intent import ImageRoute, route_image
from services.ocr.entrypoints import charge_successful_ocr as _charge

logger = logging.getLogger("mr-pilot")

# LINE 专用过程文案(与 push_confirm._ACK 同先例留 inline)。
_SKIP_ACK = {
    "th": "รับทราบค่ะ ใบนี้ไม่บันทึกและไม่ส่งเข้า ERP ให้นะคะ",
    "zh": "好的,这张不记账、也不推送。",
    "en": "Okay — this one won't be recorded or pushed to ERP.",
    "ja": "了解です。この伝票は記帳も ERP 送信もしません。",
}
_NO_ENDPOINT = {
    "th": "ยังไม่ได้เชื่อมต่อ ERP ค่ะ ไปที่เว็บ Pearnly > การเชื่อมต่อ เพื่อเพิ่มปลายทางก่อนนะคะ",
    "zh": "还没有可用的 ERP 端点,请先到网页「集成」里连接一个。",
    "en": "No ERP endpoint connected yet — add one under Integrations on the web first.",
    "ja": "ERP がまだ接続されていません。ウェブの「連携」から先に追加してください。",
}
_PUSH_DROPPED = {
    "th": "ส่วนการส่งเข้า ERP ยังไม่เปิดใช้งานค่ะ เก็บใบไว้ให้แล้ว เปิดใช้เมื่อไหร่ส่งได้เลย",
    "zh": "推送功能暂未开通,单据已留存,开通后可直接推。",
    "en": "ERP push isn't enabled yet — the document is saved and can be pushed once enabled.",
    "ja": "ERP 送信はまだ有効化されていません。伝票は保存済みで、有効化後に送信できます。",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


class Directive:
    """intercept() 给调用方的指令:handled 非 None=已完全处理直接返回;
    ws=覆盖套账;skip_ingest=跳过记账段(archive_only)。默认值=现状路零改动。"""

    __slots__ = ("handled", "ws", "skip_ingest")

    def __init__(self, handled=None, ws=None, skip_ingest=False):
        self.handled = handled
        self.ws = ws
        self.skip_ingest = skip_ingest


async def intercept(
    user,
    ws,
    tid,
    line_user_id,
    lang,
    quote,
    result,
    pages,
    cost_thb,
    filename,
    file_bytes,
    file_hash,
    quote_token,
) -> Directive:
    """line_image_ocr 的唯一挂点:决策+落地+全故障兜底收在这层,调用方只应用指令。"""
    try:
        route = decide(user, ws, tid, line_user_id, result)
        if route is None:
            return Directive()
        if route.workspace is not None:
            ws = route.workspace  # 计划步已核验存在的套账 id
        handled = await execute(
            route,
            user=user,
            ws=ws,
            tid=tid,
            line_user_id=line_user_id,
            lang=lang,
            quote=quote,
            result=result,
            pages=pages,
            cost_thb=cost_thb,
            filename=filename,
            file_bytes=file_bytes,
            file_hash=file_hash,
            quote_token=quote_token,
        )
        return Directive(
            handled=handled,
            ws=route.workspace,
            skip_ingest=route.terminal == "archive_only",
        )
    except Exception:
        logger.warning("[line_intent] intercept failed; default route", exc_info=True)
        return Directive()


def decide(user, ws_client_id, tenant_id, line_user_id, result) -> Optional[ImageRoute]:
    """闸 + 意图 → 分流。None = 现状管线(闸关/无意图普通票/任何故障)。"""
    try:
        from core import feature_flags
        from services.line_binding import line_intent_store

        uid = str(user.get("id") or "")
        if not (uid and tenant_id and line_user_id):
            return None
        if not feature_flags.agent_image_enabled_for(uid):
            return None
        pending = line_intent_store.take_intent(tenant_id, line_user_id)
        gates = {"image"}
        if feature_flags.agent_push_enabled_for(uid):
            gates.add("push")
        summary = {
            "doc_kind": "invoice",  # not_invoice 已在上游拦掉;歧义档(身份证等)LI-3 接大脑
            "confidence": "low" if str(result.get("confidence") or "") == "low" else "high",
        }
        route = route_image(summary, pending=pending, gates=frozenset(gates))
        return None if route.terminal == "default" else route
    except Exception:
        logger.warning("[line_intent] decide failed; default route", exc_info=True)
        return None


def _notify(line_user_id, tid, text, quote_token) -> None:
    from services.line_binding import line_reply

    line_reply.push_text_context(line_user_id, text, quote_token=quote_token or "", tenant_id=tid)


def _note(line_user_id, tid, bot_text) -> None:
    from services.line_binding import line_chat_memory

    line_chat_memory.note(
        line_user_id=line_user_id, tenant_id=tid, role="user", content="[ส่งรูปใบเสร็จ]"
    )
    line_chat_memory.note(line_user_id=line_user_id, tenant_id=tid, role="bot", content=bot_text)


def _insert_carrier(user, ws, tid, line_user_id, *, pages, result, quote, misc) -> Optional[str]:
    """推送载体行:推送机械(定位/幂等/日志)只认 ocr_history → 意图含 push 时补一行。"""
    return insert_ocr_history(
        user_id=str(user["id"]),
        tenant_id=tid,
        filename=misc["filename"],
        page_count=int(quote.get("page_count") or result.get("page_count") or len(pages)),
        pages=pages,
        confidence=result.get("confidence") or "unknown",
        elapsed_ms=result.get("elapsed_ms") or 0,
        file_size_kb=len(misc["file_bytes"]) // 1024,
        file_hash=misc["file_hash"],
        source="line_bot",
        source_ref=line_user_id,
        workspace_client_id=ws,
    )


def _charge_async(user, quote, hid, filename, tid, *, pages, result, cost_thb) -> None:
    """计费 + 成本埋点(拍板口径:OCR 跑了就按现行扣,与终端无关)。"""
    asyncio.create_task(asyncio.to_thread(_charge, user, quote, hid, f"LINE OCR · {filename}"))
    try:
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=tid,
            history_id=hid,
            engine="pipeline_v1",
            pages=len(pages),
            input_tokens=sum(int(p.get("input_tokens") or 0) for p in pages),
            output_tokens=sum(int(p.get("output_tokens") or 0) for p in pages),
            cost_thb=cost_thb,
            elapsed_ms=int(result.get("elapsed_ms") or 0),
        )
    except Exception as e:
        logger.warning(f"[line_intent] cost log failed (non-blocking): {e}")


def _send_push_card(user, ws, tid, line_user_id, lang, hid, route, pages, quote_token) -> bool:
    """载体行 → 端点解析 → 确认卡(push 消息)。不执行任何推送。"""
    from services.agent import push_confirm

    eps = [e for e in (db.list_erp_endpoints(str(user["id"])) or []) if e.get("enabled", True)]
    endpoint = None
    if route.endpoint_name:  # 计划步已核验过名字,这里再对一次防端点其间被删
        q = "".join(str(route.endpoint_name).lower().split())
        hits = [e for e in eps if q in "".join(str(e.get("name") or "").lower().split())]
        endpoint = hits[0] if len(hits) == 1 else None
    else:
        endpoint = eps[0] if eps else None  # 列表按 is_default DESC 排,首行即默认
    if not endpoint:
        _notify(line_user_id, tid, _t(_NO_ENDPOINT, lang), quote_token)
        return False
    fields = (pages[0] or {}).get("fields") or {} if pages else {}
    push = {
        "history_id": str(hid),
        "endpoint_id": str(endpoint["id"]),
        "endpoint_name": endpoint.get("name") or "ERP",
        "invoice_no": fields.get("invoice_number") or "",
        "vendor": fields.get("seller_name") or "",
        "amount": fields.get("total_amount"),
    }
    return push_confirm.send_confirm_card(
        user, "", push, lang, tid, ws, line_user_id, quote_token=quote_token or ""
    )


async def execute(
    route: ImageRoute,
    *,
    user,
    ws,
    tid,
    line_user_id,
    lang,
    quote,
    result,
    pages,
    cost_thb,
    filename,
    file_bytes,
    file_hash,
    quote_token,
) -> Optional[bool]:
    """终端落地。返回 True/False=已完全处理(调用方直接返回);None=继续现状代码。"""
    misc = {"filename": filename, "file_bytes": file_bytes, "file_hash": file_hash}

    if route.terminal == "nothing":
        _charge_async(
            user, quote, None, filename, tid, pages=pages, result=result, cost_thb=cost_thb
        )
        _notify(line_user_id, tid, _t(_SKIP_ACK, lang), quote_token)
        _note(line_user_id, tid, "意图:这张不记不推(已识别未落账)")
        return True

    if route.terminal not in ("push", "both"):
        # record/archive_only 由调用方按 route 微调后走现状代码;被剥掉的 push 在此如实告知。
        if route.dropped_push:
            _notify(line_user_id, tid, _t(_PUSH_DROPPED, lang), quote_token)
        return None

    both = route.terminal == "both"
    if both:
        # 记账闸关的租户没有记账终端可续 → 退化为 push(载体行=该租户的记账形态)。
        from services.purchase.intake import line_expense_gate_open

        with db.get_cursor_rls(tid, commit=True) as cur:
            expense_open = line_expense_gate_open(cur, tenant_id=tid)
        both = bool(expense_open)

    hid = _insert_carrier(
        user, ws, tid, line_user_id, pages=pages, result=result, quote=quote, misc=misc
    )
    if not hid:  # 载体写不进 → 别吞图:回 None 走现状管线(至少保住记账/识别记录)
        return None
    sent = _send_push_card(user, ws, tid, line_user_id, lang, hid, route, pages, quote_token)
    if both:
        return None  # 继续现状记账路(计费在那边,只收一次)
    _charge_async(
        user, quote, str(hid), filename, tid, pages=pages, result=result, cost_thb=cost_thb
    )
    _note(line_user_id, tid, f"意图:推送 ERP(确认卡已出={sent}·hid={str(hid)[:8]})")
    return True
