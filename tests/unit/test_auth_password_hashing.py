# -*- coding: utf-8 -*-
"""密码哈希/校验守门:注册必产 bcrypt + 校验兼容历史 sha256 兜底 + 长密码不锁死。

血泪根因(2026-06-12):signup_core._hash_password 的 fallback 链在 core.auth 找不到
hash 函数 → 靠 passlib → 偶发失败落 sha256 弱兜底;而 verify_password 只认 bcrypt →
注册成功却登不上("用户名或密码错误")。修:core.auth 补 hash_password(注册 step1
直接命中 → 必 bcrypt)+ verify_password 兼容历史 sha256 + 截 72 防长密码 bcrypt 抛错。
"""

import hashlib
import secrets
import unittest

from core.auth import hash_password, verify_password


def _legacy_sha256(password: str) -> str:
    """复刻 signup_core._hash_password 的 sha256 终极兜底格式(sha256$salt$hex)。"""
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"sha256${salt}${h}"


class HashPasswordTests(unittest.TestCase):
    def test_produces_bcrypt(self):
        h = hash_password("Secret-123")
        self.assertTrue(h.startswith("$2b$"))

    def test_roundtrip(self):
        h = hash_password("Secret-123")
        self.assertTrue(verify_password("Secret-123", h))
        self.assertFalse(verify_password("wrong", h))

    def test_long_password_does_not_crash(self):
        # >72 字节:hash 截 72,verify 也截 72,绝不抛错锁死用户
        pw = "a" * 100
        h = hash_password(pw)
        self.assertTrue(h.startswith("$2b$"))
        self.assertTrue(verify_password(pw, h))


class VerifyLegacySha256Tests(unittest.TestCase):
    def test_legacy_sha256_verifies(self):
        legacy = _legacy_sha256("Secret-123")
        self.assertEqual(len(legacy), 88)  # 旧兜底正好 88 字符
        self.assertTrue(verify_password("Secret-123", legacy))

    def test_legacy_sha256_wrong_password(self):
        self.assertFalse(verify_password("wrong", _legacy_sha256("Secret-123")))

    def test_empty_or_malformed_hash(self):
        self.assertFalse(verify_password("x", ""))
        self.assertFalse(verify_password("x", "sha256$onlytwo"))


class SignupUsesBcryptGuardTests(unittest.TestCase):
    """根因守门:注册哈希链 step1 命中 core.auth.hash_password → 必 bcrypt,不再落 sha256。"""

    def test_signup_hash_is_bcrypt_not_sha256(self):
        from services.auth.signup_core import _hash_password

        h = _hash_password("Secret-123")
        self.assertTrue(h.startswith("$2b$"), f"注册应产 bcrypt · 实得 {h[:10]}")
        self.assertFalse(h.startswith("sha256$"))
        self.assertTrue(verify_password("Secret-123", h))


if __name__ == "__main__":
    unittest.main()
