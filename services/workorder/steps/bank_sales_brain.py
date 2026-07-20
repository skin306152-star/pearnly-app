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

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from core import db, feature_flags
from services.ai_gateway.providers.openai import TAXOPS_VERDICT_TIER
from services.workorder import run_leases, store
from services.workorder.steps import bank_sales_suggest as engine
from services.workorder.steps import ocr_quota
from services.workorder.steps.bank_sales_classify import (
    BATCH_SIZE,
    build_batch_prompt,
    build_batch_question,
    parse_batch_suggestions,
)

logger = logging.getLogger(__name__)

TASK = "taxops.verdict"
BACKEND_ENV = "TAXOPS_BRAIN_BACKEND"
DEFAULT_BACKEND = "openai"
MAX_BATCHES = 30
BATCH_TIMEOUT_S = 120
BATCH_MAX_TOKENS = 12000
MAX_CONSECUTIVE_FAILURES = 3

# 终态事件(读侧 / 自动收尾单一事实源):熔断或整轮失败落 failed,正常收尾落 finished。
# bank_sales_recovery 据「最近一条终态是 failed」+ pending_rows>0 + 重试预算未耗尽决定重跑。
EVT_BRAIN_FAILED = "bank_sales_brain_failed"
EVT_BRAIN_FINISHED = "bank_sales_brain_finished"
TRIGGER_MANUAL = "manual"  # HTTP /run 触发(不计入自动重试预算)
TRIGGER_RECOVERY = "recovery"  # 自动收尾触发(计入预算)
_LEASE_PREFIX = "bank_sales_brain"
# 批失败分型:quota 型退避重试不吃熔断预算,hard 型才计 consecutive_failures。
_QUOTA = "quota"
_HARD = "hard"

# 单进程运行态只负责互斥/进度；进程重启后清空即可重跑，事件 dedupe 保证安全。
_PROGRESS: dict[str, dict] = {}
_PROGRESS_LOCK = threading.Lock()


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


def fail_start(tenant_id: str, work_order_id: str, owner: Optional[str] = None) -> None:
    """线程未成功启动时释放运行位:进程内 _PROGRESS + 跨进程 DB 租约都放掉。"""
    _finish(work_order_id, "failed")
    _release_lease(tenant_id, work_order_id, owner)


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


def _outcome_is_quota(outcome) -> bool:
    """网关把 429/限流/RESOURCE_EXHAUSTED 统一标 error_kind=quota(见 ai_gateway.tasks)。"""
    return getattr(outcome, "error_kind", "") == _QUOTA


def _backoff(governor, attempt: int) -> None:
    """撞 quota:抬全局暂停窗降速;还有重试机会才睡本 worker(用满不白等)。"""
    delay = governor.penalize(attempt)
    if attempt < governor.max_attempts - 1:
        governor.sleep(delay)


def _ask_batch(batch: list[dict], governor, tenant_id: str, work_order_id: str, batch_no: int):
    """一批判断题带配额退避取数 → (records, model, None) 成功;(None, None, _QUOTA|_HARD) 失败。

    quota 型(429/限流)在 governor 内指数退避重试至上限,不定罪、不吃熔断预算;非 quota 异常
    或空结果立即判 hard(计入 consecutive_failures)。用满退避仍 quota → _QUOTA(行留 pending)。
    """
    prompt = build_batch_prompt(build_batch_question(batch))
    allowed = {row["fingerprint"] for row in batch}
    trace_id = f"bank_sales_brain:batch:{work_order_id}:{batch_no}"
    for attempt in range(governor.max_attempts):
        governor.await_clear()
        try:
            outcome = ask_model(prompt, tenant_id=tenant_id, trace_id=trace_id)
        except Exception as exc:  # noqa: BLE001 — 单批隔离
            if not ocr_quota.is_quota_error(exc):
                logger.warning("[bank_sales_brain] batch %s raised", batch_no, exc_info=True)
                return None, None, _HARD
            _backoff(governor, attempt)
            continue
        if outcome.ok:
            records = parse_batch_suggestions(outcome.data, allowed)
            if records:
                return records, outcome.model, None
            logger.warning("[bank_sales_brain] batch %s: no valid suggestions", batch_no)
            return None, None, _HARD
        if _outcome_is_quota(outcome):
            _backoff(governor, attempt)
            continue
        logger.warning(
            "[bank_sales_brain] batch %s failed kind=%s",
            batch_no,
            getattr(outcome, "error_kind", ""),
        )
        return None, None, _HARD
    return None, None, _QUOTA


