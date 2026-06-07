# -*- coding: utf-8 -*-
"""收银员 PIN 鉴权守门测试(POS 项目 · PO-B1)。

锁定:PIN 走 bcrypt(密文≠明文 · 可验)· 登录三态(成功/停用/错PIN→对应错误码)· POS token
自含 tenant/workspace/cashier 声明且 typ='pos'(进 /home 接口因无 users 行必 401)。"""

import os
import unittest

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core import auth as core_auth  # noqa: E402
from core.pos_api import PosError  # noqa: E402
from services.pos import auth  # noqa: E402


class FakeCursor:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None


class PinHashTests(unittest.TestCase):
    def test_hash_is_not_plaintext_and_verifies(self):
        h = auth.hash_pin("1234")
        self.assertNotEqual(h, "1234")
        self.assertTrue(auth.verify_pin("1234", h))
        self.assertFalse(auth.verify_pin("0000", h))

    def test_verify_bad_hash_is_false_not_raise(self):
        self.assertFalse(auth.verify_pin("1234", "not-a-bcrypt-hash"))


class LoginTests(unittest.TestCase):
    def _cashier_row(self, pin="1234", active=True):
        return {
            "id": "c1",
            "display_name": "Nok",
            "pin_hash": auth.hash_pin(pin),
            "is_active": active,
        }

    def test_success_issues_pos_token(self):
        cur = FakeCursor(ones=[self._cashier_row(), None])  # cashier, then no open shift
        out = auth.login(cur, tenant_id="t", workspace_client_id=9, cashier_id="c1", pin="1234")
        self.assertEqual(out["cashier"]["display_name"], "Nok")
        self.assertIsNone(out["shift"])
        self.assertEqual(out["offline_ttl_hours"], core_auth.POS_TOKEN_TTL_HOURS)
        payload = core_auth.decode_access_token(out["token"])
        self.assertEqual(payload["typ"], "pos")
        self.assertEqual(payload["role"], "cashier")
        self.assertEqual(payload["tenant_id"], "t")
        self.assertEqual(payload["workspace_client_id"], 9)
        self.assertEqual(payload["cashier_id"], "c1")

    def test_missing_cashier_is_pin_invalid(self):
        cur = FakeCursor(ones=[None])
        with self.assertRaises(PosError) as ctx:
            auth.login(cur, tenant_id="t", workspace_client_id=9, cashier_id="x", pin="1234")
        self.assertEqual(ctx.exception.code, "pos.pin_invalid")
        self.assertEqual(ctx.exception.http_status, 401)

    def test_inactive_cashier(self):
        cur = FakeCursor(ones=[self._cashier_row(active=False)])
        with self.assertRaises(PosError) as ctx:
            auth.login(cur, tenant_id="t", workspace_client_id=9, cashier_id="c1", pin="1234")
        self.assertEqual(ctx.exception.code, "pos.cashier_inactive")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_wrong_pin(self):
        cur = FakeCursor(ones=[self._cashier_row(pin="1234")])
        with self.assertRaises(PosError) as ctx:
            auth.login(cur, tenant_id="t", workspace_client_id=9, cashier_id="c1", pin="9999")
        self.assertEqual(ctx.exception.code, "pos.pin_invalid")

    def test_open_shift_returned_when_present(self):
        from datetime import datetime, timezone

        shift = {
            "id": "s1",
            "terminal_id": 3,
            "opened_at": datetime(2026, 6, 7, tzinfo=timezone.utc),
            "opening_float": 500,
        }
        cur = FakeCursor(ones=[self._cashier_row(), shift])
        out = auth.login(cur, tenant_id="t", workspace_client_id=9, cashier_id="c1", pin="1234")
        self.assertEqual(out["shift"]["id"], "s1")
        self.assertEqual(out["shift"]["terminal_id"], 3)
        self.assertEqual(out["shift"]["opening_float"], 500.0)


if __name__ == "__main__":
    unittest.main()
