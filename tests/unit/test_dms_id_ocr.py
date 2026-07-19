# -*- coding: utf-8 -*-
"""DMS 身份证识别共用服务(services/erp/dms_id_ocr)· 抽出契约。

网页/LINE 同一条路:错误类型化(code/http_status/detail 与原路由响应体一致)、
余额闸 402 拦在识别前、editable_id_card 字段形状与面板同构。
"""

import unittest
from unittest.mock import patch

from services.erp import dms_id_ocr as s

_USER = {"id": "u-1", "tenant_id": "t-1"}


class TestErrors(unittest.TestCase):
    def test_empty_file(self):
        with self.assertRaises(s.DmsOcrError) as cm:
            s.recognize_id_card(_USER, b"", "a.jpg")
        self.assertEqual(cm.exception.code, "ocr.empty_file")
        self.assertEqual(cm.exception.http_status, 400)

    def test_no_endpoint(self):
        with patch.object(s, "resolve_dms_endpoint", return_value=None):
            with self.assertRaises(s.DmsOcrError) as cm:
                s.recognize_id_card(_USER, b"img", "a.jpg")
        self.assertEqual(cm.exception.code, "dms.no_endpoint")
        self.assertEqual(cm.exception.detail, "dms.no_endpoint")  # 路由响应体逐字节兼容

    def test_billing_gate_blocks_before_ocr(self):
        with (
            patch.object(s, "resolve_dms_endpoint", return_value={"id": "e1"}),
            patch.object(
                s.db,
                "get_billing_status_combined",
                return_value={"allowed": False, "is_exempt": False, "balance_thb": -1.0},
            ),
            patch.object(s.db, "estimate_pdf_cost_thb", return_value=1.5),
            patch("services.ocr.id_card_extract.extract_thai_id_card") as ocr,
        ):
            with self.assertRaises(s.DmsOcrError) as cm:
                s.recognize_id_card(_USER, b"img", "a.jpg")
        self.assertEqual(cm.exception.http_status, 402)
        self.assertEqual(cm.exception.detail["code"], "insufficient_balance")
        ocr.assert_not_called()  # 绝不先识别再扣成负

    def test_billing_infra_error_is_tolerated(self):
        # 余额闸基建抖动 → 容错放行(与热路径一致),识别照跑、计费照发。
        with (
            patch.object(s, "resolve_dms_endpoint", return_value={"id": "e1"}),
            patch.object(s.db, "get_billing_status_combined", side_effect=RuntimeError("down")),
            patch(
                "services.ocr.id_card_extract.extract_thai_id_card",
                return_value={"id_card": {}},
            ),
            patch.object(s.db, "charge_ocr_async") as charge,
        ):
            ep, ocr, _ = s.recognize_id_card(_USER, b"img", "a.jpg")
        self.assertEqual(ep["id"], "e1")
        charge.assert_called_once()
        self.assertEqual(charge.call_args.args[2], "pdf")  # 按 1 页计,与网页同口径
        self.assertEqual(charge.call_args.args[3], 1)


class TestEditableShape(unittest.TestCase):
    def test_shape_matches_panel(self):
        out = s.editable_id_card(
            {"first_name": "สมชาย", "last_name": "ใจดี", "people_id": "123", "address": {}}
        )
        self.assertEqual(out["name"], "สมชาย ใจดี")
        self.assertEqual(out["people_id"], "123")
        self.assertIn("zipcode", out["address"])
        self.assertEqual(out["phone"], "")


if __name__ == "__main__":
    unittest.main()


class TestResolveEndpointEnabled(unittest.TestCase):
    """停用是收权动作:会话残留的显式 endpoint_id 不得绕过 enabled(审查修复回归)。"""

    def test_explicit_id_disabled_endpoint_rejected(self):
        ep = {"id": "e1", "adapter": "mrerp_dms", "enabled": False}
        with patch.object(s.db, "get_erp_endpoint", return_value=ep):
            self.assertIsNone(s.resolve_dms_endpoint("u1", "e1"))

    def test_explicit_id_enabled_endpoint_returned(self):
        ep = {"id": "e1", "adapter": "mrerp_dms", "enabled": True}
        with (
            patch.object(s.db, "get_erp_endpoint", return_value=ep),
            patch.object(s.db, "find_user_by_id", return_value=None),
        ):
            self.assertEqual(s.resolve_dms_endpoint("u1", "e1"), ep)


class TestInheritTenantDefaults(unittest.TestCase):
    """操作员 endpoint 借老板管理员凭据组 + 订车默认值(2026-07-19 销售直写拍板)。"""

    _OWNER_CFG = {
        "admin_username_enc": "enc-au",
        "admin_password_enc": "enc-ap",
        "booking_defaults": {"booking_prefix": "ZX"},
    }
    _MEMBER = {"id": "m-1", "role": "member", "tenant_id": "t-1"}

    def test_member_without_admin_borrows_owner_creds_and_defaults(self):
        ep = {"id": "e1", "config": {"username_enc": "u", "password_enc": "p"}}
        with (
            patch.object(s.db, "find_user_by_id", return_value=dict(self._MEMBER)),
            patch.object(s, "_tenant_owner_endpoint_cfg", return_value=dict(self._OWNER_CFG)),
        ):
            out = s._inherit_tenant_defaults("m-1", ep)
        self.assertEqual(out["config"]["admin_username_enc"], "enc-au")
        self.assertEqual(out["config"]["admin_password_enc"], "enc-ap")
        self.assertEqual(out["config"]["booking_defaults"], {"booking_prefix": "ZX"})
        self.assertEqual(out["config"]["username_enc"], "u")  # 自己的主凭据原样
        self.assertNotIn("admin_username_enc", ep["config"])  # 不污染入参

    def test_member_own_admin_creds_not_overwritten(self):
        cfg = {"admin_username_enc": "own-u", "admin_password_enc": "own-p"}
        ep = {"id": "e1", "config": dict(cfg)}
        with (
            patch.object(s.db, "find_user_by_id", return_value=dict(self._MEMBER)),
            patch.object(s, "_tenant_owner_endpoint_cfg", return_value=dict(self._OWNER_CFG)),
        ):
            out = s._inherit_tenant_defaults("m-1", ep)
        self.assertEqual(out["config"]["admin_username_enc"], "own-u")
        self.assertEqual(out["config"]["booking_defaults"], {"booking_prefix": "ZX"})

    def test_owner_endpoint_passthrough_untouched(self):
        ep = {"id": "e1", "config": {"username_enc": "u"}}
        owner = {"id": "o-1", "role": "owner", "tenant_id": "t-1"}
        with patch.object(s.db, "find_user_by_id", return_value=owner):
            self.assertIs(s._inherit_tenant_defaults("o-1", ep), ep)

    def test_complete_config_short_circuits_without_db(self):
        ep = {"id": "e1", "config": dict(self._OWNER_CFG)}
        with patch.object(s.db, "find_user_by_id") as fu:
            self.assertIs(s._inherit_tenant_defaults("m-1", ep), ep)
        fu.assert_not_called()

    def test_owner_without_dms_endpoint_leaves_ep_unchanged(self):
        ep = {"id": "e1", "config": {"username_enc": "u"}}
        with (
            patch.object(s.db, "find_user_by_id", return_value=dict(self._MEMBER)),
            patch.object(s, "_tenant_owner_endpoint_cfg", return_value={}),
        ):
            self.assertIs(s._inherit_tenant_defaults("m-1", ep), ep)
