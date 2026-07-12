# -*- coding: utf-8 -*-
"""义务接线:工资进料 employees_paid 信号 → pnd1 点亮(纯引擎,零 DB)。

验 has_employees data_key 已从 None 改指 employees_paid(pnd1 从数据亮);画像 no 却有进料
→ conflict(防 stale 画像漏报);light_pnd1_obligation 透传 employees_paid=True + wo=None。
"""

import unittest

from services.payroll import obligations
from services.workorder import obligation_engine as oe


def _defs():
    common = {
        "due_paper_day": 7,
        "due_efiling_day": 15,
        "sso_epayment_extra_workdays": 0,
        "effective_from": "2024-02-01",
        "effective_to": None,
    }
    return {
        "pnd1": {"obligation_code": "pnd1", "trigger_kind": "has_employees", **common},
        "sso": {"obligation_code": "sso", "trigger_kind": "has_employees", **common},
    }


def _pnd1(profile, signals):
    obs = oe.generate_obligations(
        profile=profile, period="2569-05", data_signals=signals, defs=_defs()
    )
    return next(o for o in obs if o["obligation_code"] == "pnd1")


class ObligationWiringTests(unittest.TestCase):
    def test_employees_paid_registered_signal_key(self):
        self.assertIn("employees_paid", oe._DATA_SIGNAL_KEYS)
        self.assertIn("employees_paid", oe._empty_data_signals())

    def test_payroll_lights_pnd1_data_triggered(self):
        row = _pnd1(
            {"has_employees": "unknown"}, {"employees_paid": True, "has_any_material": True}
        )
        self.assertEqual(row["status"], oe.STATUS_DATA_TRIGGERED)

    def test_profile_no_but_paid_is_conflict(self):
        row = _pnd1({"has_employees": "no"}, {"employees_paid": True})
        self.assertEqual(row["status"], oe.STATUS_CONFLICT)

    def test_profile_yes_is_due(self):
        row = _pnd1({"has_employees": "yes"}, None)
        self.assertEqual(row["status"], oe.STATUS_DUE)

    def test_unknown_without_signal_is_tentative(self):
        row = _pnd1({"has_employees": "unknown"}, None)
        self.assertEqual(row["status"], oe.STATUS_TENTATIVE)

    def test_sso_also_lit_by_employees_paid(self):
        # SSO 同 has_employees 触发,进料一并点亮(诚实提醒,不代表我们做社保申报)。
        obs = oe.generate_obligations(
            profile={"has_employees": "unknown"},
            period="2569-05",
            data_signals={"employees_paid": True},
            defs=_defs(),
        )
        sso = next(o for o in obs if o["obligation_code"] == "sso")
        self.assertEqual(sso["status"], oe.STATUS_DATA_TRIGGERED)


class LightPnd1WiringTests(unittest.TestCase):
    """light_pnd1_obligation 只做「取画像 → 喂 employees_paid 真信号重物化」,验透传契约。"""

    def test_passes_employees_paid_and_no_work_order(self):
        captured = {}

        def fake_get_profile(cur, *, tenant_id, workspace_client_id):
            return {"has_employees": "unknown"}

        def fake_rematerialize(cur, **kwargs):
            captured.update(kwargs)
            return True

        orig_get = obligations.tax_profile_store.get_profile
        orig_rem = obligations.obligation_engine.rematerialize_for_profile
        obligations.tax_profile_store.get_profile = fake_get_profile
        obligations.obligation_engine.rematerialize_for_profile = fake_rematerialize
        try:
            ok = obligations.light_pnd1_obligation(
                None, tenant_id="t", workspace_client_id=1, period="2569-05"
            )
        finally:
            obligations.tax_profile_store.get_profile = orig_get
            obligations.obligation_engine.rematerialize_for_profile = orig_rem

        self.assertTrue(ok)
        self.assertEqual(
            captured["data_signals"], {"employees_paid": True, "has_any_material": True}
        )
        self.assertIsNone(captured["work_order_id"])

    def test_missing_client_not_lit(self):
        orig_get = obligations.tax_profile_store.get_profile
        obligations.tax_profile_store.get_profile = lambda cur, **k: None
        try:
            self.assertFalse(
                obligations.light_pnd1_obligation(
                    None, tenant_id="t", workspace_client_id=9, period="2569-05"
                )
            )
        finally:
            obligations.tax_profile_store.get_profile = orig_get


if __name__ == "__main__":
    unittest.main()
