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

# 四语过程文案(零逻辑)拆在 line_route_copy;import-through 保住既有引用名。
from services.ocr.line_route_copy import (
    _ASK_GOAL,
    _BANK_STMT_GUIDE,
    _CANT_PUSH,
    _ID_CARD_GUIDE,
    _NO_ENDPOINT,
    _PUSH_DROPPED,
    _SKIP_ACK,
    _t,
)

logger = logging.getLogger("mr-pilot")


class Directive:
    """intercept() 给调用方的指令:handled 非 None=已完全处理直接返回;
    ws=覆盖套账;skip_ingest=跳过记账段(archive_only)。默认值=现状路零改动。"""

    __slots__ = ("handled", "ws", "skip_ingest")

    def __init__(self, handled=None, ws=None, skip_ingest=False):
        self.handled = handled
        self.ws = ws
        self.skip_ingest = skip_ingest


# 对账单确定性记号(泰/英)。费用 OCR 路的 L2 对流水页只给 document_type=other,
# 真信号在 notes/页原文(真机探针:BAY 流水 notes="รายการเดินบัญชีเงินฝาก...")。
_STMT_KW = (
    "รายการเดินบัญชี",
    "เดินบัญชี",
    "statement of account",
    "bank statement",
    "ยอดยกมา",
)
# 身份证确定性记号(泰/英)· 与对账单同模式同挂点(LINE-DMS-PUSH-DESIGN §2)。
_ID_KW = (
    "บัตรประจำตัวประชาชน",
    "เลขประจำตัวประชาชน",
    "thai national id",
    "identification card",
)


def not_invoice_guidance(pages, lang) -> Optional[str]:
    """非票据页的靶向引导:认出银行对账单 → 指去网页对账 + 可问对账结果;认出身份证 →
    指路"先说建 DMS 客户再发"(替掉"不像票据请发费用文件"的死胡同 · 真机探针 2026-07-02)。
    认不出/故障 → None(回落通用文案)。只在 all_pages_not_invoice 分支被调,不碰票据热路。"""
    try:
        for p in pages or []:
            f = (p or {}).get("fields") or {}
            doc_type = str(f.get("document_type") or "")
            blob = f"{f.get('notes') or ''} {str((p or {}).get('text') or '')[:2000]}".lower()
            if doc_type == "bank_statement" or any(k in blob for k in _STMT_KW):
                return _t(_BANK_STMT_GUIDE, lang)
            if doc_type == "id_card" or any(k in blob for k in _ID_KW):
                return _t(_ID_CARD_GUIDE, lang)
    except Exception:
        return None
    return None


def cache_shortcut(user, line_user_id, file_hash, ws, lang, quote_token) -> bool:
    """OCR 前缓存快路(dup 状态卡 / 指纹缓存重建卡),搬自 line_image_ocr(等价零改动)。

    有活的待决意图时整段让位返回 False——"先说目的、再重发同一张图"是用户最自然的动作
    (真机第一轮就踩到:说了"只推"再发图,被 dup 短路吞成"已入账"状态卡)。无意图/闸关
    时行为与搬家前逐字节一致。
    """
    if _intent_pending(user, line_user_id):
        logger.info("[line_intent] pending intent; cache shortcut yields to full pipeline")
        return False
    from services.ocr import line_image_fastpath as fastpath
    from services.ocr.entrypoints import get_cached_history

    if fastpath.early_dup_short_circuit(user, line_user_id, file_hash, ws, lang, quote_token):
        return True
    cached = get_cached_history(user, file_hash, workspace_client_id=ws)
    if cached:
        fastpath.handle_ocr_cache_hit(user, file_hash, cached, line_user_id, lang, quote_token, ws)
        return True
    return False


async def pre_ocr_shortcut(
    user, line_user_id, file_hash, ws, lang, quote_token, *, file_bytes, filename
) -> Optional[bool]:
    """费用 OCR 前的三条快路:① 对账收件模式 → 文件归档进 job 暂存(零识别扣费);
    ② 意图=dms → 专用身份证路接管;③ 缓存快路(dup 状态卡/指纹缓存)。
    返回 True/False=已完全处理;None=继续现状管线。"""
    intake = await _recon_intake_shortcut(
        user, line_user_id, lang, file_bytes, filename, quote_token
    )
    if intake is not None:
        return intake
    dms = await _dms_shortcut(user, line_user_id, lang, file_bytes, filename, quote_token)
    if dms is not None:
        return dms
    if cache_shortcut(user, line_user_id, file_hash, ws, lang, quote_token):
        return True
    return None


async def _recon_intake_shortcut(user, line_user_id, lang, file_bytes, filename, quote_token):
    """对账收件缝:双闸开 + 有活跃收件检查点才接管;其余 None=现状。
    故障 → None(文件走现状 OCR,绝不静默蒸发)。"""
    try:
        import asyncio as _aio

        from core import feature_flags

        uid = str(user.get("id") or "")
        tid = str(user.get("tenant_id") or "")
        if not (uid and tid and line_user_id):
            return None
        if not (
            feature_flags.agent_image_enabled_for(uid)
            and feature_flags.agent_recon_intake_enabled_for(uid)
        ):
            return None
        from services.agent import recon_intake

        return await _aio.to_thread(
            recon_intake.handle_file,
            user,
            tid,
            line_user_id,
            lang,
            file_bytes,
            filename,
            quote_token,
        )
    except Exception:
        logger.warning("[recon_intake] shortcut failed; default pipeline", exc_info=True)
        return None


