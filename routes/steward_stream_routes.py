# -*- coding: utf-8 -*-
"""管家任务步骤事件 SSE(S1 便宜流式方案):推 loop_state 现成 steps 账本的增量。

一端点:
  GET /api/ai/steward/tasks/{task_id}/events   text/event-stream

不是 token 级流式:大脑输出是 JSON 决策对象(brain_loop 非流式),逐字流物理上无从
流起。这条流推的是【任务投影的变化】—— 与 GET /tasks/{tid} 同一份 store.public_task,
变了就发一帧,前端把它当加速版轮询吃(同一条渲染路,SSE 断了回落 5s 轮询零改动)。

事件契约(前端 static/ai/ai-steward-stream.js 逐条对齐):
  event: task   data=public_task JSON      投影有变化(含进门第一帧)
  event: end    data={"reason": ...}       终态已发完(terminal)/ 连接到时(timeout,
                                           任务还在跑,前端回落轮询接着盯)
  “: ping” 注释行                            保活(代理别把安静的连接掐了)

鉴权同全组(routes/steward_common 双闸,fail-closed 404),判在流开始之前。
DB 读走 asyncio.to_thread:这是常驻数分钟的 async 生成器,sync 读挂在事件循环上
会把同进程所有请求一起卡住(uvicorn 2 workers 扛不住这种自伤)。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import db
from routes.steward_common import NOT_FOUND, authorize_steward
from services.steward import store, worker

router = APIRouter()
logger = logging.getLogger(__name__)

_TICK_S = 1.0
# 单连接上限 ≈ 5 分钟(300 tick):够住绝大多数任务;到时发 end(timeout),前端回落轮询。
_MAX_TICKS = 300
# 失联收口跑在每第 5 拍(与 5s 轮询的自愈节奏同拍),不必每秒开一个写事务。
_HEAL_EVERY = 5
_PING_EVERY = 15

REASON_TERMINAL = "terminal"
REASON_TIMEOUT = "timeout"


def _read_task(tenant_id: str, task_id: str, heal: bool) -> Optional[dict]:
    """同步读一拍(线程池里跑)。heal 拍带失联收口 —— worker 死了,盯着 SSE 的人也要
    在时限后看到诚实的 failed,不是一条永远安静的流。"""
    with db.get_cursor(commit=heal) as cur:
        if heal:
            worker.heal_stale(cur, tenant_id=tenant_id, task_id=task_id)
        task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    return store.public_task(task) if task else None


def _frame(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


async def _event_stream(tenant_id: str, task_id: str):
    last = ""
    for tick in range(_MAX_TICKS):
        # 首轮(tick=0)不自愈:毫秒前 task_events() 的常规 GET 预检刚 heal 过。
        heal = tick > 0 and tick % _HEAL_EVERY == 0
        task = await asyncio.to_thread(_read_task, tenant_id, task_id, heal)
        if task is None:
            # 任务行没了(会话被删):流如实收口,前端按 end 处理。
            yield _frame("end", {"reason": REASON_TERMINAL})
            return
        snapshot = json.dumps(task, sort_keys=True, ensure_ascii=False, default=str)
        if snapshot != last:
            last = snapshot
            yield _frame("task", task)
        if task.get("status") in (
            store.TASK_DONE,
            store.TASK_FAILED,
            store.TASK_WAITING_USER,
            store.TASK_CANCELLED,
        ):
            yield _frame("end", {"reason": REASON_TERMINAL})
            return
        if tick and tick % _PING_EVERY == 0:
            yield ": ping\n\n"
        await asyncio.sleep(_TICK_S)
    yield _frame("end", {"reason": REASON_TIMEOUT})


@router.get("/api/ai/steward/tasks/{task_id}/events")
async def task_events(task_id: str, request: Request):
    """任务事件流。首帧前先确认任务存在(404 与 GET /tasks/{tid} 同口径),
    避免对不存在的 id 挂一条只会发 end 的空流。预检只查存在不 heal ——
    heal 交给流内第 5 拍起(打开视图三连读收敛:同窗口毫秒内连续读同一行)。
    """
    _user, tenant_id = authorize_steward(request)
    store.ensure_once()
    task = await asyncio.to_thread(_read_task, tenant_id, task_id, False)
    if task is None:
        raise HTTPException(404, detail=NOT_FOUND)
    return StreamingResponse(
        _event_stream(tenant_id, task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            # nginx 反代默认攒缓冲,SSE 会被整段扣到连接关闭才吐 —— 必须关。
            "X-Accel-Buffering": "no",
        },
    )
