# -*- coding: utf-8 -*-
"""页级限流治理:撞 429/quota 不立刻定罪 —— 退避重试 + 进程内共享降速窗。

病根(2026-09-18 线上):Vertex 按【项目】每分钟限流,一张 N 页的票 = N 次模型调用、4 路并发
一次打完(实测 13 页 ≈ 11 秒)。任一页撞 429 就拿不到结果,而 L2 这条路上没有任何退避或降速
—— 该页直接抛穿 → 整份文件 500「引擎错误」,已经成功的 N-1 页一起作废。实测一次 13 页上传里
12 页成功、1 页被限流,用户拿到的是「识别结果为空」。

同款治理在跑批路径早已存在(services/workorder/steps/ocr_quota.py · QuotaGovernor:单件指数
退避 + 全局降速 + 退避用尽挂待补),但**网页上传这条路径从未接入** —— 本模块把那套口径里与
「单次调用」有关的部分抽出来给上传路径复用:L1/L2 的判据、退避时长、跨线程共享的暂停窗。

与跑批版的差异:网页上传是一次同步请求,没有「待补件」这个状态,所以退避用尽仍然上抛(由
调用方决定整体失败还是转人工)。本模块只保证「先退避、先降速,不硬冲」,不改任何 OCR 判读。
"""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from typing import Callable, TypeVar

logger = logging.getLogger("mr-pilot")

T = TypeVar("T")

# 单页 L2 撞限流后的最大尝试次数(含首跑)。限流是按分钟计的,几次退避通常就能过。
_DEFAULT_ATTEMPTS = int(os.environ.get("OCR_QUOTA_MAX_ATTEMPTS", "3"))
# 指数退避基数/上限(秒)。
_BASE_SLEEP_S = float(os.environ.get("OCR_QUOTA_BASE_SLEEP_S", "1.5"))
_MAX_SLEEP_S = float(os.environ.get("OCR_QUOTA_MAX_SLEEP_S", "15"))
# 任一页撞限流后,本进程所有页起跑前要等的共享暂停窗(秒)。
_PAUSE_S = float(os.environ.get("OCR_QUOTA_PAUSE_S", "4"))
# 单次等待的硬上限,防止暂停窗把请求拖到浏览器超时之后。
_MAX_WAIT_S = float(os.environ.get("OCR_QUOTA_MAX_WAIT_S", "30"))

_lock = threading.Lock()
_pause_until = 0.0

# 只读消费 OCR 层的 quota 异常类型做精确判据(取不到则退化为子串判据,不因导入失败失灵)。
try:
    from .layer2_gemini import Layer2QuotaError

    _QUOTA_TYPES: tuple = (Layer2QuotaError,)
except Exception:  # noqa: BLE001
    _QUOTA_TYPES = ()


def is_quota_error(exc: object) -> bool:
    """异常是否属于配额/限流。先认已知类型,再兜底认名字/消息里的 quota 字样。"""
    if _QUOTA_TYPES and isinstance(exc, _QUOTA_TYPES):
        return True
    if not isinstance(exc, Exception):
        return False
    return "quota" in f"{type(exc).__name__} {exc}".lower()


def max_attempts() -> int:
    return max(1, _DEFAULT_ATTEMPTS)


def call_with_backoff(fn: Callable[[], T], *, label: str) -> T:
    """跑一次会撞限流的模型调用:撞 quota 退避重试,退避用尽上抛。

    只对配额类错误退避;其他错误(鉴权/坏 JSON)立即上抛 —— 退避治不了它们,重试只是浪费。
    起跑前先等共享暂停窗,避免并发池以同一时间点再撞一次。
    """
    attempts = max_attempts()
    for attempt in range(attempts):
        wait_for_clear()
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - 判据在下面:非配额类原样上抛
            if not is_quota_error(exc):
                raise
            note_quota()
            if attempt + 1 >= attempts:
                raise
            delay = delay_for(attempt)
            logger.warning(
                "pipeline: %s quota (attempt %d/%d) · backing off %.1fs: %s",
                label,
                attempt + 1,
                attempts,
                delay,
                exc,
            )
            time.sleep(delay)
    raise AssertionError("unreachable: loop either returns or raises")  # pragma: no cover


def delay_for(attempt: int) -> float:
    """指数退避 + 抖动。

    抖动是必须的:并发池里 N 个线程同时被限流、又同时醒来,会以完全相同的时间点再撞一次,
    等于把限流变成自我同步的脉冲。加 0~40% 抖动把它们的醒来时间打散。
    """
    base = _BASE_SLEEP_S * (2 ** max(0, attempt))
    return min(base * (1 + random.random() * 0.4), _MAX_SLEEP_S)


def note_quota() -> None:
    """任一页撞限流 → 抬高本进程共享暂停窗,让并发池别继续硬冲。"""
    global _pause_until
    with _lock:
        _pause_until = max(_pause_until, time.monotonic() + _PAUSE_S)


def wait_for_clear(*, max_wait_s: float = _MAX_WAIT_S) -> float:
    """起跑前若在暂停窗内则等到窗过;返回实际等待秒数(0 = 无需等待)。"""
    with _lock:
        remaining = _pause_until - time.monotonic()
    if remaining <= 0:
        return 0.0
    wait = min(remaining, max_wait_s)
    time.sleep(wait)
    return wait


def _reset_pause_for_tests() -> None:
    """测试用:清空共享暂停窗(生产不调用)。"""
    global _pause_until
    with _lock:
        _pause_until = 0.0


__all__ = [
    "call_with_backoff",
    "delay_for",
    "is_quota_error",
    "max_attempts",
    "note_quota",
    "wait_for_clear",
]
