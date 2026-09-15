"""All OA channels execute the same bank-selection-only transfer contract."""

import unittest
from tests.manual.dms_transfer_demo import interact
from services.line_dms.booking_payments import normalize_editor_payments
from services.erp.mrerp_dms_payments import payment_form_fields


class TransferOaParityTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_oa_and_bank_shapes_reach_slip_without_details(self):
        for channel in ("dms", "dms_a", "dms_b"):
            for branch, account in (("Rayong", "123456"), ("00", "00"), ("Rayong", "")):
                with self.subTest(channel=channel, branch=branch, account=account):
                    banks = [["1", "SCB", "SCB", branch, account]]
                    start = await interact(channel, "reset", banks=banks)
                    amount = await interact(channel, "text", "1000", start["session"], banks)
                    self.assertEqual(amount["step"], "pay_dst")
                    chosen = await interact(
                        channel, "postback", "qa:bank:1", amount["session"], banks
                    )
                    self.assertEqual(chosen["step"], "slip_after")
                    payments = chosen["session"]["payload"]["qa"]["payments"]
                    normalized = normalize_editor_payments(payments, {"company_banks": banks})
                    fields = payment_form_fields(tuple(normalized))
                    self.assertEqual(fields["banktfmonval"], "1")
                    self.assertEqual(fields["txtmoneytfmon"], "1000.00")
                    self.assertNotIn("txtowneraccnametffrom", fields)
                    uploaded = await interact(
                        channel, "image", session=chosen["session"], banks=banks
                    )
                    self.assertEqual(uploaded["step"], "pay_more")
