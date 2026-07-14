# -*- coding: utf-8 -*-
"""大脑(GPT)影子:flagged 待判项的裁决预判建议(只建议不落账 · 闸默认关)。

Pearnly AI 大脑首期两职责(裁决预判 + 审核建议)的影子实现:对工单里 flagged 且尚无
human_decision 的料,把票面读数 / flag 原因 / 税号锚等事件流上下文构成判断题,经
ai_gateway(默认 backend=openai · routing_matrix 的 taxops.verdict 车道)要建议 JSON。
钱数永不归大脑——这里不算钱、不改引擎、不碰任何业务表,唯一落点是影子日志
brain_shadow_log(分歧清单 = 转正验收单,照 shadow_money 范式)。verdict.py 的规则
narrative 是转正插座:影子命中率达标后替换其产出,前端结构不变。

硬闸(代码强制,不靠自觉):
  ① 零写业务表:本模块只 INSERT brain_shadow_log。
  ② 引用必须真实:cited_event_ids 只认题面给过的事件 id(⊆ 该单事件流),引用不实 = invalid。
  ③ 无证据必须认怂:prompt 明令 cannot_judge 禁编;parse 层对无引用的实建议判 invalid。
  ④ 异常全隔离:run_shadow 任何失败只记 warning 返回摘要,不影响任何主路径。
闸 pearnly_ai_brain_shadow 默认关:关 = run_shadow 直接 no-op(零构题零调用零落库)。
建表走 ensure 首用自愈(line_anchor_store 先例·豁免补挂于 7c9d452f,prod 无 alembic 升级路)。

backend/model 不写死:默认走 routing_matrix 声明的 openai + taxops_verdict 档(模型名由
env TAXOPS_BRAIN_MODEL 定),评测脚本可按臂传 backend/tier(scripts/brain_shadow_score.py
三模型同卷摸底考用),模型名永不出现在本文件(闸-Q4)。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from core import feature_flags
from services.ai_gateway.providers.openai import TAXOPS_VERDICT_TIER
from services.workorder import decisions, evidence, store, verdict

logger = logging.getLogger(__name__)

TASK = "taxops.verdict"
# 评测/应急切臂旋钮:缺省走 routing_matrix 声明的 openai 车道。非 openai 后端没有
# taxops_verdict 档,回落各自 flash 档(模型由其后端自己的 env 解析)。
BACKEND_ENV = "TAXOPS_BRAIN_BACKEND"
DEFAULT_BACKEND = "openai"

CANNOT_JUDGE = "cannot_judge"
_ASSIGN_PURCHASE = f"{decisions.ASSIGN_KIND}:{decisions.PURCHASE_INVOICE}"
_ASSIGN_SALES = f"{decisions.ASSIGN_KIND}:{decisions.SALES_DOC}"
_ASSIGN_NON_TAX = f"{decisions.ASSIGN_KIND}:{decisions.NON_TAX}"
# 建议词汇表 = 人工裁决动词(decisions 单一事实源)+ cannot_judge。assign_kind 带裁定方向,
# 与 human_decision payload 的 decision/kind 一一可映射,评分 CLI 直接对答案。
SUGGESTIONS = (
    decisions.FACE_VALUE,
    decisions.RECALC,
    decisions.EXCLUDE,
    _ASSIGN_PURCHASE,
    _ASSIGN_SALES,
    _ASSIGN_NON_TAX,
    decisions.WAIVE,
    CANNOT_JUDGE,
)

# 题型约束(2026-07-14 摸底考失分#2:sales_doc_review 票答成 face_value——内容对、题型错):
# 方向类 flag 只考「这张票是谁的什么票」,金额类 flag 只考「票面数字信不信」。允许集写进
# 题面,parse 层对词汇表内但超本题集的答案判 wrong_answer_type。未知 flag 不设限(全集)。
_DIRECTION_FLAGS = frozenset({*decisions.DIRECTION_PREFIXES, decisions.SALES_DOC_REVIEW})
_AMOUNT_FLAGS = frozenset(
    {
        "amount_math_fail",
        "ocr_low_confidence",
        "ocr_validation_warning",
        "ocr_error",
        "duplicate_of",
    }
)
DIRECTION_SUGGESTIONS = (_ASSIGN_PURCHASE, _ASSIGN_SALES, _ASSIGN_NON_TAX, CANNOT_JUDGE)
AMOUNT_SUGGESTIONS = (decisions.FACE_VALUE, decisions.RECALC, decisions.EXCLUDE, CANNOT_JUDGE)

_SUGGESTION_MEANINGS = {
    decisions.FACE_VALUE: "face_value=采信票面读数",
    decisions.RECALC: "recalc=票面读数有误需人工看原件补正",
    decisions.EXCLUDE: "exclude=剔除不计入合计",
    _ASSIGN_PURCHASE: "assign_kind:purchase_invoice=裁定为进项票",
    _ASSIGN_SALES: "assign_kind:sales_doc=裁定为本方销项票",
    _ASSIGN_NON_TAX: "assign_kind:non_tax=裁定为非税票",
    decisions.WAIVE: "waive=无法归位但放行留痕",
    CANNOT_JUDGE: "cannot_judge=证据不足判断不了",
}

INVALID_BAD_SHAPE = "bad_shape"
INVALID_SUGGESTION_UNKNOWN = "suggestion_unknown"
INVALID_WRONG_ANSWER_TYPE = "wrong_answer_type"
INVALID_CONFIDENCE = "confidence_out_of_range"
INVALID_CITED_MISSING = "cited_event_missing"
INVALID_CITATION_REQUIRED = "citation_required"

# 判断题 prompt:硬规则写死在模板里(禁编 / 引用只准题面 id / 证据不足必 cannot_judge),
# 与 parse_suggestion 的机器校验一一对应——prompt 防君子,parse 防小人。
_PROMPT_TEMPLATE = """你是泰国代账事务所的月结审核助手。下面是一张被系统点名(flagged)的票据的机器读数与上下文。
任务:给出建议裁决。只做判断,不算钱——钱数永远由确定性代码计算,你的建议仅供会计参考。

