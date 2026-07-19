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
import threading
from datetime import datetime, timezone

from core import db, feature_flags
from services.ai_gateway.providers.openai import TAXOPS_VERDICT_TIER
from services.workorder import store
from services.workorder.steps import bank_sales_suggest as engine
from services.workorder.steps.bank_sales_suggest import CANNOT_JUDGE, NON_SALES, SALES

logger = logging.getLogger(__name__)

TASK = "taxops.verdict"
BACKEND_ENV = "TAXOPS_BRAIN_BACKEND"
DEFAULT_BACKEND = "openai"
BATCH_SIZE = 40
MAX_BATCHES = 30
BATCH_TIMEOUT_S = 120
BATCH_MAX_TOKENS = 12000
MAX_CONSECUTIVE_FAILURES = 3

# 单进程运行态只负责互斥/进度；进程重启后清空即可重跑，事件 dedupe 保证安全。
_PROGRESS: dict[str, dict] = {}
_PROGRESS_LOCK = threading.Lock()

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


def build_prompt(question: dict) -> str:
    return _PROMPT_TEMPLATE.format(
        suggestions="\n".join(f"- {s}" for s in SUGGESTIONS),
        meanings=";".join(_MEANINGS[s] for s in SUGGESTIONS),
        question=json.dumps(question, ensure_ascii=False, default=str),
    )


