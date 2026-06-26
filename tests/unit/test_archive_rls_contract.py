# -*- coding: utf-8 -*-
"""B8 RLS wave3 3c 契约:archive_settings DAL 穿 user 上下文走 get_cursor_rls。

archive_settings 是 per-user 命名偏好(键 user_id)→ apply_user_rls 纯 user 隔离。
get_archive_settings / upsert_archive_settings 必须注入 user_id,绝不回退裸 get_cursor。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.archive import store

USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def __init__(self, fetchone=None, rowcount=1):
        self._one = fetchone
        self.rowcount = rowcount

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._one


def _capture(fetchone=None):
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur(fetchone=fetchone)

    return calls, fake


def _no_bare():
    return mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls"))


class ArchiveSettingsContext(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None):
        calls, fake = _capture(fetchone=fetchone)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args)
        self.assertTrue(calls, "未走 get_cursor_rls")
        self.assertEqual(calls[0].get("user_id"), USER)
        self.assertNotEqual(calls[0].get("bypass"), True)

    def test_get(self):
        self._run(store.get_archive_settings, USER, fetchone=None)

    def test_upsert(self):
        self._run(store.upsert_archive_settings, USER, [{"f": "date"}], "by_month")


if __name__ == "__main__":
    unittest.main()
