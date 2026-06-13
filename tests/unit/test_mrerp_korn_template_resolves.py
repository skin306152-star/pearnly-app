# -*- coding: utf-8 -*-
"""回归守门 · MR.ERP 销项赊销 xlsx 必须走 Korn 克隆,不许静默回退 openpyxl。

2026-06-03 目录重组(d05cf6d)把 mrerp_xlsx_sales_credit 移入 services/erp/,
但模板 test_data_mrerp_sample_SC.xlsx 留在仓库根 → os.path.dirname(__file__) 找不到
→ 静默回退 openpyxl 版 → MR.ERP 拒收"จำนวนคอลัมภ์ข้อมูลไม่ครบ 18 คอลัมภ์"(列数不足18)
→ 推送全失败(2026-06-13 实测确认)。本测试锁死:模板可定位 + 输出是 18 列的真模板格式。
"""

import io
import unittest
import zipfile
from pathlib import Path

from services.erp import mrerp_xlsx_generator as gen


def _min_history():
    return {
        "client_id": 99,
        "invoice_number": "GUARD-001",
        "invoice_date": "2026-05-09",
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
        "items": [{"name": "ITEM", "qty": 1, "unit_price": 100, "amount": 100}],
    }


def _min_mappings():
    return {
        "clients": [{"erp_type": "mrerp", "client_id": 99, "erp_code": "0006"}],
        "accounts": [],
        "taxes": [],
        "products": [],
    }


class KornTemplateResolvesTests(unittest.TestCase):
    def test_template_locatable_from_repo_root(self):
        root = Path(__file__).resolve().parents[2]
        self.assertTrue(
            (root / "test_data_mrerp_sample_SC.xlsx").exists(),
            "Korn 模板必须在仓库根 git-tracked · 否则销项推送回退 openpyxl 被 MR.ERP 拒收",
        )

    def test_generate_xlsx_is_korn_clone_with_18_cols(self):
        data = gen.generate_xlsx([_min_history()], _min_mappings(), sheet_kind="sales_credit")
        self.assertTrue(data.startswith(b"PK"), "应是 xlsx 字节")
        # Korn 克隆保留模板的多 sheet 结构;openpyxl 回退(单薄结构)会被 MR.ERP 判列数不足。
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
            sheets = [n for n in names if n.startswith("xl/worksheets/sheet")]
            self.assertGreaterEqual(len(sheets), 3, f"Korn 克隆应有多 sheet · 实得 {sheets}")
            # 主 sheet 列引用应到第 18 列(R..第18列字母=R)· 真模板特征,回退版没有
            sheet1 = z.read("xl/worksheets/sheet1.xml").decode("utf-8", "ignore")
            self.assertIn('r="R1"', sheet1, "主 sheet 表头应有第 18 列(R1)· 证明是 18 列真模板")


if __name__ == "__main__":
    unittest.main()
