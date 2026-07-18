# -*- coding: utf-8 -*-
"""操作员花名册编排契约(波3 · DL-8)· 无 DATABASE_URL(mock db/store/line_dms)。

覆盖:建操作员全链(用户+档案+加密 endpoint)、凭据入库为密文(gAAAAA)、不写 admin_ 键、
无 endpoint 模板→no_endpoint、endpoint 建失败补偿清理、跨租户 {user_id} 拒(get_profile 按
owner tenant 收敛)、停用=endpoint 禁+解绑、列表四态字段映射。
"""

import os
import unittest
from unittest import mock

from cryptography.fernet import Fernet

os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from services.dms_roster import service  # noqa: E402

OWNER = {"id": "owner-1", "tenant_id": "tenant-1", "company_name": "Acme", "role": "owner"}
_TEMPLATE = {
    "adapter": "mrerp_dms",
    "enabled": True,
    "config": {"system_url": "https://dms.example.com", "id_card_auto_push": True},
}


class CreateOperatorTest(unittest.TestCase):
    def test_full_chain_encrypts_creds_no_admin_keys(self):
        with (
            mock.patch("core.db.list_erp_endpoints", return_value=[_TEMPLATE]),
            mock.patch.object(service.store, "create_operator_records", return_value="op-9") as rec,
            mock.patch("core.db.create_erp_endpoint", return_value="ep-9") as ep,
        ):
            res = service.create_operator(
                OWNER,
                display_name="สมชาย",
                dms_username="salesuser",
                dms_password="pw-plain-123",
                dms_role="sales",
            )
        self.assertTrue(res.get("ok"))
        self.assertEqual(res["user_id"], "op-9")
        rec.assert_called_once()
        cfg = ep.call_args.args[3]
        self.assertTrue(cfg["username_enc"].startswith("gAAAAA"))
        self.assertTrue(cfg["password_enc"].startswith("gAAAAA"))
        self.assertNotIn("admin_username_enc", cfg)
        self.assertNotIn("admin_password_enc", cfg)
        self.assertEqual(cfg["system_url"], "https://dms.example.com")

    def test_no_owner_endpoint_template_blocks(self):
        with (
            mock.patch("core.db.list_erp_endpoints", return_value=[]),
            mock.patch.object(service.store, "create_operator_records") as rec,
        ):
            res = service.create_operator(
                OWNER, display_name="x", dms_username="u", dms_password="p", dms_role="sales"
            )
        self.assertEqual(res.get("error"), "dms_roster.no_endpoint")
        rec.assert_not_called()

    def test_invalid_role_rejected(self):
        res = service.create_operator(
            OWNER, display_name="x", dms_username="u", dms_password="p", dms_role="boss"
        )
        self.assertEqual(res.get("error"), "dms_roster.invalid_role")

    def test_endpoint_failure_compensates(self):
        with (
            mock.patch("core.db.list_erp_endpoints", return_value=[_TEMPLATE]),
            mock.patch.object(service.store, "create_operator_records", return_value="op-9"),
            mock.patch("core.db.create_erp_endpoint", return_value=None),
            mock.patch.object(service.store, "delete_operator_records") as delr,
        ):
            res = service.create_operator(
                OWNER, display_name="x", dms_username="u", dms_password="p", dms_role="admin"
            )
        self.assertEqual(res.get("error"), "dms_roster.endpoint_failed")
        delr.assert_called_once_with(tenant_id="tenant-1", user_id="op-9")


