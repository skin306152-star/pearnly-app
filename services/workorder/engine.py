# -*- coding: utf-8 -*-
"""工单流水线状态机(M0 编排层 · 任务包 §4)。

只做编排:取下一步 → 跑 handler → 落事件 → ok 推进 / stuck·needs 停。不含任何
OCR/分类/对账/记账业务逻辑(那是各步 handler 的活,T3-T6 实现);也不起线程、不重试、
不定时——M0 由 CLI 驱动跑一次,推进到底或停在卡点,再跑一次即从卡点继续。

状态唯一事实源 = work_orders.status + work_order_events 流(不建影子状态表)。断点续跑与
幂等都从事件流推导:某步的 step_done 事件存在即视为已完成,重跑直接跳过——已完成步既不
二次执行也不重复落事件,续跑天然从第一条未完成步继续。

handler 协议:run(ctx) -> StepResult。ctx 承载 cur/store/tenant/work_order 与步间数据袋;
store 注入(默认真 DAL,测试可换内存替身)让引擎逻辑可脱库验证。
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from services.workorder import store as _store

# 流水线固定顺序(任务包 §4)。M0 的 handler 实跑到 package;review/archive 是人审/归档
# 两态,M0 只落状态位、不跑 handler(人审界面属 M1)。
STEPS = (
    "intake",
    "sort",
    "classify",
    "reconcile",
    "compute",
    "package",
    "review",
    "archive",
)
_LAST_RUNNABLE = "package"
RUNNABLE_STEPS = STEPS[: STEPS.index(_LAST_RUNNABLE) + 1]
# 全部 runnable 步绿后停在此状态(review→archive 的推进是 M1 人审的事)。
TERMINAL_STATUS = "review"

# 工单 status 词汇全集(单一事实源 · decisions.py 词汇表同款收敛 · C4-R1)。
# collecting=开单默认(schema.py DDL DEFAULT 同词),running/stuck 由本引擎落,
# review=TERMINAL_STATUS,archive 由 services/workorder/archive.py 归档落。
# 任何消费方(矩阵徽章/看板/测试)一律 import 这里,不许手打字符串——
# C4 首验曾臆造 "archived"/"signed" 两词,真冻结单错标「未评估」,此表即根治。
STATUS_COLLECTING = "collecting"
STATUS_RUNNING = "running"
STATUS_STUCK = "stuck"
STATUS_REVIEW = TERMINAL_STATUS
STATUS_ARCHIVE = "archive"
ALL_STATUSES = (STATUS_COLLECTING, STATUS_RUNNING, STATUS_STUCK, STATUS_REVIEW, STATUS_ARCHIVE)

STEP_OK = "ok"
STEP_STUCK = "stuck"
STEP_NEEDS = "needs"

EVT_STARTED = "step_started"
EVT_DONE = "step_done"
EVT_STUCK = "step_stuck"
EVT_NEEDS = "step_needs"


class WorkOrderEngineError(RuntimeError):
    """引擎级契约错误(如某步无 handler 注册)。业务卡点走 StepResult,不走异常。"""


@dataclass(frozen=True)
class StepResult:
    """一步的三态结果。ok 携带并入 ctx.data 的产物;stuck/needs 携带停机原因。

    stuck 与 needs 都令工单停在 'stuck' 状态,但语义不同:stuck = 有料但过不去(内部矛盾/
    闸报警,如试算不平);needs = 缺料(要人补齐输入才能继续)。分开落事件便于人审定位。
    """

    status: str
    reasons: tuple = ()
    missing: tuple = ()
    payload: dict = field(default_factory=dict)

    @classmethod
    def ok(cls, **payload) -> "StepResult":
        return cls(STEP_OK, payload=payload)

    @classmethod
    def stuck(cls, reasons) -> "StepResult":
        return cls(STEP_STUCK, reasons=tuple(reasons))

    @classmethod
    def needs(cls, missing) -> "StepResult":
        return cls(STEP_NEEDS, missing=tuple(missing))

    @property
    def halted(self) -> bool:
        return self.status != STEP_OK


@dataclass
class StepContext:
    """步间上下文。store 可注入替身(真库 DAL 或内存 fake);data 是步与步之间的数据袋。

    cursor_factory:按步提交事务的开关(L2 教训)。给了 = 每个工单步骤各开一个独立事务
    (零参调用返回一个 `with ... as cur` 上下文管理器,如 db.get_cursor(commit=True)),步内
    业务写 + step_done + 状态位一起提交或一起回滚;进程在某步中途被杀 = 只丢该步、已完成步
    永久成立、续跑从下一未完成步继续,不重烧已完成步的 OCR。缺省 None = 全跑复用 ctx.cur
    的单事务旧路(内存驱动的测试 / CLI 兼容层由上层 get_cursor(commit=True) 收口)。
    """

    cur: Any
    tenant_id: str
    work_order_id: str
    store: Any = _store
    data: dict = field(default_factory=dict)
    cursor_factory: Optional[Callable] = None


Handler = Callable[[StepContext], StepResult]


@dataclass
class RunOutcome:
    """一次 run 的结果。completed=True 表示跑到 package 全绿(工单落 review);否则停在 stopped_at。"""

    status: str
    completed: bool
    stopped_at: Optional[str] = None
    result: Optional[StepResult] = None


def _preset_handler(step: str) -> Handler:
    """占位 handler:默认返回 ok,或读 ctx.data['_presets'][step] 的预置结果。

    T2 只交引擎骨架,各步真实业务(OCR/分类/对账/算税)是 T3-T6。预置结果让引擎自己的测试
    能驱动整条链跑绿,或在指定步注入 stuck/needs 验证停机与续跑。
    """

    def run(ctx: StepContext) -> StepResult:
        preset = (ctx.data.get("_presets") or {}).get(step)
        return preset if preset is not None else StepResult.ok()

    return run


def default_handlers() -> dict:
    """每步一个占位 handler 的注册表。T3-T6 用真实 handler 覆盖对应步的键。"""
    return {step: _preset_handler(step) for step in RUNNABLE_STEPS}


@contextmanager
def _shared_unit(ctx: StepContext):
    """无 cursor_factory:全跑复用 ctx.cur,引擎不在步间提交(内存驱动 / 单事务旧路)。"""
    yield ctx.cur


@contextmanager
def _committed_unit(ctx: StepContext):
    """有 cursor_factory:每步一个独立事务,块正常退出即提交、异常则回滚并抛。"""
    with ctx.cursor_factory() as cur:
        yield cur


def _unit_for(ctx: StepContext) -> Callable:
    return _committed_unit if ctx.cursor_factory else _shared_unit


@contextmanager
def _bound(ctx: StepContext, cur: Any):
    """把本步事务游标临时绑到 ctx.cur,让 handler / _emit / _set_status 都落在同一事务。"""
    prev = ctx.cur
    ctx.cur = cur
    try:
        yield
    finally:
        ctx.cur = prev


def _completed_steps(ctx: StepContext, unit: Callable) -> set:
    """从事件流推导已完成步(step_done 存在即完成)——续跑/幂等的唯一依据。"""
    with unit(ctx) as cur, _bound(ctx, cur):
        events = ctx.store.list_events(
            ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
        )
    return {e["step"] for e in events if e["event_type"] == EVT_DONE}


def _emit(ctx: StepContext, step: str, event_type: str, payload: dict) -> None:
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step=step,
        event_type=event_type,
        payload=payload,
    )


def _set_status(ctx: StepContext, status: str, step: str) -> None:
    ctx.store.set_status(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        status=status,
        current_step=step,
    )


def _halt(ctx: StepContext, step: str, result: StepResult) -> RunOutcome:
    """停机:落 stuck/needs 事件 + 工单状态置 stuck(current_step 停在卡点步)。"""
    if result.status == STEP_NEEDS:
        _emit(ctx, step, EVT_NEEDS, {"missing": list(result.missing)})
    else:
        _emit(ctx, step, EVT_STUCK, {"reasons": list(result.reasons)})
    _set_status(ctx, STATUS_STUCK, step)
    return RunOutcome(status=STATUS_STUCK, completed=False, stopped_at=step, result=result)


def _mark_running(ctx: StepContext, step: str) -> None:
    """进步即在一个独立短事务里提交 current_step=step(P-4 进度诚实)。

    主步事务把 set_status 与 handler(如 classify 真跑 219s)、step_done 绑在一起,提交前对
    别的连接不可见——详情读侧因此在 classify 全程看到上一步 sort,像死机(P-4 实锤)。这里在
    主步事务之前先独立提交一次 current_step,让轮询立刻看到真实步位。只在按步提交模式
    (cursor_factory 在场)启用:单事务旧路无独立提交语义,由主事务内的 _set_status 收口
    (逐字节维持现状)。不落 step_started 事件——那仍留在主步事务里随停机/异常一并回滚,
    「被杀整步回滚连 started 都不留」的续跑不变式(见 test_workorder_step_commit)不被破坏。"""
    with ctx.cursor_factory() as cur, _bound(ctx, cur):
        _set_status(ctx, STATUS_RUNNING, step)


def _run_step(
    ctx: StepContext, unit: Callable, step: str, handler: Handler
) -> Optional[RunOutcome]:
    """在一个事务单元里跑一步:started + 业务写 + (done | stuck/needs) + 状态位同落同回滚。

    返回 RunOutcome 表示本步停机(已在同一事务里落好停机态);None 表示本步绿、继续下一步。
    handler 抛异常时不吞:_committed_unit 回滚整步(started 也一并撤销)并向上抛,续跑重做本步。
    进步先独立提交 current_step(_mark_running)让进度诚实,再进主步事务(见 _mark_running)。
    """
    if ctx.cursor_factory is not None:
        _mark_running(ctx, step)
    with unit(ctx) as cur, _bound(ctx, cur):
        _emit(ctx, step, EVT_STARTED, {})
        _set_status(ctx, STATUS_RUNNING, step)
        result = handler(ctx)
        if result.halted:
            return _halt(ctx, step, result)
        ctx.data.update(result.payload)
        _emit(ctx, step, EVT_DONE, dict(result.payload))
    return None


def run_work_order(ctx: StepContext, *, handlers: Optional[dict] = None) -> RunOutcome:
    """跑流水线:从第一条未完成步推进到 package 全绿,或停在首个卡点。

    幂等键 = (work_order_id, step):某步已有 step_done 事件即跳过,不二次执行、不重复落事件。
    因此重跑同一工单要么补齐剩余步、要么在原卡点重试,已完成部分绝不重做。事务边界由
    ctx.cursor_factory 决定(见 StepContext):给了则每步独立提交,缺省则全跑单事务。
    """
    handlers = handlers or default_handlers()
    unit = _unit_for(ctx)
    done = _completed_steps(ctx, unit)

    for step in RUNNABLE_STEPS:
        if step in done:
            continue
        handler = handlers.get(step)
        if handler is None:
            raise WorkOrderEngineError(f"步 {step!r} 未注册 handler")
        outcome = _run_step(ctx, unit, step, handler)
        if outcome is not None:
            return outcome

    # 全部 runnable 步绿:落状态位到 review(review/archive 的人审推进属 M1)。
    with unit(ctx) as cur, _bound(ctx, cur):
        _set_status(ctx, TERMINAL_STATUS, TERMINAL_STATUS)
    return RunOutcome(status=TERMINAL_STATUS, completed=True)
