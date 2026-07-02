# -*- coding: utf-8 -*-
"""M3 确认握手状态机 · resume 闸(LangGraph HITL checkpoint 范式 · 设计见
docs/agent/M3-CONFIRM-HANDSHAKE-DESIGN.md · v1 落地范围=推送卡的文本确认通道)。

推送确认卡本身就是持久化检查点(line_action_nonces · kind=agent_push):v1 不建新表,
resume 闸把 15 分钟内最近一张待确认卡与用户文本"确认/取消"接上,消费与按钮同一 nonce
(后到的撞 used 幂等)。确认判定是确定性词表精确匹配——大脑不参与(钱路红线),
词表不命中一律 None(宁可让用户再说一次,绝不把闲聊当确认)。
泛用检查点表(line_pending_actions)留给第一个无卡片消费者(DMS)落地时再建,不造死库表。
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("mr-pilot")

RECENT_MINUTES = 15  # 会话语境窗:只认这么久内铸的卡(nonce 自身 TTL 72h 是防重放口径)

# 精确匹配词表(归一化后全等)。刻意窄:只收无歧义的确认/取消词——"好/OK/ใช่"这类
# 万能应答词在卡片语境外太常见,v1 不收(误执行代价 ≫ 让用户多打两个字);
# "不确认""确认一下再说"因非全等也不命中 → 走正常轮。
_YES = frozenset(
    {
        "确认",
        "确认推送",
        "確認",
        "confirm",
        "ยืนยัน",
        "ยืนยันเลย",
        "ยืนยันส่ง",
    }
)
_NO = frozenset(
    {
        "取消",
        "不推",
        "别推",
        "取消推送",
        "cancel",
        "ยกเลิก",
        "ไม่ส่ง",
        "キャンセル",
    }
)
# 标点按字符类剥;泰文礼貌词必须按整词剥(字符类会把 ยืนยัน 的词尾 น/ั 也啃掉)。
_PUNCT_RE = re.compile(r"[\s!!。.??~〜]+$")
_POLITE_RE = re.compile(r"(?:ครับ|ค่ะ|คะ|นะ|จ้า|จ้ะ)+$")


def classify(text: str) -> Optional[str]:
    """确认词分类:'yes' / 'no' / None(不猜)。只剥尾部语气词/标点,词身必须全等。"""
    t = _PUNCT_RE.sub("", str(text or "").strip()).lower()
    t = _POLITE_RE.sub("", t).strip()
    if not t or len(t) > 12:
        return None
    if t in _YES:
        return "yes"
    if t in _NO:
        return "no"
    return None


def try_resume(bound_user, reply_token, text, lang, *, tenant_id, line_user_id) -> bool:
    """resume 闸:闸开 + 文本是确认词 + 15 分钟内有待确认推送卡 → 与点按钮同效。

    返回 True = 本轮已消费(handle_postback 已回话);False = 与本机无关,走正常对话轮。
    任何故障 fail-open 回 False——resume 闸挡在所有 LINE 文本最前,绝不许挡正常消息。
    """
    try:
        from core import db, feature_flags

        uid = str((bound_user or {}).get("id") or "")
        if not (uid and tenant_id and feature_flags.agent_confirm_enabled_for(uid)):
            return False
        word = classify(text)
        if word is None:
            return False
        # 泛用检查点(刚复述完等答复,语境最强)优先于推送卡 nonce(设计 §3 消费顺序)。
        # 先读后取:确认词只消费"确实等确认词"的检查点(收件检查点等的是文件/科目号,
        # 用户敲"确认"不该把它吞掉)。
        from services.line_binding import line_pending_actions

        action = line_pending_actions.read_action(str(tenant_id), line_user_id)
        if action:
            handled = _resume_action(
                bound_user, word, lang, action, tenant_id=tenant_id, line_user_id=line_user_id
            )
            if handled:
                return True
        from services.line_binding import line_action_nonce as nonce

        with db.get_cursor_rls(str(tenant_id)) as cur:
            token = nonce.latest_pending(
                cur,
                tenant_id=str(tenant_id),
                user_id=uid,
                kind="agent_push",
                within_minutes=RECENT_MINUTES,
            )
        if not token:
            return False  # 没有语境内的待确认卡:"确认"两字交正常轮(可能在聊别的)
        from services.agent import push_confirm
        from services.line_binding import line_postback

        action = (
            line_postback.ACTION_AGENT_PUSH_CONFIRM
            if word == "yes"
            else line_postback.ACTION_AGENT_PUSH_CANCEL
        )
        user = dict(bound_user)
        user["line_user_id"] = line_user_id
        push_confirm.handle_postback(user, reply_token, action, token, lang)
        logger.info("[confirm_machine] text-%s consumed token=%s...", word, token[:8])
        return True
    except Exception:
        logger.warning("[confirm_machine] resume failed; normal turn", exc_info=True)
        return False


def _resume_action(bound_user, word, lang, action, *, tenant_id, line_user_id) -> bool:
    """泛用检查点分发(先读后取:只在真要消费时 take,单发单用)。
    dms_push=等确认词,是/否都消费;recon_intake=等文件/科目号,只有"取消"消费,
    "确认"与它无关 → False 走后续通道。未知工具=生产者/消费者不同步 → 记日志不消费。"""
    from core import feature_flags
    from services.agent import dms_push, recon_intake
    from services.line_binding import line_pending_actions

    tool = str((action or {}).get("tool") or "")
    uid = str((bound_user or {}).get("id") or "")
    if tool == dms_push.TOOL:
        taken = line_pending_actions.take_action(str(tenant_id), line_user_id)
        if not taken:
            return False  # 并发下已被消费 → 当没看见
        if word == "no" or not feature_flags.agent_dms_enabled_for(uid):
            # 闸中途被关:检查点已取走,按取消处理(诚实,不静默吞)。
            dms_push.cancel(bound_user, str(tenant_id), line_user_id, lang)
            return True
        dms_push.execute_confirmed(bound_user, str(tenant_id), line_user_id, lang, taken)
        logger.info("[confirm_machine] checkpoint-%s consumed tool=%s", word, tool)
        return True
    if tool == recon_intake.TOOL:
        if word != "no":
            return False  # 收件流不吃"确认",检查点保留
        taken = line_pending_actions.take_action(str(tenant_id), line_user_id)
        if taken:
            recon_intake.cancel(bound_user, str(tenant_id), line_user_id, lang, taken)
        return True
    logger.warning("[confirm_machine] unknown pending action tool=%s; ignored", tool)
    return False
