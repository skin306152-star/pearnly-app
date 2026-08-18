# -*- coding: utf-8 -*-
"""DMS LINE 订车逐问状态机(DL-7):聊天内 8 步逐问替代选车面板。

会话态 "booking_qa"(TTL 见 store._STATE_TTL_MINUTES),payload["qa"] 存进度:step /
endpoint_id / customer / draft / user_id / files / answers / payments / pending_channel /
audit / pages(各主档翻页页码)/ car_search(车型搜索命中集 + 页码)/ masters_synced
(本轮主档已 live 拉取成功,后续复用 12h 缓存)。职责链:slip 凭证 →
place → car_search → paint → date → term → regis → regis_name →
pay_channel(可循环多渠道)→ preview(置 booking_review + 轮换 nonce,既有 booking_flow
的确认/取消直接接得上)。

主档超过 LINE quick reply 13 项上限时分页:翻页按钮只换页重发当前步(不推进业务 step),
postback 走内部 token "__page:<n>",永远不进 answers —— 选中真实行才清页码状态。

全局命令(เริ่มใหม่/เมนู)不由本模块吃:handle_* 先 commands.classify,命中即返 False,交上层路由接管。金额一律 Decimal;每次用户输入按序记 audit 供追单对账。
"""

from __future__ import annotations

import logging
import secrets
from datetime import date
from typing import Any, Dict, Optional

from services.erp import dms_advisor
from services.erp import dms_id_ocr as _id_ocr
from services.erp.mrerp_dms_company_banks import company_bank_label
from services.erp.mrerp_dms_client_base import to_be_date
from services.line_dms import booking_qa_pages, booking_qa_sync, commands, qa_cards, store
from services.line_dms._out import _send, _thr
from services.line_dms.qa_util import (
    CHANNEL_EXTRA_SHAPE,
    car_label,
    car_label_of,
    complete_channel,
    find_row,
    norm,
    norm_row,
    parse_amount,
    row_name,
)

logger = logging.getLogger(__name__)

_STATE = "booking_qa"

_CASH_WORD = "เงินสด"
_SKIP_WORD = "-"
_MAX_REGIS_NAME = 120


# ── 入口 ───────────────────────────────────────────────────────────────────
async def start(
    tenant_id,
    line_user_id,
    endpoint_id,
    customer_id,
    customer_name,
    id_card_mid,
    reply_token=None,
    draft=None,
    user_id="",
    summary=None,
) -> None:
    """客户档落定后开一局逐问:定提成归属 → 初始化 qa(step=slip)→ 发第 1 问。
    身份证/OCR/客户档由既有 collecting 流程负责,本函数只从「档已落定」接手:
    id_card_mid 只进 files;draft 与 user_id 原样进 qa,建单执行器从 payload["qa"] 读取。
    顾问(提成归属)在开局就定死:认不出账号的单最终必被 DMS 拒收,答完 8 问再拦等于
    白占销售 5 分钟。
    """
    ep = await _thr(_id_ocr.resolve_dms_endpoint, user_id, endpoint_id)
    advisor, dms_username = (None, "")
    if ep:
        advisor, dms_username = await _thr(dms_advisor.resolve_operator_advisor, ep)
    if advisor is None:
        # 开不了单就别留着上一阶段的复述卡会话,否则用户下一句话撞在旧卡上(客户档已落定,不受影响)。
        await _thr(store.clear_session, tenant_id, line_user_id)
        msg = qa_cards.no_endpoint() if not ep else qa_cards.advisor_block_msg(dms_username)
        # 一律 push:顾问解析可能含一次 DMS 慢登录,到这里 reply_token 大概率已过期,
        # reply 失败 = 拦截理由静默丢失,销售只会看到「没反应」。
        _send(line_user_id, msg)
        return
    qa = {
        "step": "slip",
        "endpoint_id": str(endpoint_id or ""),
        "customer": {"id": str(customer_id or ""), "name": customer_name or ""},
        "advisor": advisor,
        "draft": dict(draft or {}),
        "summary": dict(summary or {}),
        "user_id": str(user_id or ""),
        "files": {"id_card_mid": id_card_mid or None, "slip_mid": None},
        "answers": {},
        "payments": [],
        "pending_channel": {},
        "audit": [],
    }
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "slip", reply_token)


