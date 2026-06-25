# -*- coding: utf-8 -*-
"""B8 RLS wave3 契约:ocr_history + clients DAL 必须穿租户上下文走 get_cursor_rls。

锁定:clients/store + buyer_resolve + ocr_history/queries + mutations 的每个用户态 CRUD
都把 tenant_id + user_id 注入 get_cursor_rls,绝不回退裸 get_cursor(enroll 后裸游标=owner
绕过=不隔离)。check_duplicate_invoice 的 tenant_id 只喂 RLS 上下文(WHERE 仍 user_id 保 per-user)。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.clients import store as clients_store
from services.clients import buyer_resolve
from services.ocr_history import queries, mutations

TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def __init__(self, fetchone=None, fetchall=None, rowcount=1):
        self._one = fetchone
        self._all = fetchall or []
        self.rowcount = rowcount

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


def _capture(fetchone=None, fetchall=None, rowcount=1):
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur(fetchone=fetchone, fetchall=fetchall, rowcount=rowcount)

    return calls, fake


def _no_bare():
    return mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls"))


def _assert_ctx(test, calls):
    test.assertTrue(calls, "未走 get_cursor_rls")
    test.assertEqual(calls[0].get("tenant_id"), TENANT)
    test.assertEqual(calls[0].get("user_id"), USER)
    test.assertNotEqual(calls[0].get("bypass"), True)


class ClientsStoreContext(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, fetchall=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone, fetchall=fetchall)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, **kwargs)
        _assert_ctx(self, calls)

    def test_list_clients(self):
        self._run(clients_store.list_clients, USER, tenant_id=TENANT, fetchall=[])

    def test_get_client(self):
        self._run(clients_store.get_client, USER, 1, tenant_id=TENANT, fetchone=None)

    def test_create_client(self):
        self._run(clients_store.create_client, USER, TENANT, "ACME", fetchone={"id": 5})

    def test_update_client(self):
        self._run(clients_store.update_client, USER, 1, tenant_id=TENANT, name="X")

    def test_delete_client(self):
        self._run(clients_store.delete_client, USER, 1, tenant_id=TENANT)

    def test_assign_invoice_to_client(self):
        self._run(
            clients_store.assign_invoice_to_client,
            USER,
            "h1",
            1,
            tenant_id=TENANT,
            fetchone={"id": 1},
        )

    def test_buyer_resolve_try(self):
        self._run(
            buyer_resolve.try_resolve_buyer_to_client,
            "ACME",
            None,
            USER,
            tenant_id=TENANT,
            fetchone=None,
            fetchall=[],
        )

    def test_update_history_client_id(self):
        self._run(buyer_resolve.update_history_client_id, "h1", 1, USER, tenant_id=TENANT)


class OcrHistoryContext(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, fetchall=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone, fetchall=fetchall)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, **kwargs)
        _assert_ctx(self, calls)

    def test_get_detail(self):
        self._run(queries.get_ocr_history_detail, USER, "h1", tenant_id=TENANT, fetchone=None)

    def test_get_pdf_info(self):
        self._run(queries.get_history_pdf_info, USER, "h1", tenant_id=TENANT, fetchone=None)

    def test_find_by_hash(self):
        self._run(queries.find_ocr_by_hash, USER, "abc", tenant_id=TENANT, fetchone=None)

    def test_update_pages(self):
        self._run(mutations.update_ocr_history_pages, USER, "h1", [], tenant_id=TENANT)

    def test_delete(self):
        self._run(mutations.delete_ocr_history, USER, "h1", tenant_id=TENANT)

    def test_delete_with_pdf_paths(self):
        self._run(
            mutations.delete_ocr_history_with_pdf_paths,
            USER,
            ["h1"],
            tenant_id=TENANT,
            fetchall=[],
        )

    def test_pdf_storage(self):
        self._run(mutations.update_ocr_history_pdf_storage, ["h1"], "p", 1, USER, tenant_id=TENANT)

    def test_check_duplicate_threads_tenant_for_rls(self):
        # tenant_id 喂 RLS 上下文(WHERE 仍 user_id)。
        calls, fake = _capture(fetchone=None)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            queries.check_duplicate_invoice(USER, "INV1", None, None, None, tenant_id=TENANT)
        _assert_ctx(self, calls)


if __name__ == "__main__":
    unittest.main()
