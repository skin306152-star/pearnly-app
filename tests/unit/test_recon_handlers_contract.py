# -*- coding: utf-8 -*-
"""
ADR-005 #14 守门测试 · 对账重活抽成后台 handler(services/recon_jobs/handlers.py)。

锁定(防『纯搬』搬出 bug + 防接口改 submit 后行为漂移):
  1. 三个 handler 签名 (params, input_ref, progress_cb) · import 即注册进 worker · 同一份对象
  2. _read_inputs 按 role 读暂存文件 · 保序
  3. _parallel 保持输入顺序
  4. run_bank_recon:正常 → ("bank_recon_v2_task", id) · 进度走 parse→reconcile→persist→done
     · 整侧全失败 → 存失败任务记录(不抛)
  5. run_glvat:正常 → ("gl_vat_task", id) · GL 0 行 / VAT 0 行 → 抛(交工人记 failed)
  6. run_salesvat:正常 → ("vat_recon_tasks", id) · 落盘 excel

解析/对账/Gemini 全部 mock —— 本测试只锁『调用编排 + 返回结果指针』· 不验识别准确率
(那是 bank_recon_v2 / gl_vat_reconciler / vat_excel_export 自己的测试)。
"""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from services.recon_jobs import handlers, worker


class RegistrationContractTests(unittest.TestCase):
    def test_signature(self):
        import inspect

        for fn in (handlers.run_bank_recon, handlers.run_glvat, handlers.run_salesvat):
            params = list(inspect.signature(fn).parameters)
            self.assertEqual(params, ["params", "input_ref", "progress_cb"])

    def test_registered_same_object(self):
        # import handlers 即触发 _register() · worker 拿到的是同一份对象
        self.assertIs(worker._HANDLERS.get("bank"), handlers.run_bank_recon)
        self.assertIs(worker._HANDLERS.get("glvat"), handlers.run_glvat)
        self.assertIs(worker._HANDLERS.get("salesvat"), handlers.run_salesvat)


class HelperTests(unittest.TestCase):
    def test_read_inputs_by_role_ordered(self):
        with tempfile.TemporaryDirectory() as d:
            refs = []
            for i, role in enumerate(["stmt", "gl", "stmt"]):
                p = os.path.join(d, f"f{i}.bin")
                with open(p, "wb") as f:
                    f.write(f"data{i}".encode())
                refs.append({"path": p, "filename": f"orig{i}.pdf", "role": role})
            stmt = handlers._read_inputs(refs, "stmt")
            gl = handlers._read_inputs(refs, "gl")
            self.assertEqual([fn for _, fn in stmt], ["orig0.pdf", "orig2.pdf"])
            self.assertEqual(stmt[0][0], b"data0")
            self.assertEqual([fn for _, fn in gl], ["orig1.pdf"])

    def test_parallel_preserves_order(self):
        self.assertEqual(handlers._parallel(lambda x: x * 2, [1, 2, 3, 4, 5]), [2, 4, 6, 8, 10])
        self.assertEqual(handlers._parallel(lambda x: x, []), [])
        self.assertEqual(handlers._parallel(lambda x: x + 1, [9]), [10])


def _stage(d, role, name="f.pdf", data=b"x"):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(data)
    return {"path": p, "filename": name, "role": role}


class RunBankReconTests(unittest.TestCase):
    def _patch(self, **over):
        """patch recon_routes 名字 + db · 返回 (patchers, db_mock)。"""
        summary = SimpleNamespace(
            matched_count=3,
            gl_debit_only_count=1,
            gl_credit_only_count=0,
            stmt_withdrawal_only_count=0,
            stmt_deposit_only_count=2,
            formula_diff=0.0,
        )
        defaults = dict(
            parse_bank_statement_pdf=mock.Mock(return_value={"ok": True, "rows": [{}, {}]}),
            parse_gl_v2=mock.Mock(return_value={"ok": True, "rows": [{}]}),
            merge_statements=mock.Mock(return_value=([{}, {}], 100.0, 200.0, "BAY")),
            merge_gl_files=mock.Mock(return_value=([{}], ["1010"], 100.0, 200.0)),
            bank_reconcile=mock.Mock(return_value=([{"r": 1}], summary)),
            rows_to_json=mock.Mock(return_value=[{"r": 1}]),
            bank_summary_to_json=mock.Mock(return_value={}),
            _detect_recon_mismatch=mock.Mock(return_value=[]),
        )
        defaults.update(over)
        ps = [mock.patch(f"recon_routes.{k}", v) for k, v in defaults.items()]
        for p in ps:
            p.start()
            self.addCleanup(p.stop)
        dbm = mock.patch("db.create_bank_recon_v2_task", return_value=777)
        dbm.start()
        self.addCleanup(dbm.stop)
        return defaults

    def test_happy_path(self):
        self._patch()
        with tempfile.TemporaryDirectory() as d:
            refs = [_stage(d, "stmt", "s.pdf"), _stage(d, "gl", "g.xlsx")]
            stages = []
            params = {"user_id": "u1", "tenant_id": "t1", "lang": "th", "gl_account": "1010"}
            table, rid = handlers.run_bank_recon(params, refs, lambda p: stages.append(p["stage"]))
        self.assertEqual((table, rid), ("bank_recon_v2_task", 777))
        for s in ("parse", "reconcile", "persist", "done"):
            self.assertIn(s, stages)

    def test_one_side_all_fail_saves_failed_task(self):
        # stmt 全失败 → 不抛 · 存失败诊断任务 · 返回 failed task 指针
        self._patch(parse_bank_statement_pdf=mock.Mock(return_value={"ok": False, "error": "boom"}))
        with tempfile.TemporaryDirectory() as d:
            refs = [_stage(d, "stmt", "s.pdf"), _stage(d, "gl", "g.xlsx")]
            with mock.patch("db.create_bank_recon_v2_task", return_value=999) as save:
                table, rid = handlers.run_bank_recon({"user_id": "u1"}, refs, None)
        self.assertEqual((table, rid), ("bank_recon_v2_task", 999))
        save.assert_called_once()


