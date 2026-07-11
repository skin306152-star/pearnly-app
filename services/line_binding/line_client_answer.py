# -*- coding: utf-8 -*-
"""客户回答回写(D2 方案 §4 / §7.2 S5)· webhook 拦截 + NL 解析 + record_decision。

消费边界(主窗拍板修正 2/3,硬门):
- 判定「这条消息是否要被本池吃掉」全程只读、零副作用,任何阶段判不出/闸关/无
  pending 都直接 return False 回落原路(fail-open),绝不半吞。
- 一旦越过消费边界(_consume 起)视为已受理:下游任一步失败也不得再回落原路
  (防止同一条消息又被大脑记账路径处理第二遍),只记日志、按兜底转人审。
- 回写前必须重读该票事件流:问题创建之后若已有人工裁决 → 不覆盖(latest-wins
  保护会计裁决),问题转 resolved_internally,回「已处理」话术(修正 2)。

裁决词全 import services.workorder.decisions,状态词全 import client_pool_vocab,
本模块不新造裁决通道——唯一写口仍是 services.workorder.api.record_decision。
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.line_binding import client_pool_vocab as vocab
from services.workorder import decisions

logger = logging.getLogger(__name__)

# 方向/剔除关键词字典(§4.2)。中文注释标语义;两两互斥,ไม่冲突。
_PURCHASE_KEYWORDS = ("ซื้อ", "รายจ่าย", "จ่าย")  # 进项(买)
_SALES_KEYWORDS = ("ขาย", "รายรับ", "รับ")  # 销项(卖)
_NON_TAX_KEYWORDS = ("ไม่ใช่ทั้งคู่", "ไม่เกี่ยว")  # 都不是(非税)
_DROP_KEYWORDS = ("ไม่ใช่เดือนนี้", "ซ้ำ", "ไม่ต้อง", "ตัดออก")  # 剔除
_ANSWER_KEYWORDS = _PURCHASE_KEYWORDS + _SALES_KEYWORDS + _NON_TAX_KEYWORDS + _DROP_KEYWORDS

# 行首/句中编号标记:1-5 后跟标点+空白或纯空白,避免「100」「2,647.50」误判成编号。
_MARKER_RE = re.compile(r"(?:^|(?<=\s))([1-5])(?:[)\.:]\s*|\s+)")
_AMOUNT_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")

# 短答尾缀:礼貌语气词/标点/emoji,剥掉后核心=关键词本身才算短答(见 _is_strict_short_form)。
_POLITE_TAIL_RE = re.compile(
    r"(?:ค่ะ|ค่า|คะ|ครับ|ครัช|ๆ|[!?.,~。!?、]|[\U0001F300-\U0001FAFF\U00002600-\U000027BF])+$"
)

# 回执文案(四语 · 客户侧 LINE push,独立小词表 · 照 line_client_contact._BOUND_COPY
# 同款范式:这是客户身份维度的措辞,不并进会计端 UI 的大 i18n 框架)。
_APPLIED_COPY = {
    "th": "ได้รับแล้วค่ะ ✅ อัปเดตตามที่แจ้งเรียบร้อยแล้วนะคะ",
    "en": "Got it! Updated as you said.",
    "zh": "收到,已按你说的更新。",
    "ja": "承知しました。ご回答の通り更新しました。",
}
_MANUAL_COPY = {
    "th": "ได้รับแล้วค่ะ 🙏 ขอบันทึกไว้ก่อน นักบัญชีจะดูให้อีกทีนะคะ",
    "en": "Got it! Noted — your accountant will take a look.",
    "zh": "收到,先记下,会计会再确认。",
    "ja": "承知しました。会計担当が確認いたします。",
}
_ALREADY_HANDLED_COPY = {
    "th": "ไม่ต้องแล้วค่ะ 🙏 รายการนี้จัดการเรียบร้อยแล้ว",
    "en": "No worries — this one's already been taken care of.",
    "zh": "不用麻烦了,这条已经处理好了。",
    "ja": "こちらはすでに処理済みですので大丈夫です。",
}


def handle_answer(
    line_user_id: str, text: str, reply_token: Optional[str], quote_token: Optional[str]
) -> bool:
    """webhook 拦截入口。True = 本条消息已被本池吃掉(调用方应 return,不再落大脑);
    False = 与本池无关或判不出,原样回落既有路径。"""
    try:
        selected = _select_batch(line_user_id)
        if selected is None:
            return False
        from core import db

        dual_identity = bool(db.get_user_by_line_user_id(line_user_id))
        if dual_identity and not _looks_like_answer(text):
            # 修正 3 硬门:双重身份判不出是在答题 → 不吞不落 manual_review,原样回落。
            return False
    except Exception:
        logger.warning("[line_client_answer] 拦截判定异常 · fail-open 回落原路", exc_info=True)
        return False

    # 越过消费边界:此后任何失败都只兜底转人审 + 记日志,不再返回 False。
    try:
        _consume(selected, text, line_user_id, reply_token, quote_token)
    except Exception:
        logger.exception("[line_client_answer] 消费阶段异常 · 已过消费边界不回落")
    return True


def _select_batch(line_user_id: str) -> Optional[dict]:
    """反查该 sender 名下客户联系人,挑闸开租户里「最近 sent_at」那一批 pending 问题。

    一个业主可能挂多主体(§1.3),各自可能都有在途批次;消歧口径:跨全部候选取
    sent_at 最大的那一批,批内按 created_at 升序编号——与 S4(line_client_pool_push.
    stage_batch_for_client)推送时 `for idx, q in enumerate(questions, start=1)`
    的枚举顺序一致(questions 取自 store.list_for_client,该函数按 created_at
    升序出行),保证客户回「1/2/3」对应的正是消息里看到的那个编号。
    闸关的租户直接跳过(闸关时该池对该 sender 视而不见)。
    """
    from core import feature_flags
    from services.line_binding import line_client_contact
    from services.line_binding import line_client_pool_store as pool_store

    contacts = line_client_contact.list_contacts_by_line_user(line_user_id)
    if not contacts:
        return None

    best = None  # (latest_sent_at, tenant_id, workspace_client_id, rows, lang)
    for contact in contacts:
        tenant_id = contact["tenant_id"]
        if not feature_flags.pearnly_ai_client_pool_enabled_for(tenant_id):
            continue
        rows = pool_store.list_for_client(
            tenant_id, contact["workspace_client_id"], statuses=(vocab.PENDING,)
        )
        rows = [r for r in rows if r.get("sent_at")]
        if not rows:
            continue
        latest = max(r["sent_at"] for r in rows)
        if best is None or latest > best[0]:
            best = (
                latest,
                tenant_id,
                contact["workspace_client_id"],
                rows,
                contact.get("preferred_lang"),
            )
    if best is None:
        return None

    _, tenant_id, workspace_client_id, rows, lang = best
    batches: dict = {}
    for row in rows:
        batches.setdefault(row.get("batch_id"), []).append(row)
    target_batch_id = max(batches, key=lambda bid: max(r["sent_at"] for r in batches[bid]))
    batch_rows = sorted(batches[target_batch_id], key=lambda r: r["created_at"])
    return {
        "tenant_id": tenant_id,
        "workspace_client_id": workspace_client_id,
        "rows": batch_rows,
        "lang": lang,
    }


def _is_strict_short_form(text: str) -> bool:
    """短答形态(b):trim+剥离礼貌尾缀后=某关键词本身(如「ซื้อค่ะ」);不含编号。"""
    core = _POLITE_TAIL_RE.sub("", (text or "").strip()).strip()
    return core in _ANSWER_KEYWORDS


def _looks_like_answer(text: str) -> bool:
    """严格答题形态(打回修正:长句含关键词 ≠ 答题)——(a) 编号段命中关键词,或
    (b) 整条消息就是关键词本身,防「จ่ายค่าไฟ 500」被错吞。"""
    segments = _split_numbered_segments(text)
    if segments:
        return any(any(kw in seg for kw in _ANSWER_KEYWORDS) for _, seg in segments)
    return _is_strict_short_form(text)


def _split_numbered_segments(text: str) -> list[tuple[int, str]]:
    """按行首/句中编号切成 [(题号, 该题原文片段), ...];无编号返回空列表。"""
    markers = list(_MARKER_RE.finditer(text))
    if not markers:
        return []
    out = []
    for i, m in enumerate(markers):
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        out.append((int(m.group(1)), text[start:end].strip()))
    return out


def _resolve(
    question_type: str, segment: str
) -> Optional[tuple[str, Optional[str], Optional[dict]]]:
    """(decision, kind, values) 三元组,None = 解不出交人(§4.2 保守:宁可交人不瞎猜)。"""
    if question_type == vocab.QUESTION_DIRECTION:
        return _resolve_direction(segment)
    if question_type == vocab.QUESTION_DROP:
        return _resolve_drop(segment)
    if question_type == vocab.QUESTION_AMOUNT:
        return _resolve_amount(segment)
    return None  # freeform:恒交人审,不自动回写(§4.1 映射表)


def _resolve_direction(segment: str):
    hits = set()
    if any(kw in segment for kw in _PURCHASE_KEYWORDS):
        hits.add(decisions.PURCHASE_INVOICE)
    if any(kw in segment for kw in _SALES_KEYWORDS):
        hits.add(decisions.SALES_DOC)
    if any(kw in segment for kw in _NON_TAX_KEYWORDS):
        hits.add(decisions.NON_TAX)
    if len(hits) != 1:
        return None
    return (decisions.ASSIGN_KIND, hits.pop(), None)


def _resolve_drop(segment: str):
    if any(kw in segment for kw in _DROP_KEYWORDS):
        return (decisions.EXCLUDE, None, None)
    return None


def _resolve_amount(segment: str):
    candidates = set()
    for raw in _AMOUNT_RE.findall(segment):
        try:
            value = Decimal(raw.replace(",", ""))
        except InvalidOperation:
            continue
        if value.is_finite() and value >= 0:
            candidates.add(value)
    if len(candidates) != 1:
        return None
    return (decisions.RECALC, None, {"vat": format(candidates.pop(), "f")})


def _consume(
    selected: dict, text: str, line_user_id: str, reply_token: Optional[str], quote_token
) -> None:
    tenant_id = selected["tenant_id"]
    workspace_client_id = selected["workspace_client_id"]
    batch_rows = selected["rows"]
    lang = selected["lang"]

    segments = _split_numbered_segments(text)
    if segments:
        matched = False
        for num, seg in segments:
            idx = num - 1
            if 0 <= idx < len(batch_rows):
                matched = True
                _handle_one(
                    tenant_id,
                    workspace_client_id,
                    batch_rows[idx],
                    seg,
                    line_user_id,
                    reply_token,
                    quote_token,
                    lang,
                )
        if matched:
            return
        # 编号全部越界(如只有 2 条却答"5")→ 当无法定位处理。
        _handle_unlocatable(
            tenant_id, batch_rows, text, line_user_id, reply_token, quote_token, lang
        )
        return

    if len(batch_rows) == 1:
        # 无编号单条 pending:唯一「段」是整条原文,只有短答形态(b)才自动裁决(打回修正 1)。
        _handle_one(
            tenant_id,
            workspace_client_id,
            batch_rows[0],
            text,
            line_user_id,
            reply_token,
            quote_token,
            lang,
            force_manual=not _is_strict_short_form(text),
        )
        return

    _handle_unlocatable(tenant_id, batch_rows, text, line_user_id, reply_token, quote_token, lang)


def _handle_unlocatable(tenant_id, batch_rows, text, line_user_id, reply_token, quote_token, lang):
    """多条 pending 又没编号定位不出具体哪条 → 保守挂批次首条转人审,原文留底给
    会计判断(§4.2「宁可交人不瞎猜」;不逐条群发人审,避免同批其余题被误动)。"""
    logger.info(
        "[line_client_answer] 定位不出具体问题 · 默认挂批次首条 qid=%s", batch_rows[0]["id"]
    )
    _finish(
        tenant_id,
        batch_rows[0]["id"],
        vocab.MANUAL_REVIEW,
        answer_raw=text,
        resolution=None,
        reply_token=reply_token,
        quote_token=quote_token,
        line_user_id=line_user_id,
        lang=lang,
    )


def _handle_one(
    tenant_id,
    workspace_client_id,
    question: dict,
    segment: str,
    line_user_id: str,
    reply_token,
    quote_token,
    lang,
    force_manual: bool = False,
) -> None:
    qid = question["id"]
    work_order_id = question["work_order_id"]
    item_id = question["item_id"]

    # force_manual:segment 非严格答题形态(见 _consume)→ 直接当解不出,不喂给 _resolve。
    outcome = None if force_manual else _resolve(question["question_type"], segment)
    if outcome is None:
        _finish(
            tenant_id,
            qid,
            vocab.MANUAL_REVIEW,
            answer_raw=segment,
            resolution=None,
            reply_token=reply_token,
            quote_token=quote_token,
            line_user_id=line_user_id,
            lang=lang,
        )
        return

    if _decided_after(tenant_id, work_order_id, item_id, question.get("created_at")):
        # 修正 2 硬门:该票在问题创建后已有人工裁决(会计已经处理过)→ 不覆盖,回「已处理」。
        _finish(
            tenant_id,
            qid,
            vocab.RESOLVED_INTERNALLY,
            answer_raw=segment,
            resolution=None,
            reply_token=reply_token,
            quote_token=quote_token,
            line_user_id=line_user_id,
            lang=lang,
            already_handled=True,
        )
        return

    decision, kind, values = outcome
    event = _record_decision(
        tenant_id, work_order_id, item_id, decision, kind, values, line_user_id
    )
    if event is None:
        # 裁决通道本身炸了(极端情况)→ 保守转人审,绝不假装成功也绝不吞。
        _finish(
            tenant_id,
            qid,
            vocab.MANUAL_REVIEW,
            answer_raw=segment,
            resolution=None,
            reply_token=reply_token,
            quote_token=quote_token,
            line_user_id=line_user_id,
            lang=lang,
        )
        return

    resolution = {
        "decision": decision,
        "actor": f"line_client:{line_user_id}",
        "event_id": event["id"],
    }
    if kind is not None:
        resolution["kind"] = kind
    if values is not None:
        resolution["values"] = values
    _finish(
        tenant_id,
        qid,
        vocab.APPLIED,
        answer_raw=segment,
        resolution=resolution,
        reply_token=reply_token,
        quote_token=quote_token,
        line_user_id=line_user_id,
        lang=lang,
    )
    _close_siblings(tenant_id, workspace_client_id, work_order_id, item_id, qid)


def _decided_after(tenant_id, work_order_id, item_id, question_created_at) -> bool:
    """竞态守卫(修正 2):该票在问题创建之后是否已落过人工裁决。单已读不到(冻结/
    归档/异常)一律保守当「已被处理」,绝不冒险覆盖。"""
    from core import db
    from services.workorder import api as wo_api

    try:
        with db.get_cursor(commit=False) as cur:
            detail = wo_api.order_detail(
                cur, tenant_id=str(tenant_id), work_order_id=str(work_order_id)
            )
    except Exception:
        logger.warning("[line_client_answer] 竞态复核读取失败 · 保守当已处理", exc_info=True)
        return True
    if not detail:
        return True
    entry = next((f for f in detail["flagged"] if str(f["item_id"]) == str(item_id)), None)
    decision = (entry or {}).get("decision")
    at = decision.get("at") if decision else None
    return bool(at and question_created_at and at > question_created_at)


def _record_decision(tenant_id, work_order_id, item_id, decision, kind, values, line_user_id):
    from core import db
    from services.workorder import api as wo_api

    try:
        with db.get_cursor(commit=True) as cur:
            return wo_api.record_decision(
                cur,
                tenant_id=str(tenant_id),
                work_order_id=str(work_order_id),
                item_id=str(item_id),
                decision=decision,
                values=values,
                actor=f"line_client:{line_user_id}",
                kind=kind,
            )
    except Exception:
        logger.exception("[line_client_answer] record_decision 落库失败")
        return None


def _close_siblings(tenant_id, workspace_client_id, work_order_id, item_id, applied_qid) -> None:
    """同票(同 item)其它 active 问题顺手转 resolved_internally(主窗修正 1 之①)。
    uq_lcq_active_item 已保证同票同时至多一个 active 问题,这里遍历是防御性收口
    (数据异常/未来约束放宽时仍正确),常态下不会真的找到第二条。"""
    from services.line_binding import line_client_pool_store as pool_store

    try:
        active = pool_store.list_for_client(
            tenant_id, workspace_client_id, statuses=tuple(vocab.ACTIVE_STATUSES)
        )
    except Exception:
        logger.warning("[line_client_answer] 同票兄弟问题查询失败", exc_info=True)
        return
    for row in active:
        if row["id"] == applied_qid:
            continue
        if row["work_order_id"] != work_order_id or row["item_id"] != item_id:
            continue
        try:
            pool_store.transition(tenant_id, row["id"], vocab.RESOLVED_INTERNALLY)
        except pool_store.IllegalTransitionError:
            pass  # 期间已被别处并发关闭(latest-wins),静默放行
        except Exception:
            logger.warning("[line_client_answer] 同票兄弟问题关闭失败", exc_info=True)


def _finish(
    tenant_id,
    qid,
    to_status: str,
    *,
    answer_raw,
    resolution,
    reply_token,
    quote_token,
    line_user_id,
    lang,
    already_handled: bool = False,
) -> None:
    """落池状态 + 回执(§7.2 S5)。回执失败不影响已落库的裁决/状态——上面的
    record_decision/transition 已经提交,这里纯粹是给客户的一条 LINE 消息,丢了
    不该回滚已经生效的裁决。"""
    from services.line_binding import line_client_pool_store as pool_store

    try:
        pool_store.transition(
            tenant_id, qid, to_status, answer_raw=answer_raw, resolution=resolution
        )
    except pool_store.IllegalTransitionError:
        pass  # latest-wins:期间已被别处改写(如会计并发裁了这条),不覆盖
    except Exception:
        logger.warning("[line_client_answer] 池状态跳转失败", exc_info=True)

    if not reply_token:
        return
    try:
        copy = _ack_copy(to_status, already_handled)
        text = copy.get(lang or "") or copy["th"]
        from services.line_binding import line_reply

        line_reply.reply_text_context(
            reply_token,
            text,
            quote_token=quote_token or "",
            line_user_id=line_user_id,
            tenant_id=tenant_id,
        )
    except Exception:
        logger.warning("[line_client_answer] 回执发送失败(裁决已落库不受影响)", exc_info=True)


def _ack_copy(to_status: str, already_handled: bool) -> dict:
    if already_handled:
        return _ALREADY_HANDLED_COPY
    if to_status == vocab.APPLIED:
        return _APPLIED_COPY
    return _MANUAL_COPY
