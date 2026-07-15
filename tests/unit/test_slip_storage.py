# -*- coding: utf-8 -*-
"""ENC-b · 充值截图落盘(services/billing/slip_storage.py)。

复用 ENC-a 的 workorder storage.write_artifact_bytes/read_bytes(不新写加解密逻辑);
锁定:①off 态写读逐字节一致(等同今天裸文件行为)②路径穿越(../, 绝对路径)一律 None
③abs_path 越界(跳出 STORAGE_ROOT)返 None ④不存在文件读返 None。
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from services.billing import slip_storage


class SlipStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._patch = mock.patch.object(slip_storage, "_STORAGE_ROOT", self._tmp.name)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def test_write_then_read_roundtrip_off_mode(self):
        slip_storage.write_slip("slips/7.jpg", b"jpeg-bytes")
        self.assertEqual(slip_storage.read_slip("slips/7.jpg"), b"jpeg-bytes")

    def test_write_creates_parent_dirs(self):
        path = slip_storage.write_slip("slips/8.png", b"png-bytes")
        self.assertTrue(Path(path).exists())
        self.assertEqual(Path(path), Path(self._tmp.name) / "slips" / "8.png")

    def test_missing_file_returns_none(self):
        self.assertIsNone(slip_storage.read_slip("slips/nope.jpg"))

    def test_path_traversal_blocked(self):
        self.assertIsNone(slip_storage.abs_path("../../etc/passwd"))
        self.assertIsNone(slip_storage.abs_path("/etc/passwd"))
        self.assertIsNone(slip_storage.abs_path(""))

    def test_read_slip_blocks_traversal(self):
        # 即便磁盘上真有这个文件(越界路径),read_slip 也必须拒绝解析
        outside = Path(self._tmp.name).parent / "outside_7.jpg"
        outside.write_bytes(b"leak")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        self.assertIsNone(slip_storage.read_slip("../outside_7.jpg"))

    def test_on_mode_writes_ciphertext_magic(self):
        from core import file_crypto

        with (
            mock.patch.dict(os.environ, {"FILE_ENC_MODE": "on"}),
            mock.patch.object(file_crypto, "is_enabled", return_value=True),
            mock.patch.object(
                file_crypto,
                "seal",
                side_effect=lambda b: file_crypto.MAGIC + b"\x01\x00\x00" + b,
            ),
            mock.patch.object(
                file_crypto,
                "unseal",
                side_effect=lambda b: (
                    b[len(file_crypto.MAGIC) + 3 :] if file_crypto.has_magic(b) else b
                ),
            ),
        ):
            slip_storage.write_slip("slips/9.jpg", b"secret-bytes")
            raw = (Path(self._tmp.name) / "slips" / "9.jpg").read_bytes()
            self.assertTrue(raw.startswith(file_crypto.MAGIC))
            self.assertEqual(slip_storage.read_slip("slips/9.jpg"), b"secret-bytes")


if __name__ == "__main__":
    unittest.main()