可选建议(只准从下面选一个,原样输出;列表外的建议一律无效):
{suggestions}

各建议含义:{meanings}。

硬规则:
1. 只依据下面上下文判断。证据缺失、读数冲突到看不出真相、上下文不足 → 必须选 cannot_judge,严禁编造或猜测。
2. cited_event_ids 只准引用 evidence_event_ids 列表里的事件 id;没有可引用证据时给空数组并选 cannot_judge。
3. reason_zh 用一句中文人话说明理由。
4. own_tax_id 是本账套自家税号:卖方税号等于它 → 这是本方开出的销项票。
5. 只输出一个 JSON 对象,不带任何其他文字。

上下文:
{question}

输出 JSON 形状:
{{"item_id": "...", "suggestion": "...", "confidence": 0.0, "reason_zh": "...", "cited_event_ids": []}}"""

_ensured = False


def ensure_table() -> None:
    """幂等建 brain_shadow_log + RLS(首用自愈,照 line_anchor_store 先例;
    alembic/versions/0077_brain_shadow_log.py 逐字对齐留档)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS brain_shadow_log (
                id BIGSERIAL PRIMARY KEY,
                tenant_id UUID NOT NULL,
                work_order_id UUID NOT NULL,
                item_id UUID NOT NULL,
                suggestion TEXT,
                confidence NUMERIC(4, 3),
                reason_zh TEXT,
                cited_event_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                valid BOOLEAN NOT NULL DEFAULT FALSE,
                invalid_reason TEXT,
                model TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_brain_shadow_log_wo "
            "ON brain_shadow_log (tenant_id, work_order_id, created_at DESC)"
        )
        apply_tenant_rls(cur, "brain_shadow_log")


def _ensure_once() -> None:
    global _ensured
    if _ensured:
        return
    ensure_table()
    _ensured = True


