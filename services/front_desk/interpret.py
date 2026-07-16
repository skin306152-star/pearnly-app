# -*- coding: utf-8 -*-
"""前门大脑解析(FD-0b 实装)· utterance → 闭集意图 / 客户建议 / 期间建议。

用户一句话目标经 taxops.intent 车道(routing_matrix · 独立旋钮 TAXOPS_INTENT_MODEL)归成
结构化建议,供合同卡预填。解析只出「建议」——真正开工单永远在人点确认之后(confirm 端点),
本模块零写业务表,只只读 workspace_clients 名录做引用校验。

硬闸(代码强制,不靠自觉):
  ① 闭集意图:大脑只准从 intents 注册表枚举 + unsupported 里选,枚举外一律归 unsupported
     (parse_output 机器面,不悄悄采信编造意图)。prompt 亦写死「不认识→unsupported 禁止编造」。
  ② 引用校验:客户建议只准引用本租户真实 workspace_client_id;查无此 id → 建议置空(防大脑
     编 id 把 A 客户料挂到 B——账套红线)。
  ③ 零写业务表:interpret 只读客户名录,不写任何表;工具执行全在人确认之后。
  ④ fail-closed 降级:超时(15s)/异常/闸关 → degraded=True,前端出降级卡。大脑任何故障都被
     本模块吞成 degraded,绝不上抛——手动开单是另一条端点,零共享故障面。

归因:调用前 set_attribution(task="front_desk_interpret", tenant_id, trace_id=contract_id),
成本按 trace_id 落 ai_usage,超管成本页可查(单次预算 <฿0.1,utterance 截断 ≤2000 字符)。

两个入口:
  interpret(utterance, tenant_id, contract_id)  路由用:自取真实客户名录 → 降级信封
    {degraded, intent, client_suggestion, period, reason}。
  interpret_utterance(utterance, known_clients, closed_intents, trace_id)  判卷 CLI 用:显式
    传名录/闭集,返模型原始结构 {intent, client_id, period}(同卷可评测)。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Optional

from core import feature_flags
from services.front_desk import intents

logger = logging.getLogger(__name__)

TASK = "front_desk_interpret"
UNSUPPORTED = intents.UNSUPPORTED

_MAX_UTTERANCE = 2000  # §3.3:单次解析预算 ~1-2k token,超长截断
_MAX_CLIENTS = 100  # 名录候选封顶(prompt 预算·超量截断,confirm 仍须人点)
_TIMEOUT_S = 15  # §3.3:超时降级

# 降级原因(前端据此区分 degraded 类型;不覆盖 intent 语义:unsupported 走 intent 字段不走这里)。
DEGRADED_FLAG_OFF = "flag_off"
DEGRADED_TIMEOUT = "brain_timeout"
DEGRADED_BRAIN_ERROR = "brain_error"
DEGRADED_BAD_OUTPUT = "bad_output"

# 路由用闭集:注册表全集(含未开放意图)+ unsupported 哨兵。confirm 只放行 enabled 子集。
_ROUTE_CLOSED_INTENTS = tuple(intents.ALL_IDS) + (UNSUPPORTED,)

# ── 期间线索解析(容佛历缩写·纯函数·单一事实源;判卷 CLI 复用) ──────────────────────
# 解不出诚实返回 None,绝不猜——期间是「建议」,合同卡上人可改,宁缺毋错。
_THAI_MONTH_ABBR = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}
_THAI_BE_ABBR_RE = re.compile(
    "(" + "|".join(re.escape(k) for k in _THAI_MONTH_ABBR) + r")\s*(\d{2})\b"
)
_ZH_MONTH_RE = re.compile(r"(\d{1,2})\s*月")
_ISO_YM_RE = re.compile(r"\b(\d{4})[-/](\d{1,2})\b")
_LAST_MONTH_WORDS = ("เดือนที่แล้ว", "上个月", "last month", "先月")
_THIS_MONTH_WORDS = ("เดือนนี้", "这个月", "this month", "今月")
_EN_MONTH_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _backfill_year(month: int, today: date) -> str:
    """裸月份(无年份)按「不晚于今天」就近补年:晚于本月则退去年(会计谈已过去的期间)。"""
    year = today.year if month <= today.month else today.year - 1
    return f"{year:04d}-{month:02d}"


def parse_period_hint(hint: Optional[str], today: date) -> Optional[str]:
    """期间原文线索 → 规范 "YYYY-MM"(公历)。容佛历缩写、相对词、裸月份、ISO;解不出返回 None。"""
    if not hint:
        return None
    text = str(hint).strip()
    if not text:
        return None

    m = _THAI_BE_ABBR_RE.search(text)
    if m:
        month = _THAI_MONTH_ABBR[m.group(1)]
        ce_year = 1957 + int(m.group(2))  # BE 25xx → CE:2500+xx-543 = 1957+xx
        return f"{ce_year:04d}-{month:02d}"

    iso = _ISO_YM_RE.search(text)
    if iso:
        year, month = int(iso.group(1)), int(iso.group(2))
        if 1 <= month <= 12:
            if year >= 2400:  # 明显佛历年 → 折算公历
                year -= 543
            return f"{year:04d}-{month:02d}"

    lowered = text.lower()
    if any(w in text or w in lowered for w in _LAST_MONTH_WORDS):
        year, month = today.year, today.month - 1
        if month == 0:
            year, month = year - 1, 12
        return f"{year:04d}-{month:02d}"
    if any(w in text or w in lowered for w in _THIS_MONTH_WORDS):
        return f"{today.year:04d}-{today.month:02d}"

    zh_m = _ZH_MONTH_RE.search(text)
    if zh_m and 1 <= int(zh_m.group(1)) <= 12:
        return _backfill_year(int(zh_m.group(1)), today)

    for name, month in _EN_MONTH_NUM.items():
        if name in lowered:
            return _backfill_year(month, today)

    return None


# ── prompt(硬规则写死;与 parse_output 一一对应——prompt 防君子,parse 防小人) ──────────
_PROMPT_TEMPLATE = """你是泰国代账事务所的前台助理。会计说了一句目标,你把它归成一个结构化建议,供人确认。
只做归类,不执行任何操作——真正开工永远等会计在界面上点确认。

