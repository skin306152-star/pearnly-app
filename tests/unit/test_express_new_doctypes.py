# -*- coding: utf-8 -*-
"""会计手录四类单据(收款/付款/手工凭证/库存调整)的载荷组装与写路总闸。

每类各钉五条:正常组装 / 缺必填拒 / 恒等式(借贷)不平拒 / 金额异常拒 / 日期异常拒。
组装器与总闸分开钉 —— 重推/回放不经组装器,只过 check_payload 那一道;两处都必须拦得住
被改过的载荷,否则改一个 net_amount 就能让桥去反写别人的发票单头。

另钉桥门面按 direction 分派:四类各自认自己的 doctype、未知 direction 仍拒、老链路
(purchase/sales)一个字节不变。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.bridge import BridgeRejected, client  # noqa: E402
from services.erp.express_push.doctypes import (  # noqa: E402
    WRITE_SPECS,
    build_journal_payload,
    build_payment_payload,
    build_receipt_payload,
    build_stock_adjust_payload,
)
from services.erp.express_push.payload_keys import DOCTYPE_PAYLOAD_KEYS  # noqa: E402

BOOK = "DATAT"
_CONFIG = {"account_set": BOOK}


def _req(base_req, over):
    return {**base_req, **over}


def receipt_req(**over):
    """整额收款:一张赊销发票 1070,转账进钱 1070。"""
    return _req(
        {
            "receipt_date": "2026-01-15",
            "customer_code": "C001",
            "channels": [{"prefix": "TR", "kind": "transfer", "amount": "1070.00"}],
            "allocations": [
                {"doc_no": "IV690101-001", "rectyp": "3", "amount": "1070.00", "vat_amount": "70"}
            ],
            "userid": "ACC1",
        },
        over,
    )


def payment_req(**over):
    """结清一张赊购票 1000,开支票 970 + 代扣 3% 预扣税 30。"""
    return _req(
        {
            "payment_date": "2026-01-15",
            "supplier_code": "S001",
            "settlements": [{"doc_no": "RR690101-01", "rectyp": "3", "amount": "1000.00"}],
            "channels": [
                {
                    "prefix": "QP",
                    "kind": "cheque",
                    "amount": "970.00",
                    "bank_account": "1234567890",
                }
            ],
            "withholding": {
                "tax_type": "S53",
                "tax_rate": "3",
                "base_amount": "1000.00",
                "tax_amount": "30.00",
            },
            "userid": "ACC1",
        },
        over,
    )


def journal_req(**over):
    return _req(
        {
            "voucher_date": "2026-01-15",
            "journal_code": "00",
            "description": "ปรับปรุงค่าใช้จ่ายค้างจ่าย",
            "lines": [
                {"acc": "5140-10", "side": "D", "amount": "500.00"},
                {"acc": "2130-01", "side": "C", "amount": "500.00"},
            ],
            "userid": "ACC1",
        },
        over,
    )


def stock_req(**over):
    return _req(
        {
            "doc_date": "2026-01-15",
            "isrun_prefix": "ZZ",
            "remark": "ตัดสินค้าชำรุด",
            "lines": [
                {
                    "stock_code": "SKU-001",
                    "qty": "2",
                    "unit_price": "250.00",
                    "source_lot": "202512016OU690101-001  1",
                }
            ],
            "userid": "ACC1",
        },
        over,
    )


def _ok(result):
    assert result.ok, result.reason
    return result.payload


class ReceiptPayloadTests(unittest.TestCase):
    def test_normal_assembly(self):
        p = _ok(build_receipt_payload(receipt_req(), config=_CONFIG))
        self.assertEqual((p["direction"], p["doctype"]), ("ar_receipt", "RE"))
        self.assertEqual(p["docdate_be"], "690115")  # 公历 2026 → 佛历 69
        self.assertEqual((p["net_amount"], p["cheque_amount"]), ("1070.00", "1070.00"))
        self.assertEqual(p["cash_amount"], "0.00")
        self.assertEqual(p["customer"], {"code": "C001"})

    def test_unallocated_receipt_needs_explicit_flag(self):
        # 挂账收款(ARRCPIT 0 行)是真存在的形态,但必须会计显式点头。
        self.assertEqual(
            build_receipt_payload(receipt_req(allocations=[]), config=_CONFIG).reason,
            "no_allocations",
        )
        p = _ok(
            build_receipt_payload(
                receipt_req(allocations=[], allow_unallocated=True), config=_CONFIG
            )
        )
        self.assertTrue(p["allow_unallocated"])

    def test_rejects(self):
        cases = (
            ("缺客户码", {"customer_code": ""}, "no_customer_code"),
            ("缺渠道且无代扣", {"channels": []}, "no_channels"),
            (
                "C3 不闭合(冲销额与实收对不上)",
                {"allocations": [{"doc_no": "IV1", "rectyp": "3", "amount": "900.00"}]},
                "receipt_identities_not_closed",
            ),
            (
                "金额解析不了",
                {"channels": [{"prefix": "TR", "kind": "transfer", "amount": "一千"}]},
                "bad_channel_amount",
            ),
            ("日期非法", {"receipt_date": "2026-02-30"}, "bad_or_missing_date"),
            ("客户码超宽", {"customer_code": "C" * 11}, "customer_code_too_long"),
            ("v1 拒收收款销项税", {"output_vat_on_receipt": {"vat_amount": "70"}}, None),
        )
        for label, over, reason in cases:
            with self.subTest(label=label):
                res = build_receipt_payload(receipt_req(**over), config=_CONFIG)
                self.assertFalse(res.ok)
                if reason:
                    self.assertEqual(res.reason, reason)


class PaymentPayloadTests(unittest.TestCase):
    def test_normal_assembly(self):
        p = _ok(build_payment_payload(payment_req(), config=_CONFIG))
        self.assertEqual((p["direction"], p["doctype"]), ("ap_payment", "PS"))
        # A1 净额 = Σ结清额;A3 收付合计 = 净额 − 预扣。
        self.assertEqual(
            (p["net_amount"], p["cheque_amount"], p["wht_amount"]),
            ("1000.00", "970.00", "30.00"),
        )
        self.assertTrue(p["channels"][0]["is_cheque"])
        self.assertEqual(p["withholding"]["tax_type"], "S53")

    def test_v1_scope_narrowing_escalates(self):
        cases = (
            ("退货冲抵", {"settlements": [{"doc_no": "R1", "rectyp": "5", "amount": "1000.00"}]}),
            ("预付冲抵", {"settlements": [{"doc_no": "A1", "rectyp": "0", "amount": "1000.00"}]}),
            ("付款认列进项税", {"input_vat_on_payment": {"vat_amount": "70"}}),
            ("预付单", {"advance": {"doc_no": "AD1", "amount": "100"}}),
        )
        for label, over in cases:
            with self.subTest(label=label):
                self.assertFalse(build_payment_payload(payment_req(**over), config=_CONFIG).ok)

    def test_rejects(self):
        cheque = payment_req()["channels"][0]
        cases = (
            ("缺供应商码", {"supplier_code": ""}, "no_supplier_code"),
            ("缺结清明细", {"settlements": []}, "bad_settlement_amount"),
            (
                "A3 不闭合(渠道额与净额−预扣对不上)",
                {"channels": [{**cheque, "amount": "900.00"}]},
                "payment_identities_not_closed",
            ),
            (
                "W1 不闭合(税额与税基×税率对不上)",
                {"withholding": {**payment_req()["withholding"], "tax_rate": "5"}},
                "payment_identities_not_closed",
            ),
            (
                "金额为负",
                {"settlements": [{"doc_no": "RR1", "rectyp": "3", "amount": "-1"}]},
                "bad_settlement_amount",
            ),
            ("日期非法", {"payment_date": ""}, "bad_or_missing_date"),
            ("支票缺银行账号", {"channels": [{**cheque, "bank_account": ""}]}, "bad_bank_account"),
            (
                "多张支票",
                {"channels": [cheque, {**cheque, "amount": "0.01"}]},
                "multi_cheque_unsupported",
            ),
        )
        for label, over, reason in cases:
            with self.subTest(label=label):
                res = build_payment_payload(payment_req(**over), config=_CONFIG)
                self.assertFalse(res.ok)
                self.assertEqual(res.reason, reason)


class JournalPayloadTests(unittest.TestCase):
    def test_normal_assembly(self):
        p = _ok(build_journal_payload(journal_req(), config=_CONFIG))
        self.assertEqual((p["direction"], p["doctype"]), ("gl_journal", "GL"))
        self.assertEqual(p["total_amount"], "500.00")
        self.assertEqual(p["journal_code"], "00")
        # 行摘要默认抄头(真数据里行 DESCRP 从不为空)。
        self.assertEqual(p["lines"][0]["desc"], p["description"])

    def test_rejects(self):
        cases = (
            ("缺本账代码", {"journal_code": ""}, "no_journal_code"),
            ("缺摘要", {"description": ""}, "no_description"),
            (
                "借贷不平",
                {
                    "lines": [
                        {"acc": "5140-10", "side": "D", "amount": "500.00"},
                        {"acc": "2130-01", "side": "C", "amount": "400.00"},
                    ]
                },
                "bad_journal_lines",
            ),
            ("只有一行", {"lines": [{"acc": "5140-10", "side": "D", "amount": "500.00"}]}, None),
            (
                "金额为负(方向只由 side 表达)",
                {
                    "lines": [
                        {"acc": "5140-10", "side": "D", "amount": "-500.00"},
                        {"acc": "2130-01", "side": "C", "amount": "-500.00"},
                    ]
                },
                None,
            ),
            (
                "金额解析不了",
                {
                    "lines": [
                        {"acc": "5140-10", "side": "D", "amount": "五百"},
                        {"acc": "2130-01", "side": "C", "amount": "500.00"},
                    ]
                },
                None,
            ),
            ("日期非法", {"voucher_date": "15/01/26"}, "bad_or_missing_date"),
            ("凭证号超宽", {"voucher_no": "JV" + "0" * 11}, "voucher_no_too_long"),
        )
        for label, over, reason in cases:
            with self.subTest(label=label):
                res = build_journal_payload(journal_req(**over), config=_CONFIG)
                self.assertFalse(res.ok)
                self.assertEqual(res.reason, reason or "bad_journal_lines")


class StockAdjustPayloadTests(unittest.TestCase):
    def test_normal_assembly(self):
        p = _ok(build_stock_adjust_payload(stock_req(), config=_CONFIG))
        self.assertEqual((p["direction"], p["doctype"]), ("stock_adjust", "OU"))
        # 方向由 POSOPR 定,不看金额符号(45 号契约 X1)。
        self.assertEqual((p["posopr"], p["subtype"]), ("6", "internal_issue"))
        self.assertEqual(p["net_amount"], "500.00")
        self.assertEqual(p["items"][0]["amount"], "500.00")

    def test_rejects(self):
        line = stock_req()["lines"][0]
        cases = (
            ("缺单别前缀", {"isrun_prefix": ""}, "no_isrun_prefix"),
            ("缺摘要", {"remark": ""}, "no_remark"),
            ("缺明细", {"lines": []}, "no_items"),
            ("数量为负", {"lines": [{**line, "qty": "-2"}]}, "bad_item_qty"),
            ("单价为零", {"lines": [{**line, "unit_price": "0"}]}, "bad_item_unit_price"),
            ("单价解析不了", {"lines": [{**line, "unit_price": "两百五"}]}, "bad_item_unit_price"),
            ("日期非法", {"doc_date": "not-a-date"}, "bad_or_missing_date"),
            ("商品码超宽", {"lines": [{**line, "stock_code": "S" * 21}]}, "bad_stock_code"),
            ("数量调整子类", {"subtype": "quantity"}, "stock_adjust_subtype_unsupported"),
        )
        for label, over, reason in cases:
            with self.subTest(label=label):
                res = build_stock_adjust_payload(stock_req(**over), config=_CONFIG)
                self.assertFalse(res.ok)
                self.assertEqual(res.reason, reason)


def _payloads():
    return {
        # 动用 70 预收 + 转账 1070 结清一张 1140 的发票(C3/C4 两条恒等式都走到)。
        "ar_receipt": _ok(
            build_receipt_payload(
                receipt_req(
                    allocations=[
                        {"doc_no": "IV690101-001", "rectyp": "3", "amount": "1140.00"},
                        {"doc_no": "AD-001", "rectyp": "0", "amount": "70.00"},
                    ],
                    advance={"doc_no": "AD-001", "amount": "70.00"},
                    prior_docnum="RE0001",
                ),
                config=_CONFIG,
            )
        ),
        "ap_payment": _ok(
            build_payment_payload(payment_req(prior_docnum="PS0001"), config=_CONFIG)
        ),
        "gl_journal": _ok(
            build_journal_payload(
                journal_req(
                    voucher_no="JV6901-004",
                    vat={
                        "vat_rec": "P",
                        "vat_period": "2026-01-15",
                        "base_amount": "500.00",
                        "vat_amount": "35.00",
                        "ref_no": "INV-9",
                    },
                ),
                config=_CONFIG,
            )
        ),
        "stock_adjust": _ok(
            build_stock_adjust_payload(stock_req(prior_docnum="ZZ0001"), config=_CONFIG)
        ),
    }


class WriteGateDispatchTests(unittest.TestCase):
    """桥门面按 direction 分派 —— 四类各认自己的 doctype,老链路不受影响。"""

    def test_each_doctype_passes_the_write_gate(self):
        for direction, payload in _payloads().items():
            with self.subTest(direction=direction):
                self.assertEqual(client.build_write_payload(payload, BOOK)["direction"], direction)

    def test_tampered_payload_is_rejected_at_the_gate(self):
        # 重推/回放不经组装器:总闸必须自己拦得住被改过的载荷。
        bad = []
        for direction, payload in _payloads().items():
            key = "total_amount" if direction == "gl_journal" else "net_amount"
            bad.append((direction, {**payload, key: "999999.00"}))
        for direction, payload in bad:
            with self.subTest(direction=direction), self.assertRaises(BridgeRejected) as ctx:
                client.build_write_payload(payload, BOOK)
            self.assertEqual(ctx.exception.code, "bridge.bad_payload")

    def test_shape_rejects(self):
        receipt = _payloads()["ar_receipt"]
        journal = _payloads()["gl_journal"]
        cases = (
            ("doctype 与 direction 不配", {**receipt, "doctype": "PS"}, BOOK),
            ("串用老链路票种", {**journal, "doctype": "RR"}, BOOK),
            ("未知 direction", {**receipt, "direction": "ar_refund"}, BOOK),
            ("账套与 book 不一致", receipt, "OTHER"),
            ("版本不符", {**receipt, "payload_version": 2}, BOOK),
            ("日期形状不对", {**receipt, "docdate_be": "2026-01-15"}, BOOK),
            ("手工凭证借贷不平", {**journal, "lines": journal["lines"][:1]}, BOOK),
        )
        for label, payload, book in cases:
            with self.subTest(label=label), self.assertRaises(BridgeRejected) as ctx:
                client.build_write_payload(payload, book)
            self.assertEqual(ctx.exception.code, "bridge.bad_payload")

    def test_legacy_lanes_untouched(self):
        legacy = {
            "payload_version": 1,
            "direction": "purchase",
            "doctype": "RR",
            "account_set": BOOK,
            "lines": [
                {"acc": "116200", "side": "D", "amount": "100.00"},
                {"acc": "211100", "side": "C", "amount": "100.00"},
            ],
        }
        self.assertEqual(client.build_write_payload(legacy, BOOK)["doctype"], "RR")
        self.assertNotIn("purchase", WRITE_SPECS)
        self.assertNotIn("sales", WRITE_SPECS)


class PayloadKeyContractTests(unittest.TestCase):
    """桥端按 direction 分表做白名单,契约外键 = bad_payload 整条写路熄火(桥不随主站部署)。"""

    def test_keys_within_registered_contract(self):
        for direction, payload in _payloads().items():
            with self.subTest(direction=direction):
                extra = set(payload) - DOCTYPE_PAYLOAD_KEYS[direction]
                self.assertFalse(extra, f"未登记的载荷键须同步桥端白名单: {sorted(extra)}")

    def test_conditional_keys_really_appear(self):
        # 条件键不出现 → 上一条"⊆"恒真变假绿。
        payloads = _payloads()
        self.assertLessEqual({"advance", "prior_docnum"}, set(payloads["ar_receipt"]))
        self.assertIn("withholding", payloads["ap_payment"])
        self.assertLessEqual({"voucher_no", "vat"}, set(payloads["gl_journal"]))
        self.assertIn("prior_docnum", payloads["stock_adjust"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
