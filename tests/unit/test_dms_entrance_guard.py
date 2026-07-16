# -*- coding: utf-8 -*-
"""/api/dms/* 入口守卫契约(_authorize)· 各是各的。

这些路由无权限码,入口作用域闸(authz/deps)按码前缀判、管不到,故守卫本地判:
  - dms_portal 关 → 404(fail-closed 不泄漏功能存在);
  - entrance_api_scope 开且 token.entry != dms → 403(main/pos/ai 会话打不进 /api/dms);
  - entry='dms' 令牌 → 过;超管任意门 → 过。
patch 三个消费面(get_user / 两闸),不碰真库(照 test_dms_billing_gate 范式)。
"""

import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

import routes.dms_routes as dms  # noqa: E402


def _patch(user, *, portal, scope):
    return (
        mock.patch.object(dms, "get_current_user_from_request", return_value=user),
        mock.patch.object(dms, "dms_portal_enabled_for", return_value=portal),
        mock.patch.object(dms, "entrance_api_scope_enabled_for", return_value=scope),
    )


class DmsEntranceGuardTest(unittest.TestCase):
    def test_portal_closed_returns_404(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "dms"}
        p1, p2, p3 = _patch(user, portal=False, scope=True)
        with p1, p2, p3, self.assertRaises(dms.HTTPException) as ctx:
            dms._authorize(object())
        self.assertEqual(ctx.exception.status_code, 404)

    def test_main_entry_token_forbidden_403(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "main"}
        p1, p2, p3 = _patch(user, portal=True, scope=True)
        with p1, p2, p3, self.assertRaises(dms.HTTPException) as ctx:
            dms._authorize(object())
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "authz.forbidden")

    def test_dms_entry_token_passes(self):
        user = {"id": "u1", "tenant_id": "t1", "entry": "dms"}
        p1, p2, p3 = _patch(user, portal=True, scope=True)
        with p1, p2, p3:
            self.assertIs(dms._authorize(object()), user)

    def test_super_admin_passes_any_door(self):
        # 超管短路:连闸都不读(portal/scope 均设 False 也放行)
        user = {"id": "adm", "is_super_admin": True, "entry": "main"}
        p1, p2, p3 = _patch(user, portal=False, scope=False)
        with p1, p2, p3:
            self.assertIs(dms._authorize(object()), user)

    def test_scope_gate_off_does_not_block_non_dms_entry(self):
        # 入口作用域闸关(急停回退)→ 不按 entry 拦,portal 在场即放行(现状回退)
        user = {"id": "u1", "tenant_id": "t1", "entry": "main"}
        p1, p2, p3 = _patch(user, portal=True, scope=False)
        with p1, p2, p3:
            self.assertIs(dms._authorize(object()), user)


if __name__ == "__main__":
    unittest.main()
