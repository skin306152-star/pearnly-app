# -*- coding: utf-8 -*-
"""会计手录四类单据(收款/付款/手工凭证/库存调整)的载荷组装与写路总闸。

每类各钉五条:正常组装 / 缺必填拒 / 恒等式(借贷)不平拒 / 金额异常拒 / 日期异常拒。
组装器与总闸分开钉 —— 重推/回放不经组装器,只过 check_payload 那一道;两处都必须拦得住
被改过的载荷,否则改一个 net_amount 就能让桥去反写别人的发票单头。

另钉桥门面按 direction 分派:四类各自认自己的 doctype、未知 direction 仍拒、老链路
(purchase/sales)一个字节不变。

表单样例与 golden 载荷同一份(`_express_doctype_golden`)—— 契约测试喂桥端的就是它,
两处各写一份样例,改了键名只有一处会红,另一处继续照着旧形状报绿。
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
from tests.unit._express_doctype_golden import (  # noqa: E402
    BOOK,
    golden_payloads,
    journal_req,
    payment_req,
    receipt_req,
    stock_req,
)

_CONFIG = {"account_set": BOOK}


def _ok(result):
    assert result.ok, result.reason
    return result.payload


class ReceiptPayloadTests(unittest.TestCase):
    def test_normal_assembly(self):
        p = _ok(build_receipt_payload(receipt_req(), config=_CONFIG))
        self.assertEqual((p["direction"], p["doctype"]), ("ar_receipt", "RE"))
        # 日期发公历 ISO(桥端 doc_receipt 只认 date.fromisoformat),不发佛历。
        self.assertEqual(p["receipt_date"], "2026-01-15")
        self.assertEqual(p["customer_code"], "C001")
        self.assertEqual(p["channels"][0]["isrun_zr_prefix"], "TR")
        # 代扣税腿/预收腿的科目也只能来自载荷指定的 ZR 前缀(桥端 `_zr_account` 没有兜底)。
        self.assertEqual(p["wht_isrun_zr_prefix"], "TX")
        self.assertEqual(p["advance"]["isrun_zr_prefix"], "M1")
        # NETAMT/CSHRCV/CHQRCV 由桥端按 channels 自推,云端不下发派生桶。
        self.assertFalse({"net_amount", "cash_amount", "cheque_amount"} & set(p))

    def test_zr_prefix_is_mandatory_per_leg(self):
        cases = (
            ("代扣税腿", {"wht_isrun_zr_prefix": ""}, "no_wht_isrun_zr_prefix"),
            (
                "预收腿",
                {"advance": {"doc_no": "AD-001", "amount": "70.00"}},
                "no_advance_isrun_zr_prefix",
            ),
        )
        for label, over, reason in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    build_receipt_payload(receipt_req(**over), config=_CONFIG).reason, reason
                )

    def test_unallocated_receipt_needs_explicit_flag(self):
        # 挂账收款(ARRCPIT 0 行)是真存在的形态,但必须会计显式点头。
        self.assertEqual(
            build_receipt_payload(receipt_req(allocations=[]), config=_CONFIG).reason,
            "no_allocations",
        )
        p = _ok(
            build_receipt_payload(
                receipt_req(allocations=[], allow_unallocated=True, advance=None),
                config=_CONFIG,
            )
        )
        self.assertTrue(p["allow_unallocated"])

    def test_rejects(self):
        cases = (
            ("缺客户码", {"customer_code": ""}, "no_customer_code"),
            ("缺渠道且无代扣", {"channels": [], "wht_amount": "0"}, "no_channels"),
            (
                "C3 不闭合(冲销额与实收对不上)",
                {"allocations": [{"doc_no": "IV1", "rectyp": "3", "amount": "900.00"}]},
                "receipt_identities_not_closed",
            ),
            (
                "金额解析不了",
                {"channels": [{"isrun_zr_prefix": "TR", "kind": "transfer", "amount": "一千"}]},
                "bad_channel_amount",
            ),
            (
                "渠道前缀超宽(截断会指到另一条真实渠道行上)",
                {"channels": [{"isrun_zr_prefix": "TRX", "kind": "transfer", "amount": "1040"}]},
                "bad_channel_prefix",
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
        self.assertEqual(p["payment_date"], "2026-01-15")
        self.assertEqual((p["supplier_code"], p["wht_amount"]), ("S001", "30.00"))
        self.assertEqual(p["channels"][0]["isrun_zp_prefix"], "QP")
        self.assertTrue(p["channels"][0]["is_cheque"])
        self.assertEqual(p["withholding"]["tax_type"], "S53")
        # BKMAS/BKTRN.BNKACC 是银行档编码 C(2),不是银行账号 —— 发账号会在桥端写完
        # APTRN/APRCPIT/GL 之后炸在最后一张 BKTRN 上,变成半写回滚。
        self.assertEqual(p["channels"][0]["bank_account"], "01")
        # NETAMT/CSHPAY/CHQPAY 由桥端按 settlements + is_cheque 自推,云端不下发派生桶。
        self.assertFalse({"net_amount", "cash_amount", "cheque_amount"} & set(p))

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
            (
                "支票缺银行档编码",
                {"channels": [{**cheque, "bank_account": ""}]},
                "bad_bank_account",
            ),
            (
                "银行档编码填成了账号",
                {"channels": [{**cheque, "bank_account": "1234567890"}]},
                "bad_bank_account",
            ),
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
        self.assertEqual((p["voucher_date"], p["journal_code"]), ("2026-01-15", "00"))
        # 科目列名是 account —— 桥端 doc_journal 逐行读它,发 acc 等于整行没科目。
        self.assertEqual(p["lines"][0]["account"], "5140-10")
        # 行级只发桥端 `Leg` 装得下的列:DESCRP 由桥端统一抄单头,phase/coscod 那儿没有位置。
        # 发了不报错,是会计逐行敲的内容静默蒸发。
        self.assertFalse({"desc", "phase", "coscod"} & set(p["lines"][0]))
        self.assertEqual(p["lines"][0]["depcod"], "01")
        # 税期发公历 ISO:桥端 `_write_isvat` 用 iso_date 取年月,佛历串会静默回落成凭证日。
        self.assertEqual(p["vat"]["vat_period"], "2026-01-01")
        self.assertNotIn("vat_period_be", p["vat"])

    def test_rejects(self):
        cases = (
            ("缺本账代码", {"journal_code": ""}, "no_journal_code"),
            ("缺摘要", {"description": ""}, "no_description"),
            (
                "借贷不平",
                {
                    "lines": [
                        {"account": "5140-10", "side": "D", "amount": "500.00"},
                        {"account": "2130-01", "side": "C", "amount": "400.00"},
                    ]
                },
                "bad_journal_lines",
            ),
            (
                "只有一行",
                {"lines": [{"account": "5140-10", "side": "D", "amount": "500.00"}]},
                None,
            ),
            (
                "金额为负(方向只由 side 表达)",
                {
                    "lines": [
                        {"account": "5140-10", "side": "D", "amount": "-500.00"},
                        {"account": "2130-01", "side": "C", "amount": "-500.00"},
                    ]
                },
                None,
            ),
            (
                "金额解析不了",
                {
                    "lines": [
                        {"account": "5140-10", "side": "D", "amount": "五百"},
                        {"account": "2130-01", "side": "C", "amount": "500.00"},
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
        # 方向由 subtype 表达(桥端据它写 POSOPR='6'),不看金额符号(45 号契约 X1)。
        self.assertEqual((p["subtype"], p["doc_date"]), ("internal_issue", "2026-01-15"))
        self.assertEqual(p["lines"][0]["amount"], "500.00")
        # 明细键是 lines(桥端 doc_stock_adjust 读它);POSOPR/NET 由桥端自推。
        self.assertFalse({"items", "posopr", "net_amount"} & set(p))

    def test_quantity_keeps_four_decimals(self):
        # 库存余额靠 XTRNQTY = TRNQTY × TFACTOR 移动(都是 B(8,4)):数量跟着钱走两位,
        # 0.0625 公斤会变成 0.06,余额再也对不回去。
        line = stock_req()["lines"][0]
        p = _ok(
            build_stock_adjust_payload(
                stock_req(
                    lines=[{**line, "qty": "0.0625", "unit_price": "16", "tfactor": "1.408"}]
                ),
                config=_CONFIG,
            )
        )
        line = p["lines"][0]
        self.assertEqual((line["qty"], line["tfactor"]), ("0.0625", "1.4080"))
        self.assertEqual(line["amount"], "1.00")
        # 四位以下的数量落位后就是 0 —— 当场退回,不推一张数量为零的调整单。
        self.assertEqual(
            build_stock_adjust_payload(
                stock_req(lines=[{**line, "qty": "0.00004"}]), config=_CONFIG
            ).reason,
            "bad_item_qty",
        )

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


class WriteGateDispatchTests(unittest.TestCase):
    """桥门面按 direction 分派 —— 四类各认自己的 doctype,老链路不受影响。"""

    def test_each_doctype_passes_the_write_gate(self):
        for direction, payload in golden_payloads().items():
            with self.subTest(direction=direction):
                self.assertEqual(client.build_write_payload(payload, BOOK)["direction"], direction)

    def test_tampered_payload_is_rejected_at_the_gate(self):
        # 重推/回放不经组装器:总闸必须自己拦得住被改过的载荷。派生金额已不下发,所以
        # 每类改的是它唯一还能被改坏的那个数(改完对应的恒等式必须当场不闭合)。
        payloads = golden_payloads()
        stock_lines = [{**payloads["stock_adjust"]["lines"][0], "amount": "999999.00"}]
        bad = (
            ("ar_receipt", {**payloads["ar_receipt"], "shortfall_amount": "999999.00"}),
            ("ap_payment", {**payloads["ap_payment"], "wht_amount": "999999.00"}),
            ("gl_journal", {**payloads["gl_journal"], "total_amount": "999999.00"}),
            ("stock_adjust", {**payloads["stock_adjust"], "lines": stock_lines}),
        )
        for direction, payload in bad:
            with self.subTest(direction=direction), self.assertRaises(BridgeRejected) as ctx:
                client.build_write_payload(payload, BOOK)
            self.assertEqual(ctx.exception.code, "bridge.bad_payload")

    def test_shape_rejects(self):
        receipt = golden_payloads()["ar_receipt"]
        journal = golden_payloads()["gl_journal"]
        cases = (
            ("doctype 与 direction 不配", {**receipt, "doctype": "PS"}, BOOK),
            ("串用老链路票种", {**journal, "doctype": "RR"}, BOOK),
            ("未知 direction", {**receipt, "direction": "ar_refund"}, BOOK),
            ("账套与 book 不一致", receipt, "OTHER"),
            ("版本不符", {**receipt, "payload_version": 2}, BOOK),
            # 佛历串正是 P2-B 那刀:桥端只认 ISO,发 690115 一律 INVALID_DOC_DATE。
            ("日期发成佛历", {**receipt, "receipt_date": "690115"}, BOOK),
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
        for direction, payload in golden_payloads().items():
            with self.subTest(direction=direction):
                extra = set(payload) - DOCTYPE_PAYLOAD_KEYS[direction]
                self.assertFalse(extra, f"未登记的载荷键须同步桥端白名单: {sorted(extra)}")

    def test_conditional_keys_really_appear(self):
        # 条件键不出现 → 上一条"⊆"恒真变假绿。
        payloads = golden_payloads()
        self.assertLessEqual(
            {"advance", "wht_isrun_zr_prefix", "prior_docnum"}, set(payloads["ar_receipt"])
        )
        self.assertIn("withholding", payloads["ap_payment"])
        self.assertLessEqual({"voucher_no", "vat"}, set(payloads["gl_journal"]))
        self.assertIn("prior_docnum", payloads["stock_adjust"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
