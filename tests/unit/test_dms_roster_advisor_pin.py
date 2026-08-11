# -*- coding: utf-8 -*-
"""销售顾问归属钉死契约(花名册例外通道)· 无 DATABASE_URL(mock db/masters 缓存)。

覆盖:顾问下拉选项(有端点 / 无端点 / 取数失败 · tel 不外漏)、建号即钉、编辑改钉、
空串清钉且不误伤 booking_defaults 里的别的键、name 一律服务端按 id 解(不信客户端)、
id 不在名册 → invalid_advisor、列表带归属列(service 映射 + store SQL 取值)。
"""

import json
import os
import unittest
from unittest import mock

from cryptography.fernet import Fernet

os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from services.dms_roster import advisors, service, store  # noqa: E402

OWNER = {"id": "owner-1", "tenant_id": "tenant-1", "company_name": "Acme", "role": "owner"}
_OWNER_EP = {
    "id": "ep-owner",
    "adapter": "mrerp_dms",
    "enabled": True,
    "config": {"system_url": "https://dms.example.com"},
}
_OP_EP = {
    "id": "ep-op",
    "adapter": "mrerp_dms",
    "enabled": True,
    "config": {
        "system_url": "https://dms.example.com",
        "booking_defaults": {"booking_prefix": "BK", "advisor_id": "7", "advisor_name": "旧名字"},
    },
}
# DMS 顾问下拉行形 [id, code, name, tel]
_MASTERS = {"advisors": [["7", "S07", "สมชาย", "0812345678"], ["9", "S09", "阿明", "0899999999"]]}


def _endpoints_by_user(owner_eps=(_OWNER_EP,), op_eps=(_OP_EP,)):
    """core.db.list_erp_endpoints 的 side_effect:老板与操作员各拿各的端点。"""

    def _run(user_id):
        return list(owner_eps) if str(user_id) == "owner-1" else list(op_eps)

    return _run


class AdvisorOptionsTest(unittest.TestCase):
    def test_options_expose_id_code_name_only(self):
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=_MASTERS),
        ):
            res = service.list_advisors(OWNER)
        self.assertTrue(res["ok"])
        self.assertEqual(
            res["advisors"],
            [
                {"id": "7", "code": "S07", "name": "สมชาย"},
                {"id": "9", "code": "S09", "name": "阿明"},
            ],
        )
        # tel 是员工私人号码,下拉用不上 → 一个字节都不该出现在响应里。
        self.assertNotIn("0812345678", json.dumps(res, ensure_ascii=False))

    def test_no_owner_endpoint_reports_code_not_empty_list(self):
        with mock.patch("core.db.list_erp_endpoints", return_value=[]):
            res = service.list_advisors(OWNER)
        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], "no_endpoint")

    def test_fetch_failure_is_not_an_empty_roster(self):
        # 冷缓存 + 登录抓失败 → get_masters 软回退成空 dict;这里必须报取数失败,
        # 冒充「名册里没人」会让老板以为 DMS 里真没顾问。
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=None),
            mock.patch("services.erp.dms_masters_cache.get_masters", return_value={}),
        ):
            res = service.list_advisors(OWNER)
        self.assertFalse(res["ok"])
        self.assertEqual(res["code"], "fetch_failed")

    def test_empty_roster_is_ok_with_empty_list(self):
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch(
                "services.erp.dms_masters_cache.read_fresh_masters", return_value={"advisors": []}
            ),
        ):
            res = service.list_advisors(OWNER)
        self.assertTrue(res["ok"])
        self.assertEqual(res["advisors"], [])


class CreateWithPinTest(unittest.TestCase):
    def test_create_pins_advisor_with_server_resolved_name(self):
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=_MASTERS),
            mock.patch.object(service.store, "create_operator_records", return_value="op-9"),
            mock.patch("core.db.create_erp_endpoint", return_value="ep-9") as ep,
        ):
            res = service.create_operator(
                OWNER,
                display_name="x",
                dms_username="u",
                dms_password="p",
                dms_role="sales",
                dms_advisor_id="9",
            )
        self.assertTrue(res.get("ok"))
        cfg = ep.call_args.args[3]
        self.assertEqual(cfg["booking_defaults"], {"advisor_id": "9", "advisor_name": "阿明"})

    def test_create_without_advisor_writes_no_booking_defaults(self):
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch.object(service.store, "create_operator_records", return_value="op-9"),
            mock.patch("core.db.create_erp_endpoint", return_value="ep-9") as ep,
        ):
            service.create_operator(
                OWNER, display_name="x", dms_username="u", dms_password="p", dms_role="sales"
            )
        self.assertNotIn("booking_defaults", ep.call_args.args[3])

    def test_unknown_advisor_id_rejected_before_any_write(self):
        with (
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=_MASTERS),
            mock.patch.object(service.store, "create_operator_records") as rec,
            mock.patch("core.db.create_erp_endpoint") as ep,
        ):
            res = service.create_operator(
                OWNER,
                display_name="x",
                dms_username="u",
                dms_password="p",
                dms_role="sales",
                dms_advisor_id="404",
            )
        self.assertEqual(res.get("error"), "dms_roster.invalid_advisor")
        rec.assert_not_called()
        ep.assert_not_called()


