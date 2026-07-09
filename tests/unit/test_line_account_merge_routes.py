# -*- coding: utf-8 -*-
"""
P0 账户接管修复守门测试 · routes/line_account_merge_routes.py

漏洞回顾:POST /api/me/line_complete_email 只校验邮箱格式,不验证归属。
命中他人账号时旧代码会合并 line_uid 并颁发目标(受害者)账号的 token ——
任何知道受害者邮箱的人都能借自己的 LINE 占位账号顶替登录。

锁定:
  1. 命中他人账号 → 409 拒绝,不合并、不发 token(核心回归闸)。
  2. 邮箱未注册 → 正常绑到当前(自己)账号,行为不变。
  3. 命中的就是本账号自己(email_raw 恰好已是自身用户名的边界情况)→
     走同一条"绑自己"路径,不误判成"他人"。
"""

import asyncio
import unittest
from unittest import mock

from fastapi import HTTPException

from routes import line_account_merge_routes as r


class LineCompleteEmailRouteTests(unittest.TestCase):
    def setUp(self):
        self._cur_user = {"id": "temp-1", "username": "line_abc@line.local", "tenant_id": "t1"}
        p_user = mock.patch.object(r, "get_current_user_from_request", return_value=self._cur_user)
        p_user.start()
        self.addCleanup(p_user.stop)

        p_placeholder = mock.patch.object(r.db, "is_line_placeholder_username", return_value=True)
        p_placeholder.start()
        self.addCleanup(p_placeholder.stop)

        p_merge = mock.patch.object(r.db, "merge_line_account_into_existing")
        self.merge_mock = p_merge.start()
        self.addCleanup(p_merge.stop)

        p_token = mock.patch.object(r, "create_access_token", return_value="tok-xyz")
        self.token_mock = p_token.start()
        self.addCleanup(p_token.stop)

    def _payload(self, email):
        return r._LinePostEmail(email=email)

    def test_hit_other_account_rejected_no_merge_no_token(self):
        """命中他人账号 → 409,且绝不能合并或发目标账号 token(P0 回归闸)。"""
        victim = {"id": "victim-2", "username": "victim@gmail.com"}
        with mock.patch.object(r.db, "find_user_by_username", return_value=victim):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(
                    r.me_line_complete_email(self._payload("victim@gmail.com"), request=None)
                )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "email_registered_use_login")
        self.merge_mock.assert_not_called()
        self.token_mock.assert_not_called()

    def test_email_not_registered_binds_to_self(self):
        """邮箱未注册 → 正常绑到当前占位账号,不受影响。"""
        refreshed = {"id": "temp-1", "username": "new@gmail.com", "tenant_id": "t1"}
        with (
            mock.patch.object(r.db, "find_user_by_username", return_value=None),
            mock.patch.object(r.db, "update_user_email_and_username", return_value=True) as upd,
            mock.patch.object(r.db, "find_user_by_id", return_value=refreshed),
        ):
            out = asyncio.run(
                r.me_line_complete_email(self._payload("new@gmail.com"), request=None)
            )

        upd.assert_called_once_with("temp-1", "new@gmail.com")
        self.merge_mock.assert_not_called()
        self.assertEqual(out, {"ok": True, "merged": False, "token": "tok-xyz"})

    def test_self_match_treated_as_own_account_not_other(self):
        """find_user_by_username 命中的 id 恰好就是当前账号自己 → 走绑自己路径,不误判他人。"""
        self_row = {"id": "temp-1", "username": "temp-1@already-set.com"}
        refreshed = {"id": "temp-1", "username": "temp-1@already-set.com", "tenant_id": "t1"}
        with (
            mock.patch.object(r.db, "find_user_by_username", return_value=self_row),
            mock.patch.object(r.db, "update_user_email_and_username", return_value=True) as upd,
            mock.patch.object(r.db, "find_user_by_id", return_value=refreshed),
        ):
            out = asyncio.run(
                r.me_line_complete_email(self._payload("temp-1@already-set.com"), request=None)
            )

        upd.assert_called_once_with("temp-1", "temp-1@already-set.com")
        self.merge_mock.assert_not_called()
        self.assertEqual(out["ok"], True)
        self.assertEqual(out["merged"], False)


if __name__ == "__main__":
    unittest.main()
