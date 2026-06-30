# -*- coding: utf-8 -*-
"""参数确定性闸(M1-SOCKET-DESIGN §5)—— 安全核心。

铁律(记忆里钉的):连满分模型都会在边角编造单号/金额。所以接地闸不靠模型自觉 ——
大脑给的每个参数,执行前必须证明它来自【用户原话 / 锚点 / 端点配置 / 上一步结果 / 纯文本检索】
之一,否则进 missing(必填→反问)或 rejected(编造→丢弃+审计),绝不带编造值去执行。

泛化自 services/expense/line_l2.py:amount_grounded(原文找不到对应 → 不采信)。
"""

from __future__ import annotations

from typing import Optional

from services.agent import manifest
from services.agent.contracts import AgentAction, AgentContext, SlotCheck, SlotSpec

_MAX_FREEFORM = 100


def _texts(user_text: str, history: Optional[list]) -> str:
    """用户原话 + 近期对话,小写拼一起供子串接地。"""
    parts = [user_text or ""]
    parts += [h.get("content", "") for h in (history or []) if (h.get("content") or "").strip()]
    return "\n".join(parts).lower()


def _appears_in_text(value: str, blob: str) -> bool:
    v = (value or "").strip().lower()
    return bool(v) and v in blob


def _ground(
    slot: SlotSpec, value, *, blob: str, ctx: AgentContext
) -> tuple[bool, object, Optional[str]]:
    """单 slot 接地。返回 (ok, 可信值, 失败原因)。"""
    if slot.source == "model_freeform":
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
