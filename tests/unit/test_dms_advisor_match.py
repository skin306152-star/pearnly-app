# -*- coding: utf-8 -*-
"""操作员 DMS 账号 → 销售顾问匹配(提成归属)· 被测模块 services/erp/dms_advisor.py。

真机 probe(测试站 2026-08-11):顾问主档行形 [id, code, name, tel]。2026-08-12 的探针
员工(337 / 编号 WKC99 / 登录名 wkuser99)推翻了「code 列 = 登录名」——那一列是员工编号,
测试站两者相等只是录入习惯。于是匹配分两层:员工表 login 精确层优先,拿不到才回落顾问
下拉 code/name 的启发层。

本测锁:精确层胜启发层(编号撞上别人登录名时不许错配);员工已认出但没有顾问资格时拦下
而不是让启发层接着猜;员工表缺料时启发层行为逐字不变;matcher 只认唯一命中;端点上钉死
的归属优先于一切匹配;凭据解不出时不猜账号,交由调用方发拦截话术。
"""

import os
import unittest
from unittest import mock

from cryptography.fernet import Fernet

os.environ.setdefault("JWT_SECRET", "test-secret-key-for-line-dms-qa-32bytes-long")
# kms_helper import 期就要求密钥存在(生产是启动硬门),测试自备一把。
os.environ.setdefault("PEARNLY_KMS_KEY", Fernet.generate_key().decode())

from core import kms_helper  # noqa: E402
from services.erp import dms_advisor, dms_masters_cache, erp_dms_push  # noqa: E402

_ADVISORS = [
    ["297", "sale01", "สมชาย", "0811111111"],
    ["335", "sale02", "sale02"],
    ["278", "salemgr", "ผู้จัดการฝ่ายขาย", "0822222222"],
]

_EP = {"id": "E1", "config": {"username": "sale02", "password": "x"}}

# 精确层与启发层分歧的样本(真车行「编号 ≠ 登录名」形态):顾问 297 的 code 列 "sale02"
# 是他的员工【编号】,恰好等于员工 335 的登录名 —— 启发层会把 335 的单记到 297 头上。
_TRAP_ADVISORS = [
    ["297", "sale02", "สมชาย", "0811111111"],
    ["335", "S02", "สมศรี"],
]
_TRAP_EMPLOYEES = [
    {"id": "297", "code": "sale02", "login": "somchai", "name": "สมชาย"},
    {"id": "335", "code": "S02", "login": "sale02", "name": "สมศรี"},
]
# 员工表里有、顾问下拉里没有(职位/团队不够格当顾问);其登录名又恰好是某顾问的编号。
_UNQUALIFIED = {"id": "337", "code": "WKC99", "login": "wkuser99", "name": "WalkProbe"}
_BAIT_ADVISORS = _ADVISORS + [["999", "wkuser99", "คนอื่น"]]


class MatchAdvisorTests(unittest.TestCase):
    def test_matches_on_code_column(self):
        # 会话只留 id + name:code/tel 建单层按 id 重解,存下来只会变陈旧。
        hit = dms_advisor.match_advisor(_ADVISORS, "sale01")
        self.assertEqual(hit, {"id": "297", "name": "สมชาย"})

    def test_matches_on_name_column_when_no_code_hit(self):
        rows = [["12", "u9", "somchai.k"]]
        hit = dms_advisor.match_advisor(rows, "somchai.k")
        self.assertEqual(hit, {"id": "12", "name": "somchai.k"})

    def test_match_is_case_insensitive_and_trimmed(self):
        hit = dms_advisor.match_advisor(_ADVISORS, "  SALE02 ")
        self.assertEqual((hit or {}).get("id"), "335")

    def test_code_layer_wins_over_name_layer(self):
        rows = [["1", "sale01", "x"], ["2", "other", "sale01"]]
        self.assertEqual((dms_advisor.match_advisor(rows, "sale01") or {}).get("id"), "1")

    def test_ambiguous_hits_give_up(self):
        rows = [["1", "sale01", "A"], ["2", "sale01", "B"]]
        self.assertIsNone(dms_advisor.match_advisor(rows, "sale01"))

    def test_no_hit_returns_none(self):
        self.assertIsNone(dms_advisor.match_advisor(_ADVISORS, "dmstest"))

    def test_empty_username_returns_none(self):
        self.assertIsNone(dms_advisor.match_advisor(_ADVISORS, ""))
        self.assertIsNone(dms_advisor.match_advisor(_ADVISORS, "   "))

    def test_empty_master_returns_none(self):
        self.assertIsNone(dms_advisor.match_advisor([], "sale01"))


