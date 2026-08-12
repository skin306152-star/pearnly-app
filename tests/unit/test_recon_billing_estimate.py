# -*- coding: utf-8 -*-
"""修2(2026-08-12)守门测试 · 对账预检的 402 估价含 Excel/CSV 字符折算。

生产实锤:93 块余额被一笔 ฿186 的 Excel 字符折算扣成 -92.98。此前预检只按 PDF
件数估(len(files) 当页数),大 Excel 的「字符→张」折算只在事后 charge_ocr_async
硬扣,预检拦不住 → 余额被打穿。本测试锁定:
  1. estimate_recon_cost_thb = PDF 阶梯价 + Excel 字符折算张 × 基准张价(纯计算)
  2. account_status.can_cover_estimate:大字符 Excel + 低余额 → False(→402);
     余额够 → True(放行);套餐额度全覆盖 → True;not allowed → False
  3. submit 预检 _credits_precheck:大 Excel + 低余额 → 402(estimated_cost 含字符折算);
     余额够 → 放行
  4. 异步 job 开跑前闸:余额不足 → job failed(insufficient_balance);查不出 → lookup_error
"""

import asyncio
import tempfile
import unittest
from unittest import mock

from fastapi import HTTPException

from core import db  # noqa: F401 - 必须先于 account_status(否则 dal_reexports 循环导入)
from services.billing import account_status, pricing
from routes import recon_jobs_routes as rjr


class EstimateReconCostTests(unittest.TestCase):
    """估价公式:PDF 阶梯价 + Excel 字符折算成张 × 基准张价。"""

    def test_excel_chars_add_to_pdf_cost(self):
        # 纯 PDF:2 页 × ฿1.50(未用额度)
        pdf_only = pricing.estimate_recon_cost_thb(0, 2, 0)
        self.assertEqual(pdf_only, pricing.estimate_pdf_cost_thb(0, 2))
        # 1M 字符 ≈ ฿200 按量成本 → 134 张配额 → ฿201;再加 1 页 PDF ฿1.50
        with_excel = pricing.estimate_recon_cost_thb(0, 1, 1_000_000)
        quota = pricing.doc_quota_pages(1_000_000)
        self.assertEqual(quota, 134)
        self.assertEqual(
            with_excel,
            pricing.estimate_pdf_cost_thb(0, 1) + quota * pricing.DOC_QUOTA_REF_PRICE,
        )
        self.assertGreater(with_excel, pdf_only)

    def test_zero_units_zero_cost(self):
        self.assertEqual(pricing.estimate_recon_cost_thb(0, 0, 0), pricing._DecV21("0.00"))

    def test_no_excel_is_plain_pdf(self):
        self.assertEqual(
            pricing.estimate_recon_cost_thb(271, 2, 0), pricing.estimate_pdf_cost_thb(271, 2)
        )


class CanCoverEstimateTests(unittest.TestCase):
    """余额/套餐额度能否盖住整批估价的判据(钱闸单源)。"""

    def _status(self, **over):
        st = {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 100.0,
            "pages_used_this_month": 0,
            "subscription": None,
            "error_code": None,
        }
        st.update(over)
        return st

    def test_big_excel_low_balance_not_covered(self):
        # 生产实锤场景:93 块余额 vs 1M 字符 Excel(估价 ~฿202)→ 必须拒
        st = self._status(balance_thb=93.0)
        self.assertFalse(account_status.can_cover_estimate(st, pdf_units=1, excel_chars=1_000_000))

    def test_big_excel_sufficient_balance_covered(self):
        st = self._status(balance_thb=1000.0)
        self.assertTrue(account_status.can_cover_estimate(st, pdf_units=1, excel_chars=1_000_000))

    def test_not_allowed_never_covered(self):
        # 余额≤0 且无套餐额度 → 既有判据保留(与文件大小无关)
        st = self._status(allowed=False, balance_thb=0.0)
        self.assertFalse(account_status.can_cover_estimate(st, pdf_units=0, excel_chars=0))

    def test_exempt_always_covered(self):
        st = self._status(is_exempt=True, balance_thb=0.0, allowed=False)
        self.assertTrue(account_status.can_cover_estimate(st, pdf_units=99, excel_chars=99))

    def test_subscription_quota_covers_full_batch_free(self):
        # 套餐额度≥整批配额 → 免费放行,不看余额
        st = self._status(balance_thb=0.0, subscription={"remaining": 500, "over_rate": 1.5})
        self.assertTrue(account_status.can_cover_estimate(st, pdf_units=10, excel_chars=10_000))

    def test_subscription_partial_cover_checks_overage(self):
        # 套餐额度不够整批 → 超额按 over_rate 估:余额盖不住 → 拒
        st = self._status(
            balance_thb=10.0,
            subscription={"remaining": 100, "over_rate": 1.5},
        )
        # 10k 字符 → 2 张配额 + 200 页 pdf → 总 202 张,超额 102 张 × 1.5 = 153 > 10
        self.assertFalse(account_status.can_cover_estimate(st, pdf_units=200, excel_chars=10_000))
        # 余额盖得住超额 → 放行
        st2 = self._status(
            balance_thb=200.0,
            subscription={"remaining": 100, "over_rate": 1.5},
        )
        self.assertTrue(account_status.can_cover_estimate(st2, pdf_units=200, excel_chars=10_000))


