# -*- coding: utf-8 -*-
"""services/pos/provision 发放账号一条龙 + 发放制账号重置密码契约(PS-5 · 不连库 · 打桩 DB 层)。

覆盖验收:①新账号(用户名或邮箱)→ 建号 + 建租户 + grant 一条龙 + 回显初始密码;②已存在
账号 → 走既有租户开通路(不建号 · 不碰凭据 · 不回显密码);③随机初始密码满足强度(≥8 ·
含字母和数字)且【绝不落日志】;④非法账号标识早拒不碰 DB;⑤自定义密码原样生效(超管口
不设强度闸 · 留空随机);⑥重置严格限发放制账号(租户持 pos_entitlement + 成员归属),主站普通
用户/超管/不存在账号一律 not_in_scope(路由翻 404 防枚举)。"""

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
            object(), account="Shop@Example.com", tenant_name="ร้านทดสอบ", granted_by="earn"
        )
        find.assert_called_once()
        self.create.assert_called_once()
        self.ensure.assert_called_once()
        self.grant.assert_called_once()
        self.assertFalse(res["existed"])
        self.assertEqual(res["tenant_id"], "tid-new")
        self.assertEqual(res["grant_code"], "POS-ABCD-2345")
        # 邮箱账号:username 存全邮箱(小写)· email/email_norm 一并落库
        self.assertEqual(self.create.call_args.kwargs["username"], "shop@example.com")
        self.assertEqual(self.create.call_args.kwargs["email"], "shop@example.com")
        # 一次性初始密码:非空 · 满足强度
        pw = res["initial_password"]
        self.assertTrue(pw and any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw))
        # 密码明文进哈希、grant 落在新租户上
        self.hash.assert_called_once_with(pw)
        self.assertEqual(self.grant.call_args.kwargs["tenant_id"], "tid-new")

    def test_new_username_builds_account_no_email(self):
        # 核心验收:纯用户名(无邮箱)也能走通建号一条龙 · username 归一小写 · email 留空。
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        res = provision.provision_pos_account(object(), account="Skin", granted_by="earn")
        self.create.assert_called_once()
        self.assertEqual(self.create.call_args.kwargs["username"], "skin")
        self.assertIsNone(self.create.call_args.kwargs["email"])
        self.assertIsNone(self.create.call_args.kwargs["email_norm"])
        self.assertFalse(res["existed"])
        self.assertEqual(res["username"], "skin")
        pw = res["initial_password"]
        self.assertTrue(pw and any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw))

    def test_existing_email_uses_existing_tenant_no_password(self):
        mock.patch.object(
            provision,
            "find_login_user",
            return_value={"id": "uid-old", "tenant_id": "tid-old", "username": "old"},
        ).start()
        res = provision.provision_pos_account(object(), account="old@example.com")
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
        res = provision.provision_pos_account(object(), account="orphan@example.com")
        self.ensure.assert_called_once()  # orphan 补建租户
        self.create.assert_not_called()  # 但不重建账号
        self.assertTrue(res["existed"])
        self.assertIsNone(res["initial_password"])

    def test_invalid_identifier_rejected_before_db(self):
        find = mock.patch.object(provision, "find_login_user").start()
        # 空/空白 → account_missing;坏邮箱形态 → email_invalid;坏用户名 → username_invalid。
        cases = (
            ("", "account_missing"),
            ("   ", "account_missing"),
            ("no@domain", "email_invalid"),
            ("@example.com", "email_invalid"),
            ("ab", "username_invalid"),  # 太短(<3)
            ("a b c", "username_invalid"),  # 含空格
            ("x" * 65, "username_invalid"),  # 超长(>64)
        )
        for bad, code in cases:
            with self.assertRaises(ValueError) as e:
                provision.provision_pos_account(object(), account=bad)
            self.assertEqual(str(e.exception), code, bad)
        find.assert_not_called()

    def test_initial_password_never_logged(self):
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        with mock.patch.object(provision, "logger") as log:
            res = provision.provision_pos_account(object(), account="new@example.com")
        pw = res["initial_password"]
        # 扫描所有 logger 调用参数:任何一条都不得包含明文初始密码
        for call in log.mock_calls:
            for arg in call.args:
                self.assertNotIn(pw, str(arg))

    def test_custom_password_used_when_valid(self):
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        res = provision.provision_pos_account(
            object(), account="new@example.com", password="Custom1234"
        )
        # 自定义密码生效:回显它 + 哈希它
        self.assertEqual(res["initial_password"], "Custom1234")
        self.hash.assert_called_once_with("Custom1234")

    def test_custom_password_any_value_accepted(self):
        # 超管口不设强度闸:短/纯字母/纯数字都原样生效。
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        for pw in ("Ab1", "onlyletters", "12345678"):
            res = provision.provision_pos_account(object(), account="new@example.com", password=pw)
            self.assertEqual(res["initial_password"], pw)

    def test_blank_password_falls_back_to_random(self):
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        res = provision.provision_pos_account(object(), account="new@example.com", password=None)
        pw = res["initial_password"]
        self.assertTrue(pw and len(pw) >= 8)
        self.assertNotEqual(pw, "")

    def test_existing_email_never_touches_credentials(self):
        # 安全自查①:已存在账号分支不改动该账号任何凭据(不哈希 · 不写 password)。
        mock.patch.object(
            provision,
            "find_login_user",
            return_value={"id": "uid-old", "tenant_id": "tid-old", "username": "old"},
        ).start()
        write = mock.patch.object(provision, "write_login_password").start()
        provision.provision_pos_account(object(), account="old@example.com", password="Custom1234")
        self.hash.assert_not_called()
        write.assert_not_called()
        self.create.assert_not_called()

    def test_new_account_lands_only_in_fresh_tenant(self):
        # 安全自查①:建号路径的租户来自 _ensure_tenant_for_new_user(为该新 user 新建),
        # 不存在把新用户挂进他人已存在租户的入参路径。
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        provision.provision_pos_account(object(), account="new@example.com")
        args, kwargs = self.ensure.call_args
        self.assertEqual(args[1], "uid-new")  # 建租户绑的是刚建的新账号


