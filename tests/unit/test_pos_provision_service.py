# -*- coding: utf-8 -*-
"""services/pos/provision 发放账号一条龙契约(PS-5 · 不连库 · 打桩 DB 层)。

覆盖验收 ③:①新邮箱 → 建号 + 建租户 + grant 一条龙 + 回显初始密码;②已存在邮箱 → 走既有
租户开通路(不建号 · 不回显密码);③初始密码满足强度(≥8 · 含字母和数字)且【绝不落日志】;
④非法邮箱早拒不碰 DB。"""

import unittest
from unittest import mock

from services.auth import account_provision
from services.pos import provision


class GenPasswordTests(unittest.TestCase):
    def test_strength_meets_reset_gate(self):
        # 重置流强度闸:≥8 · 至少一字母一数字。连生成 200 个都得过。
        for _ in range(200):
            pw = provision._gen_initial_password()
            self.assertGreaterEqual(len(pw), 8)
            self.assertTrue(any(c.isalpha() for c in pw))
            self.assertTrue(any(c.isdigit() for c in pw))
            # 去混淆字符表:不含易混的 0/O/1/I/l
            self.assertFalse(any(c in "0O1Il" for c in pw))


class ProvisionOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.grant = mock.patch.object(
            provision.ent, "grant", return_value={"grant_code": "POS-ABCD-2345"}
        ).start()
        self.ensure = mock.patch.object(
            provision, "_ensure_tenant_for_new_user", return_value="tid-new"
        ).start()
        self.hash = mock.patch.object(
            provision, "_hash_password", side_effect=lambda p: "hash:" + p
        ).start()
        self.create = mock.patch.object(
            provision, "create_owner_login_user", return_value="uid-new"
        ).start()
        self.addCleanup(mock.patch.stopall)

    def test_new_email_builds_account_tenant_and_grants(self):
        find = mock.patch.object(provision, "find_login_user", return_value=None).start()
        res = provision.provision_pos_account(
            object(), email="Shop@Example.com", tenant_name="ร้านทดสอบ", granted_by="earn"
        )
        find.assert_called_once()
        self.create.assert_called_once()
        self.ensure.assert_called_once()
        self.grant.assert_called_once()
        self.assertFalse(res["existed"])
        self.assertEqual(res["tenant_id"], "tid-new")
        self.assertEqual(res["grant_code"], "POS-ABCD-2345")
        # 一次性初始密码:非空 · 满足强度
        pw = res["initial_password"]
        self.assertTrue(pw and any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw))
        # 密码明文进哈希、grant 落在新租户上
        self.hash.assert_called_once_with(pw)
        self.assertEqual(self.grant.call_args.kwargs["tenant_id"], "tid-new")

    def test_existing_email_uses_existing_tenant_no_password(self):
        mock.patch.object(
            provision,
            "find_login_user",
            return_value={"id": "uid-old", "tenant_id": "tid-old", "username": "old"},
        ).start()
        res = provision.provision_pos_account(object(), email="old@example.com")
        self.create.assert_not_called()  # 不建号
        self.ensure.assert_not_called()  # 有租户就不补建
        self.grant.assert_called_once()
        self.assertTrue(res["existed"])
        self.assertEqual(res["tenant_id"], "tid-old")
        self.assertIsNone(res["initial_password"])  # 已存在账号绝不回显密码

    def test_existing_user_without_tenant_gets_tenant_backfilled(self):
        mock.patch.object(
            provision,
            "find_login_user",
            return_value={"id": "uid-orphan", "tenant_id": None, "username": "orphan"},
        ).start()
        res = provision.provision_pos_account(object(), email="orphan@example.com")
        self.ensure.assert_called_once()  # orphan 补建租户
        self.create.assert_not_called()  # 但不重建账号
        self.assertTrue(res["existed"])
        self.assertIsNone(res["initial_password"])

    def test_invalid_email_rejected_before_db(self):
        find = mock.patch.object(provision, "find_login_user").start()
        for bad in ("", "  ", "noat", "no@domain"):
            with self.assertRaises(ValueError) as e:
                provision.provision_pos_account(object(), email=bad)
            self.assertEqual(str(e.exception), "email_invalid")
        find.assert_not_called()

    def test_initial_password_never_logged(self):
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        with mock.patch.object(provision, "logger") as log:
            res = provision.provision_pos_account(object(), email="new@example.com")
        pw = res["initial_password"]
        # 扫描所有 logger 调用参数:任何一条都不得包含明文初始密码
        for call in log.mock_calls:
            for arg in call.args:
                self.assertNotIn(pw, str(arg))


class AccountProvisionDalTests(unittest.TestCase):
    """services/auth/account_provision 事务级 DAL:建号 SQL 形状 + 参数化。"""

    class _Cur:
        def __init__(self, ret):
            self.ret = ret
            self.sql = None
            self.params = None

        def execute(self, sql, params=None):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return self.ret

    def test_create_owner_login_user_shape(self):
        cur = self._Cur({"id": "uid-1"})
        uid = account_provision.create_owner_login_user(
            cur, email="a@b.com", email_norm="a@b.com", password_hash="hash:x"
        )
        self.assertEqual(uid, "uid-1")
        self.assertIn("INSERT INTO users", cur.sql)
        self.assertIn("'owner'", cur.sql)  # 建的是 owner
        # 值全参数化(密码哈希不拼进 SQL 结构)
        self.assertIn("hash:x", cur.params)
        self.assertNotIn("hash:x", cur.sql)

    def test_find_login_user_three_way_lookup(self):
        cur = self._Cur({"id": "u", "tenant_id": "t", "username": "a@b.com"})
        row = account_provision.find_login_user(cur, "a@b.com")
        self.assertEqual(row["tenant_id"], "t")
        # 三路查:email / email_normalized / username 都在
        self.assertIn("email_normalized", cur.sql)
        self.assertIn("username", cur.sql)
        self.assertEqual(cur.params, ("a@b.com", "a@b.com", "a@b.com"))


if __name__ == "__main__":
    unittest.main()
