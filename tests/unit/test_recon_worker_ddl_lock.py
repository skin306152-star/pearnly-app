# -*- coding: utf-8 -*-
"""recon 内嵌 worker 启动建表必须套 startup_ddl_lock(4-worker 反死锁守门)。

内嵌 worker 每个进程启动时都会 store.ensure_table();workers=N 时并发 CREATE/ALTER
IF NOT EXISTS 抢 recon_jobs 的 AccessExclusiveLock → 互相死锁(实测回退过 workers=2)。
本测试锁定 ensure_table 在 startup_ddl_lock 持有期内执行,守住 workers=4 安全。
"""

import asyncio
import unittest
from unittest import mock

from services.recon_jobs import worker


class ReconWorkerDdlLockTests(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_table_runs_inside_startup_lock(self):
        order = []

        class TrackingLock:
            def __enter__(self):
                order.append("lock_acquired")
                return self

            def __exit__(self, *a):
                order.append("lock_released")
                return False

        stop = asyncio.Event()
        stop.set()  # 循环体不进 · ensure + bootstrap 后直接返回

        with (
            mock.patch.object(worker, "startup_ddl_lock", lambda: TrackingLock()),
            mock.patch.object(worker.store, "ensure_table", lambda: order.append("ensure")),
            mock.patch.object(worker, "bootstrap_handlers", lambda: None),
        ):
            await worker.run_worker(stop)

        # ensure 必须发生在 lock 持有期间(acquire → ensure → release)
        self.assertEqual(order[:3], ["lock_acquired", "ensure", "lock_released"])


class BootstrapHandlersTests(unittest.TestCase):
    def test_bootstrap_re_registers_after_registry_is_cleared(self):
        with mock.patch.dict(worker._HANDLERS, {}, clear=True):
            worker.bootstrap_handlers()
            self.assertIn("export", worker._HANDLERS)


class RunOneErrorCaptureTests(unittest.TestCase):
    """handler 抛异常时存真错到 error_code(别吞成通用 processing_error · 真账号诊断用)。"""

    def test_handler_exception_stores_real_message(self):
        def boom(params, input_ref, cb):
            raise ValueError("未上传 VAT 报告")

        with (
            mock.patch.dict(worker._HANDLERS, {"salesvat": boom}, clear=False),
            mock.patch.object(worker.store, "fail") as m_fail,
            mock.patch.object(worker, "_cleanup_stage"),
        ):
            worker._run_one({"id": "j1", "job_type": "salesvat", "params": {}, "input_ref": []})
        m_fail.assert_called_once()
        job_id, err = m_fail.call_args[0]
        self.assertEqual(job_id, "j1")
        self.assertIn("未上传 VAT 报告", err)
        self.assertNotEqual(err, "processing_error")

    def test_empty_message_falls_back_to_generic(self):
        def boom(params, input_ref, cb):
            raise RuntimeError("")

        with (
            mock.patch.dict(worker._HANDLERS, {"salesvat": boom}, clear=False),
            mock.patch.object(worker.store, "fail") as m_fail,
            mock.patch.object(worker, "_cleanup_stage"),
        ):
            worker._run_one({"id": "j2", "job_type": "salesvat", "params": {}, "input_ref": []})
        self.assertEqual(m_fail.call_args[0][1], "processing_error")

    def test_job_row_context_is_available_to_handler(self):
        seen = {}

        def handler(params, input_ref, cb):
            seen.update(params)
            return ("result", "1")

        job = {
            "id": "job-ctx",
            "job_type": "export",
            "user_id": "user-1",
            "tenant_id": "tenant-1",
            "workspace_client_id": 84,
            "params": {"format": "sheet"},
            "input_ref": [],
        }
        with (
            mock.patch.dict(worker._HANDLERS, {"export": handler}, clear=False),
            mock.patch.object(worker.store, "finish") as m_finish,
            mock.patch.object(worker, "_cleanup_stage"),
        ):
            worker._run_one(job)

        self.assertEqual(seen["job_id"], "job-ctx")
        self.assertEqual(seen["user_id"], "user-1")
        self.assertEqual(seen["tenant_id"], "tenant-1")
        self.assertEqual(seen["workspace_client_id"], 84)
        self.assertEqual(seen["format"], "sheet")
        m_finish.assert_called_once_with("job-ctx", "result", "1")

    def test_missing_handler_bootstraps_once_before_failing(self):
        def handler(params, input_ref, cb):
            return ("result", "2")

        def bootstrap():
            worker._HANDLERS["export"] = handler

        job = {"id": "job-bootstrap", "job_type": "export", "params": {}, "input_ref": []}
        with (
            mock.patch.dict(worker._HANDLERS, {}, clear=True),
            mock.patch.object(worker, "bootstrap_handlers", side_effect=bootstrap) as m_bootstrap,
            mock.patch.object(worker.store, "finish") as m_finish,
            mock.patch.object(worker.store, "fail") as m_fail,
            mock.patch.object(worker, "_cleanup_stage"),
        ):
            worker._run_one(job)

        m_bootstrap.assert_called_once()
        m_finish.assert_called_once_with("job-bootstrap", "result", "2")
        m_fail.assert_not_called()


if __name__ == "__main__":
    unittest.main()
