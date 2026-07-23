# -*- coding: utf-8 -*-
"""重推带上「上一版凭证号」的守门 —— 小助手防重单闸的输入。

会计纠正错票号后回导时,小助手既有的 YOUREF 幂等认不出来。不带这个键,旧单还在
ERP 里就会再建一张,同一张票记两遍账。
"""

import unittest
from unittest import mock

from services.erp.express_push.prior_doc import attach_prior_docnum, prior_docnum


class _Cur:
    def __init__(self, row):
        self._row = row

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._row


class _Ctx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def _with_row(row):
    return mock.patch("core.db.get_cursor", return_value=_Ctx(_Cur(row)))


class PriorDocnumTests(unittest.TestCase):
    def test_reads_docnum_from_response_body(self):
        with _with_row({"response_body": '{"express_docnum": "SA1-0723", "meta": {}}'}):
            self.assertEqual(prior_docnum("h1"), "SA1-0723")

    def test_falls_back_to_meta_docnum(self):
        with _with_row({"response_body": '{"meta": {"docnum": "HP690723-001"}}'}):
            self.assertEqual(prior_docnum("h1"), "HP690723-001")

    def test_no_prior_push_returns_none(self):
        with _with_row(None):
            self.assertIsNone(prior_docnum("h1"))

    def test_blank_history_id_short_circuits(self):
        self.assertIsNone(prior_docnum(""))
        self.assertIsNone(prior_docnum(None))

    def test_db_failure_degrades_to_none_not_raise(self):
        """防重单是加固 · 查库抖一下不该把正常推送整个卡死。"""
        with mock.patch("core.db.get_cursor", side_effect=RuntimeError("boom")):
            self.assertIsNone(prior_docnum("h1"))


class AttachTests(unittest.TestCase):
    def test_key_absent_on_first_push(self):
        """首次推送没有上一版 —— 带个空串会让老版本小助手困惑,干脆不带这个键。"""
        with _with_row(None):
            p = attach_prior_docnum({"ref_no": "X"}, {"id": "h1"})
        self.assertNotIn("prior_docnum", p)

    def test_key_present_on_repush(self):
        with _with_row({"response_body": '{"express_docnum": "SA1-0723"}'}):
            p = attach_prior_docnum({"ref_no": "X"}, {"id": "h1"})
        self.assertEqual(p["prior_docnum"], "SA1-0723")

    def test_missing_history_is_safe(self):
        self.assertNotIn("prior_docnum", attach_prior_docnum({}, {}))
        self.assertNotIn("prior_docnum", attach_prior_docnum({}, None))


if __name__ == "__main__":
    unittest.main()