async def _dms_shortcut(user, line_user_id, lang, file_bytes, filename, quote_token):
    """意图=dms 的图 → 身份证识别+复述检查点(services/agent/dms_push)。
    闸关/无意图/非 dms → None;接管路自身任何故障 → 人话已发 or 回 None 走现状
    (身份证会被 not_invoice 引导,图绝不静默蒸发)。take 只在确认接管后发生。"""
    try:
        import asyncio as _aio

        from core import feature_flags
        from services.line_binding import line_intent_store

        uid = str(user.get("id") or "")
        tid = str(user.get("tenant_id") or "")
        if not (uid and tid and line_user_id):
            return None
        if not (
            feature_flags.agent_image_enabled_for(uid) and feature_flags.agent_dms_enabled_for(uid)
        ):
            return None
        intent = line_intent_store.read_intent(tid, line_user_id)
        from services.agent import dms_push

        if not dms_push.wants_dms(intent):
            return None
        line_intent_store.take_intent(tid, line_user_id)  # 单发单用,与其它意图同语义
        return await _aio.to_thread(
            dms_push.handle_id_card,
            user,
            tid,
            line_user_id,
            lang,
            file_bytes,
            filename,
            quote_token,
        )
    except Exception:
        logger.warning("[line_dms] shortcut failed; default pipeline", exc_info=True)
        return None


def _intent_pending(user, line_user_id) -> bool:
    """闸开且该用户有未过期意图(只看不取,take 仍只在 decide)。故障 → False = 快路照旧。"""
    try:
        from core import feature_flags
        from services.line_binding import line_intent_store

        uid = str(user.get("id") or "")
        tid = str(user.get("tenant_id") or "")
        if not (uid and tid and line_user_id):
            return False
        if not feature_flags.agent_image_enabled_for(uid):
            return False
        return line_intent_store.peek_intent(tid, line_user_id)
    except Exception:
        logger.warning("[line_intent] peek failed; cache shortcut stays", exc_info=True)
        return False


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
        route = decide(user, ws, tid, line_user_id, result, lang=lang)
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
            skip_ingest=route.terminal in ("archive_only", "ask"),
        )
    except Exception:
        logger.warning("[line_intent] intercept failed; default route", exc_info=True)
        return Directive()


def decide(user, ws_client_id, tenant_id, line_user_id, result, lang="th") -> Optional[ImageRoute]:
    """闸 + 意图 → 分流。None = 现状管线(闸关/无意图普通票/任何故障)。
    没意图 + 读不清 → 问一次大脑(LI §3 第三层 · 2026-07-02 通电);大脑答不上
    route_image 自兜回 default,绝不因大脑抖动丢图。"""
    try:
        from core import feature_flags
        from services.agent import image_brain
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
        _f = ((result.get("pages") or [{}])[0] or {}).get("fields") or {}
        summary = {
            "doc_kind": "invoice",  # not_invoice 已在上游拦掉,歧义信号只剩置信度
            "confidence": "low" if str(result.get("confidence") or "") == "low" else "high",
            "seller": str(_f.get("seller_name") or ""),
            "total": str(_f.get("total_amount") or ""),
        }
        route = route_image(
            summary,
            pending=pending,
            gates=frozenset(gates),
            decide=image_brain.decide_image,
            lang=lang,
        )
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


def _push_blocked_reason(fields) -> Optional[str]:
    """出卡前防呆预检:注定推不过的票别给确认按钮(点了才失败=坏体验·Zihao 2026-07-02)。
    推送时的权威闸仍在 route_and_upload,这里只是同源判定前移;预检崩了不挡卡。"""
    try:
        from services.erp.express_push.doc_sanity import check_document

        return check_document(fields or {}, {"fields": fields or {}}, "purchase")
    except Exception:
        logger.warning("[line_intent] pre-card sanity failed; card proceeds", exc_info=True)
        return None


def _send_push_card(user, ws, tid, line_user_id, lang, hid, route, pages, quote_token) -> bool:
    """载体行 → 防呆预检 → 端点解析 → 确认卡(push 消息)。不执行任何推送。"""
    from services.agent import push_confirm

    _f = (pages[0] or {}).get("fields") or {} if pages else {}
    blocked = _push_blocked_reason(_f)
    if blocked:
        from services.erp import push_log_friendly

        hit = push_log_friendly.friendly_any(blocked) or {}
        reason = hit.get(lang) or hit.get("en") or blocked
        _notify(line_user_id, tid, _t(_CANT_PUSH, lang).format(reason=reason), quote_token)
        return False

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
    push = {
        "history_id": str(hid),
        "endpoint_id": str(endpoint["id"]),
        "endpoint_name": endpoint.get("name") or "ERP",
        "invoice_no": _f.get("invoice_number") or "",
        "vendor": _f.get("seller_name") or "",
        "amount": _f.get("total_amount"),
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

    if route.terminal == "ask":
        # 歧义问询落地:单据存识别记录(不丢、网页可查),用确定性文案反问该怎么办
        # (含"回一句+重发"闭环指引——缓存快路会给新意图让位,重发即按答复执行)。
        # 大脑只选终端,问句不用它的(资金面文案必须确定性)。
        hid = _insert_carrier(
            user, ws, tid, line_user_id, pages=pages, result=result, quote=quote, misc=misc
        )
        _charge_async(
            user,
            quote,
            str(hid) if hid else None,
            filename,
            tid,
            pages=pages,
            result=result,
            cost_thb=cost_thb,
        )
        _notify(line_user_id, tid, _t(_ASK_GOAL, lang), quote_token)
        _note(line_user_id, tid, "意图:读不清已反问(存识别记录未入账)")
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
