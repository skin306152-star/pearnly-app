# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 进程内监控模块 services/monitoring.py 行为契约

monitoring.py(GeminiCallStats ring buffer + 监控聚合入口)此前 0 专属测试。
本测试锁定其可观测行为(纯内存逻辑 · 无 DB / 无网络 / 无凭证):
  1) record + get_stats 计数正确(成功 / 失败 / 429 / 延迟均值)
  2) 时间窗口 GC(超 window_sec 的调用退出近期统计 · 但今日累计不受影响)
  3) 跨日 rollover 重置今日计数
  4) record_gemini_call 吞错不影响业务(监控失败不抛)
  5) get_monitoring_overview 接口契约(键齐全 + 子结构稳定)
  6) DBPoolStats 无池时 available=False
  7) 线程安全(并发 record 计数无丢失)

可控时间:用假时钟替换 services.monitoring.time(提供 time() + strftime())。
"""

import threading
import unittest
from unittest import mock

from services import monitoring


class _FakeClock:
    """假时钟 · 替换模块内的 time(time() + strftime() 两个方法够用)。"""

    def __init__(self, now=1_000.0, date="2026-05-27"):
        self.now = now
        self.date = date

    def time(self):
        return self.now

    def strftime(self, fmt):  # noqa: ARG002 - 固定返回受控日期
        return self.date


class GeminiCallStatsBasicTests(unittest.TestCase):
    def test_empty_stats_all_zero(self):
        clock = _FakeClock()
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats(window_sec=600)
            stats = s.get_stats()
        self.assertEqual(stats["rpm_now"], 0)
        self.assertEqual(stats["recent_5min_total"], 0)
        self.assertEqual(stats["recent_5min_429"], 0)
        self.assertEqual(stats["recent_5min_errors"], 0)
        self.assertEqual(stats["avg_latency_ms_5min"], 0)
        self.assertEqual(stats["today_total"], 0)
        self.assertEqual(stats["today_429"], 0)
        self.assertEqual(stats["today_errors"], 0)
        self.assertEqual(stats["today_date"], "2026-05-27")
        self.assertEqual(stats["window_sec"], 600)

    def test_counts_success_failure_429_and_latency(self):
        clock = _FakeClock(now=1_000.0)
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats(window_sec=600)
            s.record(success=True, http_status=200, latency_ms=100)
            s.record(success=True, http_status=200, latency_ms=300)
            s.record(success=False, http_status=429, latency_ms=0)  # 429 也算 error
            s.record(success=False, http_status=500, latency_ms=50)
            stats = s.get_stats()

        # 全部在同一秒 · 近 60s / 5min 都应是 4
        self.assertEqual(stats["rpm_now"], 4)
        self.assertEqual(stats["recent_5min_total"], 4)
        # 429:1 笔(http_status==429)
        self.assertEqual(stats["recent_5min_429"], 1)
        # error:success=False 的 2 笔(429 + 500)
        self.assertEqual(stats["recent_5min_errors"], 2)
        # 今日累计同步
        self.assertEqual(stats["today_total"], 4)
        self.assertEqual(stats["today_429"], 1)
        self.assertEqual(stats["today_errors"], 2)
        # 均值只统计 latency>0 的(100 / 300 / 50 → 450/3 = 150)· latency=0 的 429 不计入
        self.assertEqual(stats["avg_latency_ms_5min"], 150)

    def test_avg_latency_zero_when_no_positive_latency(self):
        clock = _FakeClock(now=2_000.0)
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats()
            s.record(success=True, http_status=200, latency_ms=0)
            stats = s.get_stats()
        self.assertEqual(stats["avg_latency_ms_5min"], 0)


class GeminiCallStatsWindowTests(unittest.TestCase):
    def test_rpm_window_60s_excludes_older_calls(self):
        clock = _FakeClock(now=1_000.0)
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats(window_sec=600)
            s.record(success=True, http_status=200, latency_ms=10)  # t=1000
            # 推进到 1061s(now-60=1001 · 旧调用 1000 < 1001 不计入 rpm)
            clock.now = 1_061.0
            stats = s.get_stats()
        self.assertEqual(stats["rpm_now"], 0)  # 退出 60s 窗
        self.assertEqual(stats["recent_5min_total"], 1)  # 仍在 5min 窗
        self.assertEqual(stats["today_total"], 1)  # 今日累计不受窗影响

    def test_gc_drops_calls_past_window(self):
        clock = _FakeClock(now=1_000.0)
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats(window_sec=600)
            s.record(success=False, http_status=429, latency_ms=10)  # t=1000
            # 推进过 window(cutoff = now-600)· 1601-600=1001 > 1000 → GC 掉
            clock.now = 1_601.0
            stats = s.get_stats()
        self.assertEqual(stats["recent_5min_total"], 0)
        self.assertEqual(stats["recent_5min_429"], 0)
        self.assertEqual(stats["recent_5min_errors"], 0)
        # 今日累计是独立计数器 · 不随 ring buffer GC 清零
        self.assertEqual(stats["today_total"], 1)
        self.assertEqual(stats["today_429"], 1)
        self.assertEqual(stats["today_errors"], 1)


class GeminiCallStatsRolloverTests(unittest.TestCase):
    def test_today_counters_reset_on_date_change(self):
        clock = _FakeClock(now=1_000.0, date="2026-05-27")
        with mock.patch.object(monitoring, "time", clock):
            s = monitoring.GeminiCallStats(window_sec=600)
            s.record(success=False, http_status=429, latency_ms=10)
            self.assertEqual(s.get_stats()["today_total"], 1)
            # 跨日
            clock.date = "2026-05-28"
            stats = s.get_stats()
        self.assertEqual(stats["today_date"], "2026-05-28")
        self.assertEqual(stats["today_total"], 0)
        self.assertEqual(stats["today_429"], 0)
        self.assertEqual(stats["today_errors"], 0)


class RecordGeminiCallSwallowsErrorTests(unittest.TestCase):
    def test_record_gemini_call_never_raises(self):
        # 监控失败不影响业务(铁律:监控 best-effort)
        with mock.patch.object(monitoring.gemini_stats, "record", side_effect=RuntimeError("boom")):
            # 不应抛
            monitoring.record_gemini_call(success=True, http_status=200, latency_ms=5)


class DBPoolStatsTests(unittest.TestCase):
    def test_no_pool_returns_unavailable(self):
        with mock.patch("db._pool", None):
            self.assertEqual(monitoring.DBPoolStats.get_stats(), {"available": False})


class MonitoringOverviewContractTests(unittest.TestCase):
    def test_overview_has_stable_keys(self):
        ov = monitoring.get_monitoring_overview()
        for key in ("gemini", "db_pool", "os", "queue", "ts"):
            self.assertIn(key, ov, f"overview 缺键 {key}")
        self.assertIsInstance(ov["ts"], int)
        # gemini 子结构键齐全(给前端 + 告警依赖)
        for key in (
            "rpm_now",
            "recent_5min_total",
            "recent_5min_429",
            "recent_5min_errors",
            "avg_latency_ms_5min",
            "today_total",
            "today_429",
            "today_errors",
            "today_date",
            "window_sec",
        ):
            self.assertIn(key, ov["gemini"], f"gemini 子结构缺键 {key}")
        # db_pool / os 永远带 available 标志(其 get_stats 必返该键)
        self.assertIn("available", ov["db_pool"])
        self.assertIn("available", ov["os"])
        # queue:正常时返真实队列统计(无 available)· 导入失败兜底才带 available
        # → 只锁定"是个 dict"的稳定契约
        self.assertIsInstance(ov["queue"], dict)


class GeminiCallStatsThreadSafetyTests(unittest.TestCase):
    def test_concurrent_records_no_loss(self):
        # 真并发 record · today_total 必须等于总写入数(锁有效)
        s = monitoring.GeminiCallStats(window_sec=600)
        n_threads, per_thread = 8, 500

        def worker():
            for _ in range(per_thread):
                s.record(success=True, http_status=200, latency_ms=1)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(s.get_stats()["today_total"], n_threads * per_thread)


if __name__ == "__main__":
    unittest.main()
