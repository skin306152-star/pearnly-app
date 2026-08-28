# -*- coding: utf-8 -*-
"""DMS 订车单建单载荷:订金支付渠道聚合 + 登记人姓名。

payment_form_fields 纯函数直接测; _apply_booking_form_fields 走假客户端
验证字段落进表单 dict(regis_name 覆盖/回落、空渠道保持现状逐字节一致)。
"""

import unittest

from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
from services.erp.mrerp_dms_payments import payment_form_fields
from services.erp.mrerp_dms_models import (
    DMSBookingPayload,
    DMSMasterRef,
    ThaiAddress,
    ThaiIdCardPayload,
)

_CHANNEL_KEYS = (
    "txtmoneycash",
    "txtmoneytfmon",
    "txtmoneycheque",
    "txtmoneycashiercq",
    "txtmoneycddbc",
    "txtmoneyother",
)


def _card(name="สมชาย ใจดี"):
    return ThaiIdCardPayload(
        people_id="1234567890121",
        first_name="สมชาย",
        last_name="ใจดี",
        birthday_be="01/01/2530",
        address=ThaiAddress(house_no="1", province_id="10"),
        phone="0891234567",
    )


def _ref(uid, code="C", name="N"):
    return DMSMasterRef(id=uid, code=code, name=name)


def _booking(**kw):
    base = dict(
        doc_date_be="01/08/2569",
        delivery_date_be="16/08/2569",
        advisor=_ref("a1"),
        car=_ref("c1"),
        paint=_ref("p1"),
        place_book=_ref("pb1"),
        term_sale=_ref("ts1"),
        branch=_ref("b1"),
        team=_ref("t1"),
        regis_behalf=_ref("rb1"),
    )
    base.update(kw)
    return DMSBookingPayload(**base)


class _FormClient(DMSClientOpsMixin):
    """只留 _apply_booking_form_fields 需要的两个辅助,其余依赖不碰。"""

    def _extra(self, ref, idx):
        return str(ref.extra[idx]) if len(ref.extra) > idx else ""

    def _apply_address_to_booking_form(self, data, address):
        pass


