# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 对称加密 kms_helper.py 行为契约

kms_helper.py(Fernet 加密 ERP 凭据 · 不许明文进 DB)此前 0 专属测试。
凭据加密是关键路径 · 补往返 + 异常 + is_encrypted 守门(只测 · 不改安全代码)。
纯逻辑 · 无 DB/网络(Wave 0 安全网 · 零冲突)。

注:kms_helper 在 import 时若缺 PEARNLY_KMS_KEY 会 ImportError(fail-fast 设计) ·
测试用 setdefault 在 import 前兜底一把 key(不覆盖真实环境已设的 key)。
"""

import os
import unittest

from cryptography.fernet import Fernet

# import 前确保有 key(本地缺则生成 · CI/真实环境已设则保留)
os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from core import kms_helper as kms  # noqa: E402 - 必须在 setdefault 之后导入


class RoundTripTests(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        for plain in ("password123", "test01_!@#", "中文泰文สวัสดี", ""):
            self.assertEqual(kms.decrypt_str(kms.encrypt_str(plain)), plain)

    def test_ciphertext_differs_from_plaintext(self):
        enc = kms.encrypt_str("secret")
        self.assertNotEqual(enc, "secret")
        self.assertNotIn("secret", enc)

    def test_each_encrypt_is_nondeterministic_but_decrypts_same(self):
        # Fernet 带时间戳/IV · 两次密文不同 · 但都还原同一明文
        a = kms.encrypt_str("same")
        b = kms.encrypt_str("same")
        self.assertNotEqual(a, b)
        self.assertEqual(kms.decrypt_str(a), "same")
        self.assertEqual(kms.decrypt_str(b), "same")

    def test_none_passthrough(self):
        self.assertIsNone(kms.encrypt_str(None))
        self.assertIsNone(kms.decrypt_str(None))

    def test_non_str_coerced(self):
        enc = kms.encrypt_str(12345)
        self.assertEqual(kms.decrypt_str(enc), "12345")


class DecryptFailureTests(unittest.TestCase):
    def test_invalid_token_raises_valueerror(self):
        # 无效密文(或 KMS_KEY 轮换)→ ValueError · 不返回部分明文
        with self.assertRaises(ValueError):
            kms.decrypt_str("not-a-valid-fernet-token")


class IsEncryptedTests(unittest.TestCase):
    def test_encrypted_output_detected(self):
        self.assertTrue(kms.is_encrypted(kms.encrypt_str("hello world data")))

    def test_plaintext_not_detected(self):
        self.assertFalse(kms.is_encrypted("plaintext password"))
        self.assertFalse(kms.is_encrypted("short"))  # < 60
        self.assertFalse(kms.is_encrypted(None))
        self.assertFalse(kms.is_encrypted(12345))


if __name__ == "__main__":
    unittest.main()
