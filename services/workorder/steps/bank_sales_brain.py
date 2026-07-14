# -*- coding: utf-8 -*-
"""大脑分类:银行入账行「是不是销售」判断题(SA-3a 漏斗第 2 层 · 题型 bank_row_sales_or_not)。

确定性规则(bank_sales_suggest)判不了的入账行(既非转出/手续费/取消,又无 EDC 互证)交大脑
判一题:sales / non_sales / cannot_judge。硬闸原样继承 brain_shadow(引用必真、无据必认怂、
钱数永不归大脑、零业务表写)——本模块唯一落点是 append-only 的 bank_sales_suggested 事件
(读侧回放,零重调),不写申报数、不写 journal、不改任何引擎数。

硬闸(代码强制,不靠自觉):
  ① 零改钱:大脑只回分类词,金额一律由 bank_sales_suggest 的确定性求和/÷1.07 算。
  ② 引用必真:cited 只认题面给的行指纹(⊆ 待判行自身),引用不实 = invalid。
  ③ 无据必认怂:prompt 明令 cannot_judge 禁编;parse 层对无引用的实分类判 invalid。
  ④ 异常全隔离:run 任何失败只记 warning 返回摘要,不影响任何主路径。
闸 pearnly_ai_bank_sales_suggest 关:run 直接 no-op(零构题零调用零落库,零支出)。

backend/model 不写死(闸-Q4):默认走 routing_matrix 的 openai + taxops_verdict 档(模型名由
env 定),评测可切臂;模型名永不出现在本文件。
"""

from __future__ import annotations

import json
import logging
import os

from core import feature_flags
from services.ai_gateway.providers.openai import TAXOPS_VERDICT_TIER
from services.workorder import store
from services.workorder.steps import bank_sales_suggest as engine
from services.workorder.steps.bank_sales_suggest import CANNOT_JUDGE, NON_SALES, SALES

logger = logging.getLogger(__name__)

TASK = "taxops.verdict"
BACKEND_ENV = "TAXOPS_BRAIN_BACKEND"
DEFAULT_BACKEND = "openai"

SUGGESTIONS = (SALES, NON_SALES, CANNOT_JUDGE)
_MEANINGS = {
    SALES: "sales=这笔入账是销售收入(应计入销项含税合计)",
    NON_SALES: "non_sales=这笔入账不是销售(如借款/内部划转/退款/私人往来)",
    CANNOT_JUDGE: "cannot_judge=摘要信息不足,判断不了",
}

INVALID_BAD_SHAPE = "bad_shape"
INVALID_SUGGESTION_UNKNOWN = "suggestion_unknown"
INVALID_CONFIDENCE = "confidence_out_of_range"
INVALID_CITED_MISSING = "cited_row_missing"
INVALID_CITATION_REQUIRED = "citation_required"

# 判断题 prompt:硬规则写死模板(禁编 / 引用只准题面行指纹 / 无据必 cannot_judge),与
# parse 的机器校验一一对应(prompt 防君子,parse 防小人)。钱数不问大脑——只问分类。
_PROMPT_TEMPLATE = """你是泰国代账事务所的月结助手。下面是一条银行账户的入账流水行(deposit)。
任务:只判断这笔入账是不是「销售收入」。不要算钱,钱数由确定性代码计算。

可选答案(只准从下面选一个,原样输出;列表外一律无效):
{suggestions}

各答案含义:{meanings}。

硬规则:
1. 只依据下面这一行的信息判断。摘要看不出是不是销售(如只是"转入/รับโอนเงิน"又无对手方线索)→ 必须选 cannot_judge,严禁编造。
2. cited_row_fingerprints 只准引用 row_fingerprint 字段给的那一个指纹;选 sales 或 non_sales 必须引用它,选 cannot_judge 给空数组。
3. reason_zh 用一句中文人话说明理由。
4. 只输出一个 JSON 对象,不带任何其他文字。

待判行:
{question}

输出 JSON 形状:
{{"row_fingerprint": "...", "suggestion": "...", "confidence": 0.0, "reason_zh": "...", "cited_row_fingerprints": []}}"""


def build_question(row: dict) -> dict:
    """一条待判入账行 → 判断题上下文(纯函数)。只给日期/入账额/摘要 + 行自身指纹(唯一可引用
    证据),不掺任何裁决或钱数结论。"""
    return {
        "row_fingerprint": row["fingerprint"],
        "date": row["date"],
        "deposit": engine._fmt(row["deposit"]),
        "description": row["description"],
    }


def build_prompt(question: dict) -> str:
    return _PROMPT_TEMPLATE.format(
        suggestions="\n".join(f"- {s}" for s in SUGGESTIONS),
        meanings=";".join(_MEANINGS[s] for s in SUGGESTIONS),
        question=json.dumps(question, ensure_ascii=False, default=str),
    )


