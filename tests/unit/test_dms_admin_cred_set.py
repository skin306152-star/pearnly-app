# -*- coding: utf-8 -*-
"""双凭据分权(admin/user 凭据组)守门(A3/A4)。

客户档写操作(save_customer 建/改)在配了 admin 时走 admin 会话;没配 admin 则
与现状逐字节一致(不进 admin 分支)。用打了身份标签的假 transport 断言写请求落在
哪个会话上——即"所用登录身份"。
"""

import unittest

from services.erp import erp_dms_push
from services.erp.mrerp_dms_client import DMSClient


class _Resp:
    def __init__(self, text="", status=200):
        self.status_code = status
        self.text = text
        self.content = text.encode()


_EDIT_FORM = """
<form>
  <select name="selprefix"><option value="17" selected>นาย</option></select>
  <input name="txtcusname" value="New Cust">
  <input name="txtpeopleid" value="1101700207366">
  <input name="txttel" value="0811111111">
  <input name="txthousenum" value="">
  <select name="selprovinces"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts"><option value="804" selected>คลองท่อม</option></select>
  <select name="selsubdistricts"><option value="6472" selected>x</option></select>
  <select name="selzipcodes"><option value="6477" selected>81120</option></select>
</form>
"""

_OVERWRITE_FIELDS = {
    "name": "New Cust",
    "people_id": "1101700207366",
    "province_id": "65",
    "district_id": "804",
    "subdistrict_id": "6472",
    "zipcode_id": "6477",
}


class _TaggedTransport:
    """带身份标签的假 transport:记录所有 POST,给客户建/改流程一条可成功的回路。"""

    def __init__(self, identity):
        self.identity = identity
        self.posts = []

    def get(self, url, timeout_ms=None):
        return _Resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.posts.append((url, dict(data or {})))
        if url.endswith("cus/form.php"):
            return _Resp(_EDIT_FORM)
        if url.endswith("cus/component/showdata.php"):
            return _Resp('<a data-val="95">row</a>')
        return _Resp("")  # new.php / edit.php 无 err:: = 成功

    def wrote_edit(self):
        return [p for p in self.posts if p[0].endswith("cus/edit.php")]


class AdminCredSetRoutingTests(unittest.TestCase):
    def test_no_admin_uses_current_session_no_admin_branch(self):
        """A3:未配 admin → 不进 admin 分支,写走当前(用户)会话。"""
        user_t = _TaggedTransport("user")
        c = DMSClient(user_t, "https://x/dms/")
        self.assertIsNone(c._resolve_admin_transport())  # 无 admin 凭据组
        cid = c.save_customer(fields=_OVERWRITE_FIELDS, mode="overwrite", customer_id="95")
        self.assertEqual(cid, "95")
        self.assertTrue(user_t.wrote_edit())  # 写落在用户会话(现状路径)

    def test_admin_configured_overwrite_uses_admin_session(self):
        """A4:配了 admin → save_customer(overwrite) 全程走 admin 会话,用户会话一次没碰。"""
        user_t = _TaggedTransport("user")
        admin_t = _TaggedTransport("admin")
        c = DMSClient(user_t, "https://x/dms/", admin_transport=admin_t)
        cid = c.save_customer(fields=_OVERWRITE_FIELDS, mode="overwrite", customer_id="95")
        self.assertEqual(cid, "95")
        self.assertTrue(admin_t.wrote_edit(), "写请求应落在 admin 会话")
        self.assertEqual(user_t.posts, [], "用户(读)会话不应承担写操作")

    def test_admin_transport_factory_resolved_once(self):
        """生产侧 admin_transport 是零参工厂(懒登录);只解析一次。"""
        admin_t = _TaggedTransport("admin")
        calls = {"n": 0}

        def factory():
            calls["n"] += 1
            return admin_t

        c = DMSClient(_TaggedTransport("user"), "https://x/dms/", admin_transport=factory)
        c.save_customer(fields=_OVERWRITE_FIELDS, mode="overwrite", customer_id="95")
        self.assertEqual(calls["n"], 1)  # 整段写流程内工厂只调一次
        self.assertTrue(admin_t.wrote_edit())


class AdminCredsBuilderTests(unittest.TestCase):
    def test_no_admin_cfg_yields_empty_kwargs(self):
        self.assertEqual(erp_dms_push._dms_admin_kwargs({}), {})
        self.assertEqual(erp_dms_push._dms_admin_kwargs({"username": "u", "password": "p"}), {})

    def test_plain_admin_cfg_yields_plaintext_kwargs(self):
        kw = erp_dms_push._dms_admin_kwargs({"admin_username": "boss", "admin_password": "s3cret"})
        self.assertEqual(kw, {"admin_username": "boss", "admin_password": "s3cret"})

    def test_partial_admin_cfg_is_ignored(self):
        # 只给一半 admin 凭据 = 不成组,视为未配。
        self.assertEqual(erp_dms_push._dms_admin_kwargs({"admin_username": "boss"}), {})


if __name__ == "__main__":
    unittest.main()
