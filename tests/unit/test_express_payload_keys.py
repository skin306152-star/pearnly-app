# -*- coding: utf-8 -*-
"""写载荷键契约锁:mapper 产物键集 ⊆ WRITE_PAYLOAD_KEYS(桥端白名单的对镜)。

桥对契约外键当场拒(bad_payload),而桥不随主站部署 —— mapper 加键忘登记 = 整条写路
熄火以天计。此前云端没有任何测试冻结键集,这里补上:两个 mapper 各走一遍会带满条件键
的分支(库存路 stock_acccod / 费用路 vat_capitalized / 重推 prior_docnum),键集必须
落在契约内;条件键必须真出现 —— 否则「空集 ⊆ 任何集」会让本测试假绿。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.mapper import build_express_payload  # noqa: E402
from services.erp.express_push.payload_keys import WRITE_PAYLOAD_KEYS  # noqa: E402
from services.erp.express_push.sales_mapper import (  # noqa: E402
    build_express_sales_payload,
)

_PURCHASE_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "51-03-00-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
    "stock_acccod": "12-01-01",  # 库存路条件键的触发源
}

_SALES_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-00-00",
    "vat_output_acc": "21-05-04-02",
    "ar_acc": "11-03-01-00",
    "stock_acccod": "12-01-01",
}

_ITEMS = [{"name": "ผงชูรส", "qty": "100", "unit": "ถัง", "price": "10.00", "subtotal": "1000.00"}]


def _purchase_history(manual="goods"):
    return {
        "id": "hist-keys-1",
        "tenant_id": "t-1",
        "invoice_date": "2026-01-15",
        "invoice_no": "PO-8001",
        "total_amount": "1070.00",
        "fields": {
            "seller_name": "บริษัท ซัพพลาย จำกัด",
            "seller_tax": "0107561000013",
            "subtotal": "1000.00",
            "vat": "70.00",
            "invoice_number": "PO-8001",
            "posting_item_type_manual": manual,
            "items": _ITEMS,
        },
    }


def _sales_history():
    return {
        "id": "hist-keys-2",
        "tenant_id": "t-1",
        "invoice_date": "2026-01-15",
        "invoice_no": "IV-8001",
        "total_amount": "1070.00",
        "fields": {
            "buyer_name": "บริษัท ลูกค้า จำกัด",
            "buyer_tax": "0105551234567",
            "subtotal": "1000.00",
            "vat": "70.00",
            "invoice_number": "IV-8001",
            "items": _ITEMS,
        },
    }


def _keys(result):
    """ok 才取键集 —— 构造失败返回空集会让 ⊆ 断言恒真(假绿),必须先炸。"""
    assert result.ok, result.reason
    return set(result.payload)


class WritePayloadKeysContractTests(unittest.TestCase):
    def _assert_within_contract(self, keys):
        extra = keys - WRITE_PAYLOAD_KEYS
        self.assertFalse(
            extra,
            "mapper 产出了契约外键,须登记 payload_keys.WRITE_PAYLOAD_KEYS 并同步桥端"
            f"白名单 + 发桥新版,否则桥会把整条写路拒成 bad_payload:{sorted(extra)}",
        )

    def test_purchase_stock_lane_keys_within_contract(self):
        with mock.patch(
            "services.erp.express_push.prior_doc.prior_docnum", return_value="RR690101-001"
        ):
            keys = _keys(
                build_express_payload(
                    _purchase_history(), config=_PURCHASE_CONFIG, posting_kind="stock"
                )
            )
        # 条件键必须真出现,证明这条测试确实覆盖到库存路/重推分支。
        self.assertLessEqual({"supplier", "stock_acccod", "prior_docnum"}, keys)
        self._assert_within_contract(keys)

    def test_purchase_expense_lane_keys_within_contract(self):
        with mock.patch("services.erp.express_push.prior_doc.prior_docnum", return_value=None):
            keys = _keys(
                build_express_payload(_purchase_history(manual="expense"), config=_PURCHASE_CONFIG)
            )
        self.assertIn("vat_capitalized", keys)
        self._assert_within_contract(keys)

    def test_sales_stock_lane_keys_within_contract(self):
        with mock.patch(
            "services.erp.express_push.prior_doc.prior_docnum", return_value="IV690101-001"
        ):
            keys = _keys(
                build_express_sales_payload(
                    _sales_history(), config=_SALES_CONFIG, posting_kind="stock"
                )
            )
        self.assertLessEqual({"customer", "stock_acccod", "prior_docnum"}, keys)
        self._assert_within_contract(keys)

    def test_preflight_injected_key_registered(self):
        # opening_stock 不出自 mapper:preflight 在 mapper 之后补进载荷(补期初卡透传),
        # mapper 键集测试照不到它,单独钉住。
        self.assertIn("opening_stock", WRITE_PAYLOAD_KEYS)


if __name__ == "__main__":
    unittest.main()
