# -*- coding: utf-8 -*-
"""影子双跑运行体守门:钱字段归一/比对、开关优先级、调度门(单票单图才跑)、
失败降级(3.5 挂了落 status=failed 不抛)。纯逻辑,DB/网关全 mock,不连真服务。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ocr import shadow_money as sm


class NumTests(unittest.TestCase):
    def test_strips_symbols_and_separators(self):
        self.assertEqual(sm._num("฿1,780.00"), 1780.0)
        self.assertEqual(sm._num("44.67"), 44.67)
        self.assertEqual(sm._num(84), 84.0)

    def test_empty_and_bad_are_none(self):
        self.assertIsNone(sm._num(None))
        self.assertIsNone(sm._num(""))
        self.assertIsNone(sm._num("N/A"))


class MimeTests(unittest.TestCase):
    def test_images_detected(self):
        self.assertEqual(sm._mime_for("receipt.JPG"), "image/jpeg")
        self.assertEqual(sm._mime_for("a.png"), "image/png")

    def test_pdf_and_unknown_are_none(self):
        self.assertIsNone(sm._mime_for("invoice.pdf"))
        self.assertIsNone(sm._mime_for(""))


class CompareTests(unittest.TestCase):
    def test_equal_all_match(self):
        b = {"total_amount": "1780", "vat": "116.45", "discount": None, "subtotal": "1663.55"}
        s = {"total_amount": 1780, "vat": 116.45, "discount": None, "subtotal": 1663.55}
        values, matches, all_m = sm._compare(b, s)
        self.assertTrue(all_m)
        self.assertTrue(all(matches.values()))
        self.assertEqual(values["total"], (1780.0, 1780.0))

    def test_total_mismatch_breaks_all(self):
        b = {"total_amount": "416"}
        s = {"total_amount": "84"}
        _, matches, all_m = sm._compare(b, s)
        self.assertFalse(matches["total"])
        self.assertFalse(all_m)

    def test_one_side_missing_is_mismatch(self):
        _, matches, all_m = sm._compare({"vat": "10"}, {"vat": None})
        self.assertFalse(matches["vat"])
        self.assertFalse(all_m)

    def test_both_missing_field_matches(self):
        _, matches, all_m = sm._compare({"discount": None}, {"discount": None})
        self.assertTrue(matches["discount"])
        self.assertTrue(all_m)

    def test_b_only_marks_none(self):
        values, matches, all_m = sm._b_only({"total_amount": "500"})
        self.assertIsNone(all_m)
        self.assertIsNone(matches["total"])
        self.assertEqual(values["total"], (500.0, None))


class SwitchTests(unittest.TestCase):
    def test_env_off_wins(self):
        with mock.patch.dict("os.environ", {"SHADOW_MONEY_CHECK": "off"}):
            self.assertEqual(sm._switch(), (False, 0.0))

    def test_setting_disabled_off(self):
        with mock.patch.dict("os.environ", {"SHADOW_MONEY_CHECK": ""}):
            with mock.patch(
                "services.platform_settings.store.get_setting", return_value={"enabled": False}
            ):
                on, _ = sm._switch()
                self.assertFalse(on)

    def test_default_on_with_min_amount(self):
        with mock.patch.dict("os.environ", {"SHADOW_MONEY_CHECK": ""}):
            with mock.patch(
                "services.platform_settings.store.get_setting",
                return_value={"enabled": True, "value": {"min_amount": 500}},
            ):
                self.assertEqual(sm._switch(), (True, 500.0))

    def test_config_error_defaults_on(self):
        with mock.patch.dict("os.environ", {"SHADOW_MONEY_CHECK": ""}):
            with mock.patch(
                "services.platform_settings.store.get_setting", side_effect=RuntimeError("db down")
            ):
                on, _ = sm._switch()
                self.assertTrue(on)  # 采样闸故障不静默关掉


_GRP = [{"invoice_fields": {"total_amount": "1780", "vat": "116"}}]


class ScheduleGateTests(unittest.TestCase):
    def _call(self, **over):
        kw = dict(
            content=b"img",
            filename="r.jpg",
            invoice_groups=_GRP,
            confidence="high",
            history_id="h1",
            tenant_id="t1",
            user_id="u1",
        )
        kw.update(over)
        with mock.patch.object(sm, "_run") as run:
            with mock.patch.object(sm, "_switch", return_value=(True, 0.0)):
                sm.schedule(**kw)
        return run

    def test_single_image_dispatches(self):
        self.assertTrue(self._call().called)

    def test_multi_invoice_skips(self):
        self.assertFalse(self._call(invoice_groups=_GRP * 2).called)

    def test_pdf_skips(self):
        self.assertFalse(self._call(filename="doc.pdf").called)

    def test_no_tenant_skips(self):
        self.assertFalse(self._call(tenant_id=None).called)

    def test_switch_off_skips(self):
        with mock.patch.object(sm, "_run") as run:
            with mock.patch.object(sm, "_switch", return_value=(False, 0.0)):
                sm.schedule(
                    content=b"x",
                    filename="r.jpg",
                    invoice_groups=_GRP,
                    confidence="high",
                    history_id="h1",
                    tenant_id="t1",
                    user_id="u1",
                )
            self.assertFalse(run.called)

    def test_below_min_amount_skips(self):
        with mock.patch.object(sm, "_run") as run:
            with mock.patch.object(sm, "_switch", return_value=(True, 5000.0)):
                sm.schedule(
                    content=b"x",
                    filename="r.jpg",
                    invoice_groups=_GRP,
                    confidence="high",
                    history_id="h1",
                    tenant_id="t1",
                    user_id="u1",
                )
            self.assertFalse(run.called)  # 1780 < 5000


class RunBranchTests(unittest.TestCase):
    def test_ok_path_logs_match(self):
        s_ret = {"total_amount": "1780", "vat": "116"}
        with mock.patch.object(sm, "_call_strong", return_value=s_ret):
            with mock.patch("services.ocr.shadow_money_store.insert") as ins:
                sm._run(
                    b"img",
                    "image/jpeg",
                    {"total_amount": "1780", "vat": "116"},
                    "high",
                    "h1",
                    "t1",
                    "u1",
                )
        kw = ins.call_args.kwargs
        self.assertEqual(kw["status"], "ok")
        self.assertTrue(kw["match_all"])

    def test_shadow_failure_logs_failed_not_raise(self):
        with mock.patch.object(sm, "_call_strong", side_effect=TimeoutError("boom")):
            with mock.patch("services.ocr.shadow_money_store.insert") as ins:
                sm._run(b"img", "image/jpeg", {"total_amount": "1780"}, "high", "h1", "t1", "u1")
        kw = ins.call_args.kwargs
        self.assertEqual(kw["status"], "failed")
        self.assertIsNone(kw["match_all"])

    def test_mismatch_logs_false(self):
        with mock.patch.object(sm, "_call_strong", return_value={"total_amount": "84"}):
            with mock.patch("services.ocr.shadow_money_store.insert") as ins:
                sm._run(
                    b"img", "image/jpeg", {"total_amount": "416"}, "needs_review", "h1", "t1", "u1"
                )
        kw = ins.call_args.kwargs
        self.assertEqual(kw["status"], "ok")
        self.assertFalse(kw["match_all"])
        self.assertFalse(kw["matches"]["total"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
