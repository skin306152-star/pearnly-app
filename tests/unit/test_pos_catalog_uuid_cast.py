#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POS catalog 的 product_id 数组查询必须 ::uuid[] 转型(回归守门)。

根因(2026-06-07 prod 真账号抓到):psycopg2 把 Python str 列表适配成 text[],而 product_id 列是
uuid;`uuid = ANY(text[])` 无隐式转换 → "operator does not exist: uuid = text" → list_products 整个
抛错 → /pos 商品网格空(收银员看不到任何商品)。单个 `id = %s` 靠 unknown 字面量能隐式转所以没炸,
唯独 ANY(数组)会。修法 = `ANY(%s::uuid[])`。本测试静态钉死,防 catalog 再写裸 ANY(%s) 复发。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[2] / "services" / "pos" / "catalog.py"


class CatalogUuidCastTest(unittest.TestCase):
    def test_product_id_any_is_uuid_cast(self):
        src = CATALOG.read_text(encoding="utf-8")
        # 任何 `product_id = ANY(%s)`(无 ::uuid[])都是这个 bug
        bad = re.findall(r"product_id\s*=\s*ANY\(%s\)(?!::uuid)", src)
        self.assertEqual(
            bad,
            [],
            "catalog.py 有未转型的 product_id = ANY(%s) → uuid 列需 ANY(%s::uuid[])(否则 /pos 取品整体抛错)",
        )

    def test_every_product_id_any_carries_uuid_cast(self):
        src = CATALOG.read_text(encoding="utf-8")
        anys = re.findall(r"product_id\s*=\s*ANY\(%s::uuid\[\]\)", src)
        # 至少 3 处(_units_by_product + _stock_by_product 两处)都已转型
        self.assertGreaterEqual(
            len(anys), 3, f"product_id = ANY(%s::uuid[]) 应 ≥3 处,实得 {len(anys)}"
        )


if __name__ == "__main__":
    unittest.main()
