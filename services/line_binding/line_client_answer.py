# -*- coding: utf-8 -*-
"""客户回答回写(D2 方案 §4 / §7.2 S5)· webhook 拦截 + NL 解析 + record_decision。

消费边界(主窗拍板修正 2/3,硬门):判「是否被本池吃掉」全程只读零副作用,判不出/闸关/
无 pending 一律 return False 回落原路(fail-open)绝不半吞;越过 _consume 视为已受理,
下游失败只兜底转人审不再回落(防同一条消息又被大脑记账路径处理第二遍)。回写前重读该票
事件流:问题创建后若已有人工裁决 → 不覆盖(latest-wins 护会计裁决),转 resolved_internally
回「已处理」。裁决词全 import decisions、状态词全 import client_pool_vocab,不新造裁决通道。
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_answer_copy
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
    """反查该 sender 名下客户联系人,挑闸开租户里「最近 sent_at」那一批问题。

    一个业主可能挂多主体(§1.3),候选口径:只在还有 ≥1 条 pending 的批次里挑(无 pending
    说明没在等这位客户),跨全部候选取 pending 行 sent_at 最大者所属批次。选定后取该批次
    【全状态】行交 _consume,由行自带的 batch_seq(推送时落的固定编号)定位「第 N 题」,不
    随期间某题答完退出 pending、列表收缩而位移(R3 串题已根治)。闸关租户直接跳过。
    """
    from core import feature_flags
    from services.line_binding import line_client_contact
    from services.line_binding import line_client_pool_store as pool_store

    contacts = line_client_contact.list_contacts_by_line_user(line_user_id)
    if not contacts:
        return None

    best = None  # (latest_sent_at, tenant_id, workspace_client_id, batch_id, lang)
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
        top = max(rows, key=lambda r: r["sent_at"])
        if best is None or top["sent_at"] > best[0]:
            best = (
                top["sent_at"],
                tenant_id,
                contact["workspace_client_id"],
                top.get("batch_id"),
                contact.get("preferred_lang"),
            )
    if best is None:
        return None

    _, tenant_id, workspace_client_id, batch_id, lang = best
    return {
        "tenant_id": tenant_id,
        "workspace_client_id": workspace_client_id,
        "rows": pool_store.list_batch(tenant_id, workspace_client_id, batch_id),
        "lang": lang,
    }


def _is_strict_short_form(text: str) -> bool:
    """短答形态(b):trim+剥离礼貌尾缀后=某关键词本身(如「ซื้อค่ะ」);不含编号。"""
    core = _POLITE_TAIL_RE.sub("", (text or "").strip()).strip()
    return core in _ANSWER_KEYWORDS


def _looks_like_answer(text: str) -> bool:
    """严格答题形态(长句含关键词 ≠ 答题):(a) 编号段命中关键词,或 (b) 整条=关键词本身。"""
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
    full_rows = selected["rows"]  # 完整批次(全状态)
    pending_rows = [r for r in full_rows if r["status"] == vocab.PENDING]
    lang = selected["lang"]
    # 编号→行:batch_seq 持久列是单一事实源(推送时 mark_sent 落的固定编号);迁移前存量批次
    # 无 batch_seq 时回落按位序(1..N,与旧行为一致)。整批要么全有列要么全 NULL(mark_sent
    # 原子盖整批),故一次性选定 locator,越界编号 .get 自然落 None,不再靠两侧排序对齐(R3 根治)。
    by_seq = {r["batch_seq"]: r for r in full_rows if r.get("batch_seq") is not None}
    locator = by_seq or {i + 1: r for i, r in enumerate(full_rows)}

    segments = _split_numbered_segments(text)
    if segments:
        matched = False
        for num, seg in segments:
            row = locator.get(num)
            if row is None:
                continue
            matched = True
            # 终态槽(客户重复答已处理的票)由 _handle_one 顶部统一挡下,回「已处理」不重复裁决。
            _handle_one(
                tenant_id,
                workspace_client_id,
                row,
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
            tenant_id, pending_rows, text, line_user_id, reply_token, quote_token, lang
        )
        return

    if len(pending_rows) == 1:
        # 无编号且此刻恰只剩一道 pending → 落它。此路径【故意】依赖实时 pending 态(与编号路径锚
        # 固定序相反):无号答案本无固定槽位可锚,"只剩一道就落它"是有界便利,别按"锚固定序"直觉改。
        # 唯一「段」是整条原文,只有短答形态(b)才自动裁决。
        _handle_one(
            tenant_id,
            workspace_client_id,
            pending_rows[0],
            text,
            line_user_id,
            reply_token,
            quote_token,
            lang,
            force_manual=not _is_strict_short_form(text),
        )
        return

    _handle_unlocatable(tenant_id, pending_rows, text, line_user_id, reply_token, quote_token, lang)


def _handle_unlocatable(
    tenant_id, pending_rows, text, line_user_id, reply_token, quote_token, lang
):
    """定位不出具体哪条(编号全越界 / 多条 pending 又没编号)→ 保守挂首条 pending 转人审,
    原文留底给会计判断(§4.2「宁可交人不瞎猜」;只挂 pending 行,不误动已终态题)。"""
    if not pending_rows:
        logger.info("[line_client_answer] 无 pending 可挂 · 放弃(消息已受理不回落)")
        return
    target_id = pending_rows[0]["id"]
    logger.info("[line_client_answer] 定位不出具体问题 · 默认挂首条 pending qid=%s", target_id)
    _finish(
        tenant_id,
        target_id,
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

    if question["status"] in vocab.TERMINAL_STATUSES:
        # 编号指向已处理过的票(客户重复答)→ 只回「已处理」不重复裁决(终态→终态非法跳转被
        # latest-wins 吞成 no-op)。无号单 pending 路径传入的必是 pending,此守卫对它是 no-op。
        _finish(
            tenant_id,
            qid,
            question["status"],
            answer_raw=None,
            resolution=None,
            reply_token=reply_token,
            quote_token=quote_token,
            line_user_id=line_user_id,
            lang=lang,
            already_handled=True,
        )
        return

    # force_manual:segment 非严格答题形态(见 _consume)→ 直接当解不出,不喂给 _resolve。
    outcome = None if force_manual else _resolve(question["question_type"], segment)

    if outcome is not None and _decided_after(
        tenant_id, work_order_id, item_id, question.get("created_at")
    ):
        # 修正 2 硬门:该票在问题创建后已有人工裁决(会计已处理过)→ 不覆盖,回「已处理」。
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

    # 解不出(含 force_manual)或裁决落库失败 → 同归人审,原文留底,绝不假装成功也不吞。
    event = None
    if outcome is not None:
        decision, kind, values = outcome
        event = _record_decision(
            tenant_id, work_order_id, item_id, decision, kind, values, line_user_id
        )
    if event is None:
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
    _resume_run(tenant_id, work_order_id, line_user_id)


def _decided_after(tenant_id, work_order_id, item_id, question_created_at) -> bool:
    """竞态守卫(修正 2):该票在问题创建后是否已落过人工裁决。读不到(冻结/异常)保守当已处理。"""
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


def _resume_run(tenant_id, work_order_id, line_user_id) -> None:
    """裁决落库后自动续跑工单(P-7 LINE 径,MC2-A1 补的漏接):客户答完题不再停等会计手点
    /run。尽力而为——裁决已提交,续跑排程失败绝不连坐回写(照 _auto_advance 的
    mutation-already-committed 语义),最多退化成会计手点一次。"""
    from services.workorder import runner

    try:
        runner.request_run(str(tenant_id), str(work_order_id), actor=f"line_client:{line_user_id}")
    except Exception:  # noqa: BLE001 - 自驱是增益不是主路径
        logger.warning("[line_client_answer] 自动续跑排程失败(裁决已落库不受影响)", exc_info=True)


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
    """同票其它 active 问题顺手转 resolved_internally(修正 1 之①)。uq_lcq_active_item
    已保证同票至多一个 active,遍历是防御性收口,常态找不到第二条。"""
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
    """落池状态 + 回执(§7.2 S5)。跳转失败/latest-wins 不阻塞回执,回执失败不回滚裁决。"""
    from services.line_binding import line_client_pool_store as pool_store

    try:
        pool_store.transition(
            tenant_id, qid, to_status, answer_raw=answer_raw, resolution=resolution
        )
    except pool_store.IllegalTransitionError:
        pass  # latest-wins:期间已被别处改写(如会计并发裁了这条)/终态复答,不覆盖
    except Exception:
        logger.warning("[line_client_answer] 池状态跳转失败", exc_info=True)

    if not reply_token:
        return
    try:
        copy = line_client_answer_copy.ack_copy(to_status, already_handled)
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
