# -*- coding: utf-8 -*-
"""工单落盘布局 + 取盘防穿越守门(services/workorder/storage.py)。

租户前 8 位隔离目录;补料落 materials/;取盘 resolve_within_order 只放行工单目录之下的
真文件,越界(../ 逃逸 / 别的工单 / 不存在)一律返 None。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.workorder import storage


class StorageLayoutTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = storage._BASE
        storage._BASE = self._tmp.name
        self.addCleanup(setattr, storage, "_BASE", self._orig)
        self.tenant = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        self.wo = "wo-123"

    def test_tenant_and_order_isolated_in_path(self):
        d = storage.order_dir(self.tenant, self.wo)
        self.assertIn("aaaaaaaa", str(d))  # 租户前 8 位
        self.assertTrue(str(d).endswith(self.wo))

    def test_save_material_writes_under_order_and_keeps_suffix(self):
        path = storage.save_material(self.tenant, self.wo, b"hello", ".jpg")
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), b"hello")
        self.assertEqual(path.suffix, ".jpg")
        self.assertIn("materials", path.parts)

    def test_resolve_accepts_real_file_inside_order(self):
        path = storage.save_material(self.tenant, self.wo, b"x", ".md")
        got = storage.resolve_within_order(self.tenant, self.wo, str(path))
        self.assertEqual(got, path.resolve())

    def test_resolve_rejects_traversal_and_other_order(self):
        outside = Path(self._tmp.name) / "secret.txt"
        outside.write_bytes(b"nope")
        # 直接给工单目录外的路径 → None
        self.assertIsNone(storage.resolve_within_order(self.tenant, self.wo, str(outside)))
        # 另一张工单的文件 → None(跨单不可下载)
        other = storage.save_material(self.tenant, "wo-999", b"y", ".md")
        self.assertIsNone(storage.resolve_within_order(self.tenant, self.wo, str(other)))
        # 不存在的路径 → None
        self.assertIsNone(
            storage.resolve_within_order(
                self.tenant, self.wo, str(storage.order_dir(self.tenant, self.wo) / "ghost.md")
            )
        )

    def test_resolve_empty_returns_none(self):
        self.assertIsNone(storage.resolve_within_order(self.tenant, self.wo, ""))


if __name__ == "__main__":
    unittest.main()
