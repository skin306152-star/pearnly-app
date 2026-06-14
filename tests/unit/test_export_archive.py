# -*- coding: utf-8 -*-
"""归档编排可测部分(export.archive.flatten_categories)· 纯函数(阶段二)。

run_export / gather_items / Drive·Sheets 真调用 = 用户验收(需真凭据),本测只锁
分类树扁平(喂 rows 的大类/小类名)。
"""

import unittest

from services.export.archive import flatten_categories


class FlattenCategoriesTests(unittest.TestCase):
    def test_flattens_two_levels(self):
        tree = [
            {"id": "c1", "name": "办公", "children": [{"id": "s1", "name": "文具"}]},
            {"id": "c2", "name": "差旅", "children": []},
        ]
        out = flatten_categories(tree)
        self.assertEqual(out, {"c1": "办公", "s1": "文具", "c2": "差旅"})

    def test_empty(self):
        self.assertEqual(flatten_categories([]), {})

    def test_missing_name_safe(self):
        self.assertEqual(flatten_categories([{"id": "c1"}]), {"c1": ""})


if __name__ == "__main__":
    unittest.main()
