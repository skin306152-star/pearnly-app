"""
v118.35.0.25 · 进程内监控模块
- 记录最近 10 分钟的 Gemini API 调用统计
- 给 admin 监控面板拉取
- 给 alerts.py 检测告警条件

设计:
- 内存 ring buffer · 0 DB 写入开销
- 线程安全(threading.Lock)
- 进程重启清零(可接受 · 长期统计走 credit_transactions)
"""

from __future__ import annotations
import time
import threading
from collections import deque
from typing import Dict, Any


class GeminiCallStats:
    """Gemini API 调用统计 · 进程内 ring buffer"""

    def __init__(self, window_sec: int = 600):
        self._win = window_sec  # 默认保留 10 分钟
        self._calls: deque = deque()
        # 每条: (ts, success: bool, http_status: int, latency_ms: int)
        self._today_total = 0
        self._today_429 = 0
        self._today_error = 0
        self._today_date = time.strftime("%Y-%m-%d")
        self._lock = threading.Lock()

    def _gc(self, now: float):
        """清理过期数据(O(N) · N 很小)"""
        cutoff = now - self._win
        while self._calls and self._calls[0][0] < cutoff:
            self._calls.popleft()

    def _rollover_today(self):
        """日期变了 → 重置今日计数"""
        today = time.strftime("%Y-%m-%d")
        if today != self._today_date:
            self._today_date = today
            self._today_total = 0
            self._today_429 = 0
            self._today_error = 0

    def record(self, success: bool, http_status: int = 0, latency_ms: int = 0):
        """记一次 Gemini 调用结果"""
        now = time.time()
        with self._lock:
            self._rollover_today()
            self._gc(now)
            self._calls.append((now, success, http_status, latency_ms))
            self._today_total += 1
            if http_status == 429:
                self._today_429 += 1
            if not success:
                self._today_error += 1

    def get_stats(self) -> Dict[str, Any]:
        """返当前监控数据 · 给前端 + 告警检查用"""
        now = time.time()
        with self._lock:
            self._rollover_today()
            self._gc(now)
            recent_60s = sum(1 for c in self._calls if c[0] >= now - 60)
            recent_5min = sum(1 for c in self._calls if c[0] >= now - 300)
            recent_5min_429 = sum(1 for c in self._calls if c[0] >= now - 300 and c[2] == 429)
            recent_5min_err = sum(1 for c in self._calls if c[0] >= now - 300 and not c[1])
            # 平均延迟(最近 5 分钟)
            recent_latencies = [c[3] for c in self._calls if c[0] >= now - 300 and c[3] > 0]
            avg_latency = (
                int(sum(recent_latencies) / len(recent_latencies)) if recent_latencies else 0
            )

            return {
                "rpm_now": recent_60s,  # 当前每分钟请求数
                "recent_5min_total": recent_5min,
                "recent_5min_429": recent_5min_429,
                "recent_5min_errors": recent_5min_err,
                "avg_latency_ms_5min": avg_latency,
                "today_total": self._today_total,
                "today_429": self._today_429,
                "today_errors": self._today_error,
                "today_date": self._today_date,
                "window_sec": self._win,
            }


class DBPoolStats:
    """DB 连接池统计 · 反映 db._pool 状态"""

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        try:
            from core import db as _db

            pool = _db._pool
            if pool is None:
                return {"available": False}
            # SimpleConnectionPool 内部状态(psycopg2 私有 API · best-effort)
            used = len(pool._used) if hasattr(pool, "_used") else 0
            available = (pool.maxconn - used) if hasattr(pool, "maxconn") else 0
            return {
                "available": True,
                "used": used,
                "max": pool.maxconn if hasattr(pool, "maxconn") else 0,
                "min": pool.minconn if hasattr(pool, "minconn") else 0,
                "free": available,
            }
        except Exception:
            return {"available": False}


# 全局单例
gemini_stats = GeminiCallStats(window_sec=600)


def record_gemini_call(success: bool, http_status: int = 200, latency_ms: int = 0):
    """调用入口 · 给 layer2/layer3 埋点用"""
    try:
        gemini_stats.record(success, http_status, latency_ms)
    except Exception:
        pass  # 监控失败不影响业务


def get_os_stats() -> Dict[str, Any]:
    """v0.26 · 服务器 OS 指标(尽可能不引新依赖)"""
    out = {"available": False}
    try:
        import os

        # Linux /proc 读法 · 0 额外依赖
        # 内存
        with open("/proc/meminfo") as f:
            mi = f.read()
        mem = {}
        for line in mi.splitlines():
            k, _, v = line.partition(":")
            v = v.strip().split()[0]
            try:
                mem[k.strip()] = int(v) * 1024  # KB → bytes
            except Exception:
                pass
        mem_total = mem.get("MemTotal", 0)
        mem_avail = mem.get("MemAvailable", 0)
        mem_used = mem_total - mem_avail
        # CPU(瞬时采样不准 · 取 loadavg)
        with open("/proc/loadavg") as f:
            la = f.read().strip().split()
        # 进程数
        try:
            import subprocess

            uvc = int(
                subprocess.run(
                    ["pgrep", "-cf", "uvicorn app:app"], capture_output=True, text=True, timeout=3
                ).stdout.strip()
                or "0"
            )
        except Exception:
            uvc = 0
        out = {
            "available": True,
            "mem_total_mb": mem_total // (1024 * 1024),
            "mem_used_mb": mem_used // (1024 * 1024),
            "mem_pct": round(mem_used / mem_total * 100, 1) if mem_total else 0,
            "loadavg_1min": float(la[0]) if len(la) > 0 else 0,
            "loadavg_5min": float(la[1]) if len(la) > 1 else 0,
            "loadavg_15min": float(la[2]) if len(la) > 2 else 0,
            "cpu_cores": os.cpu_count() or 1,
            "uvicorn_procs": uvc,
        }
    except Exception:
        pass
    return out


def get_queue_stats() -> Dict[str, Any]:
    """v0.27 · 任务队列状态(最小版 · 接口契约稳定)"""
    try:
        from services.task_queue import get_queue_stats as _q

        return _q()
    except Exception:
        return {"available": False}


def get_monitoring_overview() -> Dict[str, Any]:
    """admin 面板拉取入口"""
    return {
        "gemini": gemini_stats.get_stats(),
        "db_pool": DBPoolStats.get_stats(),
        "os": get_os_stats(),
        "queue": get_queue_stats(),
        "ts": int(time.time()),
    }
