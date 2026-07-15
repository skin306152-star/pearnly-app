# -*- coding: utf-8 -*-
"""ENC-b · 存量 slips 搬家脚本(scripts/ops/migrate_slips_dir.py)。

锁定:①搬移=源删除+新址可读且字节一致 ②幂等:重跑对已搬好的文件只跳过,不报错
③--keep-source 不删源 ④--dry-run 不落盘不删源 ⑤非文件(子目录)跳过不炸。
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from services.billing import slip_storage

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "migrate_slips_dir.py"
_spec = importlib.util.spec_from_file_location("migrate_slips_dir", _MOD)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


class MigrateSlipsDirTests(unittest.TestCase):
    def setUp(self):
        self._src = tempfile.TemporaryDirectory()
        self._dst = tempfile.TemporaryDirectory()
        self.addCleanup(self._src.cleanup)
        self.addCleanup(self._dst.cleanup)
        self._patch = mock.patch.object(slip_storage, "_STORAGE_ROOT", self._dst.name)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        self.src_dir = Path(self._src.name)

    def _write_src(self, name: str, data: bytes) -> Path:
        p = self.src_dir / name
        p.write_bytes(data)
        return p

    def test_moves_file_and_deletes_source(self):
        self._write_src("12.jpg", b"jpeg-bytes")
        rep = m.migrate(self.src_dir)
        self.assertEqual(rep, {"moved": 1, "skipped": 0, "corrupt": []})
        self.assertFalse((self.src_dir / "12.jpg").exists())
        self.assertEqual(slip_storage.read_slip("slips/12.jpg"), b"jpeg-bytes")

    def test_idempotent_rerun_skips(self):
        self._write_src("13.jpg", b"a")
        m.migrate(self.src_dir)
        # 源已被删,第二次跑对空目录也不该炸
        rep2 = m.migrate(self.src_dir)
        self.assertEqual(rep2, {"moved": 0, "skipped": 0, "corrupt": []})

    def test_rerun_when_source_kept_and_dest_matches_skips(self):
        self._write_src("14.jpg", b"same-bytes")
        m.migrate(self.src_dir, keep_source=True)
        self.assertTrue((self.src_dir / "14.jpg").exists())
        rep = m.migrate(self.src_dir, keep_source=True)
        self.assertEqual(rep["skipped"], 1)
        self.assertEqual(rep["moved"], 0)

    def test_keep_source_leaves_original_file(self):
        self._write_src("15.jpg", b"x")
        m.migrate(self.src_dir, keep_source=True)
        self.assertTrue((self.src_dir / "15.jpg").exists())
        self.assertEqual(slip_storage.read_slip("slips/15.jpg"), b"x")

    def test_dry_run_touches_nothing(self):
        self._write_src("16.jpg", b"x")
        rep = m.migrate(self.src_dir, dry_run=True)
        self.assertEqual(rep["moved"], 1)
        self.assertTrue((self.src_dir / "16.jpg").exists())
        self.assertIsNone(slip_storage.read_slip("slips/16.jpg"))

    def test_missing_source_dir_returns_empty_report(self):
        rep = m.migrate(self.src_dir / "does-not-exist")
        self.assertEqual(rep, {"moved": 0, "skipped": 0, "corrupt": []})

    def test_subdirectory_is_skipped_not_crashed(self):
        (self.src_dir / "subdir").mkdir()
        self._write_src("17.jpg", b"y")
        rep = m.migrate(self.src_dir)
        self.assertEqual(rep["moved"], 1)


if __name__ == "__main__":
    unittest.main()