# ── 每步发问(内部 · slip_after 复用) ─────────────────────────────────────
async def send_step(tenant_id, line_user_id, qa, step, reply_token=None) -> None:
    """按步发问。reply_token 有则 reply,无则 push(逐问可被 postback / 收料两种上下文调)。"""
    if step in ("place", "paint", "term", "regis", "pay_dst"):  # 这些步发问前要取主档
        # 闭包绑定 tenant_id,让 booking_qa_sync 首次 live 拉取后能把 masters_synced 落会话
        msg = await booking_qa_pages.question(
            line_user_id,
            qa,
            step,
            lambda luid, q, key: booking_qa_sync.masters(tenant_id, luid, q, key, persist=_persist),
            lambda luid, q: booking_qa_sync.paints(tenant_id, luid, q, persist=_persist),
        )
    else:
        msg = booking_qa_pages.static_question(step, qa)
    _send(line_user_id, msg, reply_token)


# ── webhook 入口 ───────────────────────────────────────────────────────────
async def handle_text(tenant_id, line_user_id, text, reply_token, sess=None) -> bool:
    """state==booking_qa 时消费文本;全局命令与其它态一律返 False 让上层接管。"""
    if commands.classify(text):
        return False
    qa = await _qa(tenant_id, line_user_id, sess)
    if qa is None:
        return False
    step = qa.get("step") or ""
    await _audit(tenant_id, line_user_id, qa, step, text)
    handler = _TEXT_HANDLERS.get(step, _reask)
    await handler(tenant_id, line_user_id, qa, text, reply_token)
    return True


async def handle_image(tenant_id, line_user_id, message_id, reply_token, sess=None) -> bool:
    """slip / slip_after 步收凭证图;其它步与其它态返 False(图片不是它们要的输入)。"""
    qa = await _qa(tenant_id, line_user_id, sess)
    if qa is None:
        return False
    step = qa.get("step") or ""
    if step not in ("slip", "slip_after"):
        return False
    await _audit(tenant_id, line_user_id, qa, step, f"image:{message_id}")
    qa["files"]["slip_mid"] = message_id
    if step == "slip":
        qa["step"] = "place"
        await _persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "place", reply_token)
    else:
        await _persist(tenant_id, line_user_id, qa)
        await _to_preview(tenant_id, line_user_id, qa, reply_token)
    return True


_POSTBACK_ACTIONS = {
    "place": "place",
    "car_search": "car",
    "paint": "paint",
    "date": "date",
    "term": "term",
    "regis": "regis",
    "regis_name": "regisname",
    "pay_channel": "pay",
    "pay_dst": "bank",
    "pay_more": "more",
}


