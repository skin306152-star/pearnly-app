# -*- coding: utf-8 -*-
"""B8 RLS 契约:vat_recon_store + field_override 只收主键的函数必须穿租户上下文(hard point 2)。

锁定:reconciliation_task / reconciliation_row / vat_report 的每个 CRUD 都把 tenant_id + user_id
注入 get_cursor_rls,绝不回退裸 get_cursor。reconciliation_row 经 task_id 传递式隔离(hard point 1),
其读写在 RLS 下靠上下文匹配父 task 的租户 —— 缺上下文则查空 / WITH CHECK 拒(money 陷阱)。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.recon import vat_recon_store as vrs
from services.recon import field_override as fo

TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def __init__(self, fetchone=None):
        self._fetchone = fetchone if fetchone is not None else {"id": 1}
        self.rowcount = 1

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return []


def _capture(fetchone=None):
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur(fetchone=fetchone)

    return calls, fake


def _no_bare():
    return mock.patch(
        "core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")
    )


def _assert_ctx(test, calls):
    test.assertTrue(calls, "未走 get_cursor_rls")
    test.assertEqual(calls[0].get("tenant_id"), TENANT)
    test.assertEqual(calls[0].get("user_id"), USER)
    test.assertNotEqual(calls[0].get("bypass"), True)


class VatReconStoreContext(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, tenant_id=TENANT, user_id=USER, **kwargs)
        _assert_ctx(self, calls)

    def test_get_recon_task(self):
        self._run(vrs.get_recon_task, 1)

    def test_update_recon_task_status(self):
        self._run(vrs.update_recon_task_status, 1, "running")

    def test_update_recon_task_completed(self):
        self._run(vrs.update_recon_task_completed, 1, {"status": "completed"})

    def test_get_recon_row(self):
        self._run(vrs.get_recon_row, 1, fetchone={"id": 1, "report_rows": None})

    def test_update_recon_row_action(self):
        self._run(vrs.update_recon_row_action, 1, "resolved")

    def test_update_recon_row_ai_analysis(self):
        self._run(vrs.update_recon_row_ai_analysis, 1, {"v": 1})

    def test_list_recon_rows_detailed(self):
        self._run(vrs.list_recon_rows_detailed, 1, fetchone={"vat_report_id": None})

    def test_list_recon_rows(self):
        self._run(vrs.list_recon_rows, 1)

    def test_get_vat_report(self):
        self._run(vrs.get_vat_report, 1, fetchone={"id": 1, "parsed_rows": []})

    def test_bulk_insert_recon_rows(self):
        self._run(vrs.bulk_insert_recon_rows, [{"task_id": 1, "status": "matched"}])

    def test_create_vat_report_positional_user(self):
        # create_vat_report(tenant_id, user_id, ...) 位置传 user_id
        calls, fake = _capture(fetchone={"id": 9})
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            vrs.create_vat_report(TENANT, USER, 1, 2026, 5, [], {})
        _assert_ctx(self, calls)

    def test_create_recon_task_positional(self):
        calls, fake = _capture(fetchone={"id": 3})
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            vrs.create_recon_task(TENANT, USER, 1, 2026, 5, 9)
        _assert_ctx(self, calls)


class FieldOverrideContext(unittest.TestCase):
    def test_record_field_override_threads_context(self):
        # get_recon_row 经传递式隔离;_write_overrides 写 reconciliation_row 也必须带上下文。
        calls, fake = _capture()
        row = {"buyer_name": "ABC", "field_overrides": {}}
        with (
            mock.patch("core.db.get_recon_row", return_value=row) as grr,
            mock.patch("core.db.get_cursor_rls", fake),
            _no_bare(),
        ):
            fo.record_field_override(1, "buyer_name", "ABC Co", tenant_id=TENANT, user_id=USER)
        # get_recon_row 收到上下文
        self.assertEqual(grr.call_args.kwargs.get("tenant_id"), TENANT)
        self.assertEqual(grr.call_args.kwargs.get("user_id"), USER)
        # _write_overrides 的 get_cursor_rls 收到上下文
        _assert_ctx(self, calls)


if __name__ == "__main__":
    unittest.main()
