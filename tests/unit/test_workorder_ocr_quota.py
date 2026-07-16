# -*- coding: utf-8 -*-
"""跑批 OCR 撞配额退避 + 全局降速守门(services/workorder/steps/ocr_quota.py · R1 件二)。

脱时钟脱真等待:注入 fake clock + fake sleep,断言 ①单件撞 quota 指数退避重试至上限、
用满仍 quota 返回该异常;②非 quota 异常不重试立即返回;③撞 quota 抬高全局暂停窗(别的
worker await_clear 会被降速);④调用时间轴按 base·2^i 退避展开。
"""

from __future__ import annotations

import unittest

from services.workorder.steps import ocr_quota


class _QuotaBoom(Exception):
    """名字/消息带 quota 的假异常(is_quota_error 子串判据命中)。"""


class _FakeClock:
    def __init__(self):
        self.t = 0.0
        self.slept: list = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += seconds  # sleep 推进虚拟时钟,免真等


class IsQuotaErrorTests(unittest.TestCase):
    def test_recognizes_quota_by_substring(self):
        self.assertTrue(ocr_quota.is_quota_error(_QuotaBoom("layer2: gateway (quota)")))
        self.assertTrue(ocr_quota.is_quota_error(RuntimeError("RESOURCE_EXHAUSTED quota hit")))

    def test_non_quota_is_false(self):
        self.assertFalse(ocr_quota.is_quota_error(ValueError("cannot decode image")))
        self.assertFalse(ocr_quota.is_quota_error("not even an exception"))


class FetchWithRetryTests(unittest.TestCase):
    def _governor(self, clock, *, attempts=3, base=2.0):
        return ocr_quota.QuotaGovernor(
            attempts=attempts, backoff_base=base, clock=clock.now, sleep=clock.sleep
        )

    def test_no_governor_single_attempt_returns_exc(self):
        got = ocr_quota.fetch_with_retry(lambda: (_ for _ in ()).throw(_QuotaBoom("quota")))
        self.assertIsInstance(got, _QuotaBoom)

    def test_quota_retries_to_limit_then_returns_quota_exc(self):
        clock = _FakeClock()
        calls = {"n": 0}

        def fetch():
            calls["n"] += 1
            raise _QuotaBoom("quota")

        result = ocr_quota.fetch_with_retry(fetch, governor=self._governor(clock))
        self.assertIsInstance(result, _QuotaBoom)
        self.assertEqual(calls["n"], 3)  # 首读 + 2 退避重试 = max_attempts
        # 时间轴:两次退避睡 base·2^0=2、base·2^1=4(指数退避在生效);末次不再睡。
        self.assertEqual(clock.slept, [2.0, 4.0])

    def test_quota_then_success_returns_fields(self):
        clock = _FakeClock()
        seq = [_QuotaBoom("quota"), {"total_amount": "107.00"}]

        def fetch():
            item = seq.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        result = ocr_quota.fetch_with_retry(fetch, governor=self._governor(clock))
        self.assertEqual(result, {"total_amount": "107.00"})
        self.assertEqual(clock.slept, [2.0])  # 只退避一次就成功

    def test_non_quota_exception_not_retried(self):
        clock = _FakeClock()
        calls = {"n": 0}

        def fetch():
            calls["n"] += 1
            raise ValueError("corrupt image")

        result = ocr_quota.fetch_with_retry(fetch, governor=self._governor(clock))
        self.assertIsInstance(result, ValueError)
        self.assertEqual(calls["n"], 1)  # 非配额异常不重试
        self.assertEqual(clock.slept, [])


class GlobalSlowdownTests(unittest.TestCase):
    def test_penalize_raises_global_pause_window(self):
        # 全局降速:一个 worker 撞 quota penalize 后,另一个 worker await_clear 会被睡够暂停窗。
        clock = _FakeClock()
        gov = ocr_quota.QuotaGovernor(
            attempts=3, backoff_base=2.0, clock=clock.now, sleep=clock.sleep
        )
        gov.penalize(1)  # base·2^1 = 4:全局暂停窗抬到 now+4
        gov.await_clear()  # 另一 worker 起跑前先睡够这段窗
        self.assertEqual(clock.slept, [4.0])
        # 窗过后再起跑不再空睡。
        clock.slept.clear()
        gov.await_clear()
        self.assertEqual(clock.slept, [])


if __name__ == "__main__":
    unittest.main()