async def handle_postback(tenant_id, line_user_id, data, params, reply_token) -> bool:
    """处理所有 "qa:" 前缀 postback;datetimepicker 的 params 携带所选日期。"""
    qa = await _qa(tenant_id, line_user_id)
    if qa is None or not (data or "").startswith("qa:"):
        return False
    parts = (data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""
    value = ":".join(parts[2:])
    step = qa.get("step") or ""
    await _audit(tenant_id, line_user_id, qa, step, data)
    # 旧卡残留 / 串步按钮:吃下不推进状态,原步重问(避免翻历史卡误跳步)。
    if action != _POSTBACK_ACTIONS.get(step):
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return True
    # 翻页导航 token:只换页重发当前步,绝不当作 DMS id 写进 answers。
    page = booking_qa_pages.page_number(value)
    if page is not None:
        await booking_qa_pages.flip_page(
            tenant_id,
            line_user_id,
            qa,
            action,
            page,
            reply_token,
            send_step=send_step,
            persist=_persist,
            reask=_reask,
        )
        return True
    if action in _MASTER_PICKS:  # place / term / regis 同一通用单选
        key, ans, nxt = _MASTER_PICKS[action]
        await _pick_master(tenant_id, line_user_id, qa, key, ans, value, nxt, reply_token)
    elif action == "car":
        await _pick_car(tenant_id, line_user_id, qa, value, reply_token)
    elif action == "paint":
        await _pick_paint(tenant_id, line_user_id, qa, value, reply_token)
    elif action == "date":
        await _pick_date(tenant_id, line_user_id, qa, params, reply_token)
    elif action == "regisname":
        await _pick_regis_name(tenant_id, line_user_id, qa, reply_token)
    elif action == "pay":
        await _pick_channel(tenant_id, line_user_id, qa, value, reply_token)
    elif action == "bank":
        await _pick_company_bank(tenant_id, line_user_id, qa, value, reply_token)
    elif action == "more":
        await _pick_more(tenant_id, line_user_id, qa, value, reply_token)
    return True


_MASTER_PICKS = {
    "place": ("place_books", "place", "car_search"),
    "term": ("term_sales", "term", "regis"),
    "regis": ("regis_behalfs", "regis", "regis_name"),
}


# ── 文本步 ─────────────────────────────────────────────────────────────────
async def _on_slip(tenant_id, line_user_id, qa, text, reply_token) -> None:
    if text.strip() == _CASH_WORD:
        qa["step"] = "place"  # 现金声明 → 无凭证图,slip_mid 保持空
        await _persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "place", reply_token)
        return
    _send(line_user_id, qa_cards.slip_only_image(), reply_token)


async def _on_car_search(tenant_id, line_user_id, qa, text, reply_token) -> None:
    rows = await booking_qa_sync.masters(tenant_id, line_user_id, qa, "cars", persist=_persist)
    needle = norm(text)
    hits = [r for r in rows if needle and needle in norm_row(r)]
    if not hits:
        _send(line_user_id, qa_cards.car_none(), reply_token)
        return
    # 命中集落进会话:翻页 postback 直接取,搜索结果不随翻页丢失;选中后清理。
    qa["car_search"] = {"hits": hits, "page": 0}
    await _persist(tenant_id, line_user_id, qa)
    _send(line_user_id, qa_cards.car_results(hits, len(hits)), reply_token)


async def _on_paint(tenant_id, line_user_id, qa, text, reply_token) -> None:
    paints = await booking_qa_sync.paints(tenant_id, line_user_id, qa, persist=_persist)
    needle = norm(text)
    hits = [r for r in paints if needle and needle in norm_row(r)]
    if len(hits) == 1:
        await _commit_paint(tenant_id, line_user_id, qa, hits[0], reply_token)
    else:
        # 0 命中(重列全部)/ 多命中(列命中项)都回颜色按钮,不推进状态。
        page = (qa.get("pages") or {}).get("paints", 0)
        _send(line_user_id, qa_cards.ask_paint(car_label_of(qa), hits or paints, page), reply_token)


async def _on_date(tenant_id, line_user_id, qa, text, reply_token) -> None:
    # 交车日只认 datetimepicker;打字无法解析 → 重发选择器(不推进状态)。
    await send_step(tenant_id, line_user_id, qa, "date", reply_token)


async def _on_regis_name(tenant_id, line_user_id, qa, text, reply_token) -> None:
    name = text.strip()
    if not name or len(name) > _MAX_REGIS_NAME:
        await send_step(tenant_id, line_user_id, qa, "regis_name", reply_token)
        return
    qa["answers"]["regis_name"] = name
    qa["step"] = "pay_channel"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_channel", reply_token)


async def _on_pay_amount(tenant_id, line_user_id, qa, text, reply_token) -> None:
    amount = parse_amount(text)
    if amount is None:
        _send(line_user_id, qa_cards.bad_amount(), reply_token)
        return
    pending = qa["pending_channel"]
    pending["amount"] = f"{amount:.2f}"
    shape = CHANNEL_EXTRA_SHAPE.get(pending.get("channel", ""))
    if shape == "src_dst":
        qa["step"] = next_step = "pay_src"
    elif shape in ("ref", "detail"):
        qa["step"] = next_step = "pay_ref"
    else:  # cash:金额即渠道完结
        complete_channel(qa)
        next_step = "pay_more"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, next_step, reply_token)