def _run_rows(rows, tenant_id: str, work_order_id: str, write_batch, *, renew=None) -> dict:
    """批循环:逐批取数落库。quota 退避不熔断、hard 三连熔断;renew(可选)每批前续跨进程租约。"""
    limited = rows[: BATCH_SIZE * MAX_BATCHES]
    governor = ocr_quota.QuotaGovernor()
    asked = logged = failed = batches = consecutive = 0
    breaker_tripped = False
    for offset in range(0, len(limited), BATCH_SIZE):
        if renew is not None:
            renew()
        batch = limited[offset : offset + BATCH_SIZE]
        batches += 1
        asked += len(batch)
        records, model, kind = _ask_batch(batch, governor, tenant_id, work_order_id, batches)
        if records is None:
            failed += 1
            _update_progress(work_order_id, failed_batches=failed)
            if kind == _HARD:  # 只有非 quota 才吃熔断预算
                consecutive += 1
                if consecutive >= MAX_CONSECUTIVE_FAILURES:
                    breaker_tripped = True
                    break
            continue
        write_batch(records, model)
        consecutive = 0
        logged += len(records)
        _update_progress(work_order_id, done=logged, failed_batches=failed)
    status = (
        "failed" if breaker_tripped else ("capped" if len(rows) > len(limited) else "completed")
    )
    _finish(work_order_id, status)
    return {
        "enabled": True,
        "asked": asked,
        "logged": logged,
        "failed": failed,
        "batches": batches,
        "consecutive_failures": consecutive,
        "status": status,
    }


def _terminal_event_type(summary) -> str:
    """整轮异常(summary=None)/熔断/任一失败批 → failed(行仍 pending,让自动收尾择时重跑);
    否则 finished。quota 型失败批也算 failed——退避用满仍卡的行靠 failed 事件被自动收尾接续。"""
    if summary is None:
        return EVT_BRAIN_FAILED
    if summary.get("status") == "failed" or summary.get("failed", 0) > 0:
        return EVT_BRAIN_FAILED
    return EVT_BRAIN_FINISHED


def _emit_terminal(cur, tenant_id: str, work_order_id: str, summary, trigger: str, owner) -> None:
    """落终态事件(dedupe 锚 owner:一次运行至多一条,重放不重记)。空跑(0 待判行且未失败)
    不落,免每次点击刷一条 finished。"""
    if summary is not None and summary.get("asked", 0) == 0 and summary.get("status") != "failed":
        return
    etype = _terminal_event_type(summary)
    s = summary or {}
    store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=engine.STEP,
        event_type=etype,
        payload={
            "trigger": trigger,
            "status": s.get("status", "failed"),
            "failed_batches": s.get("failed", 0),
            "consecutive_failures": s.get("consecutive_failures", 0),
            "logged": s.get("logged", 0),
        },
        dedupe_key=f"{etype}:{owner}" if owner else None,
    )


def _emit_terminal_async(tenant_id, work_order_id, summary, trigger, owner) -> None:
    """run_async 侧:自开短事务落终态(自吞异常,终态是佐证不阻断已成结果)。"""
    try:
        with db.get_cursor(commit=True) as cur:
            _emit_terminal(cur, tenant_id, work_order_id, summary, trigger, owner)
    except Exception:  # noqa: BLE001
        logger.warning(
            "[bank_sales_brain] terminal event skipped wo=%s", work_order_id, exc_info=True
        )


def _lease_ttl() -> int:
    from services.workorder import runner  # 延迟导入避免导入环(runner → steps 包)

    return runner.run_lease_ttl_seconds()


def _acquire_lease(tenant_id: str, work_order_id: str, owner: str) -> bool:
    store.ensure_runtime()  # 建租约列(独立事务)· 先于锁 work_orders 的 UPDATE
    with db.get_cursor(commit=True) as cur:
        return run_leases.acquire_run_lease(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=_lease_ttl(),
        )


def _renew_lease(tenant_id: str, work_order_id: str, owner: str) -> None:
    try:
        with db.get_cursor(commit=True) as cur:
            run_leases.renew_run_lease(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                owner=owner,
                ttl_seconds=_lease_ttl(),
            )
    except Exception:  # noqa: BLE001 — 续约失败不致命:TTL 到期自然让位
        logger.warning("[bank_sales_brain] lease renew failed wo=%s", work_order_id, exc_info=True)