class RunGlvatTests(unittest.TestCase):
    def _patch_parse(self, gl_ret, vat_ret):
        for name, ret in (("parse_gl", gl_ret), ("parse_vat_report", vat_ret)):
            p = mock.patch(f"recon_routes.{name}", return_value=ret)
            p.start()
            self.addCleanup(p.stop)

    def test_happy_path(self):
        self._patch_parse(
            {"ok": True, "rows": [{"a": 1}], "row_count": 1},
            {"ok": True, "rows": [{"b": 2}], "row_count": 1},
        )
        detail = [
            SimpleNamespace(gl_amount=10.0, diff=0.0),
            SimpleNamespace(gl_amount=None, diff=0),
        ]
        with (
            mock.patch("recon_routes.reconcile_gl_vat", return_value=(detail, object())),
            mock.patch("recon_routes.detail_to_json", return_value=[]),
            mock.patch("recon_routes.summary_to_json", return_value={}),
            mock.patch("db.create_gl_vat_task", return_value=555),
        ):
            with tempfile.TemporaryDirectory() as d:
                refs = [_stage(d, "gl", "g.xlsx"), _stage(d, "vat", "v.pdf")]
                table, rid = handlers.run_glvat(
                    {"user_id": "u1", "revenue_prefix": "4"}, refs, None
                )
        self.assertEqual((table, rid), ("gl_vat_task", 555))

    def test_gl_no_rows_raises(self):
        self._patch_parse({"ok": True, "rows": []}, {"ok": True, "rows": [{"b": 2}]})
        with tempfile.TemporaryDirectory() as d:
            refs = [_stage(d, "gl", "g.xlsx"), _stage(d, "vat", "v.pdf")]
            with self.assertRaises(ValueError):
                handlers.run_glvat({"user_id": "u1"}, refs, None)

    def test_vat_no_rows_raises(self):
        self._patch_parse(
            {"ok": True, "rows": [{"a": 1}], "row_count": 1}, {"ok": True, "rows": []}
        )
        with tempfile.TemporaryDirectory() as d:
            refs = [_stage(d, "gl", "g.xlsx"), _stage(d, "vat", "v.pdf")]
            with self.assertRaises(ValueError):
                handlers.run_glvat({"user_id": "u1"}, refs, None)


class RunSalesvatTests(unittest.TestCase):
    def test_happy_path(self):
        rep = {
            "ok": True,
            "rows": [{"x": 1}],
            "row_count": 1,
            "seller_name": "ACME",
            "seller_tax_id": "0105",
            "period_year": 2026,
            "period_month": 5,
        }
        summary = {"n_total": 1, "n_ok": 1, "n_diff": 0, "diff_amount_total": 0.0}
        with (
            mock.patch("vat_excel_export.merge_vat_reports", return_value=rep),
            mock.patch("vat_excel_export.extract_invoices_parallel", return_value=[{"ok": True}]),
            mock.patch("vat_excel_export.build_excel", return_value=(b"XLSX", summary)),
            mock.patch("vat_excel_routes._save_excel_file", return_value="/tmp/x.xlsx"),
            mock.patch("db.create_vat_recon_task", return_value="abc-uuid"),
            mock.patch("db.get_cursor"),
            mock.patch("db.log_ocr_cost"),
            mock.patch("db.get_latest_balance", return_value={"calibration_factor": 1.1}),
        ):
            with tempfile.TemporaryDirectory() as d:
                refs = [_stage(d, "invoice", "i.pdf"), _stage(d, "report", "r.pdf")]
                params = {"user_id": "u1", "tenant_id": "t1", "lang": "th", "is_exempt": True}
                table, rid = handlers.run_salesvat(params, refs, None)
        self.assertEqual((table, rid), ("vat_recon_tasks", "abc-uuid"))


if __name__ == "__main__":
    unittest.main()
