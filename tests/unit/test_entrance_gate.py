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
    def _derive(self, *, business_type, pos_on, ai_on):
        with (
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch("services.modules.store.get_business_type", return_value=business_type),
            mock.patch("services.modules.store.is_enabled", return_value=pos_on),
            mock.patch("core.feature_flags.pearnly_ai_m1_enabled_for", return_value=ai_on),
        ):
            return entrance.authorized_entrances("t1", "u1")

    def test_firm_account_gets_main_only(self) -> None:
        self.assertEqual(self._derive(business_type="firm", pos_on=False, ai_on=False), {"main"})

    def test_pos_only_tenant_excluded_from_main(self) -> None:
        ents = self._derive(business_type="pos_only", pos_on=True, ai_on=False)
        self.assertEqual(ents, {"pos"})
        self.assertNotIn("main", ents)

    def test_multi_line_account_holds_all(self) -> None:
        self.assertEqual(
            self._derive(business_type="firm", pos_on=True, ai_on=True),
            {"main", "pos", "ai"},
        )

    def test_no_tenant_falls_back_to_main(self) -> None:
        self.assertEqual(entrance.authorized_entrances(None, "u1"), {"main"})


class LoginEntranceAllowedTests(unittest.TestCase):
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

    def test_derivation_error_fails_open(self) -> None:
        with (
            mock.patch("core.feature_flags.entrance_gate_enabled_for", return_value=True),
            mock.patch(
                "services.auth.entrance.authorized_entrances", side_effect=RuntimeError("db down")
            ),
        ):
            self.assertTrue(entrance.login_entrance_allowed("pos", {"tenant_id": "t1", "id": "u1"}))


if __name__ == "__main__":
    unittest.main()