async def _on_pay_src(tenant_id, line_user_id, qa, text, reply_token) -> None:
    extra = qa["pending_channel"].setdefault("extra", {})
    extra["src"] = "" if text.strip() == _SKIP_WORD else text.strip()
    qa["step"] = "pay_dst"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_dst", reply_token)


async def _on_pay_ref(tenant_id, line_user_id, qa, text, reply_token) -> None:
    pending = qa["pending_channel"]
    extra = pending.setdefault("extra", {})
    slot = "detail" if CHANNEL_EXTRA_SHAPE.get(pending.get("channel")) == "detail" else "ref"
    extra[slot] = text.strip()
    complete_channel(qa)
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_more", reply_token)


async def _on_slip_after(tenant_id, line_user_id, qa, text, reply_token) -> None:
    # 用户已声明有转账渠道:打 เงินสด 也不放行,必须先送凭证图才能看总结。
    _send(line_user_id, qa_cards.need_slip(), reply_token)


async def _reask(tenant_id, line_user_id, qa, text, reply_token) -> None:
    """按钮步收到打字 / 串步按钮 → 原步重问,不推进状态(audit 已在入口记过)。"""
    await send_step(tenant_id, line_user_id, qa, qa.get("step") or "", reply_token)


_TEXT_HANDLERS = {
    "slip": _on_slip,
    "place": _reask,
    "car_search": _on_car_search,
    "paint": _on_paint,
    "date": _on_date,
    "term": _reask,
    "regis": _reask,
    "regis_name": _on_regis_name,
    "pay_channel": _reask,
    "pay_amount": _on_pay_amount,
    "pay_src": _on_pay_src,
    "pay_dst": _reask,
    "pay_ref": _on_pay_ref,
    "pay_more": _reask,
    "slip_after": _on_slip_after,
}


# ── postback 步 ────────────────────────────────────────────────────────────
async def _pick_master(
    tenant_id,
    line_user_id,
    qa,
    masters_key,
    answer_key,
    value,
    next_step,
    reply_token,
) -> None:
    """通用主档单选:id → 存 answers.<key>={"id","name"} → 进下一步(清该主档页码)。"""
    rows = await booking_qa_sync.masters(tenant_id, line_user_id, qa, masters_key, persist=_persist)
    row = find_row(rows, value)
    if row is None:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    (qa.get("pages") or {}).pop(masters_key, None)
    qa["answers"][answer_key] = {"id": str(row[0]), "name": row_name(row)}
    qa["step"] = next_step
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, next_step, reply_token)


async def _pick_company_bank(tenant_id, line_user_id, qa, value, reply_token) -> None:
    rows = await booking_qa_sync.masters(
        tenant_id, line_user_id, qa, "company_banks", persist=_persist
    )
    row = find_row(rows, value)
    if row is None:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    (qa.get("pages") or {}).pop("company_banks", None)
    extra = qa["pending_channel"].setdefault("extra", {})
    extra["dst_id"] = str(row[0])
    extra["dst"] = company_bank_label(row)
    complete_channel(qa)
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_more", reply_token)


async def _pick_car(tenant_id, line_user_id, qa, value, reply_token) -> None:
    rows = await booking_qa_sync.masters(tenant_id, line_user_id, qa, "cars", persist=_persist)
    row = find_row(rows, value)
    if row is None:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa.pop("car_search", None)  # 选完即清命中集,不留残渣
    qa["answers"]["car"] = {"id": str(row[0]), "label": car_label(row)}
    qa["step"] = "paint"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "paint", reply_token)


async def _pick_paint(tenant_id, line_user_id, qa, value, reply_token) -> None:
    rows = await booking_qa_sync.paints(tenant_id, line_user_id, qa, persist=_persist)
    row = find_row(rows, value)
    if row is None:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    await _commit_paint(tenant_id, line_user_id, qa, row, reply_token)


