# -*- coding: utf-8 -*-
"""心跳上报的商品/客户目录 + 记账指纹净化守门(纯函数 · 不碰 DB)。

净化是可信边界:小助手上报的目录直接喂 catalog_resolver / posting_profile,脏数据必须挡在
入库前(限键/限量/限长、指纹归一非负整数)。SQL 写入路径无 DB 不单测(catch 异常,同现有
store_* 先例)。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.erp.express_push.agent_reporting import (  # noqa: E402
    _PRODUCT_KEYS,
    _sanitize_catalog,
    _sanitize_fingerprint,
)


class SanitizeCatalogTests(unittest.TestCase):
    def test_keeps_known_keys_only(self):
        raw = [{"code": "14-01", "name": "น้ำแข็ง", "kind": "stock", "evil": "drop"}]
        out = _sanitize_catalog(raw, _PRODUCT_KEYS)
        self.assertEqual(out, [{"code": "14-01", "name": "น้ำแข็ง", "kind": "stock"}])

    def test_drops_rows_without_code_or_name(self):
        raw = [{"kind": "stock"}, {"code": "P1"}]
        self.assertEqual(len(_sanitize_catalog(raw, _PRODUCT_KEYS)), 1)

    def test_caps_volume(self):
        raw = [{"code": f"P{i}"} for i in range(25000)]
        self.assertEqual(len(_sanitize_catalog(raw, _PRODUCT_KEYS)), 20000)

    def test_caps_field_length(self):
        out = _sanitize_catalog([{"code": "P1", "name": "x" * 500}], _PRODUCT_KEYS)
        self.assertEqual(len(out[0]["name"]), 200)

    def test_non_list_is_empty(self):
        self.assertEqual(_sanitize_catalog("nope", _PRODUCT_KEYS), [])
        self.assertEqual(_sanitize_catalog(None, _PRODUCT_KEYS), [])


class SanitizeFingerprintTests(unittest.TestCase):
    def test_keeps_three_counts_as_ints(self):
        raw = {"stock_master_count": "672", "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
        fp = _sanitize_fingerprint(raw)
        self.assertEqual(
            fp, {"stock_master_count": 672, "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
        )

    def test_drops_unknown_and_bad(self):
        raw = {"stcrd_lines": "x", "evil": 1, "stock_master_count": 4}
        self.assertEqual(_sanitize_fingerprint(raw), {"stock_master_count": 4})

    def test_negatives_clamped(self):
        self.assertEqual(_sanitize_fingerprint({"stcrd_lines": -5})["stcrd_lines"], 0)

    def test_non_dict_is_empty(self):
        self.assertEqual(_sanitize_fingerprint(None), {})
        self.assertEqual(_sanitize_fingerprint([1, 2]), {})


if __name__ == "__main__":
    unittest.main()
