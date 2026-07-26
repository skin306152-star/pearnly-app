# -*- coding: utf-8 -*-
"""管家大脑层:一句话 → 闭集里的一个工具 + 参数(降级信封 fail-closed)。

范式照 services/front_desk/interpret.py(同一个 /ai 面、同一条 taxops.intent 车道):
  ① 闭集:大脑只准从 registry.TOOLS 里选一个 name,枚举外一律归 OUT_OF_SCOPE
     (parse_plan 是机器面,不悄悄采信编造的工具名);提示词亦写死「不认识→out_of_scope」。
  ② 零副作用:本模块只问模型,不碰任何业务表。
  ③ fail-closed 降级:超时/异常/坏形状 → degraded=True,上层出降级卡,绝不上抛。
  ④ 模型不算账:提示词禁止它在 message 里写任何数字——数字只能由工具返回后由 copy.py 填。

刻意不把客户名录喂进提示词(与 front_desk 的差别):管家要的是「用户嘴里那个词」,名录里的
正式全名反而会让模型把 "sister" 改写成 "Sister Makeup Co.,Ltd.",在 slots 的 user_text 接地
闸上被判编造。改成模型原样抄用户的词 + tools 侧对名录做确定性模糊匹配,两头都硬。

归因:调用前 set_attribution(task="steward_plan", tenant_id, trace_id=session_id),成本按
trace_id 落 ai_usage(单次预算 <฿0.1,utterance 截断 ≤2000 字符)。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.agent import reply_guard
from services.front_desk.interpret import (
    DEGRADED_BAD_OUTPUT,
    DEGRADED_BRAIN_ERROR,
    DEGRADED_TIMEOUT,
)
from services.steward import registry

logger = logging.getLogger(__name__)

TASK = "steward_plan"

_MAX_UTTERANCE = 2000
_MAX_HISTORY_TURNS = 6
_MAX_ARG_LEN = 200
_TIMEOUT_S = 15

_PROMPT_TEMPLATE = """你是泰国代账事务所的智能管家,坐在会计的工作台上。会计说一句话,你判断该用哪个工具去查,
然后把工具名和参数交给系统去执行。你只负责听懂和挑工具——查数、算数、组织数字全归系统。

可用工具(闭集,只准从下面选一个 name 原样输出):
{catalog}

参数说明:
{slot_hints}

硬规则:
1. 认不出该用哪个工具,或会计只是闲聊/问知识/要你改数据推送数据 → tool 必须是 "out_of_scope"。
   严禁编造列表外的工具名。这一版只读:任何"改/删/推送/开单/审批"类请求一律 out_of_scope。
2. 参数里的客户名、关键词必须原样抄会计说的那几个字,不许补全成正式全名、不许翻译、不许猜。
   会计没提到的参数一律给 null。
3. message 只在 tool 是 "out_of_scope" 时写,用会计说话的语言解释你为什么帮不上、能帮什么。
   选了工具时 message 留空字符串。
4. 任何情况下都不要在 message 里写数字(金额、条数、家数、日期)——你没查过库,数字由系统填。
5. 只输出一个 JSON 对象,不带任何其他文字。
{history}
会计说:{utterance}

