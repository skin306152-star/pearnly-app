# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · ocr_history 读/改/删 DAL 抽取契约

锁定:
  1. 5 个函数从 services.ocr_history.store 提供,db.py 经 re-export 暴露同一对象
     (调用点 db.xxx / from db import 零改动)。
  2. 纯结构性 0 逻辑改:跨域调用改 db.*(find_user_by_id 等)后,关键行为经
     mock.patch("core.db.get_cursor") 仍生效:retention_days==0 早返空 · 空 record_ids 早返。
"""

import unittest
from unittest import mock

from core import db
from services.ocr_history import store


class OcrHistoryReexportContract(unittest.TestCase):
    def test_funcs_reexported_same_object(self):
        for n in [
            "list_ocr_history",
            "get_ocr_history_detail",
            "update_ocr_history_pages",
            "delete_ocr_history",
            "delete_ocr_history_with_pdf_paths",
            # 写入/去重半边(REFACTOR-B2 第二刀)
            "insert_ocr_history",
            "get_history_pdf_info",
            "find_ocr_by_hash",
            "check_duplicate_invoice",
            "_extract_summary_fields",
        ]:
            self.assertTrue(hasattr(store, n), f"service missing {n}")
            self.assertIs(
                getattr(db, n), getattr(store, n), f"db.{n} not re-exporting service object"
            )

    def test_extract_summary_fields_picks_main_page(self):
        # 纯逻辑(无 DB):非副本主页优先
        pages = [
            {"is_copy": True, "fields": {"invoice_number": "COPY"}},
            {"fields": {"invoice_number": "MAIN", "total_amount": "100", "seller_name": "S"}},
        ]
        self.assertEqual(store._extract_summary_fields(pages)["invoice_no"], "MAIN")


class OcrHistoryBehaviorContract(unittest.TestCase):
    def test_list_retention_zero_returns_empty_without_db(self):
        # retention_days==0 → 早返空,不应触库
        with mock.patch("core.db.get_cursor", side_effect=AssertionError("must not hit DB")):
            out = store.list_ocr_history("u1", retention_days=0)
        self.assertEqual(
            out,
            {
                "items": [],
                "total": 0,
                "status_counts": {"all": 0, "confirmed": 0, "pending": 0, "failed": 0},
            },
        )

    def test_delete_with_pdf_paths_empty_ids_early_return(self):
        with mock.patch("core.db.get_cursor", side_effect=AssertionError("must not hit DB")):
            self.assertEqual(store.delete_ocr_history_with_pdf_paths("u1", []), (0, []))

    def test_list_builds_items_via_mocked_cursor(self):
        cur = mock.MagicMock()
        import datetime as _dt

        # fetchone 三段:① 汇总卡状态聚合 ② 列表分页总数(SELECT rows 走 fetchall)
        cur.fetchone.side_effect = [
            {"all_c": 1, "confirmed_c": 1, "failed_c": 0},
            {"c": 1},
        ]
        cur.fetchall.return_value = [
            {
                "id": "abc",
                "filename": "f.pdf",
                "page_count": 1,
                "confidence": "high",
                "elapsed_ms": 10,
                "invoice_no": "INV1",
                "invoice_date": _dt.date(2026, 5, 1),
                "seller_name": "S",
                "total_amount": 100,
                "archive_name": None,
                "category_tag": None,
                "fields_edited_at": None,
                "edit_count": 0,
                "created_at": _dt.datetime(2026, 5, 1, 9, 0, 0),
                "source_pdf_id": None,
                "source_index": None,
                "source_total": None,
                "source": None,
                "source_ref": None,
                "pdf_storage_path": None,
                # 销项重做新增列(派生状态 + 从 pages 抽买方/税额)
                "derived_status": "confirmed",
                "buyer_name": "BuyerCo",
                "vat_amount": "7.00",
            }
        ]
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        ctx.__exit__.return_value = False
        with mock.patch("core.db.get_cursor", return_value=ctx):
            out = store.list_ocr_history("u1", retention_days=90)
        self.assertEqual(out["total"], 1)
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["items"][0]["invoice_no"], "INV1")
        self.assertFalse(out["items"][0]["has_pdf"])
        # 销项重做契约:买方 / 派生状态 / 汇总卡分布
        self.assertEqual(out["items"][0]["buyer_name"], "BuyerCo")
        self.assertEqual(out["items"][0]["vat_amount"], "7.00")
        self.assertEqual(out["items"][0]["status"], "confirmed")
        self.assertEqual(
            out["status_counts"], {"all": 1, "confirmed": 1, "failed": 0, "pending": 0}
        )


if __name__ == "__main__":
    unittest.main()