def parse_suggestion(data, allowed_fingerprints) -> dict:
    """模型回复 → 规范化建议记录(纯函数)。校验即硬闸②③的机器面:引用只认题面行指纹,
    实分类(sales/non_sales)必须带引用;任何不合规照单落 invalid,不悄悄修正。"""
    out = {
        "suggestion": None,
        "confidence": None,
        "reason_zh": "",
        "cited": [],
        "valid": False,
        "invalid_reason": None,
    }
    if not isinstance(data, dict):
        out["invalid_reason"] = INVALID_BAD_SHAPE
        return out
    suggestion = str(data.get("suggestion") or "").strip()
    out["suggestion"] = suggestion or None
    out["reason_zh"] = str(data.get("reason_zh") or "").strip()
    if suggestion not in SUGGESTIONS:
        out["invalid_reason"] = INVALID_SUGGESTION_UNKNOWN
        return out
    try:
        confidence = float(data.get("confidence"))
    except (TypeError, ValueError):
        confidence = -1.0
    if not 0.0 <= confidence <= 1.0:
        out["invalid_reason"] = INVALID_CONFIDENCE
        return out
    out["confidence"] = confidence
    raw_cited = data.get("cited_row_fingerprints")
    if not isinstance(raw_cited, list):
        out["invalid_reason"] = INVALID_BAD_SHAPE
        return out
    allowed = set(allowed_fingerprints)
    cited = [str(c) for c in raw_cited]
    out["cited"] = cited
    if any(c not in allowed for c in cited):
        out["invalid_reason"] = INVALID_CITED_MISSING
        return out
    if suggestion != CANNOT_JUDGE and not cited:
        out["invalid_reason"] = INVALID_CITATION_REQUIRED
        return out
    out["valid"] = True
    return out


def _resolve_backend(backend) -> str:
    return (backend or os.environ.get(BACKEND_ENV) or DEFAULT_BACKEND).strip().lower()


def _default_ask(prompt: str, *, tenant_id=None, trace_id=None, backend=None, tier=None):
    """经网关问一题(text_to_json)。tier 缺省按后端解析:openai 走 taxops_verdict 档,
    其余后端走各自 flash 档(与 brain_shadow 同一车道)。"""
    from services.ai_gateway import transport

    effective = _resolve_backend(backend)
    return transport.text_to_json(
        prompt,
        tier=tier or (TAXOPS_VERDICT_TIER if effective == DEFAULT_BACKEND else "flash"),
        backend=effective,
        temperature=0.0,
        timeout_s=60,
        task=TASK,
        tenant_id=tenant_id,
        trace_id=trace_id,
    )


# 注入点:测试 patch bank_sales_brain.ask_model,零真调用(brain_shadow 同款范式)。
ask_model = _default_ask


def run(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """对未决入账行调大脑分类,结果落 bank_sales_suggested 事件(行指纹幂等,已有结果不重调)。
    闸关 = no-op;任何失败隔离成摘要,绝不上抛。"""
    if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        return {"enabled": False, "asked": 0, "logged": 0}
    try:
        return _run(cur, tenant_id, work_order_id)
    except Exception:  # noqa: BLE001 — 硬闸④:大脑层任何炸法都不许波及主路径
        logger.warning("[bank_sales_brain] run failed; suggestions skipped", exc_info=True)
        return {"enabled": True, "error": "brain_failed", "asked": 0, "logged": 0}


def _run(cur, tenant_id: str, work_order_id: str) -> dict:
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    rows = engine.pending_rows(events)
    asked = failed = logged = 0
    for row in rows:
        fp = row["fingerprint"]
        asked += 1
        outcome = ask_model(
            build_prompt(build_question(row)),
            tenant_id=tenant_id,
            trace_id=f"bank_sales_brain:{fp}",
        )
        if not outcome.ok:
            failed += 1  # 网关已按 error_kind 记账(ai_usage),不重复留痕
            continue
        rec = parse_suggestion(outcome.data, {fp})
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=engine.STEP,
            event_type=engine.EVT_SUGGESTED,
            payload={
                "fingerprint": fp,
                "verdict": rec["suggestion"],
                "confidence": rec["confidence"],
                "reason_zh": rec["reason_zh"] or None,
                "cited": rec["cited"],
                "valid": rec["valid"],
                "invalid_reason": rec["invalid_reason"],
                "model": outcome.model,
            },
            dedupe_key=f"{engine.SUGGEST_DEDUPE_PREFIX}:{fp}",
        )
        logged += 1
    return {"enabled": True, "asked": asked, "logged": logged, "failed": failed}
