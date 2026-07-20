# -*- coding: utf-8 -*-
"""银行入账行「是不是销售」判断题的题面构造 + 模型回复解析(纯函数,零 IO)。

从 bank_sales_brain 拆出:大脑分类有两层职责——① 构题/解析回复的硬闸(本模块,纯函数,
prompt 防君子、parse 防小人)② 跑批编排(退避/熔断/租约/终态,在 bank_sales_brain)。
硬闸③④:实分类(sales/non_sales)必须只引用题面给的行指纹;无据必 cannot_judge;任何不合规
照单落 invalid,不悄悄修正。钱数不问大脑——只问分类词(金额由 bank_sales_suggest 确定性算)。
"""

from __future__ import annotations

import json

from services.workorder.steps import bank_sales_suggest as engine
from services.workorder.steps.bank_sales_suggest import CANNOT_JUDGE, NON_SALES, SALES

BATCH_SIZE = 40  # 一题至多 40 行(题面构造与跑批切片共用单一事实源)

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
_BATCH_PROMPT_TEMPLATE = """你是泰国代账事务所的月结助手。请对下列每一条银行入账行独立判断是否为销售收入，不要算钱。

可选答案:{suggestions}。{meanings}。
摘要不足（如普通“转入/รับโอนเงิน”且无对手方线索）必须选 cannot_judge，禁止猜测。
只输出一个 JSON 对象，形状 {{"suggestions": [...]}}；suggestions 数组每个元素必须含
row_fingerprint/suggestion/confidence/reason_zh/cited_row_fingerprints。
sales 或 non_sales 必须只引用该元素自己的 row_fingerprint；cannot_judge 引用空数组。
禁止编造题面外指纹，禁止遗漏能够判断的行，禁止输出对象外文字。

待判行:
{question}
"""


def build_question(row: dict) -> dict:
    """一条待判入账行 → 判断题上下文(纯函数)。只给日期/入账额/摘要 + 行自身指纹(唯一可引用
    证据),不掺任何裁决或钱数结论。"""
    return {
        "row_fingerprint": row["fingerprint"],
        "date": row["date"],
        "deposit": engine._fmt(row["deposit"]),
        "description": row["description"],
    }


def build_batch_question(rows: list[dict]) -> dict:
    """至多 40 行组成一题；调用方切片,函数本身也拒绝把超量题面送出。"""
    return {"rows": [build_question(row) for row in rows[:BATCH_SIZE]]}


def build_batch_prompt(question: dict) -> str:
    return _BATCH_PROMPT_TEMPLATE.format(
        suggestions=" / ".join(SUGGESTIONS),
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


def parse_batch_suggestions(data, allowed_fps) -> list[dict]:
    """批量回复逐元素走单行硬闸；缺行、重复行、题面外行及非法元素均不落事件。
    openai 结构化输出顶层必须是对象(真供应商拒裸数组)→ 认 {"suggestions": [...]},裸数组兼容。"""
    data = data.get("suggestions") if isinstance(data, dict) else data
    if not isinstance(data, list):
        return []
    allowed = set(allowed_fps)
    seen: set[str] = set()
    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        fp = str(item.get("row_fingerprint") or "")
        if fp not in allowed or fp in seen:
            continue
        rec = parse_suggestion(item, {fp})
        if not rec["valid"]:
            continue
        seen.add(fp)
        out.append({"row_fingerprint": fp, **rec})
    return out
