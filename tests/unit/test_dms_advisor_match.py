# -*- coding: utf-8 -*-
"""LINE 操作员 → DMS 销售顾问匹配(提成归属)。

真机 probe(测试站 2026-08-11):顾问主档行形 [id, code, name, tel],code 列就是 DMS
登录名(297/sale01/sale · 335/sale02/sale02)。本测锁:matcher 只认唯一命中(重名/重号
一律弃权,宁可开局拦下也不把提成算到别人头上);端点上钉死的归属优先于名册匹配;
凭据解不出时不猜账号,交由调用方发拦截话术。
"""

import os
import unittest
from unittest import mock

from cryptography.fernet import Fernet

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-line-dms-qa-32bytes-long")
# kms_helper import 期就要求密钥存在(生产是启动硬门),测试自备一把。
os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from core import kms_helper  # noqa: E402
from services.erp import erp_dms_push  # noqa: E402
from services.line_dms import advisor_match, masters_cache  # noqa: E402

_ADVISORS = [
    ["297", "sale01", "สมชาย", "0811111111"],
    ["335", "sale02", "sale02"],
    ["278", "salemgr", "ผู้จัดการฝ่ายขาย", "0822222222"],
]

_EP = {"id": "E1", "config": {"username": "sale02", "password": "x"}}


class MatchAdvisorTests(unittest.TestCase):
    def test_matches_on_code_column(self):
        # 会话只留 id + name:code/tel 建单层按 id 重解,存下来只会变陈旧。
        hit = advisor_match.match_advisor(_ADVISORS, "sale01")
        self.assertEqual(hit, {"id": "297", "name": "สมชาย"})

    def test_matches_on_name_column_when_no_code_hit(self):
        rows = [["12", "u9", "somchai.k"]]
        hit = advisor_match.match_advisor(rows, "somchai.k")
        self.assertEqual(hit, {"id": "12", "name": "somchai.k"})

    def test_match_is_case_insensitive_and_trimmed(self):
        hit = advisor_match.match_advisor(_ADVISORS, "  SALE02 ")
        self.assertEqual((hit or {}).get("id"), "335")

    def test_code_layer_wins_over_name_layer(self):
        rows = [["1", "sale01", "x"], ["2", "other", "sale01"]]
        self.assertEqual((advisor_match.match_advisor(rows, "sale01") or {}).get("id"), "1")

    def test_ambiguous_hits_give_up(self):
        rows = [["1", "sale01", "A"], ["2", "sale01", "B"]]
        self.assertIsNone(advisor_match.match_advisor(rows, "sale01"))

    def test_no_hit_returns_none(self):
        self.assertIsNone(advisor_match.match_advisor(_ADVISORS, "dmstest"))

    def test_empty_username_returns_none(self):
        self.assertIsNone(advisor_match.match_advisor(_ADVISORS, ""))
        self.assertIsNone(advisor_match.match_advisor(_ADVISORS, "   "))

    def test_empty_master_returns_none(self):
        self.assertIsNone(advisor_match.match_advisor([], "sale01"))


