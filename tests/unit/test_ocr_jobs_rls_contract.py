# -*- coding: utf-8 -*-
"""RLS 契约:ocr_jobs store(缺口④ · tenant_or_user 队列表)。

约束(镜像 recon_jobs):
- 用户面 enqueue / get 必须把 tenant_id + user_id 注入 get_cursor_rls(无 bypass),
  否则启用 RLS 后用户读不到自己任务 / INSERT 被 WITH CHECK 拒。
- worker 队列操作(claim_next / update_progress / finish / set_failed / fail / reclaim_stale / gc_old)
  必须 bypass=True —— 跨租户后台调度,无 HTTP 单租户上下文。
锁定:不回退到裸 get_cursor。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

import core.db  # noqa: F401 — 先初始化 core.db
from services.ocr.jobs import store


class _Cur:
    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return {"id": "job-1", "user_id": "u1", "tenant_id": None, "status": "queued"}

    def fetchall(self):
        return []

    rowcount = 1


def _capture():
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur()

    return calls, fake


def _no_bare_get_cursor():
    return mock.patch(
        "services.ocr.jobs.store.get_cursor",
        side_effect=AssertionError("must use get_cursor_rls"),
    )


class OcrJobsUserFacingRls(unittest.TestCase):
    def test_enqueue_threads_tenant_and_user(self):
        calls, fake = _capture()
        with mock.patch("services.ocr.jobs.store.get_cursor_rls", fake), _no_bare_get_cursor():
            store.enqueue("u1", "ten-1", workspace_client_id=5)
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "u1")
        self.assertEqual(calls[0].get("workspace_client_id"), 5)
        self.assertNotEqual(calls[0].get("bypass"), True)

    def test_get_threads_tenant_and_user(self):
        calls, fake = _capture()
        with mock.patch("services.ocr.jobs.store.get_cursor_rls", fake), _no_bare_get_cursor():
            store.get("job-1", user_id="u1", tenant_id="ten-1")
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "u1")
        self.assertNotEqual(calls[0].get("bypass"), True)


class OcrJobsWorkerBypass(unittest.TestCase):
    """每个 worker 队列操作必须显式 bypass=True(系统级跨租户)。"""

    def _assert_bypass(self, fn, *args, **kwargs):
        calls, fake = _capture()
        with mock.patch("services.ocr.jobs.store.get_cursor_rls", fake), _no_bare_get_cursor():
            fn(*args, **kwargs)
        self.assertTrue(calls, f"{fn.__name__} 未走 get_cursor_rls")
        self.assertTrue(calls[0].get("bypass"), f"{fn.__name__} 必须 bypass=True")

    def test_claim_next(self):
        self._assert_bypass(store.claim_next, "w1")

    def test_update_progress(self):
        self._assert_bypass(store.update_progress, "job-1", {})

    def test_finish(self):
        self._assert_bypass(store.finish, "job-1")

    def test_set_failed(self):
        self._assert_bypass(store.set_failed, "job-1", "err")

    def test_fail(self):
        self._assert_bypass(store.fail, "job-1", "err")

    def test_reclaim_stale(self):
        self._assert_bypass(store.reclaim_stale)

    def test_gc_old(self):
        self._assert_bypass(store.gc_old)

    def test_get_status_map(self):
        # ENC-c janitor:跨租户批量状态查询,同样必须 bypass。
        self._assert_bypass(store.get_status_map, ["11111111-1111-1111-1111-111111111111"])


if __name__ == "__main__":
    unittest.main()