class TestPaymentFormFields(unittest.TestCase):
    def test_empty_payments_returns_empty(self):
        self.assertEqual(payment_form_fields(()), {})

    def test_single_cash_channel(self):
        fields = payment_form_fields(({"channel": "cash", "amount": "5000", "extra": {}},))
        self.assertEqual(fields["txtmoneycash"], "5000.00")
        self.assertEqual(fields["txtearnestmoney"], "5000.00")

    def test_transfer_src_dst_verbatim(self):
        fields = payment_form_fields(
            (
                {
                    "channel": "transfer",
                    "amount": "2000.50",
                    "extra": {"src": "ACC-SRC", "dst": "ACC-DST"},
                },
            )
        )
        self.assertEqual(fields["txtmoneytfmon"], "2000.50")
        self.assertEqual(fields["txtaccountnumtffrom"], "ACC-SRC")
        self.assertEqual(fields["txtaccountnumtfmon"], "ACC-DST")
        self.assertEqual(fields["txtearnestmoney"], "2000.50")

    def test_transfer_dash_src_skipped(self):
        fields = payment_form_fields(
            (
                {
                    "channel": "transfer",
                    "amount": "1000",
                    "extra": {"src": "-", "dst": "ACC-DST"},
                },
            )
        )
        self.assertNotIn("txtaccountnumtffrom", fields)
        self.assertEqual(fields["txtaccountnumtfmon"], "ACC-DST")
        self.assertEqual(fields["txtmoneytfmon"], "1000.00")

    def test_same_channel_sums_decimals(self):
        fields = payment_form_fields(
            (
                {"channel": "cash", "amount": "1000.50", "extra": {}},
                {"channel": "cash", "amount": "2000", "extra": {}},
            )
        )
        self.assertEqual(fields["txtmoneycash"], "3000.50")
        self.assertEqual(fields["txtearnestmoney"], "3000.50")

    def test_multi_entry_text_joined(self):
        fields = payment_form_fields(
            (
                {
                    "channel": "transfer",
                    "amount": "1000",
                    "extra": {"src": "SRC-A", "dst": "DST-A"},
                },
                {
                    "channel": "transfer",
                    "amount": "1500.75",
                    "extra": {"src": "SRC-B", "dst": "DST-B"},
                },
            )
        )
        self.assertEqual(fields["txtmoneytfmon"], "2500.75")
        self.assertEqual(fields["txtaccountnumtffrom"], "SRC-A / SRC-B")
        self.assertEqual(fields["txtaccountnumtfmon"], "DST-A / DST-B")

    def test_all_six_channels(self):
        pays = (
            {"channel": "cash", "amount": "100", "extra": {}},
            {"channel": "transfer", "amount": "200", "extra": {"src": "S", "dst": "D"}},
            {"channel": "cheque", "amount": "300", "extra": {"ref": "CHQ1"}},
            {"channel": "cashier_cheque", "amount": "400", "extra": {"ref": "CCQ1"}},
            {"channel": "card", "amount": "500", "extra": {"ref": "CARD1"}},
            {"channel": "other", "amount": "600", "extra": {"detail": "cash on delivery"}},
        )
        fields = payment_form_fields(pays)
        self.assertEqual(fields["txtmoneycash"], "100.00")
        self.assertEqual(fields["txtmoneytfmon"], "200.00")
        self.assertEqual(fields["txtaccountnumtffrom"], "S")
        self.assertEqual(fields["txtaccountnumtfmon"], "D")
        self.assertEqual(fields["txtmoneycheque"], "300.00")
        self.assertEqual(fields["txtchequeno"], "CHQ1")
        self.assertEqual(fields["txtmoneycashiercq"], "400.00")
        self.assertEqual(fields["txtcashiercqno"], "CCQ1")
        self.assertEqual(fields["txtmoneycddbc"], "500.00")
        self.assertEqual(fields["txttypenamecddbc"], "CARD1")
        self.assertEqual(fields["txtmoneyother"], "600.00")
        self.assertEqual(fields["txtdetailother"], "cash on delivery")
        self.assertEqual(fields["txtearnestmoney"], "2100.00")

    def test_unknown_channel_raises(self):
        with self.assertRaises(ValueError):
            payment_form_fields(({"channel": "bitcoin", "amount": "1", "extra": {}},))

    def test_comma_amount_normalized(self):
        fields = payment_form_fields(({"channel": "cash", "amount": "1,000.50", "extra": {}},))
        self.assertEqual(fields["txtmoneycash"], "1000.50")
        self.assertEqual(fields["txtearnestmoney"], "1000.50")


class TestApplyBookingFormFields(unittest.TestCase):
    def test_empty_payments_keeps_legacy_defaults(self):
        """空渠道 → 与现状逐字节一致:txtearnestmoney 0.00、无任何渠道键。"""
        data = {}
        _FormClient()._apply_booking_form_fields(
            data, customer_id="100", booking=_booking(), card=_card()
        )
        self.assertEqual(data["txtearnestmoney"], "0.00")
        for key in _CHANNEL_KEYS:
            self.assertNotIn(key, data)

    def test_channel_fields_land_in_form(self):
        data = {}
        _FormClient()._apply_booking_form_fields(
            data,
            customer_id="100",
            booking=_booking(payments=({"channel": "cash", "amount": "5000", "extra": {}},)),
            card=_card(),
        )
        self.assertEqual(data["txtmoneycash"], "5000.00")
        self.assertEqual(data["txtearnestmoney"], "5000.00")

    def test_regis_name_overrides_card_name(self):
        data = {}
        _FormClient()._apply_booking_form_fields(
            data,
            customer_id="100",
            booking=_booking(regis_name="นายแดง ทองดี"),
            card=_card(),
        )
        self.assertEqual(data["txtregisname"], "นายแดง ทองดี")

    def test_regis_name_empty_falls_back_to_card_name(self):
        data = {}
        _FormClient()._apply_booking_form_fields(
            data, customer_id="100", booking=_booking(), card=_card()
        )
        self.assertEqual(data["txtregisname"], "สมชาย ใจดี")


if __name__ == "__main__":
    unittest.main()
