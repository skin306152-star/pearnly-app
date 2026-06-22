# -*- coding: utf-8 -*-
"""T2-A 账套白名单(云端·逐端点):只放行 == 端点配置 account_set;不等拒、缺失拒。"""
import json
import unittest
from unittest import mock

from services.erp.express_push import account_set_allowed, agent_store


def _ep(configured):
    return {"id": "ep1", "user_id": "u1", "config": {"account_set": configured}}


class PerEndpointWhitelist(unittest.TestCase):
    def test_matches_configured_account_set(self):
        self.assertTrue(account_set_allowed("58ASIASP", _ep("58ASIASP")))
        self.assertTrue(account_set_allowed("DATAT", _ep("DATAT")))

    def test_mismatch_rejected(self):
        ep = _ep("58ASIASP")
        self.assertFalse(account_set_allowed("DATAT", ep))  # 跨账套即拒
        self.assertFalse(account_set_allowed("OTHER", ep))

    def test_missing_payload_account_set_rejected(self):
        self.assertFalse(account_set_allowed("", _ep("DATAT")))
        self.assertFalse(account_set_allowed(None, _ep("DATAT")))

    def test_missing_endpoint_config_rejected(self):
        self.assertFalse(account_set_allowed("DATAT", _ep("")))  # 端点未配 account_set
        self.assertFalse(account_set_allowed("DATAT", {"config": {}}))
        self.assertFalse(account_set_allowed("DATAT", None))

    def test_whitespace_normalized(self):
        self.assertTrue(account_set_allowed("58ASIASP", _ep(" 58ASIASP ")))


class EnqueueGate(unittest.TestCase):
    def test_endpoint_without_account_set_goes_manual(self):
        from services.erp.express_push.enqueue import MANUAL_PREFIX, enqueue_express

        ep = {"id": "ep1", "user_id": "u1", "config": {"account_set": ""}}
        with mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "1"}):
            res = enqueue_express(ep, {"id": "h1"})
        self.assertFalse(res["success"])
        self.assertTrue(res["error_msg"].startswith(MANUAL_PREFIX))
        self.assertIn("account_set_not_allowed", res["error_msg"])

    def test_disabled_flag_short_circuits(self):
        from services.erp.express_push.enqueue import enqueue_express

        ep = _ep("DATAT")
        with mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "0"}):
            res = enqueue_express(ep, {"id": "h1"})
        self.assertFalse(res["success"])
        self.assertEqual(res["error_msg"], "ERR_EXPRESS_DISABLED")


class StoreSelectedAccount(unittest.TestCase):
    """heartbeat 上报所选账套【整组】→ 存 config(方法无关·直录/RPA 共用·可扩展性契约)。"""

    def test_missing_account_set_is_noop(self):
        self.assertFalse(agent_store.store_selected_account("ep1", {}))
        self.assertFalse(agent_store.store_selected_account("ep1", {"account_set": "  "}))
        self.assertFalse(agent_store.store_selected_account("ep1", {"account_dir": "x"}))  # 缺名

    def test_stores_whole_group(self):
        cur = mock.MagicMock()
        cm = mock.MagicMock()
        cm.__enter__.return_value = cur
        body = {
            "account_set": "DATAT", "account_dir": r"\\srv\70EXP\test",
            "account_company": "บริษัท X", "account_set_row": 2, "method": "dbf",
        }
        with mock.patch("core.db.get_cursor", return_value=cm):
            ok = agent_store.store_selected_account("ep1", body)
        self.assertTrue(ok)
        _sql, params = cur.execute.call_args[0]
        stored = json.loads(params[0])
        self.assertEqual(stored["account_set"], "DATAT")
        self.assertEqual(stored["account_dir"], r"\\srv\70EXP\test")
        self.assertEqual(stored["account_company"], "บริษัท X")
        self.assertEqual(stored["account_set_row"], 2)  # RPA 用 · 整组带出 · 零返工
        self.assertNotIn("method", stored)  # 只存账套整组,不混入别的字段
        self.assertEqual(params[1], "ep1")

    def test_changed_guard_skips_unchanged(self):
        cur = {"account_set": "DATAT", "account_dir": "d", "account_company": "Co",
               "account_set_row": 2}
        same = {"account_set": "DATAT", "account_dir": "d", "account_company": "Co",
                "account_set_row": 2, "method": "dbf"}  # 多带 method 不算变更
        self.assertFalse(agent_store.selected_account_changed(cur, same))
        self.assertTrue(agent_store.selected_account_changed(cur, {**same, "account_set": "58X"}))
        self.assertTrue(agent_store.selected_account_changed({}, same))  # 首次上报 = 变更


if __name__ == "__main__":
    unittest.main()
