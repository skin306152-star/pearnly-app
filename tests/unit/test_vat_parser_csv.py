# -*- coding: utf-8 -*-
"""F23 · VAT csv 支路确定性直读(vat_parser_csv.py)行为契约。

背景(bench 实弹):779 行真表被 layer2 30K 窗口截到 20 行(B 档召回 0.64%)、qwen
60s 超时 —— CSV 是结构化文本,列名映射命中就代码直读,映射不命中回原 pipeline 兜底。
锁:同一契约形状(pipeline 出口 report_* 键齐备)· Decimal 金额 · 日期归一化成 ISO ·
cp874/utf-8 双编码 · 坏行跳过进 warnings · 空文件兜底 · 直读不看引擎档。
"""

import io
import os
import unittest
from unittest import mock

from services.vat import vat_parser_csv as vpc
from services.vat import vat_report_parser as vp

# 与真 csv(acvatsaled_5月779单.csv)同结构的 12 列表头
_ERP_HEADER = (
    "ref,vat_no,vat_date,detail_id,txtdoctype,txtsino,txtsidate,"
    "txtsvatno,txtvatdate,txtamt,txtvatamt,txtvatamtbal"
)


def _erp_rows(n: int = 20, start: int = 1) -> list:
    rows = []
    for i in range(start, start + n):
        inv = f"SI690531-{i:03d}"
        amt = 100.0 + i
        vat = round(amt * 0.07, 2)
        rows.append(
            [
                inv,
                inv[2:],
                "31/05/2569",
                str(1000 + i),
                "VS",
                inv,
                "31/05/2569",
                inv[2:],
                "31/05/2569",
                f"{amt:.2f}",
                f"{vat:.2f}",
                "0.00",
            ]
        )
    return rows


def _erp_csv_bytes(n: int = 20, encoding: str = "utf-8") -> bytes:
    lines = [_ERP_HEADER] + [",".join(r) for r in _erp_rows(n)]
    return "\n".join(lines).encode(encoding)


def _erp_csv_bytes_cp874(n: int = 20) -> bytes:
    lines = [_ERP_HEADER] + [",".join(r) for r in _erp_rows(n)]
    return "\n".join(lines).encode("cp874")


class ParseCsvDirectTests(unittest.TestCase):
    def test_all_rows_extracted_with_amounts_and_iso_dates(self):
        out = vpc.parse_csv_direct(_erp_csv_bytes(), "acvatsaled.csv")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 20)
        self.assertEqual(len(out["rows"]), 20)
        self.assertEqual(out["method"], "csv_direct_v1")
        self.assertEqual(out["warnings"], [])
        # 抽出行数与金额合计对
        self.assertEqual(
            sum(r["report_amount_pre_vat"] for r in out["rows"]),
            round(sum(100.0 + i for i in range(1, 21)), 2),
        )
        self.assertAlmostEqual(
            sum(r["report_vat_amount"] for r in out["rows"]),
            round(sum(round((100.0 + i) * 0.07, 2) for i in range(1, 21)), 2),
            places=2,
        )
        # 日期归一化成 ISO(佛历 2569 → 2026)
        self.assertEqual(out["rows"][0]["report_date"], "2026-05-31")
        # 单据号双字段同值(与 pipeline 出口一致)
        self.assertEqual(out["rows"][0]["report_invoice_no"], "SI690531-001")
        self.assertEqual(out["rows"][0]["report_ref_no"], "SI690531-001")

    def test_contract_shape_matches_pipeline(self):
        """直读器必须产出与 pipeline 出口同一形状(下游零改动)。"""
        out = vpc.parse_csv_direct(_erp_csv_bytes(), "acvatsaled.csv")
        row = out["rows"][0]
        for key in (
            "row_no",
            "report_date",
            "report_invoice_no",
            "report_ref_no",
            "report_buyer_name",
            "report_buyer_tax_id",
            "report_buyer_branch",
            "report_amount_pre_vat",
            "report_vat_amount",
            "report_amount",
            "is_individual",
        ):
            self.assertIn(key, row)
        for key in (
            "ok",
            "rows",
            "row_count",
            "meta",
            "warnings",
            "parser_version",
            "method",
            "needs_review",
        ):
            self.assertIn(key, out)
        # ERP 无买方列 → 空字符串 + 总部分支码 + 个人买家
        self.assertEqual(row["report_buyer_name"], "")
        self.assertEqual(row["report_buyer_tax_id"], "")
        self.assertEqual(row["report_buyer_branch"], "00000")
        self.assertTrue(row["is_individual"])
        self.assertFalse(out["needs_review"])

    def test_amounts_are_decimal_precise(self):
        """带千分位金额 + 括号负数也能精解析。"""
        lines = [
            _ERP_HEADER,
            'REF1,690531-001,31/05/2569,1,VS,SI690531-001,31/05/2569,690531-001,31/05/2569,"2,336.45",163.55,0.00',
            "REF2,690531-002,31/05/2569,2,VS,SI690531-002,31/05/2569,690531-002,31/05/2569,(100.50),7.04,0.00",
        ]
        out = vpc.parse_csv_direct("\n".join(lines).encode(), "acvatsaled.csv")
        self.assertEqual(out["rows"][0]["report_amount_pre_vat"], 2336.45)
        self.assertEqual(out["rows"][1]["report_amount_pre_vat"], -100.5)  # 括号负数
        self.assertEqual(out["rows"][0]["report_amount"], round(2336.45 + 163.55, 2))

    def test_unknown_columns_fall_back_to_none(self):
        """列结构不认识的 csv → None,调用方走原 pipeline 兜底。"""
        bad = "foo,bar,baz\n1,2,3\n"
        self.assertIsNone(vpc.parse_csv_direct(bad.encode(), "x.csv"))

    def test_empty_file_returns_none(self):
        self.assertIsNone(vpc.parse_csv_direct(b"", "x.csv"))
        self.assertIsNone(vpc.parse_csv_direct(b"\n\n", "x.csv"))

    def test_cp874_encoding(self):
        out = vpc.parse_csv_direct(_erp_csv_bytes_cp874(), "acvatsaled.csv")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 20)

    def test_utf8_with_bom(self):
        data = _erp_csv_bytes()
        out = vpc.parse_csv_direct(b"\xef\xbb\xbf" + data, "acvatsaled.csv")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 20)

    def test_bad_rows_skipped_with_warning(self):
        lines = [
            _ERP_HEADER,
            "SI690531-001,690531-001,31/05/2569,1,VS,SI690531-001,31/05/2569,690531-001,31/05/2569,100.00,7.00,0.00",
            ",,,,VS,,,,,100.00,7.00,0.00",  # 无单据号 → 跳过
            "SI690531-003,690531-003,31/05/2569,3,VS,SI690531-003,31/05/2569,690531-003,31/05/2569,120.00,8.40,0.00",
        ]
        out = vpc.parse_csv_direct("\n".join(lines).encode(), "acvatsaled.csv")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 2)
        self.assertEqual(len(out["warnings"]), 1)
        self.assertIn("跳过 1 行", out["warnings"][0])

    def test_tsv_delimiter(self):
        lines = [_ERP_HEADER.replace(",", "\t")] + ["\t".join(r) for r in _erp_rows(3)]
        out = vpc.parse_csv_direct("\n".join(lines).encode(), "acvatsaled.tsv")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 3)


