# -*- coding: utf-8 -*-

import json
import unittest
from unittest import mock

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_company_banks import (
    PAYMENT_BANK_MASTERS,
    bank_row_name,
    company_bank_label,
    company_bank_payment_extra,
    fetch_company_banks,
    fetch_payment_bank_masters,
    manual_bank_allowed_for_rows,
    normalize_company_bank_rows,
    resolve_bank_identity,
    validate_company_bank_payments,
)
from services.erp.mrerp_dms_payments import MANUAL_BANK_FLAG

# 生产租户真形态(2026-09-13 OA A):收款账户 2 行,来源/支票/本票/银行卡目录都是 0 行。
PRODUCTION_BANKS = {
    "company_banks": [
        ["1", "SCB", "SCB", "ระยอง", "1234567890123"],
        ["2", "BBL", "BBL", "ระยอง", "9876543210"],
    ],
    "source_banks": [],
    "cheque_banks": [],
    "cashier_banks": [],
    "card_banks": [],
}


def _transfer_extra(**over):
    extra = {
        "src_account_name": "สมชาย ใจดี",
        "src_account_no": "1234567890",
        "src_branch_name": "ระยอง",
        "src_time": "14:36",
        "dst_business_name": "บริษัท ตัวอย่าง จำกัด",
        "dst_id": "1",
    }
    extra.update(over)
    return extra


class _Client:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def _bshsd_all(self, elemname, **kwargs):
        self.calls.append((elemname, kwargs))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _Adapter:
    def __init__(self, results):
        self.client = _Client(results)

    def _client(self):
        return self.client


class CompanyBankTests(unittest.TestCase):
    def test_typeahead_fetch_retries_once_then_reads_complete_rows(self):
        adapter = _Adapter([None, [[1, "SCB", "SCB", "ระยอง", "1234567890123"]]])
        self.assertEqual(
            fetch_company_banks(adapter),
            [["1", "SCB", "SCB", "ระยอง", "1234567890123"]],
        )
        self.assertEqual(
            adapter.client.calls,
            [
                ("txtbanknametfmon", {"page_size": 200}),
                ("txtbanknametfmon", {"page_size": 200}),
            ],
        )

    def test_normalizes_page_rows_and_labels(self):
        rows = normalize_company_bank_rows(
            [
                {"id": "1", "details": ["SCB", "SCB"]},
                {"id": "2", "details": ["KBANK", "บัญชีรับจอง"]},
                {"id": "", "details": ["dirty"]},
            ]
        )
        self.assertEqual(
            rows,
            [["1", "SCB", "SCB", "", ""], ["2", "KBANK", "บัญชีรับจอง", "", ""]],
        )
        self.assertEqual(company_bank_label(rows[0]), "SCB")
        self.assertEqual(company_bank_label(rows[1]), "KBANK · บัญชีรับจอง")

    def test_label_and_payment_extra_include_account_and_branch(self):
        row = ["2", "BBL", "BBL", "ระยอง", "Bbl 987654321"]
        self.assertEqual(company_bank_label(row), "BBL · Bbl 987654321 · ระยอง")
        self.assertEqual(
            company_bank_payment_extra(row),
            {
                "dst_id": "2",
                "dst": "BBL · Bbl 987654321 · ระยอง",
                "dst_bank_id": "2",
                "dst_bank_name": "BBL",
                "dst_branch_name": "ระยอง",
                "dst_account_no": "Bbl 987654321",
            },
        )

    def test_submit_revalidates_selected_bank(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": {
                    "src_bank_name": "KBank",
                    "src_bank_id": "S1",
                    "src_account_name": "Customer",
                    "src_branch_name": "Bangkok",
                    "src_time": "14:36",
                    "dst_business_name": "Company",
                    "src_account_no": "123",
                    "dst_id": "1",
                    "dst": "old",
                },
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            side_effect=[
                [["1", "SCB", "SCB", "ระยอง", "1234567890123"]],
                [["S1", "KBANK", "KBank"]],
            ],
        ):
            out = validate_company_bank_payments(object(), payments)
        self.assertEqual(out[0]["extra"]["dst"], "SCB · 1234567890123 · ระยอง")
        self.assertEqual(out[0]["extra"]["dst_account_no"], "1234567890123")
        self.assertEqual(out[0]["extra"]["dst_bank_id"], "1")
        self.assertEqual(payments[0]["extra"]["dst"], "old")

    def test_submit_rejects_removed_or_legacy_free_text_bank(self):
        payment = {"channel": "transfer", "amount": "1.00", "extra": {"dst": "SCB"}}
        with mock.patch("services.erp.mrerp_dms_company_banks._fetch_banks", return_value=[]):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), [payment])
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_generic_bank_row_preserves_explicit_receiving_account(self):
        extra = company_bank_payment_extra(
            ["3", "000002", "Bangkok", "", ""],
            {
                "dst_account_no": "1234567890",
                "dst_branch_name": "Rayong",
            },
        )
        self.assertEqual(extra["dst_account_no"], "1234567890")
        self.assertEqual(extra["dst_branch_name"], "Rayong")
        self.assertEqual(extra["dst_bank_id"], "3")

    def test_every_payment_channel_reads_its_own_native_bank_selector(self):
        adapter = _Adapter([[[str(n), "CODE", "Bank"]] for n in range(5)])
        masters = fetch_payment_bank_masters(adapter)
        self.assertEqual(
            list(masters),
            ["company_banks", "source_banks", "cheque_banks", "cashier_banks", "card_banks"],
        )
        self.assertEqual(
            [call[0] for call in adapter.client.calls],
            [
                "txtbanknametfmon",
                "txtbanknametffrom",
                "txtbanknamecheque",
                "txtbanknamecashiercq",
                "txtbanknamecddbc",
            ],
        )

    def test_generic_bank_and_amount_do_not_count_as_complete_payment(self):
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            return_value=[["1", "SCB", "SCB", "", ""]],
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(
                    object(),
                    [
                        {
                            "channel": "transfer",
                            "amount": "1000",
                            "extra": {"dst_id": "1", "src_bank_id": "1"},
                        }
                    ],
                )
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_PAYMENT_INCOMPLETE")


