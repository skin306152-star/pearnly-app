# -*- coding: utf-8 -*-
"""参数确定性闸(M1-SOCKET-DESIGN §5)—— 安全核心。

铁律(记忆里钉的):连满分模型都会在边角编造单号/金额。所以接地闸不靠模型自觉 ——
大脑给的每个参数,执行前必须证明它来自【用户原话 / 锚点 / 端点配置 / 上一步结果 / 纯文本检索】
之一,否则进 missing(必填→反问)或 rejected(编造→丢弃+审计),绝不带编造值去执行。

泛化自 services/expense/line_l2.py:amount_grounded(原文找不到对应 → 不采信)。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.agent import manifest
from services.agent.contracts import AgentAction, AgentContext, SlotCheck, SlotSpec

_MAX_FREEFORM = 100

# 数字接地的取词与清洗:千分位逗号、货币符、百分号是排版不是数值,两侧都先剥掉再按值比。
# token 里不含空白 —— "1 ใบ 200 บาท" 合成 1200 会把两个数字粘成一个不存在的金额。
_NUM_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?")
_NUM_NOISE = str.maketrans("", "", ", ฿%")


def _texts(user_text: str, history: Optional[list]) -> str:
    """用户原话 + 近期对话,小写拼一起供子串接地。"""
    parts = [user_text or ""]
    parts += [h.get("content", "") for h in (history or []) if (h.get("content") or "").strip()]
    return "\n".join(parts).lower()


def _as_number(text: str) -> Optional[Decimal]:
    """排版剥干净后转 Decimal:「10,700」「฿10700」「3%」都认;不是纯数字一律 None。"""
    cleaned = (text or "").translate(_NUM_NOISE)
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def _numbers_in(blob: str) -> set:
    """用户原话里真出现过的数值集合(数值相等的 Decimal 哈希相同,可直接查集合)。"""
    out = set()
    for token in _NUM_TOKEN.findall(blob):
        value = _as_number(token)
        if value is not None:
            out.add(value)
    return out


def _appears_in_text(value: str, blob: str) -> bool:
    """字面接地;字面对不上且值是纯数字时,再按【数值】接地一次。

    金额天生带排版:会计打「10,700 含税的」,模型交回 10700,逐字比会把真数判成编造,
    追问一轮等于逼人重打一遍。数值面只认用户原话里真出现过的那些数(集合取自 blob),
    编造的数照样进不来。

    只加不减:字面能接地的一律照旧放行 —— 这道闸是 LINE Agent 与管家共用的安全核心,
    收紧字面判据会连带改掉别处的单号/税号接地口径,不在本次改动的射程里。
    """
    v = (value or "").strip().lower()
    if not v:
        return False
    if v in blob:
        return True
    number = _as_number(v)
    return number is not None and number in _numbers_in(blob)


def _ground(
    slot: SlotSpec, value, *, blob: str, ctx: AgentContext
) -> tuple[bool, object, Optional[str]]:
    """单 slot 接地。返回 (ok, 可信值, 失败原因)。"""
    if slot.source == "model_freeform":
        if isinstance(value, (list, tuple)):
            # 列表槽(如 plan 的 goals 枚举)保形状逐元清洗;str() 压平会把枚举毁成 "['x']"。
            vals = [str(v).strip()[:_MAX_FREEFORM] for v in value if str(v).strip()]
            return True, vals[:10], None
        return True, str(value).strip()[:_MAX_FREEFORM], None
    if slot.source == "user_text":
        if _appears_in_text(str(value), blob):
            return True, str(value).strip(), None
        return False, None, "not_in_user_text"
    if slot.source == "anchor":
        anchored = ctx.anchors.get(slot.name)
        return (True, anchored, None) if anchored is not None else (False, None, "no_anchor")
    if slot.source == "endpoint_config":
        cfg = ctx.endpoint_config.get(slot.name)
        return (True, cfg, None) if cfg is not None else (False, None, "no_endpoint_config")
    if slot.source == "prior_result":
        prior = ctx.prior_results.get(slot.name)
        return (True, prior, None) if prior is not None else (False, None, "no_prior_result")
    return False, None, "unknown_source"  # 防御:未知来源一律不采信


def check_slots(
    action: AgentAction,
    *,
    user_text: str,
    history: Optional[list],
    ctx: AgentContext,
    spec=None,
) -> SlotCheck:
    """逐 slot 验接地。spec 缺省从 manifest 取(测试可注入合成 spec)。"""
    spec = spec or manifest.TOOLS_BY_NAME.get(action.tool)
    if spec is None:
        return SlotCheck(ok=False, missing=["__tool__"])

    blob = _texts(user_text, history)
    chk = SlotCheck(ok=True)
    for slot in spec.slots:
        raw = action.args.get(slot.name)
        empty = raw is None or (isinstance(raw, str) and not raw.strip())
        if empty:
            if slot.required:
                chk.missing.append(slot.name)
            continue
        ok, value, reason = _ground(slot, raw, blob=blob, ctx=ctx)
        if ok:
            chk.grounded[slot.name] = value
        else:
            # 值在但接不了地 = 模型猜的。必填→反问;选填→静默丢弃(绝不流到执行)。
            chk.rejected[slot.name] = reason or "ungrounded"
            if slot.required:
                chk.missing.append(slot.name)

    chk.ok = not chk.missing
    return chk