def _release_lease(tenant_id: str, work_order_id: str, owner) -> None:
    if not owner:
        return
    try:
        with db.get_cursor(commit=True) as cur:
            run_leases.release_run_lease(
                cur, tenant_id=tenant_id, work_order_id=work_order_id, owner=owner
            )
    except Exception:  # noqa: BLE001 — 释放失败不致命:TTL 到期自然让位
        logger.warning(
            "[bank_sales_brain] lease release failed wo=%s", work_order_id, exc_info=True
        )


def begin_run(tenant_id: str, work_order_id: str, total: int) -> Optional[str]:
    """占运行位:进程内 _PROGRESS + 跨进程 DB 租约都拿到才返 owner;任一被占 → None(有人在跑,
    拒绝)。工单 review 态时 runner 租约空闲,复用它免费得跨进程互斥 + 过期自愈,不另造第三套。"""
    if not begin(work_order_id, total):
        return None
    owner = f"{_LEASE_PREFIX}:{uuid.uuid4().hex}"
    try:
        acquired = _acquire_lease(tenant_id, work_order_id, owner)
    except Exception:  # noqa: BLE001 — DB 故障:退回进程内位并拒绝(不裸奔双跑)
        logger.warning(
            "[bank_sales_brain] lease acquire failed wo=%s", work_order_id, exc_info=True
        )
        _finish(work_order_id, "failed")
        return None
    if not acquired:
        _finish(work_order_id, "running")  # 释放进程内位:跨进程有人持约
        return None
    return owner


def run(cur, *, tenant_id: str, work_order_id: str) -> dict:
    """同步测试/兼容入口(单事务,无跨进程租约);生产 HTTP/自动收尾走 run_async。"""
    if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        return {"enabled": False, "asked": 0, "logged": 0}
    try:
        events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        rows = engine.pending_rows(events)
        if not begin(work_order_id, len(rows)):
            return {"enabled": True, "running": True, "asked": 0, "logged": 0}
        summary = _run_rows(
            rows,
            tenant_id,
            work_order_id,
            lambda records, model: _append_records(cur, tenant_id, work_order_id, records, model),
        )
        _emit_terminal(cur, tenant_id, work_order_id, summary, TRIGGER_MANUAL, None)
        return summary
    except Exception:  # noqa: BLE001 — 大脑层任何炸法都不许波及主路径
        logger.warning("[bank_sales_brain] run failed; suggestions skipped", exc_info=True)
        _finish(work_order_id, "failed")
        _emit_terminal(cur, tenant_id, work_order_id, None, TRIGGER_MANUAL, None)
        return {"enabled": True, "error": "brain_failed", "asked": 0, "logged": 0}


def run_async(
    *,
    tenant_id: str,
    work_order_id: str,
    claimed: bool = False,
    lease_owner: Optional[str] = None,
    trigger: str = TRIGGER_MANUAL,
) -> dict:
    """后台入口:读取与每批写入各用短事务;已提交批构成断点(重跑只补剩余行)。

    claimed=True(生产):begin_run 已占进程内位 + 抢跨进程租约,owner 经 lease_owner 传入,
    批间续约、收尾释放。claimed=False(直调/测试):仅占进程内位,不涉 DB 租约。"""
    if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        if claimed:
            _finish(work_order_id, "disabled")
        _release_lease(tenant_id, work_order_id, lease_owner)
        return {"enabled": False, "asked": 0, "logged": 0}
    owner = lease_owner
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

        renew = (lambda: _renew_lease(tenant_id, work_order_id, owner)) if owner else None
        summary = _run_rows(rows, tenant_id, work_order_id, write_batch, renew=renew)
        _emit_terminal_async(tenant_id, work_order_id, summary, trigger, owner)
        return summary
    except Exception:  # noqa: BLE001 — 后台线程不可泄漏异常
        logger.warning("[bank_sales_brain] async run failed", exc_info=True)
        _finish(work_order_id, "failed")
        _emit_terminal_async(tenant_id, work_order_id, None, trigger, owner)
        return {"enabled": True, "error": "brain_failed", "asked": 0, "logged": 0}
    finally:
        _release_lease(tenant_id, work_order_id, owner)
