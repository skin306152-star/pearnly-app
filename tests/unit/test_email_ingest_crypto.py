# -*- coding: utf-8 -*-
"""services/email_ingest/email_ingest_crypto.py 行为单测(ENC-c 堵洞)。

命门断言:cryptography 缺失 = fail-fast(raise),不再降级 base64 假加密;
ENC-c 前遗留的 base64 降级密文,读侧要能识别 + 报错点名,不能静默当真密码用。
"""

import base64
import importlib
import os
import sys
import unittest
from unittest import mock

from cryptography.fernet import Fernet

from services.email_ingest import email_ingest_crypto as crypto


def _with_key(key: str):
    """重置懒加载单例 + 打上 EMAIL_ENCRYPTION_KEY · 各测试独立跑不互相污染。"""
    crypto._FERNET = None
    crypto._FERNET_INIT_DONE = False
    return mock.patch.dict(os.environ, {"EMAIL_ENCRYPTION_KEY": key})


def _without_key():
    crypto._FERNET = None
    crypto._FERNET_INIT_DONE = False
    return mock.patch.dict(os.environ, {"EMAIL_ENCRYPTION_KEY": ""})


class EmailIngestCryptoRoundtripTests(unittest.TestCase):
    def setUp(self):
        crypto._FERNET = None
        crypto._FERNET_INIT_DONE = False

    def tearDown(self):
        crypto._FERNET = None
        crypto._FERNET_INIT_DONE = False

    def test_encrypt_decrypt_roundtrip(self):
        key = Fernet.generate_key().decode()
        with _with_key(key):
            cipher = crypto.encrypt_password("s3cr3t!สวัสดี")
            self.assertTrue(cipher.startswith(b"gAAAAA"))
            self.assertEqual(crypto.decrypt_password(cipher), "s3cr3t!สวัสดี")

    def test_is_available_true_with_key(self):
        key = Fernet.generate_key().decode()
        with _with_key(key):
            self.assertTrue(crypto.is_available())

    def test_is_available_false_without_key(self):
        with _without_key():
            self.assertFalse(crypto.is_available())

    def test_encrypt_empty_returns_empty_bytes(self):
        key = Fernet.generate_key().decode()
        with _with_key(key):
            self.assertEqual(crypto.encrypt_password(""), b"")

    def test_decrypt_empty_cipher_returns_none(self):
        self.assertIsNone(crypto.decrypt_password(b""))


class EmailIngestCryptoFailFastTests(unittest.TestCase):
    """ENC-c 堵洞:不再有 base64 假加密回落 · 该 raise 就 raise,该 None 就 None(不吞假货)。"""

    def setUp(self):
        crypto._FERNET = None
        crypto._FERNET_INIT_DONE = False

    def tearDown(self):
        crypto._FERNET = None
        crypto._FERNET_INIT_DONE = False

    def test_encrypt_without_key_raises_not_base64_fallback(self):
        with _without_key():
            with self.assertRaises(RuntimeError):
                crypto.encrypt_password("x")

    def test_decrypt_without_key_returns_none(self):
        with _without_key():
            self.assertIsNone(crypto.decrypt_password(b"whatever"))

    def test_decrypt_legacy_base64_downgrade_rejected_with_named_log(self):
        # 模拟 ENC-c 之前的降级行:密码原文被 base64(而非 Fernet)编码存进 bytea 列。
        key = Fernet.generate_key().decode()
        legacy_cipher = base64.b64encode("old-plain-password".encode("utf-8"))
        with _with_key(key):
            with self.assertLogs(crypto.logger, level="ERROR") as cm:
                self.assertIsNone(crypto.decrypt_password(legacy_cipher))
        self.assertTrue(any("base64" in line and "降级" in line for line in cm.output))

    def test_decrypt_wrong_key_reports_generic_corruption_not_legacy(self):
        # 真 Fernet token(只是密钥不对)· 不能被误判成 legacy base64 降级行。
        key_a = Fernet.generate_key().decode()
        key_b = Fernet.generate_key().decode()
        cipher = Fernet(key_a.encode()).encrypt(b"secret-password")
        with _with_key(key_b):
            with self.assertLogs(crypto.logger, level="ERROR") as cm:
                self.assertIsNone(crypto.decrypt_password(cipher))
        self.assertTrue(any("密钥轮换或数据损坏" in line for line in cm.output))
        self.assertFalse(any("降级" in line for line in cm.output))

    def test_missing_cryptography_raises_at_import(self):
        mod_name = "services.email_ingest.email_ingest_crypto"
        sys.modules.pop(mod_name, None)
        try:
            with mock.patch.dict(sys.modules, {"cryptography": None, "cryptography.fernet": None}):
                with self.assertRaises(ImportError):
                    importlib.import_module(mod_name)
        finally:
            sys.modules.pop(mod_name, None)
            importlib.import_module(mod_name)  # 恢复干净态供其它测试用


if __name__ == "__main__":
    unittest.main()
