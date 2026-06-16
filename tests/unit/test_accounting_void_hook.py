# -*- coding: utf-8 -*-
"""acct_hooks.void_for_source 单测(docs/purchasing/03):源单作废 → 作废做账凭证。

验:模块未开通 / 无凭证 → no-op;有凭证 → 走 void_voucher;period_closed 透传不吞
(与 enqueue_posting 的吞错反差——作废失败必须让整事务回滚,不留半作废)。
"""

import unittest
from unittest import mock

from core.pos_api import PosError
from services.accounting import hooks as acct_hooks


class _Cur:
    def execute(self, *a, **k):
        return None


def _call():
    acct_hooks.void_for_source(
        _Cur(), tenant_id="t", workspace_client_id=1, source_type="purchase", source_id="D"
    )


class VoidForSourceTests(unittest.TestCase):
    def test_module_disabled_noop(self):
        from services.accounting import posting
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=False),
            mock.patch.object(posting, "void_voucher") as vv,
        ):
            _call()
        vv.assert_not_called()

    def test_no_active_voucher_noop(self):
        from services.accounting import posting
        from services.accounting import vouchers as jv
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=True),
            mock.patch.object(jv, "find_active_by_source", return_value=None),
            mock.patch.object(posting, "void_voucher") as vv,
        ):
            _call()
        vv.assert_not_called()

    def test_active_voucher_voided(self):
        from services.accounting import posting
        from services.accounting import vouchers as jv
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=True),
            mock.patch.object(jv, "find_active_by_source", return_value={"id": "v1"}),
            mock.patch.object(
                posting, "void_voucher", return_value={"id": "v1", "status": "void"}
            ) as vv,
        ):
            _call()
        vv.assert_called_once()
        self.assertEqual(vv.call_args.kwargs["voucher_id"], "v1")

    def test_period_closed_propagates(self):
        from services.accounting import posting
        from services.accounting import vouchers as jv
        from services.modules import store as modules_store

        with (
            mock.patch.object(modules_store, "is_enabled", return_value=True),
            mock.patch.object(jv, "find_active_by_source", return_value={"id": "v1"}),
            mock.patch.object(
                posting, "void_voucher", side_effect=PosError("acct.period_closed", 409)
            ),
            self.assertRaises(PosError) as e,
        ):
            _call()
        self.assertEqual(e.exception.code, "acct.period_closed")


if __name__ == "__main__":
    unittest.main()