class ResetPosAccountPasswordTests(unittest.TestCase):
    """发放制账号重置密码:范围闸(租户持 pos_entitlement + 成员归属)+ 密码三分支 + 不落日志。"""

    def setUp(self):
        self.hash = mock.patch.object(
            provision, "_hash_password", side_effect=lambda p: "hash:" + p
        ).start()
        self.write = mock.patch.object(provision, "write_login_password").start()
        self.ent = mock.patch.object(
            provision.ent, "get_for_tenant", return_value={"status": "active"}
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _user(self, **over):
        row = {"id": "uid-1", "tenant_id": "tid-1", "username": "u", "is_super_admin": False}
        row.update(over)
        return mock.patch.object(provision, "find_login_user", return_value=row).start()

    def test_entitled_member_reset_ok_random(self):
        self._user()
        res = provision.reset_pos_account_password(object(), account="shop@example.com")
        pw = res["new_password"]
        self.assertTrue(pw and len(pw) >= 8)
        self.hash.assert_called_once_with(pw)
        self.write.assert_called_once()
        self.assertEqual(self.write.call_args.kwargs["user_id"], "uid-1")
        # 范围判定真查了该租户的 entitlement(任意 status)
        self.assertEqual(self.ent.call_args.kwargs["tenant_id"], "tid-1")
        self.assertFalse(self.ent.call_args.kwargs["active_only"])

    def test_username_account_reset_ok(self):
        # 纯用户名账号也可重置(与发放同口径 · 范围闸不变)。
        u = self._user(username="skin")
        res = provision.reset_pos_account_password(object(), account="Skin")
        # find_login_user 收到的是归一小写用户名(lower(username) 命中)
        self.assertEqual(u.call_args.args[1], "skin")
        self.assertEqual(res["account"], "skin")
        self.write.assert_called_once()

    def test_custom_password_three_branches(self):
        self._user()
        # ①过校验用它
        res = provision.reset_pos_account_password(
            object(), account="shop@example.com", password="Custom1234"
        )
        self.assertEqual(res["new_password"], "Custom1234")
        # ②超管口不设强度闸:短/纯字母也原样生效
        for pw in ("Ab1", "onlyletters"):
            res_weak = provision.reset_pos_account_password(
                object(), account="shop@example.com", password=pw
            )
            self.assertEqual(res_weak["new_password"], pw)
        # ③留空走随机
        res2 = provision.reset_pos_account_password(
            object(), account="shop@example.com", password=None
        )
        self.assertNotEqual(res2["new_password"], "Custom1234")
        self.assertGreaterEqual(len(res2["new_password"]), 8)

    def test_out_of_scope_plain_user_without_entitlement(self):
        # 安全自查③:主站自由注册用户(租户无 pos_entitlement)→ not_in_scope(路由 404)。
        self._user()
        self.ent.return_value = None
        with self.assertRaises(ValueError) as e:
            provision.reset_pos_account_password(object(), account="free@example.com")
        self.assertEqual(str(e.exception), "not_in_scope")
        self.write.assert_not_called()

    def test_out_of_scope_super_admin(self):
        # 安全自查③:超管账号一律拒(即便其租户有授权也不许 · 防锁死+防提权)。
        self._user(is_super_admin=True)
        with self.assertRaises(ValueError) as e:
            provision.reset_pos_account_password(object(), account="admin@example.com")
        self.assertEqual(str(e.exception), "not_in_scope")
        self.write.assert_not_called()

    def test_out_of_scope_unknown_account(self):
        # 安全自查③:不存在账号 → 同一个 not_in_scope(不区分缘由 · 防枚举)。
        mock.patch.object(provision, "find_login_user", return_value=None).start()
        with self.assertRaises(ValueError) as e:
            provision.reset_pos_account_password(object(), account="ghost@example.com")
        self.assertEqual(str(e.exception), "not_in_scope")
        self.write.assert_not_called()

    def test_out_of_scope_malformed_identifier(self):
        # 安全自查③:标识非法(空/带空格)与查无此账号同归 not_in_scope(不泄露差异 · 防枚举)。
        find = mock.patch.object(provision, "find_login_user").start()
        for bad in ("", "  ", "a b"):
            with self.assertRaises(ValueError) as e:
                provision.reset_pos_account_password(object(), account=bad)
            self.assertEqual(str(e.exception), "not_in_scope")
        find.assert_not_called()

    def test_out_of_scope_tenantless_user(self):
        self._user(tenant_id=None)
        with self.assertRaises(ValueError) as e:
            provision.reset_pos_account_password(object(), account="orphan@example.com")
        self.assertEqual(str(e.exception), "not_in_scope")
        self.write.assert_not_called()

    def test_reset_password_never_logged(self):
        # 安全自查④:重置流明文密码绝不进日志。
        self._user()
        with mock.patch.object(provision, "logger") as log:
            res = provision.reset_pos_account_password(object(), account="shop@example.com")
        pw = res["new_password"]
        for call in log.mock_calls:
            for arg in call.args:
                self.assertNotIn(pw, str(arg))
        # 低层写入只收哈希不收明文
        self.assertEqual(self.write.call_args.kwargs["password_hash"], "hash:" + pw)


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
            cur, username="a@b.com", email="a@b.com", email_norm="a@b.com", password_hash="hash:x"
        )
        self.assertEqual(uid, "uid-1")
        self.assertIn("INSERT INTO users", cur.sql)
        self.assertIn("'owner'", cur.sql)  # 建的是 owner
        # 值全参数化(密码哈希不拼进 SQL 结构)
        self.assertIn("hash:x", cur.params)
        self.assertNotIn("hash:x", cur.sql)

    def test_create_owner_login_user_username_only(self):
        # 纯用户名账号:email/email_norm 为 None(邮箱非必填),username 仍入库。
        cur = self._Cur({"id": "uid-2"})
        uid = account_provision.create_owner_login_user(
            cur, username="skin", password_hash="hash:y"
        )
        self.assertEqual(uid, "uid-2")
        self.assertIn("skin", cur.params)
        self.assertIn(None, cur.params)  # email / email_norm 落 NULL

    def test_validate_username_policy(self):
        for bad in ("", "ab", "a b", "has space", "x" * 65, "line\ttab"):
            with self.assertRaises(ValueError):
                account_provision.validate_username(bad)
        for ok in ("skin", "shop_01", "ร้านทดสอบ", "a" * 64, "user.name-9"):
            account_provision.validate_username(ok)  # 合格不抛

    def test_resolve_account_identifier_email_branch(self):
        ident = account_provision.resolve_account_identifier("  Shop@Example.COM ")
        self.assertTrue(ident["is_email"])
        self.assertEqual(ident["username"], "shop@example.com")  # 存全邮箱(小写)
        self.assertEqual(ident["email"], "shop@example.com")
        self.assertEqual(ident["lookup_key"], ident["email_norm"])

    def test_resolve_account_identifier_username_branch(self):
        ident = account_provision.resolve_account_identifier("Skin")
        self.assertFalse(ident["is_email"])
        self.assertEqual(ident["username"], "skin")  # 大小写不敏感 → 归一小写
        self.assertIsNone(ident["email"])
        self.assertIsNone(ident["email_norm"])
        self.assertEqual(ident["lookup_key"], "skin")

    def test_resolve_account_identifier_rejects_bad(self):
        for bad, code in (
            ("", "account_missing"),
            ("no@domain", "email_invalid"),
            ("@example.com", "email_invalid"),
            ("ab", "username_invalid"),
        ):
            with self.assertRaises(ValueError) as e:
                account_provision.resolve_account_identifier(bad)
            self.assertEqual(str(e.exception), code, bad)

    def test_find_login_user_three_way_lookup(self):
        cur = self._Cur({"id": "u", "tenant_id": "t", "username": "a@b.com"})
        row = account_provision.find_login_user(cur, "a@b.com")
        self.assertEqual(row["tenant_id"], "t")
        # 三路查:email / email_normalized / username 都在,并带 is_super_admin(重置范围闸用)
        self.assertIn("email_normalized", cur.sql)
        self.assertIn("username", cur.sql)
        self.assertIn("is_super_admin", cur.sql)
        self.assertEqual(cur.params, ("a@b.com", "a@b.com", "a@b.com"))

    def test_write_login_password_single_account_scoped(self):
        # 安全自查②:低层改密 UPDATE 精确 WHERE id=该账号,且只收哈希不收明文。
        cur = self._Cur(None)
        account_provision.write_login_password(cur, user_id="uid-9", password_hash="hash:z")
        self.assertIn("UPDATE users SET password_hash", cur.sql)
        self.assertIn("WHERE id = %s", cur.sql)
        self.assertEqual(cur.params, ("hash:z", "uid-9"))

    def test_resolve_password_passthrough_and_random_fallback(self):
        # 超管口不设强度闸:自定义原样透传;留空才生成强随机(≥8 · 字母+数字)。
        for pw in ("Ab1", "onlyletters", "12345678"):
            self.assertEqual(account_provision.resolve_password(pw), pw)
        generated = account_provision.resolve_password(None)
        self.assertGreaterEqual(len(generated), 8)
        self.assertTrue(any(c.isalpha() for c in generated))
        self.assertTrue(any(c.isdigit() for c in generated))


if __name__ == "__main__":
    unittest.main()
