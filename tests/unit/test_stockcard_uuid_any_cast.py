# -*- coding: utf-8 -*-
"""stockcard 的 uuid 数组查询必须 ::uuid[] 转型(回归守门 · 同 test_workorder_uuid_any_cast.py)。

根因(2026-08-07 集成测试跑到真库才炸):psycopg2 把 Python id 列表适配成 text[],而
products.id / purchase_lines.id / sales_document_lines.id 是 uuid;`uuid = ANY(text[])`
无隐式转换 → "operator does not exist: uuid = text"。movements.product_names 用假的
purchase-only 夹具(全走 n: 名称轨)时不会命中这条查询,直到集成测试真种一个 p: 商品键
才炸出来——本测试静态钉死,防止哪天有人"顺手"改掉转型又不巧只跑了名称轨的用例。

merge.py 的采购/销售两条 UPDATE(2026-08 收口重复代码后)共用同一个 _merge_lines 模板,
源码里 ANY(%s::uuid[]) 只写一次、两条运行路径都吃这一份转型——比此前两处各自一份更不容易
漂移,故这里门槛降到 1(不是"少了一处",是"两处从此不可能各判各的")。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_STOCKCARD = Path(__file__).resolve().parents[2] / "services" / "stockcard"
_UUID_FILES = (_STOCKCARD / "movements.py", _STOCKCARD / "merge.py")


class StockcardUuidCastTest(unittest.TestCase):
    def test_no_bare_any_on_uuid_columns(self):
        for path in _UUID_FILES:
            src = path.read_text(encoding="utf-8")
            bad = re.findall(r"ANY\(%s\)(?!::uuid)", src)
            self.assertEqual(
                bad,
                [],
                f"{path.name} 有未转型的 ANY(%s) → uuid 列需 ANY(%s::uuid[])(否则真数据一到就 500)",
            )

    def test_uuid_casts_present(self):
        counts = {
            p.name: len(re.findall(r"ANY\(%s::uuid\[\]\)", p.read_text(encoding="utf-8")))
            for p in _UUID_FILES
        }
        self.assertGreaterEqual(counts["movements.py"], 1, f"实得 {counts}")
        self.assertGreaterEqual(counts["merge.py"], 1, f"实得 {counts}")


if __name__ == "__main__":
    unittest.main()
