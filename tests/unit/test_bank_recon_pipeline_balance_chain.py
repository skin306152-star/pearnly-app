# -*- coding: utf-8 -*-
"""台账#11 · 图片/扫描件银行对账单路必须跑余额链三件套。

实弹坐实:_parse_bank_stmt_via_pipeline 拿到行直接返回,方向纠正/逐行核对只在
PDF 与 xlsx 路生效 → 5/56 行存取方向翻转静默放行。本测试锁三条:
① 方向翻转行被余额涨跌纠正回来;② 对不上的行标 balance_ok=False 并顶起
needs_review;③ 文档级期初/期末透传 + 汇总行过滤。
"""

import unittest
from unittest.mock import patch

from services.recon.bank_recon_pipeline import _parse_bank_stmt_via_pipeline


def _legacy(entries, opening="", closing="", needs_review=False):
    return {
        "pages": [
            {
                "document": {
                    "bank_name": "KBANK",
                    "opening_balance": opening,
                    "closing_balance": closing,
                    "entries": entries,
                }
            }
        ],
        "_needs_review": needs_review,
    }


def _run(legacy_dict):
    with (
        patch("services.ocr.pipeline.run_on_image_bytes", return_value=object()),
        patch(
            "services.ocr.legacy_adapter.pipeline_result_to_legacy_dict",
            return_value=legacy_dict,
        ),
    ):
        return _parse_bank_stmt_via_pipeline(b"\xff\xd8fake", "stmt.jpg")


class DirectionFlipAutocorrectTests(unittest.TestCase):
    def test_flipped_row_corrected_by_balance_delta(self):
        # 余额 1000→1500(涨 500)却被记成取款 500 → 应纠为存款
        res = _run(
            _legacy(
                [
                    {
                        "transaction_date": "2026-07-01",
                        "description": "ฝากเงิน",
                        "deposit": "500",
                        "withdrawal": "",
                        "balance": "1500",
                    },
                    {
                        "transaction_date": "2026-07-02",
                        "description": "โอนออก",
                        "deposit": "200",
                        "withdrawal": "",
                        "balance": "1300",
                    },
                ],
                opening="1000",
            )
        )
        self.assertTrue(res["ok"])
        r2 = res["rows"][1]
        self.assertEqual(r2.withdrawal, 200.0)
        self.assertEqual(r2.deposit, 0.0)
        self.assertTrue(r2.direction_autocorrected)
        self.assertEqual(res["balance_warn_count"], 0)

    def test_broken_chain_flags_review(self):
        # 金额与余额涨跌都对不上(非单纯方向反)→ 不瞎改 · 标 balance_ok=False 顶起复核
        res = _run(
            _legacy(
                [
                    {
                        "transaction_date": "2026-07-01",
                        "description": "ฝากเงิน",
                        "deposit": "500",
                        "withdrawal": "",
                        "balance": "1500",
                    },
                    {
                        "transaction_date": "2026-07-02",
                        "description": "ถอนเงิน",
                        "deposit": "",
                        "withdrawal": "100",
                        "balance": "1250",
                    },
                ],
                opening="1000",
            )
        )
        self.assertIs(res["rows"][1].balance_ok, False)
        self.assertEqual(res["balance_warn_count"], 1)
        self.assertTrue(res["needs_review"])


class DocLevelFieldsTests(unittest.TestCase):
    def test_opening_closing_passthrough_and_summary_filtered(self):
        res = _run(
            _legacy(
                [
                    {
                        "transaction_date": "2026-07-01",
                        "description": "ฝากเงิน",
                        "deposit": "500",
                        "withdrawal": "",
                        "balance": "1500",
                    },
                    {
                        "transaction_date": "",
                        "description": "รวมรายการ",
                        "deposit": "500",
                        "withdrawal": "",
                        "balance": "",
                    },
                ],
                opening="1000",
                closing="1500",
            )
        )
        self.assertEqual(res["opening"], 1000.0)
        self.assertEqual(res["closing"], 1500.0)
        self.assertEqual(res["row_count"], 1)  # 汇总行不是交易

    def test_closing_backfilled_from_last_balance(self):
        res = _run(
            _legacy(
                [
                    {
                        "transaction_date": "2026-07-01",
                        "description": "ฝากเงิน",
                        "deposit": "500",
                        "withdrawal": "",
                        "balance": "1500",
                    },
                ],
                opening="1000",
            )
        )
        self.assertEqual(res["closing"], 1500.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
