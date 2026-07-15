# -*- coding: utf-8 -*-
"""会话硬化契约:JWT 最小声明 + logout 撤销 active_jti。"""

from __future__ import annotations

import os
import asyncio
import unittest
from contextlib import contextmanager
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")


class _Req:
    def __init__(self, token: str = "") -> None:
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}


class _Cursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple | None]] = []

    def execute(self, sql, params=None) -> None:
        self.executed.append((sql, params))


def _ctx(cursor):
    @contextmanager
    def _gc(commit=False):
        yield cursor

    return _gc


class AuthSessionHardeningTests(unittest.TestCase):
    def test_access_token_contains_no_business_claims(self) -> None:
        from core import auth

        cur = _Cursor()
        with (
            mock.patch("core.db.get_cursor", _ctx(cur)),
            mock.patch("core.db.evict_user_cache"),
        ):
            token = auth.create_access_token(
                user_id="u1",
                username="owner@example.com",
                plan="credits",
                tenant_id="tenant-1",
                role="owner",
                is_super_admin=True,
                remember_me=True,
            )
        payload = auth.decode_access_token(token)

        self.assertEqual(payload["sub"], "u1")
        self.assertEqual(payload["typ"], "access")
        for key in ("username", "plan", "tenant_id", "role", "is_super_admin"):
            self.assertNotIn(key, payload)

    def test_access_token_carries_entry_claim(self) -> None:
        """token 烙会话入口 entry(main/pos/ai)· 缺省 main · 未知值收敛回 main。"""
        from core import auth

        cur = _Cursor()
        with (
            mock.patch("core.db.get_cursor", _ctx(cur)),
            mock.patch("core.db.evict_user_cache"),
        ):
            default = auth.decode_access_token(auth.create_access_token("u1", "a", "free"))
            pos = auth.decode_access_token(auth.create_access_token("u1", "a", "free", entry="pos"))
            ai = auth.decode_access_token(auth.create_access_token("u1", "a", "free", entry="ai"))
            junk = auth.decode_access_token(
                auth.create_access_token("u1", "a", "free", entry="firm-picker")
            )

        self.assertEqual(default["entry"], "main")
        self.assertEqual(pos["entry"], "pos")
        self.assertEqual(ai["entry"], "ai")
        self.assertEqual(junk["entry"], "main")

    def test_logout_revokes_current_active_jti(self) -> None:
        from core import auth

        cur = _Cursor()
        with (
            mock.patch.object(auth, "decode_access_token", return_value={"sub": "u1", "jti": "j1"}),
            mock.patch("core.db.get_cursor", _ctx(cur)),
            mock.patch("core.db.evict_user_cache") as evict,
        ):
            self.assertTrue(auth.revoke_current_token(_Req("tok")))

        self.assertIn("UPDATE users SET active_jti=NULL", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("u1", "j1"))
        evict.assert_called_once_with("u1")

    def test_logout_is_idempotent_without_token(self) -> None:
        from core import auth

        self.assertFalse(auth.revoke_current_token(_Req()))

    def test_logout_route_is_idempotent_and_calls_revoker(self) -> None:
        import routes.login_routes as login_routes

        with mock.patch.object(login_routes, "revoke_current_token") as revoke:
            out = asyncio.run(login_routes.logout(_Req("tok")))

        self.assertEqual(out, {"ok": True})
        revoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
