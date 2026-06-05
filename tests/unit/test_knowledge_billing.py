# -*- coding: utf-8 -*-
"""知识库计费 + 全格式入库守门(钱路径 · 铁律 #26/#28)。

- deduct_thb:扣 balance_thb 的算术 + credit_transactions 记账 + 豁免/零额放行。
- host_provider.charge_credits:satang → THB 换算正确传给 deduct_thb。
- process_uploaded_any:文本走纯核心(ocr_pages=0·按字符),图片走 OCR(ocr_pages>0·按页)。
"""

import unittest
from decimal import Decimal
from unittest import mock


class _FakeCur:
    def __init__(self, balance):
        self._balance = balance
        self.execs = []

    def execute(self, sql, params=None):
        self.execs.append((sql, params))
        self._last = sql

    def fetchone(self):
        if "SELECT balance_thb" in self._last or "INSERT INTO tenant_credits" in self._last:
            return {"balance_thb": self._balance}
        return None


class _FakeCtx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class DeductThbTests(unittest.TestCase):
    def _run(self, balance, cost, exempt=False):
        from services.billing import charge

        cur = _FakeCur(balance)
        fake_db = mock.Mock()
        fake_db.is_user_billing_exempt.return_value = exempt
        fake_db.get_cursor.return_value = _FakeCtx(cur)
        with mock.patch.object(charge, "db", fake_db):
            res = charge.deduct_thb("u1", "t1", cost, "rag_answer", "test")
        return res, cur

    def test_deducts_and_records(self):
        res, cur = self._run(Decimal("10.00"), Decimal("0.50"))
        self.assertTrue(res["ok"])
        self.assertAlmostEqual(res["balance_after"], 9.50, places=2)
        # 末次 INSERT 进 credit_transactions · amount_thb = -0.50
        inserts = [e for e in cur.execs if "credit_transactions" in e[0]]
        self.assertEqual(len(inserts), 1)
        self.assertIn("-0.50", inserts[0][1])

    def test_zero_cost_noop(self):
        res, cur = self._run(Decimal("10.00"), Decimal("0"))
        self.assertTrue(res["ok"])
        self.assertEqual(res["charged_thb"], 0.0)
        self.assertEqual([e for e in cur.execs if "UPDATE" in e[0]], [])

    def test_exempt_skips(self):
        res, cur = self._run(Decimal("10.00"), Decimal("0.50"), exempt=True)
        self.assertTrue(res.get("exempt"))
        self.assertEqual(cur.execs, [])

    def test_can_go_negative(self):
        res, _ = self._run(Decimal("0.20"), Decimal("0.50"))
        self.assertAlmostEqual(res["balance_after"], -0.30, places=2)


class ProviderChargeTests(unittest.TestCase):
    def test_satang_to_thb(self):
        from services.knowledge import host_provider

        prov = host_provider.MainHostProvider()
        with mock.patch("services.billing.charge.deduct_thb") as deduct:
            deduct.return_value = {"ok": True}
            prov.charge_credits("t1", "rag_answer", 50, {"user_id": "u1"})
        deduct.assert_called_once()
        # 第3位参 cost_thb = 50 satang / 100 = ฿0.50
        self.assertEqual(deduct.call_args.args[2], Decimal("0.50"))

    def test_zero_amount_no_charge(self):
        from services.knowledge import host_provider

        prov = host_provider.MainHostProvider()
        with mock.patch("services.billing.charge.deduct_thb") as deduct:
            prov.charge_credits("t1", "rag_answer", 0, {})
        deduct.assert_not_called()


class OcrIngestDispatchTests(unittest.TestCase):
    def test_text_is_char_billed(self):
        from services.knowledge.ocr_ingest import process_uploaded_any

        out = process_uploaded_any("policy.csv", "a,b\n差旅费上限,5000\n".encode("utf-8"))
        self.assertEqual(out.status, "ready")
        self.assertEqual(out.ocr_pages, 0)
        self.assertGreater(out.char_count, 0)

    def test_image_routes_to_ocr_and_is_page_billed(self):
        from services.knowledge import ocr_ingest

        fake_page = mock.Mock(full_text="差旅费单笔上限 5000 泰铢")
        fake_result = mock.Mock(pages=[fake_page], page_count=1)
        fake_vision = mock.Mock()
        fake_vision.extract_from_image_bytes.return_value = fake_result
        with mock.patch.dict("sys.modules", {"services.ocr.layer1_vision": fake_vision}):
            # 让 `from services.ocr import layer1_vision` 命中 fake
            with mock.patch("services.ocr.layer1_vision", fake_vision, create=True):
                out = ocr_ingest.process_uploaded_any("scan.png", b"\x89PNG fake")
        self.assertEqual(out.status, "ready")
        self.assertEqual(out.ocr_pages, 1)


if __name__ == "__main__":
    unittest.main()