class MutateOperatorTest(unittest.TestCase):
    def test_cross_tenant_user_rejected(self):
        # get_profile 按 owner 的 tenant 收敛 → 外租户 user_id 查不到 → not_found。
        with mock.patch.object(service.store, "get_profile", return_value=None) as gp:
            res = service.set_status(OWNER, "foreign-user", "inactive")
        self.assertEqual(res.get("error"), "dms_roster.not_found")
        gp.assert_called_once_with("tenant-1", "foreign-user")

    def test_deactivate_disables_endpoint_and_unbinds_line(self):
        ep = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": True, "config": {}}
        with (
            mock.patch.object(
                service.store,
                "get_profile",
                return_value={"user_id": "op-1", "tenant_id": "tenant-1"},
            ),
            mock.patch("core.db.list_erp_endpoints", return_value=[ep]),
            mock.patch("core.db.update_erp_endpoint") as up,
            mock.patch("services.line_dms.store.unbind_by_user") as unbind,
            mock.patch.object(service.store, "set_profile_status", return_value=True) as sst,
        ):
            res = service.set_status(OWNER, "op-1", "inactive")
        self.assertTrue(res.get("ok"))
        self.assertIs(up.call_args.kwargs["enabled"], False)
        unbind.assert_called_once_with("op-1")
        sst.assert_called_once_with("tenant-1", "op-1", "inactive")

    def test_activate_enables_endpoint_no_unbind(self):
        ep = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": False, "config": {}}
        with (
            mock.patch.object(
                service.store,
                "get_profile",
                return_value={"user_id": "op-1", "tenant_id": "tenant-1"},
            ),
            mock.patch("core.db.list_erp_endpoints", return_value=[ep]),
            mock.patch("core.db.update_erp_endpoint") as up,
            mock.patch("services.line_dms.store.unbind_by_user") as unbind,
            mock.patch.object(service.store, "set_profile_status", return_value=True),
        ):
            res = service.set_status(OWNER, "op-1", "active")
        self.assertTrue(res.get("ok"))
        self.assertIs(up.call_args.kwargs["enabled"], True)
        unbind.assert_not_called()

    def test_update_reencrypts_creds(self):
        ep = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": True, "config": {"system_url": "u"}}
        with (
            mock.patch.object(
                service.store,
                "get_profile",
                return_value={"user_id": "op-1", "tenant_id": "tenant-1"},
            ),
            mock.patch.object(service.store, "update_profile") as upp,
            mock.patch("core.db.list_erp_endpoints", return_value=[ep]),
            mock.patch("core.db.update_erp_endpoint") as up,
        ):
            res = service.update_operator(OWNER, "op-1", display_name="New", dms_password="newpw")
        self.assertTrue(res.get("ok"))
        upp.assert_called_once()
        cfg = up.call_args.kwargs["config"]
        self.assertTrue(cfg["password_enc"].startswith("gAAAAA"))
        self.assertEqual(cfg["system_url"], "u")  # 既有配置保留

    def test_issue_bind_code_delegates_to_line_store(self):
        with (
            mock.patch.object(service.store, "get_profile", return_value={"user_id": "op-1"}),
            mock.patch(
                "services.line_dms.store.generate_bind_code",
                return_value={"code": "123456", "expires_at": "2026-07-19T00:00:00+00:00"},
            ),
        ):
            res = service.issue_bind_code(OWNER, "op-1")
        self.assertTrue(res.get("ok"))
        self.assertEqual(res["code"], "123456")


class ListOperatorsTest(unittest.TestCase):
    def test_maps_line_and_endpoint_state(self):
        class _Dt:
            def isoformat(self):
                return "2026-07-19T10:00:00+00:00"

        row = {
            "user_id": "op-1",
            "display_name": "สมชาย",
            "dms_role": "sales",
            "status": "active",
            "username": "dmsop-abcd1234",
            "line_name": "Somchai",
            "bound_at": _Dt(),
            "ep_enabled": True,
        }
        with mock.patch.object(service.store, "list_profiles", return_value=[row]):
            res = service.list_operators(OWNER)
        item = res["items"][0]
        self.assertTrue(item["line_bound"])
        self.assertTrue(item["endpoint_ready"])
        self.assertEqual(item["line_bound_at"], "2026-07-19T10:00:00+00:00")
        self.assertEqual(item["dms_role"], "sales")


if __name__ == "__main__":
    unittest.main()
