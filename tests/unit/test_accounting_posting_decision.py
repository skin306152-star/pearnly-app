# -*- coding: utf-8 -*-
"""过账分流 + 科目解析 + 借贷平断言单测(posting/settings/vouchers 纯函数层)。"""

import unittest
from decimal import Decimal

from core.pos_api import PosError
from services.accounting import posting
from services.accounting import settings as acct_settings
from services.accounting import vouchers as jv


def _settings(**over):
    s = dict(acct_settings.DEFAULTS)
    s.update(over)
    return s


class DecideStatusTests(unittest.TestCase):
    def test_default_suggest_mode_never_auto_posts(self):
        # 安全带③:新租户 auto_post=False → 引擎照算但全部建议待审
        status, method, reason = posting.decide_status(_settings(), "R1", Decimal("100"), [])
        self.assertEqual((status, method, reason), ("pending_review", "suggested", "suggest_mode"))

    def test_auto_post_on_high_confidence(self):
        status, method, reason = posting.decide_status(
            _settings(auto_post=True), "R1", Decimal("100"), []
        )
        self.assertEqual((status, method, reason), ("auto_posted", "auto", None))

    def test_below_threshold_stays_pending(self):
        status, method, reason = posting.decide_status(
            _settings(auto_post=True), "R2", Decimal("60"), ["item_type_guess"]
        )
        self.assertEqual((status, method), ("pending_review", "suggested"))
        self.assertEqual(reason, "item_type_guess")

    def test_rule_granular_override_beats_global(self):
        # 全局关但 R1 粒度开 → R1 自动;R4 无覆盖 → 跟全局建议模式
        s = _settings(auto_post=False, auto_post_rules={"R1": True})
        self.assertEqual(posting.decide_status(s, "R1", Decimal("100"), [])[0], "auto_posted")
        self.assertEqual(posting.decide_status(s, "R4", Decimal("100"), [])[0], "pending_review")
        # 反向:全局开但 R8 粒度关
        s2 = _settings(auto_post=True, auto_post_rules={"R8": False})
        self.assertEqual(posting.decide_status(s2, "R8", Decimal("100"), [])[0], "pending_review")


class ResolveEntriesTests(unittest.TestCase):
    _MAPPINGS = {
        "inventory": "a-inv",
        "input_vat": "a-vat",
        "ap": "a-ap",
        "expense_default": "a-exp",
    }

    def _entry(self, role, dr_cr="debit", amount="100"):
        return {
            "role": role,
            "account_id": None,
            "dr_cr": dr_cr,
            "amount": Decimal(amount),
            "memo": None,
        }

    def test_roles_resolve_to_accounts(self):
        resolved, missing, extra = posting._resolve_entries(
            [self._entry("inventory"), self._entry("ap", "credit")], self._MAPPINGS
        )
        self.assertEqual(missing, [])
        self.assertEqual(extra, [])
        self.assertEqual(resolved[0]["account_id"], "a-inv")

    def test_category_role_falls_back_with_uncertainty(self):
        resolved, missing, extra = posting._resolve_entries(
            [self._entry("expense:cat1")], self._MAPPINGS
        )
        self.assertEqual(missing, [])
        self.assertEqual(extra, ["category_unmapped"])
        self.assertEqual(resolved[0]["account_id"], "a-exp")

    def test_core_role_missing_reported(self):
        resolved, missing, extra = posting._resolve_entries(
            [self._entry("wht_payable", "credit")], self._MAPPINGS
        )
        self.assertEqual(missing, ["wht_payable"])
        self.assertEqual(resolved, [])

    def test_direct_account_passthrough(self):
        e = self._entry("x")
        e["role"], e["account_id"] = None, "a-learned"
        resolved, missing, _ = posting._resolve_entries([e], {})
        self.assertEqual(missing, [])
        self.assertEqual(resolved[0]["account_id"], "a-learned")


class BalanceAssertTests(unittest.TestCase):
    def test_balanced_passes(self):
        debit, credit = jv.assert_balanced(
            [
                {"dr_cr": "debit", "amount": Decimal("107")},
                {"dr_cr": "credit", "amount": Decimal("100")},
                {"dr_cr": "credit", "amount": Decimal("7")},
            ]
        )
        self.assertEqual(debit, credit)

    def test_unbalanced_rejected(self):
        with self.assertRaises(PosError) as ctx:
            jv.assert_balanced(
                [
                    {"dr_cr": "debit", "amount": Decimal("100")},
                    {"dr_cr": "credit", "amount": Decimal("99")},
                ]
            )
        self.assertEqual(ctx.exception.code, "acct.unbalanced")

    def test_zero_and_negative_rejected(self):
        with self.assertRaises(PosError):
            jv.assert_balanced([])
        with self.assertRaises(PosError):
            jv.assert_balanced(
                [
                    {"dr_cr": "debit", "amount": Decimal("-5")},
                    {"dr_cr": "credit", "amount": Decimal("-5")},
                ]
            )


class SettingsHelpersTests(unittest.TestCase):
    def test_period_lock(self):
        self.assertFalse(acct_settings.is_period_closed(_settings(), "2026-06"))
        s = _settings(closed_through="2026-05")
        self.assertTrue(acct_settings.is_period_closed(s, "2026-05"))
        self.assertTrue(acct_settings.is_period_closed(s, "2026-04"))
        self.assertFalse(acct_settings.is_period_closed(s, "2026-06"))

    def test_defaults_are_suggest_mode(self):
        self.assertFalse(acct_settings.DEFAULTS["auto_post"])
        self.assertEqual(acct_settings.DEFAULTS["auto_post_threshold"], 90)


if __name__ == "__main__":
    unittest.main()