def build_batch_question(rows: list[dict]) -> dict:
    """至多 40 行组成一题；调用方切片，函数本身也拒绝把超量题面送出。"""
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

    openai 结构化输出顶层必须是对象不能是数组(真供应商实锤拒过裸数组),题面要求
    {"suggestions": [...]} 包装;裸数组仍兼容(测试夹具/别家后端)。"""
    if isinstance(data, dict):
        data = data.get("suggestions")
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


def _resolve_backend(backend) -> str:
    return (backend or os.environ.get(BACKEND_ENV) or DEFAULT_BACKEND).strip().lower()


def _default_ask(
    prompt: str,
    *,
    tenant_id=None,
    trace_id=None,
    backend=None,
    tier=None,
    timeout_s=BATCH_TIMEOUT_S,
    max_tokens=BATCH_MAX_TOKENS,
    temperature=0.0,
):
    """经网关问一题(text_to_json)。tier 缺省按后端解析:openai 走 taxops_verdict 档,
    其余后端走各自 flash 档(与 brain_shadow 同一车道)。"""
    from services.ai_gateway import transport

    effective = _resolve_backend(backend)
    return transport.text_to_json(
        prompt,
        tier=tier or (TAXOPS_VERDICT_TIER if effective == DEFAULT_BACKEND else "flash"),
        backend=effective,
        temperature=temperature,
        timeout_s=timeout_s,
        max_tokens=max_tokens,
        task=TASK,
        tenant_id=tenant_id,
        trace_id=trace_id,
    )


# 注入点:测试 patch bank_sales_brain.ask_model,零真调用(brain_shadow 同款范式)。
ask_model = _default_ask


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def begin(work_order_id: str, total: int) -> bool:
    """原子占用运行位；同工单已在跑时返回 False。进程重启清空后可安全重跑。"""
    with _PROGRESS_LOCK:
        current = _PROGRESS.get(work_order_id)
        if current and current.get("running"):
            return False
        _PROGRESS[work_order_id] = {
            "running": True,
            "status": "running",
            "total": total,
            "done": 0,
            "failed_batches": 0,
            "started_at": _now(),
            "finished_at": None,
        }
    return True


def progress(work_order_id: str) -> dict | None:
    with _PROGRESS_LOCK:
        value = _PROGRESS.get(work_order_id)
        return dict(value) if value else None


def _update_progress(work_order_id: str, **changes) -> None:
    with _PROGRESS_LOCK:
        if work_order_id in _PROGRESS:
            _PROGRESS[work_order_id].update(changes)


def _finish(work_order_id: str, status: str) -> None:
    _update_progress(
        work_order_id,
        running=False,
        status=status,
        finished_at=_now(),
        capped=status == "capped",
    )


def fail_start(work_order_id: str) -> None:
    """线程未成功启动时释放运行位。"""
    _finish(work_order_id, "failed")


def _payload(rec: dict, model) -> dict:
    return {
        "fingerprint": rec["row_fingerprint"],
        "verdict": rec["suggestion"],
        "confidence": rec["confidence"],
        "reason_zh": rec["reason_zh"] or None,
        "cited": rec["cited"],
        "valid": True,
        "invalid_reason": None,
        "model": model,
    }


def _append_records(cur, tenant_id: str, work_order_id: str, records: list[dict], model) -> None:
    for rec in records:
        fp = rec["row_fingerprint"]
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=engine.STEP,
            event_type=engine.EVT_SUGGESTED,
            payload=_payload(rec, model),
            dedupe_key=f"{engine.SUGGEST_DEDUPE_PREFIX}:{fp}",
        )


def _run_rows(rows, tenant_id: str, work_order_id: str, write_batch) -> dict:
    limited = rows[: BATCH_SIZE * MAX_BATCHES]
    asked = logged = failed = batches = consecutive_failures = 0
    for offset in range(0, len(limited), BATCH_SIZE):
        batch = limited[offset : offset + BATCH_SIZE]
        batches += 1
        asked += len(batch)
        try:
            outcome = ask_model(
                build_batch_prompt(build_batch_question(batch)),
                tenant_id=tenant_id,
                trace_id=f"bank_sales_brain:batch:{work_order_id}:{batches}",
                timeout_s=BATCH_TIMEOUT_S,
                max_tokens=BATCH_MAX_TOKENS,
                temperature=0.0,
            )
            records = (
                parse_batch_suggestions(outcome.data, {row["fingerprint"] for row in batch})
                if outcome.ok
                else []
            )
            if not records:
                raise ValueError("batch yielded no valid suggestions")
            write_batch(records, outcome.model)
        except Exception:  # noqa: BLE001 — 单批失败隔离，连续三批才熔断本次运行
            failed += 1
            consecutive_failures += 1
            logger.warning(
                "[bank_sales_brain] batch %s failed; rows remain pending", batches, exc_info=True
            )
            _update_progress(work_order_id, failed_batches=failed)
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                _finish(work_order_id, "failed")
                break
            continue
        consecutive_failures = 0
        logged += len(records)
        _update_progress(work_order_id, done=logged, failed_batches=failed)
    else:
        _finish(work_order_id, "capped" if len(rows) > len(limited) else "completed")
    return {
        "enabled": True,
        "asked": asked,
        "logged": logged,
        "failed": failed,
        "batches": batches,
        "status": (progress(work_order_id) or {}).get("status"),
    }


def run(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """同步测试/兼容入口；生产 HTTP 走 run_async，让每批使用独立短事务。"""
    if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        return {"enabled": False, "asked": 0, "logged": 0}
    try:
        return _run(cur, tenant_id, work_order_id)
    except Exception:  # noqa: BLE001 — 大脑层任何炸法都不许波及主路径
        logger.warning("[bank_sales_brain] run failed; suggestions skipped", exc_info=True)
        _finish(work_order_id, "failed")
        return {"enabled": True, "error": "brain_failed", "asked": 0, "logged": 0}


def _run(cur, tenant_id: str, work_order_id: str) -> dict:
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    rows = engine.pending_rows(events)
    if not begin(work_order_id, len(rows)):
        return {"enabled": True, "running": True, "asked": 0, "logged": 0}
    return _run_rows(
        rows,
        tenant_id,
        work_order_id,
        lambda records, model: _append_records(cur, tenant_id, work_order_id, records, model),
    )


def run_async(*, tenant_id: str, work_order_id: str, claimed: bool = False) -> dict:
    """后台入口：读取与每批写入各用短事务；已提交批次构成断点，重跑只补剩余行。"""
    if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        if claimed:
            _finish(work_order_id, "disabled")
        return {"enabled": False, "asked": 0, "logged": 0}
    try:
        with db.get_cursor() as cur:
            events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        rows = engine.pending_rows(events)
        if not claimed and not begin(work_order_id, len(rows)):
            return {"enabled": True, "running": True, "asked": 0, "logged": 0}
        _update_progress(work_order_id, total=len(rows))

        def write_batch(records, model):
            with db.get_cursor(commit=True) as cur:
                _append_records(cur, tenant_id, work_order_id, records, model)

        return _run_rows(rows, tenant_id, work_order_id, write_batch)
    except Exception:  # noqa: BLE001 — 后台线程不可泄漏异常
        logger.warning("[bank_sales_brain] async run failed", exc_info=True)
        _finish(work_order_id, "failed")
        return {"enabled": True, "error": "brain_failed", "asked": 0, "logged": 0}
