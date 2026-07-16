# -*- coding: utf-8 -*-
"""跑批 OCR 撞配额(quota / 429 / RESOURCE_EXHAUSTED)退避治理(R1 · 件二)。

病根:gateway 把限流标准化为 error_kind=quota,OCR 层升为 Layer2QuotaError/Layer3QuotaError
上抛;classify 旧路对任何异常一视同仁(单件 flagged),无退避、无降速 → 一股脑撞满触发限流
+ 贵回落 + 半路死(真跑 15/104 就 stuck 的病根之一)。

本模块两件事:
  ① 单件退避重试:撞 quota 不立即定罪,指数退避后重试(上限 max_attempts 次),仍 quota 才
     交回异常(classify 据此 flag ocr_error:quota、诚实待补,续跑再试)。
  ② 全局降速:任一 worker 撞 quota 即抬高一个共享「暂停窗」,所有 worker 起跑前先睡够这段窗
     (不许并发池继续硬冲)。

配额判据只读异常(isinstance 已知 quota 类型 + 兜底子串),不改 OCR 判读/路由;时钟与 sleep
可注入,便于脱时钟脱真等待地断言调用时间轴。
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable

# 只读消费 OCR 层的 quota 异常类型做精确判据(取不到则退化为子串判据,绝不因导入失败失灵)。
try:
    from services.ocr.layer2_gemini import Layer2QuotaError
    from services.ocr.layer3_gemini import Layer3QuotaError

    _QUOTA_TYPES: tuple = (Layer2QuotaError, Layer3QuotaError)
except Exception:  # noqa: BLE001 - 判据兜底,导入不可用不影响运行
    _QUOTA_TYPES = ()


def is_quota_error(exc: object) -> bool:
    """异常是否为配额/限流类。先认已知 quota 异常类型,再兜底认名字/消息里的 quota 字样。"""
    if _QUOTA_TYPES and isinstance(exc, _QUOTA_TYPES):
        return True
    if not isinstance(exc, Exception):
        return False
    return "quota" in f"{type(exc).__name__} {exc}".lower()


def max_attempts() -> int:
    """单件撞 quota 的总尝试上限(含首次)。默认 3:配额多为瞬时限流,3 次退避足够穿过大多数
    限流窗;仍撞则诚实待补(续跑再试)。env PEARNLY_WORKORDER_OCR_QUOTA_MAX_ATTEMPTS 覆写。"""
    try:
        return max(1, int(os.environ.get("PEARNLY_WORKORDER_OCR_QUOTA_MAX_ATTEMPTS", "3")))
    except ValueError:
        return 3


def backoff_base_seconds() -> float:
    """指数退避基数(秒)。第 i 次退避睡 base·2^i。默认 2.0。
    env PEARNLY_WORKORDER_OCR_QUOTA_BACKOFF_SECONDS 覆写(测试注入小值免真等)。"""
    try:
        return max(0.0, float(os.environ.get("PEARNLY_WORKORDER_OCR_QUOTA_BACKOFF_SECONDS", "2.0")))
    except ValueError:
        return 2.0


class QuotaGovernor:
    """配额退避 + 全局降速协调器(线程安全)。一次跑批一个实例,所有 OCR worker 共享。"""

    def __init__(
        self,
        *,
        attempts: int | None = None,
        backoff_base: float | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.max_attempts = attempts if attempts is not None else max_attempts()
        self._backoff_base = backoff_base if backoff_base is not None else backoff_base_seconds()
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._pause_until = 0.0

    def await_clear(self) -> None:
        """起跑前把上一次 quota 设的全局暂停窗睡完(全局降速:别的 worker 也不硬冲)。"""
        while True:
            with self._lock:
                remaining = self._pause_until - self._clock()
            if remaining <= 0:
                return
            self._sleep(remaining)

    def backoff_for(self, attempt: int) -> float:
        return self._backoff_base * (2**attempt)

    def penalize(self, attempt: int) -> float:
        """撞 quota:抬高全局暂停窗(降速),返回本次退避时长。"""
        delay = self.backoff_for(attempt)
        with self._lock:
            self._pause_until = max(self._pause_until, self._clock() + delay)
        return delay

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            self._sleep(seconds)


def fetch_with_retry(fetch: Callable[[], object], *, governor: QuotaGovernor | None = None):
    """取一件 OCR,单件隔离 + 配额退避。返回 fields dict 或异常对象(不抛,不拖垮整批)。

    无 governor(直调/测试)→ 单次尝试,异常原样返回(旧行为)。有 governor → 撞 quota 指数
    退避重试至上限;非 quota 异常立即返回(不重试);用满仍 quota 返回最后那个 quota 异常。"""
    if governor is None:
        return _attempt_once(fetch)
    result: object = None
    for attempt in range(governor.max_attempts):
        governor.await_clear()
        result = _attempt_once(fetch)
        if not (isinstance(result, Exception) and is_quota_error(result)):
            return result
        delay = governor.penalize(attempt)  # 全局降速(含最后一次,续跑的 worker 也慢下来)
        if attempt < governor.max_attempts - 1:
            governor.sleep(delay)  # 只在还要重试时睡本 worker
    return result


def _attempt_once(fetch: Callable[[], object]):
    try:
        return fetch()
    except Exception as exc:  # noqa: BLE001 - 单件隔离,绝不拖垮整步
        return exc
