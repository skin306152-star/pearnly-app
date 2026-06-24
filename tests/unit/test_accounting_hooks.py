# -*- coding: utf-8 -*-
"""挂点防爆闸(docs/accounting/05 §5):做账失败绝不拖垮业务主路径。

1. enqueue_posting 内部异常 → SAVEPOINT 回滚 + 静默吞,调用方不见任何异常。
2. 模块未开 → 早退(不跑引擎)。
3. 四个业务挂点(进项 post/付款 · 销项 issue/红冲 · POS 零售/餐厅)源码确实只调 hooks
   一行(不直连引擎)。
4. 付款事件 id 确定性(重放同 id 幂等,分次付款各自成凭证)。"""

import pathlib
import unittest
from unittest import mock

from services.accounting import hooks


class FakeCursor:
    def __init__(self, fail_on=None):
        self.executed = []
        self.fail_on = fail_on

    def execute(self, sql, params=None):
        self.executed.append(sql)
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError(f"boom on {self.fail_on}")

    def fetchone(self):
        return {"enabled": True}


class EnqueueSafetyTests(unittest.TestCase):
    def test_engine_exception_swallowed_and_rolled_back(self):
        cur = FakeCursor()
        with mock.patch(
            "services.accounting.posting.generate_for_source",
            side_effect=RuntimeError("engine down"),
        ):
            with mock.patch("services.modules.store.is_enabled", return_value=True):
                with mock.patch("services.accounting.posting_failures.record_failure") as record:
                    hooks.enqueue_posting(
                        cur,
                        tenant_id="t1",
                        workspace_client_id=1,
                        source_type="purchase",
                        source_id="d1",
                    )
        self.assertIn("SAVEPOINT acct_enqueue", cur.executed)
        self.assertIn("ROLLBACK TO SAVEPOINT acct_enqueue", cur.executed)
        record.assert_called_once()

    def test_savepoint_failure_swallowed(self):
        cur = FakeCursor(fail_on="SAVEPOINT")
        hooks.enqueue_posting(
            cur, tenant_id="t1", workspace_client_id=1, source_type="purchase", source_id="d1"
        )

    def test_module_disabled_early_returns_without_engine(self):
        cur = FakeCursor()
        with mock.patch("services.accounting.posting.generate_for_source") as gen:
            with mock.patch("services.modules.store.is_enabled", return_value=False):
                hooks.enqueue_posting(
                    cur,
                    tenant_id="t1",
                    workspace_client_id=1,
                    source_type="pos",
                    source_id="s1",
                )
        gen.assert_not_called()
        self.assertIn("RELEASE SAVEPOINT acct_enqueue", cur.executed)

    def test_missing_workspace_skips_silently(self):
        cur = FakeCursor()
        hooks.enqueue_posting(
            cur, tenant_id="t1", workspace_client_id=None, source_type="sale", source_id="d1"
        )
        self.assertEqual(cur.executed, [])

    def test_success_releases_savepoint(self):
        cur = FakeCursor()
        with mock.patch(
            "services.accounting.posting.generate_for_source", return_value={"id": "v1"}
        ):
            with mock.patch("services.modules.store.is_enabled", return_value=True):
                with mock.patch("services.accounting.posting_failures.mark_resolved") as resolved:
                    hooks.enqueue_posting(
                        cur,
                        tenant_id="t1",
                        workspace_client_id=1,
                        source_type="purchase",
                        source_id="d1",
                    )
        self.assertIn("RELEASE SAVEPOINT acct_enqueue", cur.executed)
        self.assertNotIn("ROLLBACK TO SAVEPOINT acct_enqueue", cur.executed)
        resolved.assert_called_once()


class PaymentEventIdTests(unittest.TestCase):
    def test_deterministic_and_distinct_per_cumulative_paid(self):
        a1 = hooks.payment_event_id("doc-1", "500.00")
        a2 = hooks.payment_event_id("doc-1", "500.00")
        b = hooks.payment_event_id("doc-1", "1000.00")
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, b)


class HookWiringTests(unittest.TestCase):
    """业务模块只许经 hooks 挂做账(一行 enqueue),不许直连引擎。"""

    _HOSTS = (
        "services/purchase/posting.py",
        "services/sales/document.py",
        "services/sales/credit_note.py",
        "services/pos/sale.py",
        "services/pos/restaurant/checkout.py",
    )

    def test_hosts_call_enqueue_not_engine(self):
        for path in self._HOSTS:
            src = pathlib.Path(path).read_text(encoding="utf-8")
            self.assertIn("acct_hooks.enqueue_posting(", src, f"{path} 缺挂点")
            self.assertNotIn("from services.accounting import posting", src, f"{path} 直连引擎")

    def test_purchase_pay_uses_event_id(self):
        src = pathlib.Path("services/purchase/posting.py").read_text(encoding="utf-8")
        self.assertIn("payment_event_id", src)


if __name__ == "__main__":
    unittest.main()
