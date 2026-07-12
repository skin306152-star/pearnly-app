import pathlib
import unittest

OFFLINE = pathlib.Path("static/pos/pos-offline.js").read_text(encoding="utf-8")
CASHIER = pathlib.Path("static/pos/pos-cashier.js").read_text(encoding="utf-8")


class PosOfflineSyncContractTests(unittest.TestCase):
    def test_receipt_is_device_scoped_and_temporary(self):
        self.assertIn("offline_device_id", OFFLINE)
        self.assertIn("if (!state.terminalId)", OFFLINE)
        self.assertIn("temporary_receipt: true", OFFLINE)
        self.assertIn("status: 'pending'", OFFLINE)
        self.assertNotIn("qty_base = String(Number(p.stock.qty_base || 0) - base)", OFFLINE)
        self.assertIn("canDeductCache(payload.lines)", OFFLINE)

    def test_success_mapping_is_persisted_before_outbox_delete(self):
        saved = OFFLINE.index("await kvSet('receipt_' + it.client_uuid")
        deleted = OFFLINE.index("await outboxDel(it.client_uuid)")
        self.assertLess(saved, deleted)
        self.assertIn("status: 'synced'", OFFLINE)
        self.assertIn("await kvSet('receipt_' + it.receipt_no", OFFLINE)
        self.assertIn("findReceipt:", OFFLINE)
        self.assertIn("if (!r || r.client_uuid !== it.client_uuid)", OFFLINE)

    def test_failures_are_classified_and_backed_off(self):
        for token in ("'retrying'", "'blocked'", "next_retry_at", "tries", "last_error"):
            self.assertIn(token, OFFLINE)
        self.assertIn("status === 401 || status === 403", OFFLINE)
        self.assertIn("'auth_paused'", OFFLINE)
        self.assertIn("status === 409 || status === 422", OFFLINE)

    def test_cashier_reconciles_visible_receipt(self):
        self.assertIn("pos:sale-synced", CASHIER)
        self.assertIn("temporary_receipt", CASHIER)


if __name__ == "__main__":
    unittest.main()
