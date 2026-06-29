# -*- coding: utf-8 -*-
"""官方名核验 ③ · 后台回填逻辑(mock RD + DB·无外部/无 DB)。"""

import unittest
from unittest import mock

from services.rd import official_name


class ValidTaxTests(unittest.TestCase):
    def test_13_digits_ok(self):
        self.assertEqual(official_name._valid_tax("0105556000001"), "0105556000001")

    def test_strips_separators(self):
        self.assertEqual(official_name._valid_tax("0-1055-56000-00-1"), "0105556000001")

    def test_wrong_length_empty(self):
        self.assertEqual(official_name._valid_tax("123"), "")
        self.assertEqual(official_name._valid_tax(None), "")


class EnrichRecordsTests(unittest.IsolatedAsyncioTestCase):
    def _rd(self, name="บริษัท ก จำกัด"):
        return {"ok": True, "data": {"name": name}}

    async def test_stores_official_name(self):
        with (
            mock.patch("services.rd.rd_api.lookup_vat", return_value=self._rd()) as lv,
            mock.patch(
                "services.rd.official_name.db.update_history_official_name", return_value=True
            ) as upd,
        ):
            n = await official_name.enrich_records([("h1", "0105556000001")], "u1", "t1")
        self.assertEqual(n, 1)
        lv.assert_called_once_with("0105556000001")
        self.assertEqual(upd.call_args[0][1], "บริษัท ก จำกัด")

    async def test_invalid_tax_skipped(self):
        with mock.patch("services.rd.rd_api.lookup_vat") as lv:
            n = await official_name.enrich_records([("h1", "123")], "u1", "t1")
        self.assertEqual(n, 0)
        lv.assert_not_called()

    async def test_same_tax_looked_up_once(self):
        with (
            mock.patch("services.rd.rd_api.lookup_vat", return_value=self._rd()) as lv,
            mock.patch(
                "services.rd.official_name.db.update_history_official_name", return_value=True
            ),
        ):
            n = await official_name.enrich_records(
                [("h1", "0105556000001"), ("h2", "0105556000001")], "u1", "t1"
            )
        self.assertEqual(n, 2)
        self.assertEqual(lv.call_count, 1)  # 同税号只打一次外部

    async def test_not_found_no_store(self):
        with (
            mock.patch(
                "services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "not_found"}
            ),
            mock.patch("services.rd.official_name.db.update_history_official_name") as upd,
        ):
            n = await official_name.enrich_records([("h1", "0105556000001")], "u1", "t1")
        self.assertEqual(n, 0)
        upd.assert_not_called()

    async def test_lookup_exception_non_fatal(self):
        with mock.patch("services.rd.rd_api.lookup_vat", side_effect=RuntimeError("rd down")):
            n = await official_name.enrich_records([("h1", "0105556000001")], "u1", "t1")
        self.assertEqual(n, 0)


class ScheduleTests(unittest.TestCase):
    def test_no_running_loop_skips_quietly(self):
        # 同步上下文无 event loop → 不抛
        official_name.schedule([("h1", "0105556000001")], "u1", "t1")

    def test_empty_pairs_noop(self):
        official_name.schedule([], "u1", "t1")


class UpdateOfficialNameContractTests(unittest.TestCase):
    """update_history_official_name 窄更新契约(mock cursor)。"""

    class _Cur:
        def __init__(self):
            self.rowcount = 1
            self.sql = ""

        def execute(self, sql, params=None):
            self.sql = sql

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _patch(self, cur):
        from contextlib import contextmanager

        @contextmanager
        def _fake(**kw):
            yield cur

        from services.ocr_history import mutations

        return mock.patch.object(mutations.db, "get_cursor_rls", lambda **kw: _fake(**kw))

    def test_writes_official_and_verified(self):
        from services.ocr_history import mutations

        cur = self._Cur()
        with self._patch(cur):
            ok = mutations.update_history_official_name("h1", "บริษัท ก", "u1", "t1")
        self.assertTrue(ok)
        self.assertIn("seller_name_verified = TRUE", cur.sql)
        self.assertIn("seller_name_official", cur.sql)

    def test_empty_name_no_write(self):
        from services.ocr_history import mutations

        cur = self._Cur()
        with self._patch(cur):
            self.assertFalse(mutations.update_history_official_name("h1", "  ", "u1", "t1"))
        self.assertEqual(cur.sql, "")  # 空名不写


if __name__ == "__main__":
    unittest.main()
