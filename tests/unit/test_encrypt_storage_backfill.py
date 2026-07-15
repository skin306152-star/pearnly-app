# -*- coding: utf-8 -*-
"""存量加密回填脚本契约(ENC-a · scripts/ops/encrypt_storage_backfill.py)。

三道保险 + 双向:明文全转 / 密文跳过(幂等)/ 损坏点名停 / --decrypt 往返逐字节一致 /
verify 计数正确。
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from core import file_crypto

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "encrypt_storage_backfill.py"
_spec = importlib.util.spec_from_file_location("encrypt_storage_backfill", _MOD)
bf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bf)


class BackfillContract(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("FILE_ENC_MODE", "PEARNLY_FILE_KMS_KEY")}
        os.environ["PEARNLY_FILE_KMS_KEY"] = Fernet.generate_key().decode()
        os.environ["FILE_ENC_MODE"] = "on"
        file_crypto._FERNET = file_crypto._load_fernet()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        file_crypto._FERNET = file_crypto._load_fernet()

    def _write(self, rel, data):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def test_mixed_dir_converts_skips_and_names_corrupt(self):
        p1 = self._write("a/plain1.txt", b"alpha plaintext")
        p2 = self._write("b/plain2.bin", b"\x00\x01beta")
        cipher = self._write("c/already.enc", file_crypto.seal(b"gamma"))
        corrupt = self._write("c/broken.enc", file_crypto.MAGIC + os.urandom(48))

        with self.assertRaises(bf.BackfillError) as ctx:
            bf.run_backfill([self.root])
        report = ctx.exception.report
        self.assertEqual(report["converted"], 2)  # 两个明文全转
        self.assertEqual(report["skipped"], 1)  # 有效密文跳过(幂等)
        self.assertEqual(report["corrupt"], [str(corrupt)])  # 损坏点名

        # 明文已就地加密,解回明文逐字节一致
        for p, original in ((p1, b"alpha plaintext"), (p2, b"\x00\x01beta")):
            disk = p.read_bytes()
            self.assertTrue(file_crypto.has_magic(disk))
            self.assertEqual(file_crypto.unseal(disk), original)
        # 已密文件内容不变
        self.assertEqual(file_crypto.unseal(cipher.read_bytes()), b"gamma")

    def test_idempotent_rerun_skips_all(self):
        self._write("x/f.txt", b"data-x")
        bf.run_backfill([self.root])
        rep = bf.run_backfill([self.root])  # 二次跑
        self.assertEqual(rep["converted"], 0)
        self.assertEqual(rep["skipped"], 1)

    def test_decrypt_roundtrip_byte_identical(self):
        originals = {"m/one.txt": b"one plaintext", "m/two.bin": b"\xfftwo"}
        for rel, data in originals.items():
            self._write(rel, data)
        digests = {rel: hashlib.sha256(data).hexdigest() for rel, data in originals.items()}
        bf.run_backfill([self.root])  # 加密
        bf.run_backfill([self.root], decrypt=True)  # 解密回滚
        for rel, expected in digests.items():
            disk = (self.root / rel).read_bytes()
            self.assertFalse(file_crypto.has_magic(disk))  # 已回明文
            self.assertEqual(hashlib.sha256(disk).hexdigest(), expected)

    def test_verify_counts(self):
        self._write("p/plain.txt", b"still plaintext")
        self._write("q/enc.bin", file_crypto.seal(b"encrypted"))
        self._write("q/bad.bin", file_crypto.MAGIC + os.urandom(32))
        rep = bf.verify([self.root])
        self.assertEqual(rep["ciphertext"], 1)
        self.assertEqual(rep["plaintext"], 1)
        self.assertEqual(len(rep["corrupt"]), 1)


if __name__ == "__main__":
    unittest.main()
