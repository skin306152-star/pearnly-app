#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""守门 · `_search_listing` 必须按**本模块**列表路径决定是否导航(2026-05-26 修)。

抓的真 bug:`_search_listing` 旧检查 `"allview.php" not in page.url` 是
模块无关的。fail-safe 复核同一批先验客户(armas/allview.php)再验商品时,
页面已停在 armas/allview.php → 商品 `_search_listing` 误判"已在列表页"、
跳过导航 → 在客户页搜商品码 → 搜不到/回退 → 假 ERR_PRODUCT_VERIFY_UNAVAILABLE。
后果:任何需要同时复核客户+商品的推送,第二个必炸 → 绿色推送永远拿不到
(沙箱 TEST2019 真账号实测复现 + 本修复后真·成功推送 db_row_id 落库)。

本测试锁定:当前页在**另一个模块**的 allview.php 时,`_search_listing` 必须
导航到自己模块的 LISTING_PATH;已在本模块页上时不重复导航。纯单测无网络。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_customer_sync import MRERPCustomerSyncService  # noqa: E402
from services.erp.mrerp_product_sync import MRERPProductSyncService  # noqa: E402

LOGIN_URL = "https://mock.example.com"


def _make_page(current_url: str):
    """假 Playwright page:停在 current_url · #txtsearch 存在 · 搜索返空 HTML。"""
    page = MagicMock()
    page.url = current_url
    txt = MagicMock()
    txt.count.return_value = 1  # 搜索框存在 → 不走回退
    page.locator.return_value = txt
    page.content.return_value = ""  # parse → []
    return page


class SearchListingModulePathTests(unittest.TestCase):
    def _svc(self, cls, page):
        adapter = MagicMock()
        adapter.login_url = LOGIN_URL
        adapter._page = page
        adapter.select_company.return_value = None
        return cls(adapter)

    # ---- 商品(stkmas)----
    def test_product_search_navigates_when_on_customer_page(self):
        """页停在 armas(客户)→ 商品搜索必须导航到 stkmas。"""
        page = _make_page(LOGIN_URL + "/armas/allview.php?searchdata=0006")
        svc = self._svc(MRERPProductSyncService, page)
        svc._search_listing("P001")
        page.goto.assert_called_once()
        self.assertIn("/stkmas/allview.php", page.goto.call_args.args[0])

    def test_product_search_no_renav_when_already_on_product_page(self):
        """已在 stkmas → 不重复导航。"""
        page = _make_page(LOGIN_URL + "/stkmas/allview.php?searchdata=P001")
        svc = self._svc(MRERPProductSyncService, page)
        svc._search_listing("P001")
        page.goto.assert_not_called()

    # ---- 客户(armas)----
    def test_customer_search_navigates_when_on_product_page(self):
        """页停在 stkmas(商品)→ 客户搜索必须导航到 armas。"""
        page = _make_page(LOGIN_URL + "/stkmas/allview.php?searchdata=P001")
        svc = self._svc(MRERPCustomerSyncService, page)
        svc._search_listing("0006")
        page.goto.assert_called_once()
        self.assertIn("/armas/allview.php", page.goto.call_args.args[0])

    def test_customer_search_no_renav_when_already_on_customer_page(self):
        """已在 armas → 不重复导航。"""
        page = _make_page(LOGIN_URL + "/armas/allview.php?searchdata=0006")
        svc = self._svc(MRERPCustomerSyncService, page)
        svc._search_listing("0006")
        page.goto.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
