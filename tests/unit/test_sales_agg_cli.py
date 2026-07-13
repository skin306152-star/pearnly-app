# -*- coding: utf-8 -*-
"""CLI 入口(services.sales_agg.cli):退出码契约 + 报告落盘。"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from services.sales_agg import cli

CLEAN = {
    "edc_settlement": [
        {
            "settle_date": "15/05/2569",
            "gross_amount": "10,700.00",
            "fee_amount": "160.50",
            "net_amount": "10,539.50",
            "batch_no": "B001",
            "terminal_id": "70001234",
        }
    ],
    "bank_credit": [
        {
            "tx_date": "2026-05-16",
            "amount": "10,539.50",
            "direction": "IN",
            "description": "EDC SETTLEMENT KBANK",
            "_tx_id": "tx1",
        }
    ],
}


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def _run(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(list(argv))
        return code, buf.getvalue()

    def _write(self, name, payload):
        path = self.dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_clean_month_exit_zero_and_report_written(self):
        src = self._write("in.json", CLEAN)
        out = self.dir / "out.json"
        code, text = self._run(str(src), str(out))
        self.assertEqual(code, 0, text)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(report["month_total"]["gross"], "10700.00")
        self.assertEqual(report["month_total"]["output_vat"], "700.00")
        self.assertEqual(len(report["links"]), 1)

    def test_conflicts_or_gaps_exit_two(self):
        payload = dict(CLEAN)
        payload["bank_credit"] = CLEAN["bank_credit"] + [
            {"tx_date": "2026-05-20", "amount": "2,000.00", "_tx_id": "tx9"}
        ]
        src = self._write("in.json", payload)
        code, text = self._run(str(src))
        self.assertEqual(code, 2, text)
        self.assertIn("credit_without_evidence", text)

    def test_usage_and_io_errors_exit_one(self):
        self.assertEqual(self._run()[0], 1)
        self.assertEqual(self._run(str(self.dir / "missing.json"))[0], 1)
        bad = self.dir / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        self.assertEqual(self._run(str(bad))[0], 1)


if __name__ == "__main__":
    unittest.main()
