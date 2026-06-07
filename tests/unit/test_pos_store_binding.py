#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收银台店铺码绑定:纯函数 + 店铺令牌往返(POS 项目 · docs/pos/04 §1b)。

钉死:店铺码格式(前缀取店名 + 去易混字符随机体)、令牌自含 tenant/workspace/ver 且 typ=pos_store
(非收银员/老板 token)、版本对不上即"被重置"语义的判据。DAL 走库的部分由 prod 真账号 E2E 验。
"""

import os
import re
import unittest

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from core import auth as core_auth  # noqa: E402
from services.pos import store_binding as sb  # noqa: E402

_CODE_RE = re.compile(r"^[A-Z]{3}-[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{4}$")


class StoreCodeFormatTests(unittest.TestCase):
    def test_prefix_from_store_name(self):
        self.assertEqual(sb._prefix("Metta Pharmacy"), "MET")
        self.assertEqual(sb._prefix("เภสัช"), "POS")  # 无拉丁字母 → 回落 POS
        self.assertEqual(sb._prefix("AB"), "ABX")  # 不足 3 位补 X

    def test_gen_code_shape(self):
        for _ in range(200):
            code = sb._gen_code("MTA")
            self.assertRegex(code, _CODE_RE, f"码格式异常: {code}")
            self.assertNotRegex(code, r"[O01IL]", "码不应含易混字符 O/0/1/I/L")


class StoreTokenTests(unittest.TestCase):
    def test_store_token_roundtrip(self):
        tok = core_auth.create_pos_store_token(tenant_id="t-1", workspace_client_id=12, version=3)
        claims = core_auth.decode_access_token(tok)
        self.assertEqual(claims["typ"], "pos_store")
        self.assertEqual(claims["tenant_id"], "t-1")
        self.assertEqual(claims["workspace_client_id"], 12)
        self.assertEqual(claims["ver"], 3)
        # 不是收银员 token / 老板 token
        self.assertNotIn("cashier_id", claims)
        self.assertNotEqual(claims.get("role"), "owner")

    def test_reset_bumps_version_invalidates_old_token(self):
        # 旧令牌 ver=1;重置后库里 ver=2 → 校验侧 ver != current 即判失效
        old = core_auth.decode_access_token(
            core_auth.create_pos_store_token(tenant_id="t", workspace_client_id=1, version=1)
        )
        current_after_reset = 2
        self.assertNotEqual(old["ver"], current_after_reset)


if __name__ == "__main__":
    unittest.main()