可选意图(闭集,只准从下面选一个 id,原样输出):
{intents}

硬规则:
1. 认不出属于哪个意图,或只是寒暄/闲聊/知识问答/要求跳过人工审批 → intent 必须是 "unsupported"。
   严禁编造列表外的意图,严禁把不支持的活(如年度所得税 ภ.ง.ด.50/51、社保 สปส.)硬套成别的意图。
2. client_id 只准从下面客户名录里选一个 id 原样返回;会计没点名、或名录里找不到对应客户 → 给 null,
   绝不猜、绝不编 id(挂错账套是红线)。
3. period 是会计话里的期间线索原文(如 "มิ.ย.69" / "上个月" / "June" / "2569-05");没提到给 null。
4. 一句话夹带多个意图,只取主意图(会计最想先做的那件),其余忽略。
5. 只输出一个 JSON 对象,不带任何其他文字。

客户名录(只准引用以下 id):
{clients}
{inventory}
会计说({lang}):{utterance}

输出 JSON 形状:
{{"intent": "...", "client_id": null, "period": null}}"""


def build_prompt(
    utterance: str,
    known_clients: list,
    closed_intents,
    *,
    lang: str = "auto",
    inventory_summary: Optional[dict] = None,
) -> str:
    """确定性拼 prompt(判卷 CLI 与真调同源,保证考的就是产线 prompt)。名录空时明示无候选。"""
    clients_txt = (
        "\n".join(f"  - {c['id']}: {c.get('name') or ''}".rstrip() for c in known_clients)
        or "  (无·会计未建档或未选客户,client_id 一律 null)"
    )
    intents_txt = "\n".join(f"  - {i}" for i in closed_intents)
    inv_txt = ""
    if inventory_summary:
        inv_txt = f"\n已投料盘点摘要(零成本信号,仅供参考):\n  {json.dumps(inventory_summary, ensure_ascii=False)}\n"
    return _PROMPT_TEMPLATE.format(
        intents=intents_txt,
        clients=clients_txt,
        inventory=inv_txt,
        lang=lang,
        utterance=utterance,
    )


# ── 机械校验(硬闸①②的机器面:枚举外意图归 unsupported·编造客户 id 归 null) ────────────
def parse_output(data, *, closed_intents, known_ids, today: date) -> dict:
    """模型回复 → 规范化建议。任何越界都收敛成安全值,不悄悄采信编造:
      intent 不在闭集 → unsupported;client_id 不在名录 → None;period 经 parse_period_hint 规范。
    非 dict(坏形状)→ bad_shape=True,上层据此降级(不是「装懂」而是诚实认降级)。"""
    if not isinstance(data, dict):
        return {"intent": UNSUPPORTED, "client_id": None, "period": None, "bad_shape": True}
    closed = set(closed_intents)
    intent_raw = str(data.get("intent") or "").strip()
    intent = intent_raw if intent_raw in closed else UNSUPPORTED

    cid_raw = data.get("client_id")
    if cid_raw is None:
        cid_raw = data.get("workspace_client_id")
    client_id = str(cid_raw) if cid_raw is not None and str(cid_raw) in known_ids else None

    period = parse_period_hint(data.get("period"), today)
    return {"intent": intent, "client_id": client_id, "period": period, "bad_shape": False}


# ── 大脑调用(注入点:测试 patch interpret.ask_model / fetch_clients,零真调用) ──────────
def _default_ask(prompt: str, *, tenant_id=None, trace_id=None):
    """经网关问一次(taxops.intent 车道·openai 后端·15s 超时)。模型名永不出现于本文件(闸-Q4)。"""
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


ask_model = _default_ask


def _default_fetch_clients(tenant_id: str) -> list:
    """本租户客户名录(引用校验用·只读)。名录封顶 _MAX_CLIENTS(prompt 预算)。"""
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT id, name, tax_id FROM workspace_clients "
            "WHERE tenant_id = %s ORDER BY created_at, id LIMIT %s",
            (tenant_id, _MAX_CLIENTS),
        )
        return [dict(r) for r in cur.fetchall()]


fetch_clients = _default_fetch_clients


def _reason_for_error(error_kind: Optional[str]) -> str:
    return DEGRADED_TIMEOUT if error_kind == "timeout" else DEGRADED_BRAIN_ERROR


def _degraded_core(reason: str) -> dict:
    return {
        "degraded": True,
        "reason": reason,
        "intent": UNSUPPORTED,
        "client_id": None,
        "period": None,
    }


def _interpret_core(
    utterance: str,
    *,
    known_clients: list,
    closed_intents,
    tenant_id: Optional[str],
    trace_id: Optional[str],
    today: date,
    inventory_summary: Optional[dict] = None,
) -> dict:
    """一次解析(纯编排):归因 → 问大脑 → 机械校验。任何炸法收敛成 degraded,绝不上抛。"""
    from services.ai_gateway.attribution import reset_attribution, set_attribution

    prompt = build_prompt(
        utterance, known_clients, closed_intents, inventory_summary=inventory_summary
    )
    token = set_attribution(TASK, tenant_id=tenant_id, trace_id=trace_id)
    try:
        outcome = ask_model(prompt, tenant_id=tenant_id, trace_id=trace_id)
        if not outcome.ok:
            return _degraded_core(_reason_for_error(outcome.error_kind))
        known_ids = {str(c["id"]) for c in known_clients}
        parsed = parse_output(
            outcome.data, closed_intents=closed_intents, known_ids=known_ids, today=today
        )
        if parsed.pop("bad_shape"):
            return _degraded_core(DEGRADED_BAD_OUTPUT)
        return {"degraded": False, "reason": None, **parsed}
    except Exception:  # noqa: BLE001 — 硬闸④:大脑层任何炸法都不许波及调用方/手动开单路径
        logger.warning("[front_desk.interpret] brain call failed; degrading", exc_info=True)
        return _degraded_core(DEGRADED_BRAIN_ERROR)
    finally:
        reset_attribution(token)


def interpret_utterance(
    utterance: str,
    *,
    known_clients: list,
    closed_intents,
    trace_id: Optional[str] = None,
    today: Optional[date] = None,
) -> dict:
    """判卷 CLI 入口:显式名录/闭集 → 模型原始结构 {intent, client_id, period}(同卷可评测)。"""
    out = _interpret_core(
        (utterance or "")[:_MAX_UTTERANCE],
        known_clients=list(known_clients),
        closed_intents=list(closed_intents),
        tenant_id=None,
        trace_id=trace_id,
        today=today or date.today(),
    )
    return {"intent": out["intent"], "client_id": out["client_id"], "period": out["period"]}


def _to_ws_id(client_id: Optional[str]) -> Optional[int]:
    """名录 id 字符串 → workspace_client_id(int)。非法/空 → None(引用校验已保证 ⊆ 真实名录)。"""
    if client_id is None:
        return None
    try:
        return int(client_id)
    except (TypeError, ValueError):
        return None


def interpret(
    utterance: str,
    *,
    inventory_summary: Optional[dict] = None,
    tenant_id: Optional[str] = None,
    contract_id: Optional[str] = None,
) -> dict:
    """路由入口:自取真实客户名录 → 解析 → 降级信封。

    返回 {degraded, intent, client_suggestion, period, reason}:
      degraded=True  → intent/client/period 全空 + reason(降级卡)。
      intent==unsupported → 诚实拒绝(拒绝卡),client/period 可空。
      否则 intent=闭集 id + client_suggestion(int|None)+ period(YYYY-MM|None)(合同卡)。
    """
    utterance = (utterance or "")[:_MAX_UTTERANCE]
    try:
        if tenant_id and not feature_flags.pearnly_ai_front_desk_enabled_for(tenant_id):
            return _envelope(_degraded_core(DEGRADED_FLAG_OFF))
        clients = fetch_clients(tenant_id) if tenant_id else []
        known = [{"id": str(c["id"]), "name": c.get("name")} for c in clients]
        out = _interpret_core(
            utterance,
            known_clients=known,
            closed_intents=list(_ROUTE_CLOSED_INTENTS),
            tenant_id=tenant_id,
            trace_id=contract_id,
            today=date.today(),
            inventory_summary=inventory_summary,
        )
        return _envelope(out)
    except Exception:  # noqa: BLE001 — 硬闸④:即便名录读取等前置步骤炸,也只降级不上抛
        logger.warning("[front_desk.interpret] failed; degrading", exc_info=True)
        return _envelope(_degraded_core(DEGRADED_BRAIN_ERROR))


def _envelope(out: dict) -> dict:
    """core 结果 → 前端信封(degraded 时清空建议;client_id 字符串折回 workspace_client_id)。"""
    if out["degraded"]:
        return {
            "degraded": True,
            "intent": None,
            "client_suggestion": None,
            "period": None,
            "reason": out["reason"],
        }
    return {
        "degraded": False,
        "intent": out["intent"],
        "client_suggestion": _to_ws_id(out["client_id"]),
        "period": out["period"],
        "reason": None,
    }