class _FakeUpload:
    """记账用假上传:read() 计数 + seek(0) 还原(Submit 预检只读 Excel/CSV)。"""

    def __init__(self, filename, data=b"x"):
        self.filename = filename
        self._data = data
        self.reads = 0

    async def read(self, *a):
        self.reads += 1
        return self._data

    async def seek(self, *a):
        return None


def _billing_status(balance=93.0, allowed=True, sub=None):
    return {
        "allowed": allowed,
        "is_exempt": False,
        "balance_thb": balance,
        "pages_used_this_month": 271,
        "subscription": sub,
        "error_code": None,
    }


class CreditsPrecheckTests(unittest.IsolatedAsyncioTestCase):
    """submit 预检:_credits_precheck 估价必须含 Excel 字符折算。"""

    async def test_big_excel_low_balance_raises_402_with_excel_estimate(self):
        # 1 页 PDF + 1M 字符 CSV → 估价含 134 张 × ฿1.50 = ฿201+  → 93 块拒
        with mock.patch("core.db.get_billing_status_combined", return_value=_billing_status()):
            with self.assertRaises(HTTPException) as ctx:
                await rjr._credits_precheck(
                    "u1", "t1", [_FakeUpload("s.pdf"), _FakeUpload("g.csv", b"a" * 1_000_000)]
                )
        self.assertEqual(ctx.exception.status_code, 402)
        detail = ctx.exception.detail
        self.assertEqual(detail["code"], "insufficient_balance")
        self.assertGreater(detail["estimated_cost"], 100)  # 字符折算计入(旧实现只有 ~฿0.75)
        self.assertEqual(detail["balance"], 93.0)

    async def test_sufficient_balance_passes(self):
        ok = _billing_status(balance=1000.0)
        with mock.patch("core.db.get_billing_status_combined", return_value=ok):
            out = await rjr._credits_precheck(
                "u1", "t1", [_FakeUpload("s.pdf"), _FakeUpload("g.csv", b"a" * 1_000_000)]
            )
        self.assertIs(out, ok)

    async def test_exempt_skips_estimate_reads(self):
        with mock.patch(
            "core.db.get_billing_status_combined",
            return_value={"allowed": True, "is_exempt": True, "error_code": None},
        ):
            up = _FakeUpload("g.csv", b"a" * 1000)
            out = await rjr._credits_precheck("u1", "t1", [up])
        self.assertTrue(out["is_exempt"])
        self.assertEqual(up.reads, 0)  # 豁免不读文件估字符

    async def test_subscription_quota_covers_does_not_402(self):
        ok = _billing_status(balance=0.0, sub={"remaining": 500, "over_rate": 1.5})
        with mock.patch("core.db.get_billing_status_combined", return_value=ok):
            out = await rjr._credits_precheck("u1", "t1", [_FakeUpload("g.csv", b"a" * 10_000)])
        self.assertIs(out, ok)


