# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · PDF 留底存储 pdf_storage.py 行为契约

pdf_storage.py(本地文件系统留底 · 含路径穿越防护)此前 0 专属测试。
用临时目录隔离 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。

重点锁定安全契约:get_pdf_abs_path 必须挡住 '..' 穿越 / 绝对路径逃逸,
+ save/delete 幂等 + 健康检查。
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pdf_storage


class PdfStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = self._tmp.name
        self._patch = mock.patch.object(pdf_storage, "PDF_STORAGE_BASE", self.base)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._tmp.cleanup()

    def test_save_returns_rel_and_size_and_writes_file(self):
        rel, size = pdf_storage.save_pdf("abcdef12-3456-7890-aaaa-bbbbbbbbbbbb", b"%PDF-1.4 data")
        self.assertIsNotNone(rel)
        self.assertEqual(size, len(b"%PDF-1.4 data"))
        # 路径格式:user_short(8)/YYYY-MM/uuid.pdf
        parts = rel.split("/")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "abcdef12")  # 去横线取前 8
        self.assertTrue(parts[2].endswith(".pdf"))
        self.assertTrue((Path(self.base) / rel).exists())

    def test_save_empty_content_returns_none(self):
        self.assertEqual(pdf_storage.save_pdf("u", b""), (None, 0))

    def test_save_get_delete_round_trip(self):
        rel, _ = pdf_storage.save_pdf("user1234", b"data")
        p = pdf_storage.get_pdf_abs_path(rel)
        self.assertIsNotNone(p)
        self.assertTrue(p.exists())
        self.assertTrue(pdf_storage.delete_pdf(rel))
        self.assertIsNone(pdf_storage.get_pdf_abs_path(rel))  # 删后取不到

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(pdf_storage.get_pdf_abs_path("user1234/2026-05/nope.pdf"))

    def test_get_blocks_path_traversal(self):
        self.assertIsNone(pdf_storage.get_pdf_abs_path("../../etc/passwd"))
        self.assertIsNone(pdf_storage.get_pdf_abs_path("/etc/passwd"))
        self.assertIsNone(pdf_storage.get_pdf_abs_path(""))

    def test_delete_idempotent(self):
        # 不存在 / 空 → 都视为成功(幂等)
        self.assertTrue(pdf_storage.delete_pdf("user1234/2026-05/ghost.pdf"))
        self.assertTrue(pdf_storage.delete_pdf(""))

    def test_health_check_ok_when_writable(self):
        h = pdf_storage.storage_health_check()
        self.assertTrue(h["ok"])
        self.assertEqual(h["path"], self.base)
        # 健康检查不留垃圾文件
        self.assertFalse((Path(self.base) / ".health_check").exists())


if __name__ == "__main__":
    unittest.main()
