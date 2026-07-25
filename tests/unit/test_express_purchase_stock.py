# -*- coding: utf-8 -*-
"""采购 mapper 认「本批过账去向」→ 商品行走真实库存(C5 · 确定性纯函数 · 无 DB/网络)。

闭环的另一半:销售侧扣库存要有货可扣,货得靠采购票建。故 posting_kind='stock' 的**货品**票
每行发 item_mode='stock_item',小助手据此建 STKTYP=0 主档 + 真入库 + 真成本。

钉死四件事:
1. posting_kind='stock' + 货道 → 逐行 item_mode == stock_item(不是只标第一行);
2. 费用票(doc_lane=expense)即便声明 stock 也不走库存 —— 费用不进库存是会计口径,不是习惯;
3. 未声明 posting_kind → 载荷逐字不变(库存路是新增分支,不许顺手改既有行为);
4. 每批显式选「库存」压过画像的 escalate(镜像销项),否则永续客户 —— 库存路的目标用户 ——
   永远推不出一张进货票,C6 整条路等于没通。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.common import (  # noqa: E402
    ITEM_MODE_NONSTOCK,
    ITEM_MODE_STOCK,
)
from services.erp.express_push.mapper import build_express_payload  # noqa: E402
from services.erp.express_push.posting_profile import (  # noqa: E402
    ESCALATE_REASON_PREFIX,
)

_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "51-03-00-00",  # 购货(小助手走库存时会重分类到存货)
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}

# 高动库存占比 → 画像判 perpetual;库存路全局闸未开时 posting_mode=manual_review。
_PERPETUAL_FINGERPRINT = {"stcrd_lines": 100, "stcrd_lines_moving_stock": 90}


def _history(*, manual="goods", items=None, **over):
    """一张完整税票的采购票。posting_item_type_manual 显式钉货/费道,不让判据随样例漂。"""
    fields = {
        "seller_name": "บริษัท ซัพพลาย จำกัด",
        "seller_tax": "0107561000013",
        "subtotal": "1000.00",
        "vat": "70.00",
        "invoice_number": "PO-7001",
        "posting_item_type_manual": manual,
        "items": (
            items
            if items is not None
            else [
                {
                    "name": "ผงชูรส",
                    "qty": "100",
                    "unit": "ถัง",
                    "price": "10.00",
                    "subtotal": "1000.00",
                }
            ]
        ),
    }
    fields.update(over.pop("fields", {}))
    h = {
        "id": "hist-stock-1",
        "invoice_date": "2026-01-15",
        "invoice_no": "PO-7001",
        "total_amount": "1070.00",
        "fields": fields,
    }
    h.update(over)
    return h


def _build(history, **kwargs):
    """跑 mapper 并屏蔽防重单回查(那一步要连库,与本模块的确定性映射无关)。"""
    with mock.patch("services.erp.express_push.prior_doc.prior_docnum", return_value=None):
        return build_express_payload(history, config=_CONFIG, **kwargs)


# 未声明 posting_kind 时的载荷逐字基线(C5 落地前实测抓取)。库存路是新增分支,
# 老票(邮件收料 / LINE / 重试队列 —— 手里没有向导会话)的载荷不许被顺手改掉一个字。
_UNDECLARED_PAYLOAD = {
    "account_review": True,
    "account_set": "DATAT",
    "account_source": "config_default",
    "base_amount": "1000.00",
    "direction": "purchase",
    "doc_lane": "goods",
    "docdate_be": "690115",
    "doctype": "RR",
    "doctype_src": "config_default",
    "item_src": "manual",
    "items": [
        {
            "amount": "1000.00",
            "item_mode": "non_stock_item",
            "name": "ผงชูรส",
            "qty": "100.00",
            "unit": "ถัง",
            "unit_price": "10.00",
        }
    ],
    "items_account": "51-03-00-00",
    "items_line_sum": "1000.00",
    "items_status": "ok",
    "lines": [
        {"acc": "51-03-00-00", "amount": "1000.00", "desc": "บริษัท ซัพพลาย จำกัด", "side": "D"},
        {"acc": "11-05-04-01", "amount": "70.00", "desc": "ภาษีซื้อ", "side": "D"},
        {"acc": "21-02-01-00", "amount": "1070.00", "desc": "เจ้าหนี้การค้า", "side": "C"},
    ],
    "payload_version": 1,
    "ref_no": "PO-7001",
    "source": {"filename": None, "history_id": "hist-stock-1"},
    "supplier": {
        "address": "",
        "code": "",
        "name": "บริษัท ซัพพลาย จำกัด",
        "prename": "บริษัท",
        "supplier_new": True,
        "tax_id": "0107561000013",
    },
    "total_amount": "1070.00",
    "vat_amount": "70.00",
    "vat_period_be": "690101",
    "vat_rate": 7.0,
}


class StockLaneTests(unittest.TestCase):
    def test_wire_constant_matches_companion(self):
        # 小助手 dbf_detail.ITEM_MODE_STOCK 认的就是这个串;两边改一边 = 库存行静默走回非库存路。
        self.assertEqual(ITEM_MODE_STOCK, "stock_item")

    def test_stock_kind_marks_every_goods_line(self):
        items = [
            {"name": "ผงชูรส", "qty": "60", "price": "10.00", "subtotal": "600.00"},
            {"name": "น้ำตาลทราย", "qty": "40", "price": "10.00", "subtotal": "400.00"},
        ]
        r = _build(_history(items=items), posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        # 逐行都得标:只标首行会让第二种货静默走非库存路,库存永远建不起来。
        self.assertEqual([it["item_mode"] for it in r.payload["items"]], [ITEM_MODE_STOCK] * 2)
        self.assertEqual(r.payload["items_status"], "ok")
        self.assertEqual(r.payload["doc_lane"], "goods")

    def test_expense_invoice_never_goes_stock(self):
        # 费用票即便本批声明了库存也不进库存:VAT 已折进成本、明细收成一行通用费用物料,
        # 拿它建库存品会在客户库存目录里长出「ค่าใช้จ่าย」这种假商品并计成本。
        r = _build(_history(manual="expense"), posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doc_lane"], "expense")
        self.assertEqual([it["item_mode"] for it in r.payload["items"]], [ITEM_MODE_NONSTOCK])
        self.assertEqual(r.payload["vat_amount"], "0.00")

    def test_service_kind_stays_non_stock(self):
        r = _build(_history(), posting_kind="service")
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items"][0]["item_mode"], ITEM_MODE_NONSTOCK)


class UndeclaredPayloadUnchangedTests(unittest.TestCase):
    """没人声明过去向的票(邮件收料 / LINE / 重试队列)行为不许动。"""

    def test_payload_byte_identical_without_posting_kind(self):
        self.assertEqual(_build(_history()).payload, _UNDECLARED_PAYLOAD)

    def test_explicit_none_is_the_same_as_omitted(self):
        # None = 没人声明过,不是「选了服务」——两种写法必须同一条路。
        self.assertEqual(_build(_history(), posting_kind=None).payload, _UNDECLARED_PAYLOAD)


class PerpetualProfileTests(unittest.TestCase):
    """画像 escalate 与每批开关的关系(镜像 sales_mapper 的判据,防两侧漂移)。"""

    def _config(self):
        cfg = dict(_CONFIG)
        cfg["catalog_fingerprint"] = _PERPETUAL_FINGERPRINT
        return cfg

    def _build_with_profile(self, **kwargs):
        with mock.patch("services.erp.express_push.prior_doc.prior_docnum", return_value=None):
            return build_express_payload(_history(), config=self._config(), **kwargs)

    def test_no_declaration_still_escalates(self):
        # 安全网原样:永续客户 + 库存路未开 + 没人显式选 → 交会计,绝不静默按周期制落。
        r = self._build_with_profile()
        self.assertFalse(r.ok)
        self.assertTrue(r.reason.startswith(ESCALATE_REASON_PREFIX), r.reason)

    def test_explicit_stock_batch_is_honoured(self):
        # 永续客户正是库存路的目标用户;这条红 = 他们一张进货票也推不出去,C6 等于没通。
        r = self._build_with_profile(posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items"][0]["item_mode"], ITEM_MODE_STOCK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
