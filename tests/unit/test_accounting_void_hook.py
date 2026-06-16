# -*- coding: utf-8 -*-
"""acct_hooks 作废/红冲 seam 单测(docs/purchasing/03+04)。

void_for_source:源单 → 找凭证 → 派给 void_or_reverse(模块未开/无凭证 no-op)。
void_or_reverse:开放期 → void_voucher;已结/已申报期 → reverse_voucher(红冲)。不吞错。
"""

import unittest
from unittest import mock

from services.accounting import hooks as acct_hooks


class _Cur:
    def execute(self, *a, **k):
        return None


def _call_source():
    acct_hooks.void_for_source(
        _Cur(),
        tenant_id="t",
        workspace_client_id=1,
        source_type="purchase",
        source_id="D",
        created_by="u",
    )


class VoidForSourceTests(unittest.TestCase):
    def test_module_disabled_noop(self):
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=False),
            mock.patch.object(acct_hooks, "void_or_reverse") as vor,
        ):
            _call_source()
        vor.assert_not_called()

    def test_no_active_voucher_noop(self):
        from services.accounting import vouchers as jv
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=True),
            mock.patch.object(jv, "find_active_by_source", return_value=None),
            mock.patch.object(acct_hooks, "void_or_reverse") as vor,
        ):
            _call_source()
        vor.assert_not_called()

    def test_active_voucher_dispatched(self):
        from services.accounting import vouchers as jv
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=True),
            mock.patch.object(jv, "find_active_by_source", return_value={"id": "v1"}),
            mock.patch.object(acct_hooks, "void_or_reverse") as vor,
        ):
            _call_source()
        vor.assert_called_once()
        self.assertEqual(vor.call_args.kwargs["voucher_id"], "v1")


class VoidOrReverseTests(unittest.TestCase):
    def _run(self, *, status="auto_posted", closed=False):
        from services.accounting import posting
        from services.accounting import settings as acct_settings
        from services.accounting import vouchers as jv

        calls = []
        with (
            mock.patch.object(
                jv,
                "get_voucher",
                return_value={"id": "v1", "status": status, "period": "2026-02"},
            ),
            mock.patch.object(acct_settings, "get_settings", return_value={}),
            mock.patch.object(acct_settings, "is_period_closed", return_value=closed),
            mock.patch.object(
                posting, "void_voucher", side_effect=lambda *a, **k: calls.append("void")
            ),
            mock.patch.object(
                posting, "reverse_voucher", side_effect=lambda *a, **k: calls.append("reverse")
            ),
        ):
            acct_hooks.void_or_reverse(
                _Cur(), tenant_id="t", workspace_client_id=1, voucher_id="v1", created_by="u"
            )
        return calls

    def test_open_period_voids(self):
        self.assertEqual(self._run(closed=False), ["void"])

    def test_closed_period_reverses(self):
        self.assertEqual(self._run(closed=True), ["reverse"])

    def test_already_void_noop(self):
        self.assertEqual(self._run(status="void"), [])


if __name__ == "__main__":
    unittest.main()