class UpdatePinTest(unittest.TestCase):
    def _update(self, **kw):
        with (
            mock.patch.object(
                service.store,
                "get_profile",
                return_value={"user_id": "op-1", "tenant_id": "tenant-1"},
            ),
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=_MASTERS),
            mock.patch("core.db.update_erp_endpoint", return_value=True) as up,
        ):
            res = service.update_operator(OWNER, "op-1", **kw)
        return res, up

    def test_repin_overwrites_stale_name_from_roster(self):
        res, up = self._update(dms_advisor_id="9")
        self.assertTrue(res.get("ok"))
        defaults = up.call_args.kwargs["config"]["booking_defaults"]
        self.assertEqual(defaults["advisor_id"], "9")
        self.assertEqual(defaults["advisor_name"], "阿明")  # 名字重解,不留库里的旧名字
        self.assertEqual(defaults["booking_prefix"], "BK")  # 同 dict 的别的键不许被吞

    def test_empty_string_clears_pin_and_keeps_other_defaults(self):
        res, up = self._update(dms_advisor_id="")
        self.assertTrue(res.get("ok"))
        defaults = up.call_args.kwargs["config"]["booking_defaults"]
        self.assertEqual(defaults, {"booking_prefix": "BK"})

    def test_absent_field_leaves_pin_untouched(self):
        res, up = self._update(dms_password="newpw")
        self.assertTrue(res.get("ok"))
        defaults = up.call_args.kwargs["config"]["booking_defaults"]
        self.assertEqual(defaults["advisor_id"], "7")
        self.assertEqual(defaults["advisor_name"], "旧名字")

    def test_unknown_id_rejected_before_profile_write(self):
        with (
            mock.patch.object(
                service.store,
                "get_profile",
                return_value={"user_id": "op-1", "tenant_id": "tenant-1"},
            ),
            mock.patch("core.db.list_erp_endpoints", side_effect=_endpoints_by_user()),
            mock.patch("services.erp.dms_masters_cache.read_fresh_masters", return_value=_MASTERS),
            mock.patch.object(service.store, "update_profile") as upp,
            mock.patch("core.db.update_erp_endpoint") as up,
        ):
            res = service.update_operator(OWNER, "op-1", display_name="New", dms_advisor_id="404")
        self.assertEqual(res.get("error"), "dms_roster.invalid_advisor")
        upp.assert_not_called()
        up.assert_not_called()


class MergeIntoConfigTest(unittest.TestCase):
    def test_drops_empty_booking_defaults_key(self):
        cfg = advisors.merge_into_config({"booking_defaults": {"advisor_id": "7"}}, None)
        self.assertNotIn("booking_defaults", cfg)

    def test_does_not_mutate_caller_config(self):
        src = {"booking_defaults": {"booking_prefix": "BK"}}
        advisors.merge_into_config(src, {"id": "9", "name": "阿明"})
        self.assertEqual(src["booking_defaults"], {"booking_prefix": "BK"})


class ListShowsAttributionTest(unittest.TestCase):
    def test_list_operators_maps_advisor_columns(self):
        row = {
            "user_id": "op-1",
            "display_name": "สมชาย",
            "dms_role": "sales",
            "status": "active",
            "username": "dmsop-abcd1234",
            "advisor_id": "9",
            "advisor_name": "阿明",
        }
        with mock.patch.object(service.store, "list_profiles", return_value=[row]):
            item = service.list_operators(OWNER)["items"][0]
        self.assertEqual(item["advisor_id"], "9")
        self.assertEqual(item["advisor_name"], "阿明")

    def test_list_operators_defaults_to_empty_when_not_pinned(self):
        with mock.patch.object(service.store, "list_profiles", return_value=[{"user_id": "op-1"}]):
            item = service.list_operators(OWNER)["items"][0]
        self.assertEqual(item["advisor_name"], "")

    def test_store_sql_reads_pin_from_endpoint_config(self):
        class _Cur:
            def __init__(self):
                self.sql = ""

            def execute(self, sql, params=None):
                self.sql = sql

            def fetchall(self):
                return []

        class _Ctx:
            def __init__(self, cur):
                self.cur = cur

            def __enter__(self):
                return self.cur

            def __exit__(self, *a):
                return False

        cur = _Cur()
        with mock.patch("core.db.get_cursor", return_value=_Ctx(cur)):
            store.list_profiles("tenant-1")
        self.assertIn("'booking_defaults' ->> 'advisor_name'", cur.sql)
        self.assertIn("'booking_defaults' ->> 'advisor_id'", cur.sql)


if __name__ == "__main__":
    unittest.main()