class ManualBankDirectoryTests(unittest.TestCase):
    """目录权威为空 vs 读取失败:「空」才允许手工银行名称,「没读到」一律不放行。"""

    def test_empty_directory_allows_a_manual_name_only_for_channel_banks(self):
        self.assertTrue(manual_bank_allowed_for_rows("source_banks", []))
        self.assertFalse(manual_bank_allowed_for_rows("company_banks", []))
        self.assertFalse(manual_bank_allowed_for_rows("source_banks", None))
        self.assertFalse(manual_bank_allowed_for_rows("source_banks", [["S1", "KBANK", "KBank"]]))
        self.assertEqual(
            resolve_bank_identity([], "source_banks", "", "KBank"),
            {"id": "", "name": "KBank", "manual": True},
        )
        self.assertIsNone(resolve_bank_identity([], "company_banks", "", "SCB"))
        self.assertIsNone(resolve_bank_identity(None, "source_banks", "", "KBank"))
        self.assertIsNone(resolve_bank_identity([], "source_banks", "", "  "))

    def test_directory_rows_need_a_real_match_and_never_fall_back_by_name(self):
        rows = [["S1", "KBANK", "KBank"], ["S2", "SCB", "SCB"]]
        self.assertEqual(bank_row_name(rows[0]), "KBank")
        self.assertEqual(
            resolve_bank_identity(rows, "source_banks", "S1", ""),
            {
                "id": "S1",
                "name": "KBank",
                "manual": False,
            },
        )
        # 只给名称:唯一精确同名(含大小写)可认领;歧义/对不上都不放行。
        self.assertEqual(resolve_bank_identity(rows, "source_banks", "", "kbank")["id"], "S1")
        self.assertIsNone(resolve_bank_identity(rows, "source_banks", "", "KB"))
        self.assertIsNone(resolve_bank_identity(rows, "source_banks", "S9", "KBank"))
        self.assertIsNone(
            resolve_bank_identity(rows + [["S3", "K", "KBank"]], "source_banks", "", "KBank")
        )


class _BshsdTransport:
    """复刻 DMS bshsd 端点在两个真实协议形态上的原始响应:
    · 已登录、目录 0 行 → HTTP 200 + 空正文(0 字节,本租户四类付款银行目录);
    · 已登录、目录有行 → HTTP 200 + JSON 数组(公司收款账户 2 行)。
    """

    def __init__(self, bodies):
        self.bodies = dict(bodies)

    def post(self, url, data=None, files=None, timeout_ms=None):
        elem = str((data or {}).get("elemname") or "")
        status = 200
        text = self.bodies.get(elem, "")
        if isinstance(text, tuple):
            status, text = text
        return mock.Mock(status_code=status, text=text, content=text.encode())


