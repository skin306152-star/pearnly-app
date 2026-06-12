# -*- coding: utf-8 -*-
"""OAuth state HMAC 无状态签名守门(Google/LINE 登录跨 worker 不再 invalid_state)。

根因(2026-06-12):state 原存进程内存 _oauth_state_cache·workers>1 时发起与回调可能
不同 worker → 回调 worker 内存无此 state → invalid_state 登不上(workers=4 后必坏)。
改 HMAC 签名(JWT_SECRET 签·无服务端存储)→ 任一 worker 都能验。
"""

import hashlib
import hmac
import os
import time
import unittest

os.environ.setdefault("JWT_SECRET", "test-oauth-state-secret-1234567890")

from routes.oauth_routes import _gen_oauth_state, _verify_oauth_state, _oauth_state_secret


class OAuthStateTests(unittest.TestCase):
    def test_roundtrip(self):
        s = _gen_oauth_state()
        self.assertEqual(s.count("."), 2)
        self.assertTrue(_verify_oauth_state(s))

    def test_stateless_cross_worker(self):
        # 关键:验证不依赖任何进程内存(同 secret 即可验)→ 模拟另一 worker 验本 worker 发的 state。
        s = _gen_oauth_state()
        # 重新构造期望签名(等价于"另一进程"用同 JWT_SECRET 重算)→ 应通过
        nonce, ts, sig = s.split(".")
        expected = hmac.new(
            _oauth_state_secret(), f"{nonce}.{ts}".encode("utf-8"), hashlib.sha256
        ).hexdigest()[:32]
        self.assertEqual(sig, expected)
        self.assertTrue(_verify_oauth_state(s))

    def test_tampered_sig_rejected(self):
        s = _gen_oauth_state()
        self.assertFalse(_verify_oauth_state(s[:-4] + "dead"))

    def test_garbage_and_empty_rejected(self):
        self.assertFalse(_verify_oauth_state("garbage"))
        self.assertFalse(_verify_oauth_state(""))
        self.assertFalse(_verify_oauth_state("a.b"))

    def test_expired_rejected(self):
        old_payload = f"abc.{int(time.time()) - 700}"  # 700s > 600s TTL
        sig = hmac.new(
            _oauth_state_secret(), old_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()[:32]
        self.assertFalse(_verify_oauth_state(old_payload + "." + sig))


if __name__ == "__main__":
    unittest.main()
