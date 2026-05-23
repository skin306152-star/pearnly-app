"""
v118.35.0.27 · 任务队列基础架构(最小版 · 内存实现)

目的:
- 为以后 100+ 并发铺路 · 不动 OCR 关键路径(避免 v0.20 那种事故)
- 接口契约稳定 · 以后装 Redis 时只 swap 实现 · 不改业务代码

当前实现:
- 进程内 deque + threading.Lock · 0 外部依赖
- 单实例进程内有效(多 worker 各自独立 · OK)

以后(装 Redis 时):
- 切到 redis.Redis(host, port).lpush / brpop
- consumer worker 独立进程(systemd 加 unit)
- 跨 uvicorn worker 共享队列
"""

from __future__ import annotations
import time
import uuid
import logging
import threading
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    kind: str  # 'ocr' / 'erp_push' / 'recon' 等
    payload: Dict[str, Any]
    state: str = "pending"  # pending / running / done / failed
    attempts: int = 0
    max_attempts: int = 3
    error: str = ""
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class InMemoryQueue:
    """进程内任务队列 · 线程安全 · 接口跟 Redis-based 实现对齐
    今晚部署不接 OCR · 仅作 Earn 监控展示 + 为以后铺路。
    """

    def __init__(self, max_size: int = 10000):
        self._pending: deque = deque()  # 待消费
        self._running: Dict[str, Task] = {}  # 处理中
        self._done: deque = deque(maxlen=200)  # 最近 200 条 done(给 dashboard 看)
        self._failed: deque = deque(maxlen=200)  # 最近 200 条 failed
        self._max_size = max_size
        self._lock = threading.Lock()

    def enqueue(self, kind: str, payload: Dict[str, Any], max_attempts: int = 3) -> str:
        with self._lock:
            if len(self._pending) >= self._max_size:
                raise RuntimeError(f"queue full(max={self._max_size})")
            t = Task(
                id=str(uuid.uuid4()),
                kind=kind,
                payload=payload,
                max_attempts=max_attempts,
            )
            self._pending.append(t)
            return t.id

    def dequeue(self) -> Optional[Task]:
        """consumer worker 拉一条"""
        with self._lock:
            if not self._pending:
                return None
            t = self._pending.popleft()
            t.state = "running"
            t.attempts += 1
            t.updated_at = time.time()
            self._running[t.id] = t
            return t

    def complete(self, task_id: str, result: Any = None):
        with self._lock:
            t = self._running.pop(task_id, None)
            if not t:
                return
            t.state = "done"
            t.result = result
            t.updated_at = time.time()
            self._done.append(t)

    def fail(self, task_id: str, error: str):
        with self._lock:
            t = self._running.pop(task_id, None)
            if not t:
                return
            t.error = error[:500]
            t.updated_at = time.time()
            if t.attempts < t.max_attempts:
                # 重试 · 回 pending 队列尾
                t.state = "pending"
                self._pending.append(t)
            else:
                # 终态失败
                t.state = "failed"
                self._failed.append(t)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pending": len(self._pending),
                "running": len(self._running),
                "done_recent": len(self._done),
                "failed_recent": len(self._failed),
                "max_size": self._max_size,
                "implementation": "in-memory(单进程 · 多 worker 各自独立)",
                "ready_for_redis": True,
            }

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            out = []
            for t in list(self._failed)[-limit:]:
                out.append(asdict(t))
            for t in list(self._done)[-(limit - len(out)) :]:
                out.append(asdict(t))
            out.sort(key=lambda x: x["updated_at"], reverse=True)
            return out[:limit]


# 全局单例
queue = InMemoryQueue()


def get_queue_stats() -> Dict[str, Any]:
    return queue.get_stats()


def enqueue_task(kind: str, payload: Dict[str, Any], max_attempts: int = 3) -> str:
    """对外入口 · TODO: 接 OCR 时换成这个 enqueue + asyncio 轮询 task 状态
    今晚不接 · 留契约。
    """
    return queue.enqueue(kind, payload, max_attempts)