class ProductionProtocolShapeTests(unittest.TestCase):
    """0 字节空正文 / 非 JSON 壳在真实 DMSClient 取数层上的分流(不连真 DMS)。"""

    def _client(self, bodies):
        from services.erp.mrerp_dms_client import DMSClient

        return DMSClient(_BshsdTransport(bodies), "https://x/dms/")

    def test_two_company_banks_plus_four_empty_bodies_form_a_complete_bank_snapshot(self):
        """company_banks=2 行 + 四类 0 字节空目录 → 完整快照,四类可走手工付款字段。"""
        company_rows = json.dumps(PRODUCTION_BANKS["company_banks"], ensure_ascii=False)
        bodies = {PAYMENT_BANK_MASTERS["company_banks"]: company_rows}
        for key in ("source_banks", "cheque_banks", "cashier_banks", "card_banks"):
            bodies[PAYMENT_BANK_MASTERS[key]] = ""  # 0 字节空正文
        banks = fetch_payment_bank_masters(object(), client=self._client(bodies))

        self.assertEqual(
            sorted(banks),
            ["card_banks", "cashier_banks", "cheque_banks", "company_banks", "source_banks"],
        )
        self.assertEqual(len(banks["company_banks"]), 2)
        for key in ("source_banks", "cheque_banks", "cashier_banks", "card_banks"):
            with self.subTest(key=key):
                self.assertEqual(banks[key], [])  # 权威空目录,不是 None
                self.assertTrue(manual_bank_allowed_for_rows(key, banks[key]))

        # 快照带完整银行键(含四类空表)→ 手工来源银行名称这一笔走通。
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(src_bank_name="KBank", src_bank_id=""),
            }
        ]
        out = validate_company_bank_payments(object(), payments, client=self._client(bodies))
        extra = out[0]["extra"]
        self.assertEqual(extra[MANUAL_BANK_FLAG], "1")
        self.assertEqual(extra["src_bank_name"], "KBank")
        self.assertEqual(extra["dst_bank_name"], "SCB")

    def test_unauthenticated_non_json_body_fails_closed(self):
        """未登录/认证失效 = 65 字节非 JSON 壳 → 取数层 None → 失败关闭,绝不落成空目录。"""
        from services.erp.mrerp_dms_client_base import DMSClientError

        unauth = "0" * 65  # 非 JSON、非数组:模拟未登录壳
        bodies = {elem: unauth for elem in PAYMENT_BANK_MASTERS.values()}
        with self.assertRaises(DMSClientError) as ctx:
            fetch_payment_bank_masters(object(), client=self._client(bodies))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")

        # 提交前校验同样失败关闭:「读到非 JSON」不等于「公司没配这类银行」,不许退回手工填写。
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(src_bank_name="KBank", src_bank_id=""),
            }
        ]
        with self.assertRaises(DMSClientError) as ctx:
            validate_company_bank_payments(object(), payments, client=self._client(bodies))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")

    def test_http_non_200_still_fails_closed(self):
        """HTTP 非 200 → 技术异常 fail closed,不落成空目录。"""
        from services.erp.mrerp_dms_client_base import DMSClientError

        bodies = {PAYMENT_BANK_MASTERS["company_banks"]: (500, "")}
        with self.assertRaises(DMSClientError) as ctx:
            fetch_payment_bank_masters(object(), client=self._client(bodies))
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")


class ProductionShapeSubmitTests(unittest.TestCase):
    """提交前校验按生产真形态:收款账户 2 行 + 其余四类 0 行。"""

    def test_manual_source_bank_passes_when_that_directory_is_empty(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(src_bank_name="KBank", src_bank_id=""),
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            side_effect=[PRODUCTION_BANKS["company_banks"], []],
        ):
            out = validate_company_bank_payments(object(), payments)  # 不抛 = 放行
        extra = out[0]["extra"]
        self.assertEqual(extra["src_bank_name"], "KBank")
        self.assertEqual(extra["src_bank_id"], "")
        self.assertEqual(extra[MANUAL_BANK_FLAG], "1")
        self.assertEqual(extra["dst_id"], "1")  # 收款账户仍来自实时目录
        self.assertEqual(extra["dst_bank_name"], "SCB")

    def test_manual_source_bank_without_a_name_is_incomplete(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(src_bank_id=""),
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            side_effect=[PRODUCTION_BANKS["company_banks"], []],
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), payments)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_PAYMENT_INCOMPLETE")

    def test_manual_channel_bank_passes_but_only_where_the_directory_is_empty(self):
        manual = {
            "channel": "cheque",
            "amount": "500.00",
            "extra": {"cheque_no": "123456", "cheque_book_no": "01", "bank_name": "KBank"},
        }
        with mock.patch("services.erp.mrerp_dms_company_banks._fetch_banks", return_value=[]):
            out = validate_company_bank_payments(object(), [manual])
        self.assertEqual(out[0]["extra"]["bank_id"], "")
        self.assertEqual(out[0]["extra"][MANUAL_BANK_FLAG], "1")

        # 目录里有行 → 手工名称必须能唯一精确命中;否则就是已删除/不存在的选项,不放行。
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            return_value=[["1", "SCB", "SCB"]],
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), [manual])
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_receiving_account_stays_strict_even_with_an_empty_source_directory(self):
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(dst_id="9", src_bank_name="KBank", src_bank_id=""),
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            side_effect=[PRODUCTION_BANKS["company_banks"], []],
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), payments)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_unreadable_directory_cannot_be_used_as_an_empty_one(self):
        """目录取数失败 → 抛错失败关闭;绝不当成「公司没配这类银行」再退回手工填写。"""
        payments = [
            {
                "channel": "transfer",
                "amount": "1500.00",
                "extra": _transfer_extra(src_bank_name="KBank", src_bank_id=""),
            }
        ]
        with mock.patch(
            "services.erp.mrerp_dms_company_banks._fetch_banks",
            side_effect=[
                PRODUCTION_BANKS["company_banks"],
                DMSClientError("bank master not ready", "ERR_DMS_MASTER_UNAVAILABLE"),
            ],
        ):
            with self.assertRaises(DMSClientError) as ctx:
                validate_company_bank_payments(object(), payments)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
