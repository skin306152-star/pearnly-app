# -*- coding: utf-8 -*-
"""file_crypto 信封加密层契约(ENC-a)。

覆盖:off 态逐字节等同今天 / on 态 seal-unseal 往返 / 篡改必炸不吞 / 无 MAGIC 存量明文双轨读 /
每文件独立 DEK / 启动 fail-fast(mode=on 无 KEK)。
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from core import file_crypto

_ENV_KEYS = ("FILE_ENC_MODE", "PEARNLY_FILE_KMS_KEY")


def _snapshot_env():
    return {k: os.environ.get(k) for k in _ENV_KEYS}


def _restore_env(saved):
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    file_crypto._FERNET = file_crypto._load_fernet()


class ModeOffIdentity(unittest.TestCase):
    def setUp(self):
        self._saved = _snapshot_env()
        os.environ["FILE_ENC_MODE"] = "off"

    def tearDown(self):
        _restore_env(self._saved)

    def test_maybe_seal_off_is_byte_identical(self):
        data = b"\x00hello\xffplain bytes"
        out = file_crypto.maybe_seal(data)
        self.assertEqual(out, data)  # 逐字节等同今天
        self.assertFalse(file_crypto.has_magic(out))

    def test_unseal_passthrough_plaintext(self):
        self.assertEqual(file_crypto.unseal(b"legacy no magic"), b"legacy no magic")


class ModeOnEnvelope(unittest.TestCase):
    def setUp(self):
        self._saved = _snapshot_env()
        os.environ["PEARNLY_FILE_KMS_KEY"] = Fernet.generate_key().decode()
        os.environ["FILE_ENC_MODE"] = "on"
        file_crypto._FERNET = file_crypto._load_fernet()

    def tearDown(self):
        _restore_env(self._saved)

    def test_seal_roundtrip_and_magic(self):
        data = b"secret invoice bytes \x89PNG money 12345.67"
        sealed = file_crypto.maybe_seal(data)
        self.assertTrue(sealed.startswith(file_crypto.MAGIC))
        self.assertNotIn(b"secret invoice", sealed)  # 明文片段不可见
        self.assertNotIn(b"12345.67", sealed)
        self.assertEqual(file_crypto.unseal(sealed), data)

    def test_tamper_any_byte_raises(self):
        sealed = bytearray(file_crypto.seal(b"balance 999.99"))
        sealed[-1] ^= 0x01  # 翻密文末字节
        with self.assertRaises(file_crypto.FileCryptoError):
            file_crypto.unseal(bytes(sealed))

    def test_legacy_plaintext_still_readable(self):
        # 双轨读:无 MAGIC 的存量明文原样返回(迁移中断/明密混布可读)。
        self.assertEqual(file_crypto.unseal(b"old plaintext"), b"old plaintext")

    def test_distinct_dek_nonce_per_file(self):
        self.assertNotEqual(file_crypto.seal(b"x"), file_crypto.seal(b"x"))

    def test_empty_plaintext_roundtrips(self):
        self.assertEqual(file_crypto.unseal(file_crypto.seal(b"")), b"")


class StartupFailFast(unittest.TestCase):
    def test_mode_on_without_kek_fails_import(self):
        env = {k: v for k, v in os.environ.items() if k != "PEARNLY_FILE_KMS_KEY"}
        env["FILE_ENC_MODE"] = "on"
        env.pop("PEARNLY_FILE_KMS_KEY", None)
        repo = Path(__file__).resolve().parents[2]
        proc = subprocess.run(
            [sys.executable, "-c", "import core.file_crypto"],
            cwd=str(repo),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)  # 起不来
        self.assertIn("PEARNLY_FILE_KMS_KEY", proc.stderr)


if __name__ == "__main__":
    unittest.main()
