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


if __name__ == "__main__":
    unittest.main()
