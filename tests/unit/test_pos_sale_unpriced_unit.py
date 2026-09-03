# -*- coding: utf-8 -*-
"""同类漏洞 · 没挂牌价的单位不许在收银台卖出(与 P0-① 同源)。

餐厅那条路早就有这道闸(services/pos/restaurant/sessions.add_lines → detail="no_price",
反证见 test_product_price_nullable.RestaurantRefusesToServeAnUnpricedDishTests),
收银台卖货这条路没有:`unit_price = Decimal(str(ln.get("unit_price", 0)))` —— 价从客户端来,
键缺了就是 0。前端 pos-cashier.priced 拦得住,可判据只活在前端就等于没有:直调 API、换个屏、
将来某个 `+val || 0`,整箱货都能 ฿0 出门、฿0 落账,小票和日结上一个字都看不出来。

会出事的输入(不是"挂了 ฿350 的箱"那种永远绿的):
  · 商品建了「箱」这条单位行但价留空(product_units.price IS NULL)—— 扫箱码就是这条路;
  · 基本单位没设价(products.unit_price IS NULL)—— 扫码就地建品建出来的货全长这样;
  · 真的赠品(挂牌价就是 0)也不能单独结成整单 0 元;免费赠送应与有价商品同单。
"""

import unittest
from decimal import Decimal
from unittest.mock import patch

from core.pos_api import PosError
from services.pos import sale


class _Cur:
    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return None

    def fetchall(self):
        return []


BOX = {"factor_to_base": 24, "price": None}
PROD = {
    "id": "p-1",
    "base_unit": "ขวด",
    "unit_price": None,
    "vat_applicable": True,
    "track_batch": False,
}


def _sell(prod_price, unit_row, sell_unit, charge="0", payments=()):
    """真跑 create_sale 到明细那一段。协作者打桩,判据本身跑的是产品代码。

    charge = 客户端报上来的成交价(病灶就在这:键缺了就是 0,后端照收)。
    """
    prod = dict(PROD, unit_price=prod_price)
    payload = {
        "shift_id": "sh-1",
        "lines": [{"product_id": "p-1", "qty": 1, "sell_unit": sell_unit, "unit_price": charge}],
        "payments": list(payments),
        "price_includes_vat": True,
    }
    with (
        patch.object(sale, "_assert_shift_open"),
        patch.object(
            sale,
            "_resolve_sale_binding",
            return_value={"terminal_id": "term-1", "shift_id": "sh-1", "cashier_id": None},
        ),
        patch.object(sale.inv_store, "get_or_create_default_warehouse", return_value={"id": "w-1"}),
        patch.object(sale.sales_store, "find_sale_by_client_uuid", return_value=None),
        patch.object(sale.sales_store, "get_product_for_sale", return_value=prod),
        patch.object(sale.sales_store, "get_unit_factor", return_value=unit_row),
        patch.object(sale.numbering, "next_number", return_value=("R-0001", 1)) as receipt,
        patch.object(sale.stock, "deduct_for_sale", return_value=[]) as deduct,
    ):
        try:
            sale.create_sale(_Cur(), tenant_id="t-1", workspace_client_id=1, payload=payload)
            raised = None
        except PosError as exc:
            raised = exc
        except Exception:
            # 桩只铺到发号为止,再往后是真落库(insert_sale 等)—— 那不是这道闸的题。
            # 业务拒绝一律是 PosError,所以别的异常说明这一单已经【过了】闸。
            raised = None
    return raised, receipt, deduct


class UnpricedUnitIsRefusedTests(unittest.TestCase):
    def test_named_unit_without_a_price_cannot_be_sold(self):
        """扫箱码这条路:箱建了但价留空 → 一整箱 ฿0 出门。"""
        err, _, _ = _sell(Decimal("15"), BOX, "ลัง")
        self.assertIsNotNone(err, "没挂牌价的箱被卖出去了")
        self.assertEqual(err.detail, "no_price")

    def test_base_unit_without_a_price_cannot_be_sold(self):
        """扫码就地建品建出来的货就是这个形状(products.unit_price IS NULL)。"""
        err, _, _ = _sell(None, None, None)
        self.assertIsNotNone(err)
        self.assertEqual(err.detail, "no_price")

    def test_refused_sale_takes_no_receipt_number_and_moves_no_stock(self):
        """拦住 ≠ 拦在半路:号发了、库存扣了再抛,货就凭空少了一件还没有小票对得上。"""
        _, receipt, deduct = _sell(Decimal("15"), BOX, "ลัง")
        receipt.assert_not_called()
        deduct.assert_not_called()

    def test_a_real_zero_priced_unit_cannot_be_the_whole_order(self):
        """免费赠品可以作为有价订单的一行,但整单 0 元不许发号、不动库存。"""
        err, receipt, deduct = _sell(
            Decimal("15"), {"factor_to_base": 24, "price": Decimal("0")}, "ลัง"
        )
        self.assertIsNotNone(err)
        self.assertEqual(err.code, "pos.zero_total")
        receipt.assert_not_called()
        deduct.assert_not_called()

    def test_a_priced_unit_still_sells(self):
        err, receipt, _ = _sell(
            Decimal("15"),
            {"factor_to_base": 24, "price": Decimal("350")},
            "ลัง",
            charge="350",
            payments=[{"method": "cash", "amount": "350"}],
        )
        self.assertIsNone(err)
        receipt.assert_called()


if __name__ == "__main__":
    unittest.main()