class MatchInMastersTests(unittest.TestCase):
    """两层顺序:员工表 login 精确层 → (缺料才) 顾问下拉 code/name 启发层。"""

    def test_exact_layer_beats_heuristic(self):
        hit = dms_advisor.match_in_masters(
            {"advisors": _TRAP_ADVISORS, "employees": _TRAP_EMPLOYEES}, "sale02"
        )
        self.assertEqual(hit, {"id": "335", "name": "สมศรี"})

    def test_employee_without_advisor_seat_blocks_instead_of_guessing(self):
        # 人已经认出来了,只是没顾问资格 —— 再让启发层去比 code 列就会记到 999 头上。
        hit = dms_advisor.match_in_masters(
            {"advisors": _BAIT_ADVISORS, "employees": [_UNQUALIFIED]}, "wkuser99"
        )
        self.assertIsNone(hit)

    def test_name_comes_from_the_advisor_dropdown_row(self):
        # 预览卡显示的是顾问栏的名字,不是员工表的花名。
        employees = [{"id": "297", "code": "E297", "login": "sale01", "name": "Somchai (HR)"}]
        hit = dms_advisor.match_in_masters(
            {"advisors": _ADVISORS, "employees": employees}, "sale01"
        )
        self.assertEqual(hit, {"id": "297", "name": "สมชาย"})

    def test_empty_employees_falls_back_to_heuristic(self):
        for masters in (
            {"advisors": _ADVISORS, "employees": []},
            {"advisors": _ADVISORS},
            None,
        ):
            with self.subTest(masters=masters):
                hit = dms_advisor.match_in_masters(masters or {"advisors": _ADVISORS}, "sale02")
                self.assertEqual((hit or {}).get("id"), "335")

    def test_unknown_login_still_reaches_heuristic(self):
        # 员工表拿到了但没这个人(如老板借号):启发层仍有机会按顾问名匹配。
        hit = dms_advisor.match_in_masters(
            {"advisors": _ADVISORS, "employees": [_UNQUALIFIED]}, "sale01"
        )
        self.assertEqual((hit or {}).get("id"), "297")