class JobRunGateTests(unittest.IsolatedAsyncioTestCase):
    """异步 job 开跑前闸:提交时过 ≠ 现在够,跑前回查余额,不足置 failed。"""

    def _stage(self, d, role, name, data):
        import os

        p = os.path.join(d, name)
        with open(p, "wb") as f:
            f.write(data)
        return {"path": p, "filename": name, "role": role}

    def test_bank_handler_insufficient_balance_fails_job(self):
        from services.recon_jobs.bank_handler import run_bank_recon

        billing_low = {
            "allowed": False,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "subscription": None,
            "error_code": None,
        }
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch("core.db.get_billing_status_combined", return_value=billing_low) as status,
        ):
            refs = [
                self._stage(d, "stmt", "s.pdf", b"stmt"),
                self._stage(d, "gl", "g.xlsx", b"gl"),
            ]
            sentinel, payload = run_bank_recon(
                {"user_id": "u1", "tenant_id": "t1", "is_exempt": False}, refs, None
            )
        self.assertEqual(sentinel, "__failed__")
        self.assertEqual(payload["error_code"], "insufficient_balance")
        status.assert_called_once()

    def test_glvat_handler_lookup_error_fails_job_fail_closed(self):
        from services.recon_jobs.handlers import run_glvat

        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch(
                "core.db.get_billing_status_combined",
                return_value={"allowed": False, "is_exempt": False, "error_code": "lookup_error"},
            ),
        ):
            refs = [
                self._stage(d, "gl", "g.xlsx", b"gl"),
                self._stage(d, "vat", "v.pdf", b"vat"),
            ]
            sentinel, payload = run_glvat(
                {"user_id": "u1", "tenant_id": "t1", "is_exempt": False}, refs, None
            )
        self.assertEqual(sentinel, "__failed__")
        self.assertEqual(payload["error_code"], "lookup_error")

    def test_bank_handler_big_csv_and_low_balance_fails_job(self):
        """大字符 CSV(即使余额>0)也要在开跑前拦住,否则字符折算打穿透支。"""
        from services.recon_jobs.bank_handler import run_bank_recon

        billing_pos = {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 10.0,
            "pages_used_this_month": 0,
            "subscription": None,
            "error_code": None,
        }
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch("core.db.get_billing_status_combined", return_value=billing_pos),
        ):
            refs = [
                self._stage(d, "stmt", "s.csv", b"a" * 200_000),  # ~฿40 字符折算
                self._stage(d, "gl", "g.pdf", b"gl"),
            ]
            sentinel, payload = run_bank_recon(
                {"user_id": "u1", "tenant_id": "t1", "is_exempt": False}, refs, None
            )
        self.assertEqual(sentinel, "__failed__")
        self.assertEqual(payload["error_code"], "insufficient_balance")

    def test_bank_handler_sufficient_balance_runs(self):
        """余额够 → 闸过 → 正常跑(不进 failed)。"""
        from services.recon_jobs.bank_handler import run_bank_recon

        billing_ok = {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 1000.0,
            "pages_used_this_month": 0,
            "subscription": None,
            "error_code": None,
        }
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch("core.db.get_billing_status_combined", return_value=billing_ok),
            mock.patch("core.db.create_bank_recon_v2_task", return_value=777) as save,
            mock.patch(
                "routes.recon_routes.parse_bank_statement_pdf",
                return_value={"ok": True, "rows": [{}, {}]},
            ),
            mock.patch("routes.recon_routes.parse_gl_v2", return_value={"ok": True, "rows": [{}]}),
            mock.patch(
                "routes.recon_routes.merge_statements", return_value=([{}, {}], 100.0, 200.0, "BAY")
            ),
            mock.patch(
                "routes.recon_routes.merge_gl_files", return_value=([{}], ["1010"], 100.0, 200.0)
            ),
            mock.patch(
                "routes.recon_routes.bank_reconcile",
                return_value=(
                    [{"r": 1}],
                    mock.Mock(
                        matched_count=3,
                        gl_debit_only_count=1,
                        gl_credit_only_count=0,
                        stmt_withdrawal_only_count=0,
                        stmt_deposit_only_count=2,
                        formula_diff=0.0,
                    ),
                ),
            ),
            mock.patch("routes.recon_routes.rows_to_json", return_value=[{"r": 1}]),
            mock.patch("routes.recon_routes.bank_summary_to_json", return_value={}),
            mock.patch("routes.recon_routes._detect_recon_mismatch", return_value=[]),
            mock.patch("core.db.charge_ocr_async", return_value=None),
        ):
            refs = [
                self._stage(d, "stmt", "s.pdf", b"stmt"),
                self._stage(d, "gl", "g.xlsx", b"gl"),
            ]
            table, rid = run_bank_recon(
                {"user_id": "u1", "tenant_id": "t1", "is_exempt": False}, refs, None
            )
        self.assertEqual((table, rid), ("bank_recon_v2_task", 777))
        save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
