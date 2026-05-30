#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocrperf_step1.py · REFACTOR-WA-OCRPERF Step1(PDF 留底后台化)

锁两件本地可验(无需 Gemini key · PDF 生成是本地 pdf_searchable+pdf_storage):
  A. services/ocr/pdf_backfill.generate_and_save_pdf —— 与原同步留底块语义逐字一致:
     有文本→make_searchable_pdf→save 搜索版;生成 None/抛→fallback 原文件;无文本→不调 searchable;
     save_pdf 抛→(None,None) 绝不抛(留底失败不影响识别)。
  B. services/ocr_history/mutations.update_ocr_history_pdf_storage —— tenant/user 锁 SQL +
     参数 + rowcount;空 record_ids/无 path→0;DB 抛→0 绝不抛。

纯逻辑 · mock pdf_searchable/pdf_storage + db.get_cursor。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 先 import db 完整初始化 dal_reexports 链(否则 standalone 跑本文件会触发
# services.ocr_history.mutations partial-init 循环 · 见 STATE dal_reexports 偏序坑;
# 全量 discover 下 db 被更早导入故无此问题)。
import db  # noqa: E402,F401
from services.ocr import pdf_backfill  # noqa: E402
from services.ocr_history import mutations  # noqa: E402

_CONTENT = b"%PDF-1.4 original-bytes"
_PAGES = [{"fields": {"invoice_number": "INV1"}}]


class GenerateAndSavePdfTest(unittest.TestCase):
    def _patches(self, texts, searchable, save_ret=("rel/p.pdf", 123)):
        return (
            patch("pdf_searchable.extract_searchable_text_from_pages", return_value=texts),
            patch("pdf_searchable.make_searchable_pdf", return_value=searchable),
            patch("pdf_storage.save_pdf", return_value=save_ret),
        )

    def test_text_present_uses_searchable(self) -> None:
        p1, p2, p3 = self._patches(["some text"], b"SEARCHABLE")
        with p1, p2 as mk, p3 as save:
            rel, size = pdf_backfill.generate_and_save_pdf(_CONTENT, _PAGES, "u1")
        self.assertEqual((rel, size), ("rel/p.pdf", 123))
        mk.assert_called_once()
        # save 收到的是 searchable 字节(不是原始 content)
        self.assertEqual(save.call_args.args[1], b"SEARCHABLE")

    def test_searchable_none_falls_back_to_original(self) -> None:
        p1, p2, p3 = self._patches(["text"], None)
        with p1, p2, p3 as save:
            pdf_backfill.generate_and_save_pdf(_CONTENT, _PAGES, "u1")
        self.assertEqual(save.call_args.args[1], _CONTENT)

    def test_searchable_raises_falls_back_to_original(self) -> None:
        p1 = patch("pdf_searchable.extract_searchable_text_from_pages", return_value=["t"])
        p2 = patch("pdf_searchable.make_searchable_pdf", side_effect=RuntimeError("boom"))
        p3 = patch("pdf_storage.save_pdf", return_value=("r", 1))
        with p1, p2, p3 as save:
            rel, _ = pdf_backfill.generate_and_save_pdf(_CONTENT, _PAGES, "u1")
        self.assertEqual(rel, "r")
        self.assertEqual(save.call_args.args[1], _CONTENT)  # fallback 原文件

    def test_no_text_skips_searchable(self) -> None:
        p1, p2, p3 = self._patches(["", "   "], b"SHOULD_NOT_USE")
        with p1, p2 as mk, p3 as save:
            pdf_backfill.generate_and_save_pdf(_CONTENT, _PAGES, "u1")
        mk.assert_not_called()
        self.assertEqual(save.call_args.args[1], _CONTENT)

    def test_save_raises_returns_none_none(self) -> None:
        p1 = patch("pdf_searchable.extract_searchable_text_from_pages", return_value=[""])
        p2 = patch("pdf_searchable.make_searchable_pdf", return_value=None)
        p3 = patch("pdf_storage.save_pdf", side_effect=OSError("disk full"))
        with p1, p2, p3:
            self.assertEqual(
                pdf_backfill.generate_and_save_pdf(_CONTENT, _PAGES, "u1"), (None, None)
            )


@contextmanager
def _fake_cursor(rowcount=2):
    cur = MagicMock()
    cur.rowcount = rowcount
    yield cur


class UpdatePdfStorageTest(unittest.TestCase):
    def _run(self, **kw):
        captured = {}

        @contextmanager
        def _gc(commit=False):
            cur = MagicMock()
            cur.rowcount = 2

            def _exec(sql, params):
                captured["sql"] = sql
                captured["params"] = params

            cur.execute.side_effect = _exec
            yield cur

        with patch.object(mutations.db, "get_cursor", _gc):
            rc = mutations.update_ocr_history_pdf_storage(**kw)
        return rc, captured

    def test_tenant_scoped_sql(self) -> None:
        rc, cap = self._run(
            record_ids=["id1", "id2"],
            pdf_storage_path="rel/x.pdf",
            pdf_size_bytes=99,
            user_id="u1",
            tenant_id="t1",
        )
        self.assertEqual(rc, 2)
        self.assertIn("tenant_id = %s::uuid", cap["sql"])
        self.assertIn("UPDATE ocr_history SET pdf_storage_path", cap["sql"])
        self.assertEqual(cap["params"], ("rel/x.pdf", 99, ["id1", "id2"], "t1"))

    def test_user_scoped_sql_when_no_tenant(self) -> None:
        rc, cap = self._run(
            record_ids=["id1"],
            pdf_storage_path="rel/x.pdf",
            pdf_size_bytes=10,
            user_id="u1",
            tenant_id=None,
        )
        self.assertEqual(rc, 2)
        self.assertIn("AND user_id = %s::uuid", cap["sql"])
        self.assertNotIn("tenant_id", cap["sql"])
        self.assertEqual(cap["params"], ("rel/x.pdf", 10, ["id1"], "u1"))

    def test_empty_record_ids_returns_zero_no_db(self) -> None:
        # 不该碰 DB
        with patch.object(
            mutations.db, "get_cursor", side_effect=AssertionError("must not touch DB")
        ):
            self.assertEqual(mutations.update_ocr_history_pdf_storage([], "p", 1, "u1"), 0)

    def test_no_path_returns_zero(self) -> None:
        self.assertEqual(mutations.update_ocr_history_pdf_storage(["id1"], "", 1, "u1"), 0)
        self.assertEqual(mutations.update_ocr_history_pdf_storage(["id1"], None, 1, "u1"), 0)

    def test_db_exception_returns_zero_never_raises(self) -> None:
        def _boom(commit=False):
            raise RuntimeError("db down")

        with patch.object(mutations.db, "get_cursor", _boom):
            self.assertEqual(
                mutations.update_ocr_history_pdf_storage(["id1"], "p", 1, "u1", "t1"), 0
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