class ResolveOperatorAdvisorTests(unittest.TestCase):
    def test_matches_from_live_master(self):
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("sale02", "p", "", "")
            ),
            mock.patch.object(masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(
                masters_cache, "get_masters", return_value={"advisors": _ADVISORS}
            ) as masters,
        ):
            advisor, username = advisor_match.resolve_operator_advisor(_EP)
        self.assertEqual(username, "sale02")
        self.assertEqual((advisor or {}).get("id"), "335")
        masters.assert_called_once()

    def test_cold_cache_fetches_once_without_forcing(self):
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("dmstest", "p", "", "")
            ),
            mock.patch.object(masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(
                masters_cache, "get_masters", return_value={"advisors": _ADVISORS}
            ) as masters,
        ):
            advisor, username = advisor_match.resolve_operator_advisor(_EP)
        self.assertIsNone(advisor)
        self.assertEqual(username, "dmstest")  # 拦截话术要报出是哪个账号没对上
        # 缓存本来就冷:get_masters 自己会现抓,再 force 等于同一请求连登两遍。
        masters.assert_called_once()
        self.assertEqual(masters.call_args.kwargs.get("force_refresh"), False)

    def test_just_added_advisor_is_seen_after_forced_refresh(self):
        added = _ADVISORS + [["401", "dmstest", "น้องใหม่"]]
        calls = []

        def _masters(ep, *, force_refresh=False):
            calls.append(force_refresh)
            return {"advisors": added}

        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("dmstest", "p", "", "")
            ),
            mock.patch.object(
                masters_cache, "read_fresh_masters", return_value={"advisors": _ADVISORS}
            ),
            mock.patch.object(masters_cache, "get_masters", side_effect=_masters),
        ):
            advisor, _ = advisor_match.resolve_operator_advisor(_EP)
        # 暖缓存里没有 → 必须 force 现抓一次,否则「加进名册再试」在 12 小时内都不灵。
        self.assertEqual(calls, [True])
        self.assertEqual((advisor or {}).get("id"), "401")

    def test_pinned_advisor_wins_without_touching_master(self):
        ep = {
            "id": "E1",
            "config": {
                "username": "sale02",
                "password": "x",
                "booking_defaults": {
                    "advisor_id": "335",
                    "advisor_code": "sale02",
                    "advisor_name": "sale02",
                },
            },
        }
        with mock.patch.object(masters_cache, "get_masters") as masters:
            advisor, username = advisor_match.resolve_operator_advisor(ep)
        masters.assert_not_called()
        self.assertEqual(advisor, {"id": "335", "name": "sale02"})
        self.assertEqual(username, "")

    def test_pinned_without_name_fills_from_warm_cache(self):
        ep = {"id": "E1", "config": {"booking_defaults": {"advisor_id": "297"}}}
        with mock.patch.object(
            masters_cache, "read_fresh_masters", return_value={"advisors": _ADVISORS}
        ):
            advisor, _ = advisor_match.resolve_operator_advisor(ep)
        self.assertEqual((advisor or {}).get("name"), "สมชาย")

    def test_pinned_passes_even_with_cold_cache(self):
        ep = {"id": "E1", "config": {"booking_defaults": {"advisor_id": "297"}}}
        with mock.patch.object(masters_cache, "read_fresh_masters", return_value=None):
            advisor, _ = advisor_match.resolve_operator_advisor(ep)
        self.assertEqual((advisor or {}).get("id"), "297")  # 名字回头由建单层解析

    def test_credential_decrypt_failure_blocks_without_guessing(self):
        with (
            mock.patch.object(erp_dms_push, "_dms_resolve_creds", side_effect=ValueError("boom")),
            mock.patch.object(masters_cache, "get_masters") as masters,
            self.assertLogs(advisor_match.logger, "WARNING"),  # 解密失败要留痕,不静默
        ):
            advisor, username = advisor_match.resolve_operator_advisor(_EP)
        self.assertEqual((advisor, username), (None, ""))
        masters.assert_not_called()

    def test_no_credentials_blocks(self):
        with mock.patch.object(erp_dms_push, "_dms_resolve_creds", return_value=("", "", "", "")):
            advisor, username = advisor_match.resolve_operator_advisor({"id": "E1", "config": {}})
        self.assertEqual((advisor, username), (None, ""))

    def test_encrypted_username_is_decrypted(self):
        ep = {"id": "E1", "config": {"username_enc": "enc", "password_enc": "enc"}}
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("", "", "enc", "enc")
            ),
            mock.patch.object(kms_helper, "decrypt_str", return_value="sale01"),
            mock.patch.object(masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(masters_cache, "get_masters", return_value={"advisors": _ADVISORS}),
        ):
            advisor, username = advisor_match.resolve_operator_advisor(ep)
        self.assertEqual(username, "sale01")
        self.assertEqual((advisor or {}).get("id"), "297")


if __name__ == "__main__":
    unittest.main()
