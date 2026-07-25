# -*- coding: utf-8 -*-
"""routes/ocr_jobs_routes.py 契约(缺口④ · 网页 OCR 异步 submit/状态)。

锁定:① 两路由注册(POST /api/ocr/submit · GET /api/ocr/jobs/{job_id})
     ② 状态查询带归属校验(store.get 收到 user_id + tenant_id · 防越权看别人任务)
     ③ done 才回 result · 非 done 时 result 为 None(不冒充完成)
     ④ submit 接住 posting_kind 并随 job 载荷存(与同步路对齐 · 声明不静默丢失)。
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import db  # noqa: F401
from routes import ocr_jobs_routes as r


class RouteRegistrationContract(unittest.TestCase):
    def test_both_routes_registered(self):
        paths = {(rt.path, m) for rt in r.router.routes for m in (rt.methods or set())}
        self.assertIn(("/api/ocr/submit", "POST"), paths)
        self.assertIn(("/api/ocr/jobs/{job_id}", "GET"), paths)


class SubmitPayloadContract(unittest.TestCase):
    """走真 multipart(不直调函数):字段缺省时的 None 由 FastAPI 解出,直调只会拿到 Form 哨兵。"""

    def setUp(self):
        self._patches = [
            mock.patch.object(
                r, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t1"}
            ),
            mock.patch.object(r.worker, "stage_dir_for", return_value="/tmp/ocr-stage-test"),
            mock.patch("os.makedirs"),
            mock.patch("builtins.open", mock.mock_open()),
            mock.patch.object(r.store, "enqueue", return_value="job-1"),
        ]
        started = [p.start() for p in self._patches]
        self.enqueue = started[-1]
        app = FastAPI()
        app.include_router(r.router)
        self.client = TestClient(app)

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _submit(self, data=None):
        resp = self.client.post(
            "/api/ocr/submit", files={"file": ("inv.pdf", b"PDFBYTES")}, data=data or {}
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        return self.enqueue.call_args.kwargs["params"]

    def test_posting_kind_stored_in_job_params(self):
        # 前端没声明 → 键在但值 None(= 未声明),handler 直取即可,不是缺键。
        self.assertEqual(self._submit({"posting_kind": "stock"})["posting_kind"], "stock")
        self.assertIsNone(self._submit()["posting_kind"])


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