async def _commit_paint(tenant_id, line_user_id, qa, row, reply_token) -> None:
    (qa.get("pages") or {}).pop("paints", None)
    qa["answers"]["paint"] = {"id": str(row[0]), "name": row_name(row)}
    qa["step"] = "date"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "date", reply_token)


async def _pick_date(tenant_id, line_user_id, qa, params, reply_token) -> None:
    picked = (params or {}).get("date") or ""
    try:
        delivery = date.fromisoformat(picked)
    except ValueError:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa["answers"]["delivery_date_be"] = to_be_date(delivery)  # 公历 ISO → 佛历 dd/mm/yyyy
    qa["step"] = "term"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "term", reply_token)


async def _pick_regis_name(tenant_id, line_user_id, qa, reply_token) -> None:
    qa["answers"]["regis_name"] = str((qa.get("customer") or {}).get("name") or "")
    qa["step"] = "pay_channel"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_channel", reply_token)


async def _pick_channel(tenant_id, line_user_id, qa, value, reply_token) -> None:
    if value not in qa_cards.PAY_LABELS:
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    qa["pending_channel"] = {"channel": value}
    qa["step"] = "pay_amount"
    await _persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "pay_amount", reply_token)


async def _pick_more(tenant_id, line_user_id, qa, value, reply_token) -> None:
    if value == "add":
        qa["step"] = "pay_channel"  # 回渠道选择,同渠道可重复选(金额各记一条)
        await _persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "pay_channel", reply_token)
        return
    if value != "done":
        await _reask(tenant_id, line_user_id, qa, "", reply_token)
        return
    has_transfer = "transfer" in {p.get("channel") for p in qa.get("payments") or []}
    if has_transfer and not (qa.get("files") or {}).get("slip_mid"):
        qa["step"] = "slip_after"  # 声明过转账却没凭证 → 先补要,不能放行看总结
        await _persist(tenant_id, line_user_id, qa)
        await send_step(tenant_id, line_user_id, qa, "slip_after", reply_token)
        return
    await _to_preview(tenant_id, line_user_id, qa, reply_token)


async def _to_preview(tenant_id, line_user_id, qa, reply_token) -> None:
    """逐问收官:置 booking_review(完整 qa + 轮换 nonce)→ 发预览卡。

    轮换 nonce 照预览卡约定:旧按钮的 postback 从此 mismatch,
    确认/取消仍由既有 booking_flow 处理(consume_nonce 守卫)。
    """
    sess = await _thr(store.get_session, tenant_id, line_user_id)
    payload = (sess or {}).get("payload") or {}
    nonce = secrets.token_hex(8)
    await _thr(
        store.set_session,
        tenant_id,
        line_user_id,
        "booking_review",
        {**payload, "qa": qa, "nonce": nonce},
    )
    _send(line_user_id, qa_cards.preview_card(qa, nonce), reply_token)


# ── 会话 / 主档 / 出口小工具 ───────────────────────────────────────────────
async def _qa(tenant_id, line_user_id, sess=None) -> Optional[Dict[str, Any]]:
    """读当前 qa;非 booking_qa 态 / 缺 step(会话损坏)→ None(交上层)。
    调用方已读过会话就透传 sess 免二读(text_router「入口只读一次」原则)。"""
    if sess is None:
        sess = await _thr(store.get_session, tenant_id, line_user_id)
    if not sess or sess.get("state") != _STATE:
        return None
    qa = (sess.get("payload") or {}).get("qa") or {}
    return qa if qa.get("step") else None


async def _audit(tenant_id, line_user_id, qa, step, value) -> None:
    qa.setdefault("audit", []).append({"step": step, "input": value})
    await _persist(tenant_id, line_user_id, qa)


async def _persist(tenant_id, line_user_id, qa) -> None:
    await _thr(store.set_session, tenant_id, line_user_id, _STATE, {"qa": qa})