def own_anchor(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """工单绑定账套的自家税号/名(方向题主判据,与 classify 的锚同源同表)。未绑客户
    诚实给 None,不造锚。"""
    cur.execute(
        "SELECT wc.tax_id, wc.name FROM work_orders wo "
        "JOIN workspace_clients wc "
        "ON wc.id = wo.workspace_client_id AND wc.tenant_id = wo.tenant_id "
        "WHERE wo.tenant_id = %s AND wo.id = %s",
        (tenant_id, work_order_id),
    )
    row = cur.fetchone()
    if not row:
        return {"tax_id": None, "name": None}
    row = dict(row)
    return {"tax_id": row.get("tax_id"), "name": row.get("name")}


def allowed_suggestions(flag_reason: Optional[str]) -> tuple:
    """flag_reason → 本题允许的建议集(题面枚举与 parse 校验共用,防题型漂移)。"""
    head = str(flag_reason or "").split(":", 1)[0]
    if head in _DIRECTION_FLAGS:
        return DIRECTION_SUGGESTIONS
    if head in _AMOUNT_FLAGS:
        return AMOUNT_SUGGESTIONS
    return SUGGESTIONS


def build_question(item: dict, classified_rec: Optional[dict], own: dict) -> dict:
    """一件 flagged 料 → 判断题上下文(纯函数,评分 CLI 与影子跑共用,保证同卷)。

    上下文全部来自事件 payload / items 行 / 账套锚,绝不掺 human_decision(考试防漏题
    天然成立:本函数根本不消费裁决事件)。无 item_classified 事件(没读出来的料)则
    money=None、evidence_event_ids=[]——模型按硬规则只能答 cannot_judge。flag_hint 是
    verdict.py 的判据人话(narrative_key+params,与人审卡同源):flag 具体在哪一条勾稽
    上报警(如三字段自洽但 VAT≠7%),不给会把大脑带偏成「票面算不平」(摸底考 2647)。
    刻意不带 suggested_decision——那是规则给的安全默认,漏进题面等于漏答案。"""
    payload = (classified_rec or {}).get("payload") or {}
    hint = verdict.hint(flag_reason=item.get("flag_reason"), ocr_read=payload.get("money"))
    return {
        "item_id": str(item["id"]),
        "kind": payload.get("kind") or item.get("kind"),
        "flag_reason": item.get("flag_reason"),
        "flag_hint": {"narrative_key": hint["narrative_key"], "params": hint["params"]},
        "money": payload.get("money"),
        "own_tax_id": own.get("tax_id"),
        "own_name": own.get("name"),
        "evidence_event_ids": [classified_rec["event_id"]] if classified_rec else [],
    }


def build_prompt(question: dict) -> str:
    allowed = allowed_suggestions(question.get("flag_reason"))
    return _PROMPT_TEMPLATE.format(
        suggestions="\n".join(f"- {s}" for s in allowed),
        meanings=";".join(_SUGGESTION_MEANINGS[s] for s in allowed),
        question=json.dumps(question, ensure_ascii=False, default=str),
    )


def parse_suggestion(data, allowed_event_ids, flag_reason: Optional[str] = None) -> dict:
    """模型回复 → 规范化建议记录(纯函数)。校验即硬闸②③的机器面:引用只认题面给过的
    事件 id(⊆ 该单事件流),实建议必须带引用;flag_reason 传入时同步校验题型(词汇表内
    但超本题允许集 = wrong_answer_type);任何不合规照单落 invalid,不悄悄修正。"""
    out = {
        "suggestion": None,
        "confidence": None,
        "reason_zh": "",
        "cited_event_ids": [],
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
    if suggestion not in allowed_suggestions(flag_reason):
        out["invalid_reason"] = INVALID_WRONG_ANSWER_TYPE
        return out
    try:
        confidence = float(data.get("confidence"))
    except (TypeError, ValueError):
        confidence = -1.0
    if not 0.0 <= confidence <= 1.0:
        out["invalid_reason"] = INVALID_CONFIDENCE
        return out
    out["confidence"] = confidence
    raw_cited = data.get("cited_event_ids")
    if not isinstance(raw_cited, list):
        out["invalid_reason"] = INVALID_BAD_SHAPE
        return out
    allowed = {int(i) for i in allowed_event_ids}
    cited = []
    for c in raw_cited:
        try:
            cited.append(int(c))
        except (TypeError, ValueError):
            out["invalid_reason"] = INVALID_CITED_MISSING
            return out
    out["cited_event_ids"] = cited
    if any(c not in allowed for c in cited):
        out["invalid_reason"] = INVALID_CITED_MISSING
        return out
    if suggestion != CANNOT_JUDGE and not cited:
        out["invalid_reason"] = INVALID_CITATION_REQUIRED
        return out
    out["valid"] = True
    return out


def _resolve_backend(backend: Optional[str]) -> str:
    return (backend or os.environ.get(BACKEND_ENV) or DEFAULT_BACKEND).strip().lower()


def _default_ask(prompt: str, *, tenant_id=None, trace_id=None, backend=None, tier=None):
    """经网关问一题(text_to_json · 结构化 JSON 单源)。tier 缺省按后端解析:openai 走
    taxops_verdict 档(env TAXOPS_BRAIN_MODEL),其余后端走各自 flash 档。"""
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


# 注入点:测试 patch brain_shadow.ask_model,零真调用(classify._ocr_image 同款范式)。
ask_model = _default_ask


def _insert_rows(tenant_id: str, work_order_id: str, rows: list[dict]) -> int:
    """落影子日志(自开连接独立事务:影子写挂了不毒化调用方事务,反之亦然)。"""
    if not rows:
        return 0
    from core import db

    _ensure_once()
    with db.get_cursor_rls(tenant_id=str(tenant_id), commit=True) as cur:
        for r in rows:
            cur.execute(
                "INSERT INTO brain_shadow_log "
                "(tenant_id, work_order_id, item_id, suggestion, confidence, reason_zh, "
                " cited_event_ids, valid, invalid_reason, model) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)",
                (
                    str(tenant_id),
                    str(work_order_id),
                    r["item_id"],
                    r.get("suggestion"),
                    r.get("confidence"),
                    r.get("reason_zh") or None,
                    json.dumps(r.get("cited_event_ids") or []),
                    bool(r.get("valid")),
                    r.get("invalid_reason"),
                    r.get("model"),
                ),
            )
    return len(rows)


def run_shadow(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """对该单 flagged 且未裁项影子出建议。闸关 = no-op;任何失败隔离成摘要,绝不上抛。"""
    if not feature_flags.pearnly_ai_brain_shadow_enabled_for(tenant_id):
        return {"enabled": False, "asked": 0, "logged": 0}
    try:
        return _run(cur, tenant_id, work_order_id)
    except Exception:  # noqa: BLE001 — 硬闸④:影子层任何炸法都不许波及主路径
        logger.warning("[brain_shadow] run failed; suggestions skipped", exc_info=True)
        return {"enabled": True, "error": "shadow_failed", "asked": 0, "logged": 0}


def _run(cur, tenant_id: str, work_order_id: str) -> dict:
    items = store.list_items(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    classified = evidence.replay_items_by_type(events, "item_classified")
    decided = evidence.replay_items_by_type(events, "human_decision")
    own = own_anchor(cur, tenant_id=tenant_id, work_order_id=work_order_id)

    rows: list[dict] = []
    asked = failed = 0
    for item in items:
        item_id = str(item["id"])
        if item["status"] != "flagged" or item_id in decided:
            continue
        question = build_question(item, classified.get(item_id), own)
        asked += 1
        outcome = ask_model(
            build_prompt(question), tenant_id=tenant_id, trace_id=f"brain_shadow:{item_id}"
        )
        if not outcome.ok:
            failed += 1  # 网关已按 error_kind 记账(ai_usage),这里不重复留痕
            continue
        rec = parse_suggestion(
            outcome.data, question["evidence_event_ids"], flag_reason=question["flag_reason"]
        )
        rec["item_id"] = item_id
        rec["model"] = outcome.model
        rows.append(rec)
    logged = _insert_rows(tenant_id, work_order_id, rows)
    return {"enabled": True, "asked": asked, "logged": logged, "failed": failed}
