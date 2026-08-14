# -*- coding: utf-8 -*-
"""F9 · vat_parser_gemini 7% 校验后处理(vat 列锚定)守门 + F10 并发 env 覆盖

F9 病灶实锤 doc10:模型把打印的合计 250000 读成税前,输出 subtotal=250000 /
vat=16355.14 / total=266355.14。模型自洽(pre+vat=total)所以自查抓不到,
但 250000×7%≠16355.14。修复:确定性重算 subtotal'=round(vat/0.07,2)、
total'=subtotal'+vat,行上打 vat_repaired 标记 + warnings 说明(状态诚实)。
对通过校验的行零操作是硬约束(B/C 档共用解析器)。

F10:16 个单页批次 8 并发要跑两波次,默认提到 16 单波次;env OCR_VAT_BATCH_WORKERS 可覆盖。
零网络零凭证。
"""

import importlib
import io
import os
import unittest
from unittest import mock

from services.vat import vat_parser_gemini as vpg


def row(pre, vat, total, **kw):
    r = {
        "row_no": kw.pop("row_no", 1),
        "report_date": kw.pop("date", "2026-06-15"),
        "report_invoice_no": kw.pop("inv", "IV69/06-001"),
        "report_ref_no": "",
        "report_buyer_name": "บริษัท ตัวอย่าง จำกัด",
        "report_buyer_tax_id": "0105555123456",
        "report_buyer_branch": "00000",
        "report_amount_pre_vat": pre,
        "report_vat_amount": vat,
        "report_amount": total,
        "is_individual": False,
    }
    r.update(kw)
    return r


class RepairVatConsistencyTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("OCR_VAT_REPAIR", None)

    def tearDown(self):
        os.environ.pop("OCR_VAT_REPAIR", None)

    def test_doc10_repair_anchored_on_vat(self):
        # doc10 实弹:合计 250000 被读成税前 · vat 16355.14 是锚
        out = vpg._repair_vat_consistency([row(250000.0, 16355.14, 266355.14)])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["report_amount_pre_vat"], 233644.86)
        self.assertEqual(out[0]["report_vat_amount"], 16355.14)
        self.assertEqual(out[0]["report_amount"], 250000.0)
        self.assertTrue(out[0].get("vat_repaired"))

    def test_healthy_rows_zero_operation(self):
        # 全量健康行 · 含 doc10 真值组 · 逐行原样通过,零触发
        healthy = [
            row(233644.86, 16355.14, 250000.0),
            row(5000.0, 350.0, 5350.0),
            row(100.0, 7.0, 107.0),
            row(1234.56, 86.42, 1320.98),
            row(999999.99, 70000.0, 1069999.99),
        ]
        out = vpg._repair_vat_consistency(healthy)
        self.assertEqual(out, healthy)
        self.assertFalse(any(r.get("vat_repaired") for r in out))

    def test_vat_zero_or_none_skipped(self):
        rows = [row(100.0, 0, 100.0), row(100.0, None, 100.0)]
        self.assertEqual(vpg._repair_vat_consistency(rows), rows)

    def test_subtotal_missing_skipped(self):
        rows = [row(None, 100.0, 100.0)]
        self.assertEqual(vpg._repair_vat_consistency(rows), rows)

    def test_tolerance_boundary(self):
        # 差 0.005 ≤ 0.01 不触发
        out = vpg._repair_vat_consistency([row(100.0, 7.005, 107.005)])
        self.assertFalse(out[0].get("vat_repaired"))
        # 差 0.02 > 0.01 触发
        out = vpg._repair_vat_consistency([row(100.0, 7.02, 107.02)])
        self.assertTrue(out[0].get("vat_repaired"))

    def test_env_switch_off_disables_repair(self):
        os.environ["OCR_VAT_REPAIR"] = "0"
        rows = [row(250000.0, 16355.14, 266355.14)]
        self.assertEqual(vpg._repair_vat_consistency(rows), rows)


def _fake_out(raw_rows, meta_total_pre=233644.86, meta_vat=16355.14):
    return mock.Mock(
        ok=True,
        error_kind=None,
        data={
            "rows": raw_rows,
            "meta": {"total_amount_pre_vat": meta_total_pre, "total_vat": meta_vat},
        },
        input_tokens=10,
        output_tokens=10,
    )


class ParseWithGeminiRepairWiringTests(unittest.TestCase):
    """接线:doc10 行经 parse_with_gemini 真实解析路径 → 修复 + warnings 说明"""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("GEMINI_API_KEY", None)

    def test_doc10_row_repaired_and_warned(self):
        raw = [
            {
                "row_no": 1,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 250000,
                "report_vat_amount": 16355.14,
                "report_amount": 266355.14,
            },
        ]
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=_fake_out(raw),
        ):
            out = vpg.parse_with_gemini(b"%PDF-fake", "application/pdf")
        self.assertTrue(out["ok"])
        self.assertEqual(out["rows"][0]["report_amount_pre_vat"], 233644.86)
        self.assertEqual(out["rows"][0]["report_amount"], 250000.0)
        self.assertTrue(out["rows"][0].get("vat_repaired"))
        self.assertTrue(any("7%" in w and "修复" in w for w in out["warnings"]))

    def test_healthy_rows_wire_zero_operation(self):
        raw = [
            {
                "row_no": 1,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 233644.86,
                "report_vat_amount": 16355.14,
                "report_amount": 250000.0,
            },
        ]
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=_fake_out(raw),
        ):
            out = vpg.parse_with_gemini(b"%PDF-fake", "application/pdf")
        self.assertTrue(out["ok"])
        self.assertFalse(out["rows"][0].get("vat_repaired"))
        self.assertEqual(out["warnings"], [])
        self.assertEqual(out["rows"][0]["report_amount_pre_vat"], 233644.86)


class BatchWorkersEnvTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("OCR_VAT_BATCH_WORKERS", None)
        importlib.reload(vpg)

    def test_default_is_16(self):
        os.environ.pop("OCR_VAT_BATCH_WORKERS", None)
        importlib.reload(vpg)
        self.assertEqual(vpg._BATCH_WORKERS, 16)

    def test_env_override(self):
        os.environ["OCR_VAT_BATCH_WORKERS"] = "3"
        importlib.reload(vpg)
        self.assertEqual(vpg._BATCH_WORKERS, 3)
        # 恢复默认,避免污染后续用例
        os.environ.pop("OCR_VAT_BATCH_WORKERS", None)
        importlib.reload(vpg)
        self.assertEqual(vpg._BATCH_WORKERS, 16)


if __name__ == "__main__":
    unittest.main()
