# -*- coding: utf-8 -*-
"""
ADR-005 #15 守门测试 · 对账异步 submit + 状态查询路由 + store 扩展。

锁定:
  1. 4 个路由 path+method 契约(2 recon submit + 1 vat submit + 1 jobs 状态)· app 真挂上
  2. store.enqueue 支持预生成 job_id(submit 用它命名暂存目录)· INSERT 带 id
  3. store.ensure_table 跑 CREATE TABLE IF NOT EXISTS + 索引(幂等建表)
  4. submit 端到端:落盘暂存(stmt/gl role)+ enqueue('bank') + 秒回 {ok, job_id}
  5. credits 不足 → 402(前置检查不被 submit 绕过)
  6. GET /api/recon/jobs/{id}:命中→映射 status/progress/result_*;不存在→404
  7. 权限批2:路由入口统一执行点 require_perm(services/authz/deps 单一来源)·
     逐路由码契约(submit=recon.create / GET job=recon.view / confirm-rows=recon.approve)
"""

import asyncio
import inspect
import io
import os
import re
import tempfile
import unittest
from unittest import mock

from fastapi import HTTPException

from routes import recon_jobs_routes as rjr
from services.recon_jobs import store, worker


class RouteContractTests(unittest.TestCase):
    def test_router_routes(self):
        got = set()
        for r in rjr.router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("POST", "/api/recon/bank-v2/submit"),
                ("POST", "/api/recon/gl-vat/submit"),
                ("POST", "/api/vat_excel/submit"),
                ("GET", "/api/recon/jobs/{job_id}"),
                ("POST", "/api/recon/bank-v2/confirm-rows/{job_id}"),  # S8
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/recon/bank-v2/submit", paths)
        self.assertIn("/api/recon/jobs/{job_id}", paths)

    def test_routes_use_require_perm_with_expected_codes(self):
        """权限批2:全部路由入口走统一执行点 require_perm(deps 单一来源)·
        逐路由码契约:submit=recon.create / GET job=recon.view / confirm-rows=recon.approve"""
        from services.authz import deps

        self.assertIs(rjr.require_perm, deps.require_perm)
        expected = {
            ("POST", "/api/recon/bank-v2/submit"): "recon.create",
            ("POST", "/api/recon/gl-vat/submit"): "recon.create",
            ("POST", "/api/vat_excel/submit"): "recon.create",
            ("GET", "/api/recon/jobs/{job_id}"): "recon.view",
            ("POST", "/api/recon/bank-v2/confirm-rows/{job_id}"): "recon.approve",
        }
        got = {}
        for r in rjr.router.routes:
            src = inspect.getsource(r.endpoint)
            m = re.search(r'require_perm\(request, "([\w.]+)"\)', src)
            for method in getattr(r, "methods", set()) or set():
                if method in ("GET", "POST"):
                    got[(method, r.path)] = m.group(1) if m else None
        self.assertEqual(got, expected)


class StoreEnqueueTests(unittest.TestCase):
    def _run_enqueue(self, **kw):
        cur = mock.MagicMock()
        cur.fetchone.return_value = {"id": "fixed-uuid"}
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        with mock.patch("services.recon_jobs.store.get_cursor", return_value=ctx):
            rid = store.enqueue("bank", "u1", "t1", {"a": 1}, [{"path": "x"}], **kw)
        return rid, cur.execute.call_args

    def test_enqueue_explicit_job_id(self):
        rid, call = self._run_enqueue(job_id="fixed-uuid")
        self.assertEqual(rid, "fixed-uuid")
        sql, params = call[0][0], call[0][1]
        self.assertIn("INSERT INTO recon_jobs (id", sql)
        self.assertEqual(params[0], "fixed-uuid")  # id 是第一个绑定参数
        # 关键守门:%s 占位符数必须 == 传入参数数(防『带了列却漏传值』→ tuple index out of range)
        self.assertEqual(sql.count("%s"), len(params), f"placeholder/param mismatch: {sql}")

    def test_enqueue_no_job_id_placeholder_param_match(self):
        rid, call = self._run_enqueue()
        sql, params = call[0][0], call[0][1]
        self.assertNotIn("INSERT INTO recon_jobs (id", sql)  # 走 gen_random_uuid 默认 id
        self.assertEqual(sql.count("%s"), len(params), f"placeholder/param mismatch: {sql}")

    def test_enqueue_rejects_bad_type(self):
        with self.assertRaises(ValueError):
            store.enqueue("nope", "u1", None)

    def test_ensure_table_runs_ddl(self):
        cur = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        with mock.patch("services.recon_jobs.store.get_cursor", return_value=ctx):
            ok = store.ensure_table()
        self.assertTrue(ok)
        stmts = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS recon_jobs" in s for s in stmts))
        self.assertEqual(sum("CREATE INDEX IF NOT EXISTS" in s for s in stmts), 3)


