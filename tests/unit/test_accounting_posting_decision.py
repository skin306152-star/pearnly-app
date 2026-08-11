# -*- coding: utf-8 -*-
"""过账分流 + 科目解析 + 借贷平断言单测(posting/settings/vouchers 纯函数层)
+ 会计期间的曼谷日切边界(sources 的 voucher_date 兜底 / 红冲的当前期间)。"""

import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from core.pos_api import PosError
from services.accounting import posting, sources
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


class _FrozenDatetime:
    """UTC 6-30 17:30 = 曼谷 7-01 00:30:两边不同日、且不同月,正是会计期间会错位的那一刻。"""

    @staticmethod
    def now(tz=None):
        return datetime(2026, 6, 30, 17, 30, tzinfo=timezone.utc).astimezone(tz)


class BangkokPeriodBoundaryTests(unittest.TestCase):
    """服务器跑 UTC,曼谷 00:00–07:00 期间 UTC 还停在昨天;月初那几小时按 UTC 算的
    period(%Y-%m)会把凭证整张落进上一个会计期间。"""

    def test_the_frozen_instant_really_straddles_the_month(self):
        instant = _FrozenDatetime.now(timezone.utc)
        self.assertEqual(instant.date(), date(2026, 6, 30))
        self.assertEqual((instant + timedelta(hours=7)).date(), date(2026, 7, 1))

    def test_source_fallback_voucher_date_uses_bangkok_month(self):
        with mock.patch("services.sales.dates.datetime", _FrozenDatetime):
            today = sources._today()
        self.assertEqual(today, date(2026, 7, 1))
        self.assertEqual(today.strftime("%Y-%m"), "2026-07")

    def _voucher(self):
        return {
            "id": "v-1",
            "status": "posted",
            "source_type": "purchase",
            "source_id": "p-1",
            "source_ref": "INV-001",
            "voucher_no": "JV-001",
            "lines": [
                {"account_id": "a-inv", "dr_cr": "debit", "amount": Decimal("100"), "memo": None},
                {"account_id": "a-ap", "dr_cr": "credit", "amount": Decimal("100"), "memo": None},
            ],
        }

    def _reverse(self, closed_through):
        """红冲一张凭证,返回落库的 header(is_period_closed 用真实实现,只冻结时钟)。"""
        captured = {}

        def _insert(cur, *, tenant_id, workspace_client_id, header, lines):
            captured.update(header)
            return header

        with (
            mock.patch.object(posting.jv, "get_voucher", return_value=self._voucher()),
            mock.patch.object(
                posting.acct_settings,
                "get_settings",
                return_value=_settings(closed_through=closed_through),
            ),
            mock.patch.object(posting.jv, "insert_voucher", side_effect=_insert),
            mock.patch("services.sales.dates.datetime", _FrozenDatetime),
        ):
            posting.reverse_voucher(None, tenant_id="t-1", workspace_client_id=1, voucher_id="v-1")
        return captured

    def test_reversal_lands_in_the_bangkok_period(self):
        # 6 月已结:按 UTC 日算当期 = 2026-06 会被 no_open_period 拦死;曼谷已是 7 月,红冲照走。
        header = self._reverse("2026-06")
        self.assertEqual(header["voucher_date"], date(2026, 7, 1))

    def test_reversal_blocked_when_the_bangkok_period_is_closed(self):
        # 反向自证:结到 7 月才拦得住,说明闸读的是曼谷月不是 UTC 月。
        with self.assertRaises(PosError) as ctx:
            self._reverse("2026-07")
        self.assertEqual(ctx.exception.code, "acct.no_open_period")


if __name__ == "__main__":
    unittest.main()
