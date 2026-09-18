"""页级限流治理回归(2026-09-18 线上:13 页里 1 页被限流 → 整份作废、12 页成果全丢)。

钉两件事:
  ① 单页 L2 撞 quota 会退避重试,后续成功就正常返回(不再整份 500);
  ② 退避不是单机独舞 —— 任一页撞限流会抬高进程共享暂停窗,别的页起跑前先等,避免并发池
     以完全相同的时间点再撞一次(限流按项目/分钟计,硬冲只会把窗口一直顶住)。
"""

import unittest
from pathlib import Path
from unittest import mock

from services.ocr import page_runner
from services.ocr import quota_pacing
from services.ocr.layer2_gemini import Layer2QuotaError


def _throttle(message: str = "layer2: gateway (quota)"):
    def fn():
        raise Layer2QuotaError(message)

    return fn


class QuotaPacingTests(unittest.TestCase):
    def setUp(self):
        quota_pacing._reset_pause_for_tests()

    def test_backoff_grows_with_attempt_and_is_capped(self):
        d0, d1, d2 = (quota_pacing.delay_for(i) for i in range(3))

        self.assertLess(d0, d1)
        self.assertLess(d1, d2)
        self.assertLessEqual(quota_pacing.delay_for(10), quota_pacing._MAX_SLEEP_S)

    def test_backoff_is_jittered(self):
        """并发池同时被限流、又同时醒来 = 把限流变成自我同步的脉冲,必须有抖动。"""
        seen = {round(quota_pacing.delay_for(0), 6) for _ in range(30)}

        self.assertGreater(len(seen), 1)

    def test_note_quota_opens_a_shared_window_for_other_pages(self):
        with mock.patch.object(quota_pacing.time, "sleep") as sleep:
            self.assertEqual(quota_pacing.wait_for_clear(), 0.0)
            quota_pacing.note_quota()
            waited = quota_pacing.wait_for_clear()

        self.assertGreater(waited, 0.0)
        sleep.assert_called_once()

    def test_quota_detected_by_type_and_by_substring_fallback(self):
        class Boom(Exception):
            pass

        self.assertTrue(quota_pacing.is_quota_error(Layer2QuotaError("layer2: gateway (quota)")))
        self.assertTrue(quota_pacing.is_quota_error(Boom("RESOURCE_EXHAUSTED: quota exceeded")))
        self.assertFalse(quota_pacing.is_quota_error(ValueError("layer2: bad json")))


class CallWithBackoffTests(unittest.TestCase):
    def setUp(self):
        quota_pacing._reset_pause_for_tests()

    def test_page_survives_a_throttled_first_attempt(self):
        attempts = {"n": 0}

        def fn():
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise Layer2QuotaError("layer2: gateway (quota) model=gemini-test")
            return "l2-result"

        with (
            mock.patch.object(quota_pacing.time, "sleep") as slept,
            mock.patch.object(quota_pacing, "wait_for_clear", return_value=0.0),
        ):
            result = quota_pacing.call_with_backoff(fn, label="page 7 L2")

        self.assertEqual(result, "l2-result")
        self.assertEqual(attempts["n"], 2)
        slept.assert_called_once()

    def test_page_still_raises_when_every_attempt_is_throttled(self):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            raise Layer2QuotaError("layer2: gateway (quota)")

        with (
            mock.patch.object(quota_pacing.time, "sleep"),
            mock.patch.object(quota_pacing, "wait_for_clear", return_value=0.0),
        ):
            with self.assertRaises(Layer2QuotaError):
                quota_pacing.call_with_backoff(fn, label="page 7 L2")

        self.assertEqual(calls["n"], quota_pacing.max_attempts())

    def test_non_quota_errors_are_not_retried(self):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            raise ValueError("layer2: bad json")

        with (
            mock.patch.object(quota_pacing.time, "sleep") as slept,
            mock.patch.object(quota_pacing, "wait_for_clear", return_value=0.0),
        ):
            with self.assertRaises(ValueError):
                quota_pacing.call_with_backoff(fn, label="page 7 L2")

        self.assertEqual(calls["n"], 1)
        slept.assert_not_called()

    def test_a_throttled_page_slows_the_other_pages_down(self):
        """本页撞限流 → 共享暂停窗被抬高 → 另一页起跑前先等(而不是两个线程一起再撞)。"""
        with (
            mock.patch.object(quota_pacing.time, "sleep"),
            mock.patch.object(quota_pacing, "wait_for_clear", return_value=0.0),
        ):
            with self.assertRaises(Layer2QuotaError):
                quota_pacing.call_with_backoff(_throttle(), label="page 7 L2")

        with mock.patch.object(quota_pacing.time, "sleep") as slept:
            waited = quota_pacing.wait_for_clear()

        self.assertGreater(waited, 0.0)
        slept.assert_called_once()


class L2CallSiteWiringTests(unittest.TestCase):
    def test_l2_has_exactly_one_call_site_and_it_goes_through_the_backoff(self):
        """接线回归:L2 必须走退避包装,且全程只有这一个调用点。

        加一条裸调用 = 那条路又回到「撞一次限流整份作废」,而这个回归靠行为测试很难覆盖
        (要起整条 L1→L2→校验链),所以按结构钉死。
        """
        source = Path(page_runner.__file__).read_text(encoding="utf-8")

        self.assertIn("quota_pacing.call_with_backoff(", source)
        self.assertEqual(
            source.count("_l2_extract_page("),
            1,
            "L2 调用点不止一处:新增的裸调用绕过了限流退避",
        )


if __name__ == "__main__":
    unittest.main()
