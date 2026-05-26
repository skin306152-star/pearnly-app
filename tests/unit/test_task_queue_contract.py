# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 进程内任务队列 services/task_queue.py 行为契约

task_queue.py(InMemoryQueue · 为未来 Redis 化铺路的最小实现)此前 0 专属测试。
纯内存逻辑 · 无外部依赖(Wave 0 安全网 · 零冲突)。

锁定 enqueue/dequeue/complete/fail 生命周期 + 重试语义 + 统计 + 满队列保护,
这些是「以后 swap Redis 实现时不能破坏」的接口契约。
"""

import unittest

from services.task_queue import InMemoryQueue
from services import task_queue as tq


class EnqueueDequeueTests(unittest.TestCase):
    def setUp(self):
        self.q = InMemoryQueue()

    def test_enqueue_returns_id_and_pending(self):
        tid = self.q.enqueue("ocr", {"file": "a.pdf"})
        self.assertIsInstance(tid, str)
        self.assertEqual(self.q.get_stats()["pending"], 1)

    def test_dequeue_moves_to_running_and_bumps_attempts(self):
        self.q.enqueue("ocr", {"x": 1})
        t = self.q.dequeue()
        self.assertIsNotNone(t)
        self.assertEqual(t.state, "running")
        self.assertEqual(t.attempts, 1)
        self.assertEqual(t.payload, {"x": 1})
        stats = self.q.get_stats()
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["running"], 1)

    def test_dequeue_empty_returns_none(self):
        self.assertIsNone(self.q.dequeue())

    def test_queue_full_raises(self):
        q = InMemoryQueue(max_size=2)
        q.enqueue("k", {})
        q.enqueue("k", {})
        with self.assertRaises(RuntimeError):
            q.enqueue("k", {})


class CompleteFailTests(unittest.TestCase):
    def setUp(self):
        self.q = InMemoryQueue()

    def test_complete_moves_to_done(self):
        tid = self.q.enqueue("ocr", {})
        self.q.dequeue()
        self.q.complete(tid, result={"ok": True})
        stats = self.q.get_stats()
        self.assertEqual(stats["running"], 0)
        self.assertEqual(stats["done_recent"], 1)
        recent = self.q.get_recent()
        self.assertEqual(recent[0]["state"], "done")
        self.assertEqual(recent[0]["result"], {"ok": True})

    def test_complete_unknown_id_noop(self):
        # 不抛 · 不影响统计
        self.q.complete("does-not-exist")
        self.assertEqual(self.q.get_stats()["done_recent"], 0)

    def test_fail_under_max_requeues_to_pending(self):
        self.q.enqueue("ocr", {}, max_attempts=3)
        self.q.dequeue()  # attempts=1
        self.q.fail(self.q_first_running_id(), "boom")
        stats = self.q.get_stats()
        self.assertEqual(stats["pending"], 1)  # 回队列重试
        self.assertEqual(stats["running"], 0)
        self.assertEqual(stats["failed_recent"], 0)

    def test_fail_at_max_goes_terminal(self):
        q = InMemoryQueue()
        tid = q.enqueue("ocr", {}, max_attempts=2)
        q.dequeue()
        q.fail(tid, "e1")  # attempts=1 < 2 → 回 pending
        self.assertEqual(q.get_stats()["pending"], 1)
        t2 = q.dequeue()  # attempts=2
        q.fail(t2.id, "e2")  # 2 < 2 False → 终态 failed
        stats = q.get_stats()
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["failed_recent"], 1)
        recent = q.get_recent()
        self.assertEqual(recent[0]["state"], "failed")

    def test_fail_truncates_error_to_500(self):
        q = InMemoryQueue()
        tid = q.enqueue("ocr", {}, max_attempts=1)
        q.dequeue()
        q.fail(tid, "x" * 1000)
        recent = q.get_recent()
        self.assertEqual(len(recent[0]["error"]), 500)

    def q_first_running_id(self):
        # 取当前唯一 running 任务的 id(测试 helper)
        return next(iter(self.q._running))


class StatsAndRecentTests(unittest.TestCase):
    def test_stats_keys_stable(self):
        q = InMemoryQueue(max_size=5)
        stats = q.get_stats()
        for key in (
            "pending",
            "running",
            "done_recent",
            "failed_recent",
            "max_size",
            "implementation",
            "ready_for_redis",
        ):
            self.assertIn(key, stats)
        self.assertEqual(stats["max_size"], 5)
        self.assertTrue(stats["ready_for_redis"])

    def test_get_recent_sorted_desc_by_updated_at(self):
        q = InMemoryQueue()
        for i in range(3):
            tid = q.enqueue("ocr", {"i": i})
            q.dequeue()
            q.complete(tid, result=i)
        recent = q.get_recent()
        self.assertEqual(len(recent), 3)
        times = [r["updated_at"] for r in recent]
        self.assertEqual(times, sorted(times, reverse=True))  # 最新在前

    def test_get_recent_respects_limit(self):
        q = InMemoryQueue()
        for _ in range(5):
            tid = q.enqueue("ocr", {})
            q.dequeue()
            q.complete(tid)
        self.assertEqual(len(q.get_recent(limit=2)), 2)


class ModuleEntrypointTests(unittest.TestCase):
    def test_enqueue_task_and_get_queue_stats_use_singleton(self):
        before = tq.get_queue_stats()["pending"]
        tq.enqueue_task("ocr", {"probe": True})
        after = tq.get_queue_stats()["pending"]
        self.assertEqual(after, before + 1)
        # 清理:把刚塞的消费掉 · 不污染全局单例后续统计
        t = tq.queue.dequeue()
        tq.queue.complete(t.id)


if __name__ == "__main__":
    unittest.main()
