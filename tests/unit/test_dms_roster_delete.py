# -*- coding: utf-8 -*-
"""操作员删除契约(波3 · DL-8)· 无 DATABASE_URL(mock db/store/line_dms)。

覆盖(service 层):成功链路各步调用齐(解绑→作废码→禁 endpoint→删档案→置停用)、
跨租户 {user_id} 拒、endpoint 软禁失败如实返错不装成功、无 endpoint 跳过禁连仍成功。
覆盖(store 层 · FakeCursor):删档案 SQL 严格限定 tenant+user、停用用户 SQL 限定
role='member'(member 行保留不删)。
"""

import os
import unittest
from unittest import mock

from cryptography.fernet import Fernet

os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from services.dms_roster import service  # noqa: E402
from services.dms_roster import store  # noqa: E402

OWNER = {"id": "owner-1", "tenant_id": "tenant-1", "company_name": "Acme", "role": "owner"}
_PROF = {"user_id": "op-1", "tenant_id": "tenant-1", "status": "active"}
_EP = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": True, "config": {}}


class _FakeCur:
    def __init__(self, rowcount=1):
        self.calls = []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _FakeCtx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class DeleteOperatorServiceTest(unittest.TestCase):
    def test_success_chain_calls_all_steps(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value=dict(_PROF)),
            mock.patch("core.db.list_erp_endpoints", return_value=[dict(_EP)]),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=True) as unbind,
            mock.patch("services.line_dms.store.void_bind_codes_for_user", return_value=True) as void,
            mock.patch("core.db.update_erp_endpoint", return_value=True) as up,
            mock.patch.object(service.store, "delete_operator_profile", return_value=True) as dp,
            mock.patch.object(service.store, "disable_operator_user", return_value=True) as du,
        ):
            res = service.delete_operator(OWNER, "op-1")
        self.assertTrue(res.get("ok"))
        unbind.assert_called_once_with("op-1")
        void.assert_called_once_with("op-1")  # 在外流通的未用绑定码随删除即刻失效
        self.assertIs(up.call_args.kwargs["enabled"], False)
        dp.assert_called_once_with(tenant_id="tenant-1", user_id="op-1")
        du.assert_called_once_with(tenant_id="tenant-1", user_id="op-1")

    def test_cross_tenant_user_rejected(self):
        with mock.patch.object(service.store, "get_profile", return_value=None) as gp:
            res = service.delete_operator(OWNER, "foreign-user")
        self.assertEqual(res.get("error"), "dms_roster.not_found")
        gp.assert_called_once_with("tenant-1", "foreign-user")

    def test_endpoint_disable_failure_not_ok(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value=dict(_PROF)),
            mock.patch("core.db.list_erp_endpoints", return_value=[dict(_EP)]),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=True),
            mock.patch("services.line_dms.store.void_bind_codes_for_user", return_value=True),
            mock.patch("core.db.update_erp_endpoint", return_value=False),
            mock.patch.object(service.store, "delete_operator_profile") as dp,
            mock.patch.object(service.store, "disable_operator_user") as du,
        ):
            res = service.delete_operator(OWNER, "op-1")
        self.assertEqual(res.get("error"), "dms_roster.endpoint_update_failed")
        dp.assert_not_called()  # 收权没落地就不动档案,绝不显示假删除
        du.assert_not_called()

    def test_unbind_failure_not_ok(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value=dict(_PROF)),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=False),
            mock.patch("services.line_dms.store.void_bind_codes_for_user") as void,
            mock.patch.object(service.store, "delete_operator_profile") as dp,
        ):
            res = service.delete_operator(OWNER, "op-1")
        self.assertEqual(res.get("error"), "dms_roster.delete_failed")
        void.assert_not_called()
        dp.assert_not_called()

    def test_void_codes_failure_not_ok(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value=dict(_PROF)),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=True),
            mock.patch("services.line_dms.store.void_bind_codes_for_user", return_value=False),
            mock.patch("core.db.update_erp_endpoint") as up,
            mock.patch.object(service.store, "delete_operator_profile") as dp,
        ):
            res = service.delete_operator(OWNER, "op-1")
        self.assertEqual(res.get("error"), "dms_roster.delete_failed")
        up.assert_not_called()  # 作废码没落地就不动 endpoint/档案
        dp.assert_not_called()

    def test_no_endpoint_skips_disable_still_ok(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value=dict(_PROF)),
            mock.patch("core.db.list_erp_endpoints", return_value=[]),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=True),
            mock.patch("services.line_dms.store.void_bind_codes_for_user", return_value=True),
            mock.patch("core.db.update_erp_endpoint") as up,
            mock.patch.object(service.store, "delete_operator_profile", return_value=True),
            mock.patch.object(service.store, "disable_operator_user", return_value=True),
        ):
            res = service.delete_operator(OWNER, "op-1")
        self.assertTrue(res.get("ok"))
        up.assert_not_called()  # 无 endpoint 就不动 db,不是空成功也不是假失败


class DeleteOperatorStoreTest(unittest.TestCase):
    def test_delete_profile_scoped_to_tenant_and_user(self):
        cur = _FakeCur()
        with mock.patch("core.db.get_cursor", return_value=_FakeCtx(cur)):
            self.assertTrue(store.delete_operator_profile(tenant_id="t1", user_id="u1"))
        sql, params = cur.calls[0]
        self.assertIn("DELETE FROM dms_operator_profiles", sql)
        self.assertEqual(params, ("t1", "u1"))

    def test_disable_user_only_member_row(self):
        cur = _FakeCur()
        with mock.patch("core.db.get_cursor", return_value=_FakeCtx(cur)):
            self.assertTrue(store.disable_operator_user(tenant_id="t1", user_id="u1"))
        sql, params = cur.calls[0]
        self.assertIn("UPDATE users SET is_active = FALSE", sql)
        self.assertIn("role = 'member'", sql)  # 只置停用不删行 · 且只锁 member
        self.assertEqual(params, ("u1", "t1"))


if __name__ == "__main__":
    unittest.main()
