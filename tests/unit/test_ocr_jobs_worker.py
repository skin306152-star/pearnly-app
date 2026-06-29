# -*- coding: utf-8 -*-
"""services/ocr/jobs/worker.py _run_one 派发逻辑单测(缺口④)。

不起真循环 / 不打真 DB:mock store + 假 handler,断言成功→finish、__failed__→set_failed、
抛错→fail、无 handler→fail("no_handler")、套账/归属从 job 行注入 params。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401
from services.ocr.jobs import worker as w


def _clear_handlers():
    w._HANDLERS.clear()


class RunOneDispatchTests(unittest.TestCase):
    def setUp(self):
        _clear_handlers()
        # 不触发 bootstrap 去 import 真 handler 模块
        self._bs = mock.patch.object(w, "bootstrap_handlers", lambda: None)
        self._bs.start()
        self._clean = mock.patch.object(w, "_cleanup_stage", lambda *_a: None)
        self._clean.start()

    def tearDown(self):
        self._bs.stop()
        self._clean.stop()
        _clear_handlers()

    def test_success_calls_finish_with_result_and_history(self):
        w.register_handler(
            "web_ocr", lambda p, ir, cb: {"result": {"pages": [1]}, "history_ids": ["h1"]}
        )
        with mock.patch.object(w.store, "finish") as fin:
            w._run_one({"id": "j1", "job_type": "web_ocr", "params": {}})
        fin.assert_called_once()
        _, kw = fin.call_args
        self.assertEqual(kw["result"], {"pages": [1]})
        self.assertEqual(kw["history_ids"], ["h1"])

    def test_failed_sentinel_calls_set_failed(self):
        w.register_handler(
            "web_ocr", lambda p, ir, cb: ("__failed__", {"error_code": "not_invoice"})
        )
        with (
            mock.patch.object(w.store, "set_failed") as sf,
            mock.patch.object(w.store, "finish") as fin,
        ):
            w._run_one({"id": "j2", "job_type": "web_ocr", "params": {}})
        sf.assert_called_once_with("j2", "not_invoice")
        fin.assert_not_called()

    def test_handler_exception_calls_fail(self):
        def _boom(p, ir, cb):
            raise RuntimeError("pipeline blew up")

        w.register_handler("web_ocr", _boom)
        with mock.patch.object(w.store, "fail") as fail:
            w._run_one({"id": "j3", "job_type": "web_ocr", "params": {}})
        fail.assert_called_once()
        self.assertEqual(fail.call_args[0][0], "j3")
        self.assertIn("pipeline blew up", fail.call_args[0][1])

    def test_no_handler_fails_job(self):
        with mock.patch.object(w.store, "fail") as fail:
            w._run_one({"id": "j4", "job_type": "web_ocr", "params": {}})
        fail.assert_called_once_with("j4", "no_handler")

    def test_params_injected_from_job_row(self):
        seen = {}

        def _cap(p, ir, cb):
            seen.update(p)
            return {"result": {}, "history_ids": []}

        w.register_handler("web_ocr", _cap)
        with mock.patch.object(w.store, "finish"):
            w._run_one(
                {
                    "id": "j5",
                    "job_type": "web_ocr",
                    "user_id": "u9",
                    "tenant_id": "t9",
                    "workspace_client_id": 42,
                    "params": {},
                }
            )
        self.assertEqual(seen["job_id"], "j5")
        self.assertEqual(seen["user_id"], "u9")
        self.assertEqual(seen["tenant_id"], "t9")
        self.assertEqual(seen["workspace_client_id"], 42)

    def test_progress_cb_forwards_to_update_progress(self):
        captured = {}

        def _h(p, ir, cb):
            cb({"page": 2, "total": 5})
            return {"result": {}, "history_ids": []}

        w.register_handler("web_ocr", _h)
        with (
            mock.patch.object(w.store, "finish"),
            mock.patch.object(w.store, "update_progress") as up,
        ):
            w._run_one({"id": "j6", "job_type": "web_ocr", "params": {}})
        up.assert_called_once()
        self.assertEqual(up.call_args[0][1], {"page": 2, "total": 5})


class FlagGateTests(unittest.TestCase):
    def test_embedded_not_started_when_flag_off(self):
        with mock.patch.dict("os.environ", {"OCR_ASYNC_WEB": "0"}, clear=False):
            with mock.patch.object(w.asyncio, "create_task") as ct:
                w._embedded_task = None
                w.start_embedded()
            ct.assert_not_called()


if __name__ == "__main__":
    unittest.main()