def _upload(name, data=b"x"):
    from fastapi import UploadFile

    return UploadFile(filename=name, file=io.BytesIO(data))


class SubmitFlowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        p = mock.patch.object(worker, "STAGE_DIR", self._tmp.name)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)
        # 权限批2:路由入口换统一执行点 require_perm(request, code)→ 过返 user dict
        self.perm_calls = []

        def fake_require_perm(request, code):
            self.perm_calls.append(code)
            return {"id": "u1", "tenant_id": "t1"}

        au = mock.patch.object(rjr, "require_perm", side_effect=fake_require_perm)
        au.start()
        self.addCleanup(au.stop)

    def test_bank_submit_stages_and_enqueues(self):
        captured = {}

        def fake_enqueue(
            job_type, uid, tid, params, input_ref, job_id=None, workspace_client_id=None
        ):
            captured.update(
                job_type=job_type,
                params=params,
                input_ref=input_ref,
                job_id=job_id,
                workspace_client_id=workspace_client_id,
            )
            return job_id

        with (
            mock.patch.object(rjr.store, "enqueue", side_effect=fake_enqueue),
            mock.patch.object(rjr, "_credits_precheck", return_value={"is_exempt": True}),
        ):
            out = asyncio.run(
                rjr.bank_v2_submit(
                    request=None,
                    stmt_files=[_upload("s.pdf", b"stmt")],
                    gl_files=[_upload("g.xlsx", b"gl")],
                    gl_account="1010",
                    lang="th",
                )
            )
        self.assertTrue(out["ok"])
        self.assertEqual(out["job_id"], captured["job_id"])
        self.assertEqual(captured["job_type"], "bank")
        self.assertEqual(self.perm_calls, ["recon.create"])  # 守门码契约
        roles = sorted(r["role"] for r in captured["input_ref"])
        self.assertEqual(roles, ["gl", "stmt"])
        # 文件真落盘
        for ref in captured["input_ref"]:
            self.assertTrue(os.path.isfile(ref["path"]))
        self.assertEqual(captured["params"]["gl_account"], "1010")

    def test_credits_insufficient_returns_402(self):
        def boom(*a, **k):
            raise HTTPException(402, detail={"code": "insufficient_balance"})

        with mock.patch.object(rjr, "_credits_precheck", side_effect=boom):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(
                    rjr.bank_v2_submit(
                        request=None,
                        stmt_files=[_upload("s.pdf")],
                        gl_files=[_upload("g.xlsx")],
                    )
                )
        self.assertEqual(ctx.exception.status_code, 402)


class GetJobTests(unittest.TestCase):
    def setUp(self):
        # 权限批2:GET job 守门 require_perm(request, "recon.view")→ 过返 user dict
        self.perm_calls = []

        def fake_require_perm(request, code):
            self.perm_calls.append(code)
            return {"id": "u1", "tenant_id": "t1"}

        au = mock.patch.object(rjr, "require_perm", side_effect=fake_require_perm)
        au.start()
        self.addCleanup(au.stop)

    def test_hit_maps_fields(self):
        job = {
            "id": "j1",
            "job_type": "bank",
            "status": "done",
            "progress": {"stage": "done"},
            "result_table": "bank_recon_v2_task",
            "result_id": "42",
            "error_code": None,
            "created_at": "2026-05-24T00:00:00",
            "finished_at": "2026-05-24T00:01:00",
        }
        with mock.patch.object(rjr.store, "get", return_value=job):
            out = asyncio.run(rjr.get_job("j1", request=None))
        self.assertEqual(self.perm_calls, ["recon.view"])  # 守门码契约
        self.assertEqual(out["status"], "done")
        self.assertEqual(out["result_table"], "bank_recon_v2_task")
        self.assertEqual(out["result_id"], "42")
        self.assertEqual(out["progress"], {"stage": "done"})

    def test_missing_404(self):
        with mock.patch.object(rjr.store, "get", return_value=None):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(rjr.get_job("nope", request=None))
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