class ParseCsvThroughImplTests(unittest.TestCase):
    """直读路经 _parse_vat_report_impl 生效(高敏钱路端到端)。"""

    def test_csv_direct_reads_locally_no_pipeline(self):
        with mock.patch("services.vat.vat_report_parser._parse_vat_via_pipeline") as m:
            result = vp._parse_vat_report_impl(_erp_csv_bytes(), "r.csv")
        m.assert_not_called()
        self.assertTrue(result["ok"])
        self.assertEqual(result["row_count"], 20)
        self.assertEqual(result["method"], "csv_direct_v1")

    def test_unknown_csv_falls_back_to_pipeline(self):
        with mock.patch(
            "services.vat.vat_report_parser._parse_vat_via_pipeline",
            return_value={"ok": True, "rows": [], "row_count": 0},
        ) as m:
            result = vp._parse_vat_report_impl(b"foo,bar\n1,2\n", "r.csv")
        m.assert_called_once()
        self.assertTrue(result["ok"])

    def test_tier_env_does_not_change_direct_read(self):
        """直读路根本不进引擎:OCR_ENGINE_MODE 档位改了结果不变。"""
        baseline = vpc.parse_csv_direct(_erp_csv_bytes(), "acvatsaled.csv")
        for mode in ("qwen", "economy", "direct35"):
            with mock.patch.dict(os.environ, {"OCR_ENGINE_MODE": mode}):
                out = vpc.parse_csv_direct(_erp_csv_bytes(), "acvatsaled.csv")
            self.assertEqual(out["rows"], baseline["rows"])
            self.assertEqual(out["row_count"], baseline["row_count"])


class RealCsvSmokeTests(unittest.TestCase):
    """真 779 行 csv 本地 smoke:路径不存在就 skip,不进仓库断言。"""

    _REAL = (
        r"C:\Users\skin3\Desktop\Pearnly-产品语料测试数据\MRERP-SM-SisterMakeup"
        r"(销采单据)\05_销项税登记簿(acvatsaled)\acvatsaled_5月779单.csv"
    )

    def test_real_csv_full_recall(self):
        if not os.path.exists(self._REAL):
            self.skipTest("真 csv 不在本地")
        with open(self._REAL, "rb") as f:
            out = vpc.parse_csv_direct(f.read(), os.path.basename(self._REAL))
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 779)  # 100% 召回


if __name__ == "__main__":
    unittest.main()
