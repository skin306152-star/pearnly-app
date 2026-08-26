# -*- coding: utf-8 -*-
"""登录入口准入(各是各的)判据契约:授权入口集推导 + 拒登/放行规则。"""

from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from services.auth import entrance  # noqa: E402


def _cursor_ctx():
    @contextmanager
    def _gc(commit=False):
        yield object()

    return _gc


class AuthorizedEntrancesTests(unittest.TestCase):
    def _derive(self, *, business_type, pos_on, ai_on, dms_on=False, daily_on=False, erp_on=False):
        with (
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch("services.modules.store.get_business_type", return_value=business_type),
            mock.patch("services.modules.store.is_enabled", return_value=pos_on),
            mock.patch("core.feature_flags.pearnly_ai_m1_enabled_for", return_value=ai_on),
            mock.patch("core.feature_flags.dms_portal_enabled_for", return_value=dms_on),
            mock.patch("core.feature_flags.daily_enabled_for", return_value=daily_on),
            mock.patch("core.feature_flags.erp_portal_enabled_for", return_value=erp_on),
        ):
            return entrance.authorized_entrances("t1", "u1")

    def test_firm_account_gets_main_and_cowork(self) -> None:
        # 普通非 pos_only 用户:main + cowork(协同工作台随 main 同源)
        self.assertEqual(
            self._derive(business_type="firm", pos_on=False, ai_on=False), {"main", "cowork"}
        )

    def test_pos_only_tenant_excluded_from_main(self) -> None:
        ents = self._derive(business_type="pos_only", pos_on=True, ai_on=False)
        self.assertEqual(ents, {"pos"})
        self.assertNotIn("main", ents)
        self.assertNotIn("cowork", ents)

    def test_dms_portal_invitee_gets_dms(self) -> None:
        ents = self._derive(business_type="firm", pos_on=False, ai_on=False, dms_on=True)
        self.assertIn("dms", ents)
        self.assertEqual(ents, {"main", "cowork", "dms"})

    def test_daily_finance_invitee_gets_daily(self) -> None:
        # daily_finance 白名单(daily 门)独立授予,不影响 main/cowork;默认未 mock 时为 False
        ents = self._derive(business_type="firm", pos_on=False, ai_on=False, daily_on=True)
        self.assertIn("daily", ents)
        self.assertEqual(ents, {"main", "cowork", "daily"})

    def test_no_daily_without_invite(self) -> None:
        ents = self._derive(business_type="firm", pos_on=False, ai_on=False)
        self.assertNotIn("daily", ents)

    def test_erp_portal_invitee_gets_erp(self) -> None:
        ents = self._derive(business_type="firm", pos_on=False, ai_on=False, erp_on=True)
        self.assertIn("erp", ents)
        self.assertEqual(ents, {"main", "cowork", "erp"})

    def test_no_erp_without_invite(self) -> None:
        ents = self._derive(business_type="firm", pos_on=False, ai_on=False, erp_on=False)
        self.assertNotIn("erp", ents)

    def test_multi_line_account_holds_all(self) -> None:
        self.assertEqual(
            self._derive(business_type="firm", pos_on=True, ai_on=True, dms_on=True, erp_on=True),
            {"main", "cowork", "pos", "ai", "dms", "erp"},
        )

    def test_no_tenant_gets_main_and_cowork(self) -> None:
        # 无租户兜底与推导口径严格等价(非 pos_only 天然 main+cowork)
        self.assertEqual(entrance.authorized_entrances(None, "u1"), {"main", "cowork"})


class LoginEntranceAllowedTests(unittest.TestCase):
    def _real_login(
        self,
        entry,
        *,
        gate=True,
        business_type="firm",
        pos_on=False,
        ai_on=False,
        dms_on=False,
        daily_on=False,
        erp_on=False,
    ):
        """真实跑 authorized_entrances 推导(mock 掉库/商店/FLAG),只让 login_entrance_allowed 判定。"""
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=gate),
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch("services.modules.store.get_business_type", return_value=business_type),
            mock.patch("services.modules.store.is_enabled", return_value=pos_on),
            mock.patch("core.feature_flags.pearnly_ai_m1_enabled_for", return_value=ai_on),
            mock.patch("core.feature_flags.dms_portal_enabled_for", return_value=dms_on),
            mock.patch("core.feature_flags.daily_enabled_for", return_value=daily_on),
            mock.patch("core.feature_flags.erp_portal_enabled_for", return_value=erp_on),
        ):
            return entrance.login_entrance_allowed(entry, {"tenant_id": "t1", "id": "u1"})

    def test_super_admin_allowed_any_door(self) -> None:
        # 超管连推导都不走(entrance_gate 未 mock 也不该被读)
        self.assertTrue(entrance.login_entrance_allowed("ai", {"is_super_admin": True}))

    def test_gate_off_allows_unentitled(self) -> None:
        with mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=False):
            self.assertTrue(entrance.login_entrance_allowed("pos", {"tenant_id": "t1", "id": "u1"}))

    def test_gate_on_denies_unentitled(self) -> None:
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch("services.auth.entrance.authorized_entrances", return_value={"main"}),
        ):
            self.assertFalse(
                entrance.login_entrance_allowed("pos", {"tenant_id": "t1", "id": "u1"})
            )

    def test_gate_on_allows_entitled(self) -> None:
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch("services.auth.entrance.authorized_entrances", return_value={"main", "pos"}),
        ):
            self.assertTrue(entrance.login_entrance_allowed("pos", {"tenant_id": "t1", "id": "u1"}))

    def test_empty_entry_treated_as_main(self) -> None:
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch("services.auth.entrance.authorized_entrances", return_value={"main"}),
        ):
            self.assertTrue(entrance.login_entrance_allowed(None, {"tenant_id": "t1", "id": "u1"}))

    def test_pos_derivation_error_still_fails_open(self) -> None:
        # 既有:非 erp 门推导异常仍 fail-open(登录可用性优先)
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch(
                "services.auth.entrance.authorized_entrances", side_effect=RuntimeError("db down")
            ),
        ):
            self.assertTrue(entrance.login_entrance_allowed("pos", {"tenant_id": "t1", "id": "u1"}))

    def test_real_erp_denied_when_not_invited(self) -> None:
        # 真实推导:erp_portal 未邀请 → 授权集无 erp → erp 门拒登
        self.assertFalse(self._real_login("erp", erp_on=False))

    def test_real_erp_allowed_when_invited(self) -> None:
        self.assertTrue(self._real_login("erp", erp_on=True))

    def test_real_cowork_allowed_for_firm(self) -> None:
        # 非 pos_only 天然 main+cowork → cowork 门放行
        self.assertTrue(self._real_login("cowork", business_type="firm"))

    def test_real_derivation_error_erp_fails_closed(self) -> None:
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch(
                "services.auth.entrance.authorized_entrances", side_effect=RuntimeError("db down")
            ),
        ):
            self.assertFalse(
                entrance.login_entrance_allowed("erp", {"tenant_id": "t1", "id": "u1"})
            )


if __name__ == "__main__":
    unittest.main()