class ResolveOperatorAdvisorTests(unittest.TestCase):
    def test_matches_from_live_master(self):
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("sale02", "p", "", "")
            ),
            mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(
                dms_masters_cache, "get_masters", return_value={"advisors": _ADVISORS}
            ) as masters,
        ):
            advisor, username = dms_advisor.resolve_operator_advisor(_EP)
        self.assertEqual(username, "sale02")
        self.assertEqual((advisor or {}).get("id"), "335")
        masters.assert_called_once()

    def test_cold_cache_fetches_once_without_forcing(self):
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("dmstest", "p", "", "")
            ),
            mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(
                dms_masters_cache, "get_masters", return_value={"advisors": _ADVISORS}
            ) as masters,
        ):
            advisor, username = dms_advisor.resolve_operator_advisor(_EP)
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
                dms_masters_cache, "read_fresh_masters", return_value={"advisors": _ADVISORS}
            ),
            mock.patch.object(dms_masters_cache, "get_masters", side_effect=_masters),
        ):
            advisor, _ = dms_advisor.resolve_operator_advisor(_EP)
        # 暖缓存里没有 → 必须 force 现抓一次,否则「加进名册再试」在 12 小时内都不灵。
        self.assertEqual(calls, [True])
        self.assertEqual((advisor or {}).get("id"), "401")

    def test_exact_layer_wins_from_warm_cache(self):
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("sale02", "p", "", "")
            ),
            mock.patch.object(
                dms_masters_cache,
                "read_fresh_masters",
                return_value={"advisors": _TRAP_ADVISORS, "employees": _TRAP_EMPLOYEES},
            ),
            mock.patch.object(dms_masters_cache, "get_masters") as masters,
        ):
            advisor, _ = dms_advisor.resolve_operator_advisor(_EP)
        self.assertEqual((advisor or {}).get("id"), "335")  # 启发层会答 297
        masters.assert_not_called()

    def test_unqualified_employee_stays_blocked_after_forced_refresh(self):
        blocked = {"advisors": _BAIT_ADVISORS, "employees": [_UNQUALIFIED]}
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("wkuser99", "p", "", "")
            ),
            mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=blocked),
            mock.patch.object(dms_masters_cache, "get_masters", return_value=blocked) as masters,
        ):
            advisor, username = dms_advisor.resolve_operator_advisor(_EP)
        # 「去 DMS 给他开顾问资格再试」得当场重抓才算数,但重抓完仍没资格就必须拦住。
        self.assertEqual(masters.call_args.kwargs.get("force_refresh"), True)
        self.assertIsNone(advisor)
        self.assertEqual(username, "wkuser99")

    def test_forced_refresh_keeps_exact_layer_first(self):
        stale = {"advisors": _TRAP_ADVISORS, "employees": []}
        fresh = {"advisors": _TRAP_ADVISORS, "employees": _TRAP_EMPLOYEES}
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("somchai", "p", "", "")
            ),
            mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=stale),
            mock.patch.object(dms_masters_cache, "get_masters", return_value=fresh),
        ):
            advisor, _ = dms_advisor.resolve_operator_advisor(_EP)
        # 陈旧缓存里没员工表 → 启发层比 code/name 都不中;重抓后精确层认出 297。
        self.assertEqual((advisor or {}).get("id"), "297")

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
        with mock.patch.object(dms_masters_cache, "get_masters") as masters:
            advisor, username = dms_advisor.resolve_operator_advisor(ep)
        masters.assert_not_called()
        self.assertEqual(advisor, {"id": "335", "name": "sale02"})
        self.assertEqual(username, "")

    def test_pinned_without_name_fills_from_warm_cache(self):
        ep = {"id": "E1", "config": {"booking_defaults": {"advisor_id": "297"}}}
        with mock.patch.object(
            dms_masters_cache, "read_fresh_masters", return_value={"advisors": _ADVISORS}
        ):
            advisor, _ = dms_advisor.resolve_operator_advisor(ep)
        self.assertEqual((advisor or {}).get("name"), "สมชาย")

    def test_pinned_passes_even_with_cold_cache(self):
        ep = {"id": "E1", "config": {"booking_defaults": {"advisor_id": "297"}}}
        with mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=None):
            advisor, _ = dms_advisor.resolve_operator_advisor(ep)
        self.assertEqual((advisor or {}).get("id"), "297")  # 名字回头由建单层解析

    def test_live_bundle_refreshes_pinned_name(self):
        ep = {
            "id": "E1",
            "config": {"booking_defaults": {"advisor_id": "297", "advisor_name": "Old Name"}},
        }
        advisor, _ = dms_advisor.resolve_operator_advisor(
            ep,
            masters={"advisors": [["297", "SALE01", "Current Name"]]},
        )
        self.assertEqual(advisor, {"id": "297", "name": "Current Name"})

    def test_live_bundle_blocks_deleted_pinned_advisor(self):
        ep = {
            "id": "E1",
            "config": {"booking_defaults": {"advisor_id": "297", "advisor_name": "Old Name"}},
        }
        advisor, _ = dms_advisor.resolve_operator_advisor(ep, masters={"advisors": []})
        self.assertIsNone(advisor)

    def test_credential_decrypt_failure_blocks_without_guessing(self):
        with (
            mock.patch.object(erp_dms_push, "_dms_resolve_creds", side_effect=ValueError("boom")),
            mock.patch.object(dms_masters_cache, "get_masters") as masters,
            self.assertLogs(dms_advisor.logger, "WARNING"),  # 解密失败要留痕,不静默
        ):
            advisor, username = dms_advisor.resolve_operator_advisor(_EP)
        self.assertEqual((advisor, username), (None, ""))
        masters.assert_not_called()

    def test_no_credentials_blocks(self):
        with mock.patch.object(erp_dms_push, "_dms_resolve_creds", return_value=("", "", "", "")):
            advisor, username = dms_advisor.resolve_operator_advisor({"id": "E1", "config": {}})
        self.assertEqual((advisor, username), (None, ""))

    def test_encrypted_username_is_decrypted(self):
        ep = {"id": "E1", "config": {"username_enc": "enc", "password_enc": "enc"}}
        with (
            mock.patch.object(
                erp_dms_push, "_dms_resolve_creds", return_value=("", "", "enc", "enc")
            ),
            mock.patch.object(kms_helper, "decrypt_str", return_value="sale01"),
            mock.patch.object(dms_masters_cache, "read_fresh_masters", return_value=None),
            mock.patch.object(
                dms_masters_cache, "get_masters", return_value={"advisors": _ADVISORS}
            ),
        ):
            advisor, username = dms_advisor.resolve_operator_advisor(ep)
        self.assertEqual(username, "sale01")
        self.assertEqual((advisor or {}).get("id"), "297")


if __name__ == "__main__":
    unittest.main()