输出 JSON 形状:
{{"tool": "...", "args": {{}}, "message": ""}}"""


def build_prompt(utterance: str, history: Optional[list] = None) -> str:
    """确定性拼 prompt(判卷与真调同源)。history 是最近几轮 [{role, text}],只作上下文。"""
    return _PROMPT_TEMPLATE.format(
        catalog=registry.catalog(),
        slot_hints=registry.slot_hints(),
        history=_history_block(history),
        utterance=utterance,
    )


def _history_block(history: Optional[list]) -> str:
    turns = [
        f'{h.get("role", "")}: {h.get("text", "")}'.strip()
        for h in (history or [])[-_MAX_HISTORY_TURNS:]
        if (h.get("text") or "").strip()
    ]
    if not turns:
        return ""
    return "\n最近几轮对话(仅供理解上下文,只判下面这句):\n" + "\n".join(turns) + "\n"


def parse_plan(data) -> dict:
    """模型回复 → 规范化计划。越界一律收敛成安全值,不悄悄采信编造:
      tool 不在注册表 → out_of_scope;args 非 dict → 空;message 失控 → 丢弃(出口护栏)。
    非 dict(坏形状)→ bad_shape=True,上层据此降级(诚实认降级,不装懂)。"""
    if not isinstance(data, dict):
        return {"tool": registry.OUT_OF_SCOPE, "args": {}, "message": "", "bad_shape": True}
    raw_tool = str(data.get("tool") or "").strip()
    tool = raw_tool if registry.is_known(raw_tool) else registry.OUT_OF_SCOPE
    args = data.get("args")
    message = str(data.get("message") or "").strip()
    if message and not reply_guard.sane(message):
        message = ""  # 失控生成绝不原样发给用户(换任何大脑都可能偶发抽风)
    return {
        "tool": tool,
        "args": _clean_args(args) if tool != registry.OUT_OF_SCOPE else {},
        "message": message,
        "bad_shape": False,
    }


def _clean_args(args) -> dict:
    """只留标量、截断长度。接地(值到底可不可信)在 services/agent/slots.py,不在这里。"""
    if not isinstance(args, dict):
        return {}
    out = {}
    for key, value in args.items():
        if value is None or isinstance(value, (dict, list)):
            continue
        text = str(value).strip()
        if text:
            out[str(key)] = text[:_MAX_ARG_LEN]
    return out


def _default_ask(prompt: str, *, tenant_id=None, trace_id=None):
    """经网关问一次(taxops.intent 车道 · 15s 超时)。模型名永不出现于本文件(闸-Q4)。"""
    from services.ai_gateway import transport
    from services.ai_gateway.providers.openai import TAXOPS_INTENT_TIER

    return transport.text_to_json(
        prompt,
        tier=TAXOPS_INTENT_TIER,
        backend="openai",
        temperature=0.0,
        timeout_s=_TIMEOUT_S,
        task=TASK,
        tenant_id=tenant_id,
        trace_id=trace_id,
    )


ask_model = _default_ask  # 注入点:测试直接 patch,零真调用


def _degraded(reason: str, cost_thb: float = 0.0) -> dict:
    return {
        "degraded": True,
        "reason": reason,
        "tool": registry.OUT_OF_SCOPE,
        "args": {},
        "message": "",
        "cost_thb": cost_thb,
    }


def plan(
    utterance: str,
    *,
    tenant_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    history: Optional[list] = None,
) -> dict:
    """一句话 → {degraded, reason, tool, args, message}。任何炸法收敛成 degraded,绝不上抛。"""
    from services.ai_gateway.attribution import reset_attribution, set_attribution

    prompt = build_prompt((utterance or "")[:_MAX_UTTERANCE], history)
    token = set_attribution(TASK, tenant_id=tenant_id, trace_id=trace_id)
    try:
        outcome = ask_model(prompt, tenant_id=tenant_id, trace_id=trace_id)
        # 成本随计划出去(orchestrator 拿它结算预算占坑):降级的调用也可能已计费,如实带。
        cost = float(getattr(outcome, "cost_thb", 0.0) or 0.0)
        if not outcome.ok:
            return _degraded(
                DEGRADED_TIMEOUT if outcome.error_kind == "timeout" else DEGRADED_BRAIN_ERROR,
                cost_thb=cost,
            )
        parsed = parse_plan(outcome.data)
        if parsed.pop("bad_shape"):
            return _degraded(DEGRADED_BAD_OUTPUT, cost_thb=cost)
        return {"degraded": False, "reason": None, "cost_thb": cost, **parsed}
    except Exception:  # noqa: BLE001 — 大脑层任何炸法都不许波及对话/别的入口
        logger.warning("[steward.planner] brain call failed; degrading", exc_info=True)
        return _degraded(DEGRADED_BRAIN_ERROR)
    finally:
        reset_attribution(token)
