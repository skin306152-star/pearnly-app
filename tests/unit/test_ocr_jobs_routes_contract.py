# -*- coding: utf-8 -*-
"""routes/ocr_jobs_routes.py 契约(缺口④ · 网页 OCR 异步 submit/状态)。

锁定:① 两路由注册(POST /api/ocr/submit · GET /api/ocr/jobs/{job_id})
     ② 状态查询带归属校验(store.get 收到 user_id + tenant_id · 防越权看别人任务)
     ③ done 才回 result · 非 done 时 result 为 None(不冒充完成)。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401
from routes import ocr_jobs_routes as r


class RouteRegistrationContract(unittest.TestCase):
    def test_both_routes_registered(self):
        paths = {(rt.path, m) for rt in r.router.routes for m in (rt.methods or set())}
        self.assertIn(("/api/ocr/submit", "POST"), paths)
        self.assertIn(("/api/ocr/jobs/{job_id}", "GET"), paths)


class GetJobContract(unittest.IsolatedAsyncioTestCase):
    async def test_ownership_threaded_and_done_gates_result(self):
        job = {
            "id": "job-1",
            "status": "done",
            "progress": {"stage": "done"},
            "result": {"pages": [1]},
            "error_code": None,
            "created_at": "t0",
            "finished_at": "t1",
        }
        with (
            mock.patch.object(
                r, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t1"}
            ),
            mock.patch.object(r.store, "get", return_value=job) as get,
        ):
            out = await r.get_ocr_job("job-1", request=mock.MagicMock())
        # 归属校验:store.get 必须拿到 user_id + tenant_id
        self.assertEqual(get.call_args.kwargs.get("user_id"), "u1")
        self.assertEqual(get.call_args.kwargs.get("tenant_id"), "t1")
        self.assertEqual(out["result"], {"pages": [1]})

    async def test_non_done_hides_result(self):
        job = {
            "id": "j",
            "status": "running",
            "progress": {},
            "result": {"x": 1},
            "error_code": None,
        }
        with (
            mock.patch.object(
                r, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": None}
            ),
            mock.patch.object(r.store, "get", return_value=job),
        ):
            out = await r.get_ocr_job("j", request=mock.MagicMock())
        self.assertIsNone(out["result"])  # 非 done 不回结果

    async def test_missing_job_404(self):
        from fastapi import HTTPException

        with (
            mock.patch.object(
                r, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": None}
            ),
            mock.patch.object(r.store, "get", return_value=None),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await r.get_ocr_job("missing", request=mock.MagicMock())
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
