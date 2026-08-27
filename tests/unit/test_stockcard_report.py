# -*- coding: utf-8 -*-
"""services/stockcard/report.groups() 纯计算单测(网页唯一主视图 /api/stockcard/report)。

覆盖拍板口径:各商品按 key 独立滚存移动加权平均(不跨商品混算);每组第一行是所选期间
起点的期初结转行;期间内逐笔;组尾是该商品本期入库/出库/期末结存。负库存照实显示、
成本未确立诚实置 None(不以 0 冒充);名字轨按清洗名独立成表;product 元数据只带主表
标题与期初录入所需的 key/编码/名称/单位。数字一律字符串。

数据源(mv_svc.load / product_names / purchase_units / opening_svc.load_by_key)全部打桩,
只用纯函数滚存验证形状与数值;禁止 N+1 的行为在 route 契约测试里用「单次 load_context +
批量取数」锁,这里锁算法本身。
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.stockcard import report as report_svc  # noqa: E402
from services.stockcard.movements import MovementSet  # noqa: E402
from services.stockcard.rolling import Movement  # noqa: E402


def _mov(key, *, direction, qty, price=None, doc_no="", desc="", day=2, created=0, line=0):
    return Movement(
        date=date(2024, 6, day),
        doc_no=doc_no,
        desc=desc,
        direction=direction,
        qty=Decimal(qty),
        price=None if price is None else Decimal(price),
        sort_key=(date(2024, 6, day), created, line),
    )


def _ctx():
    """一个含四把钥匙的 MovementSet + 期初表:
    p:PROD-1 商品轨(期初 + 购 + 销) · p:PROD-NEG 负库存(无期初先出库) ·
    n:น้ำแข็งหลอด 名字轨(独立成表) · p:PROD-UNK 成本未确立(退货入库,金额应为 None)。"""
    data = MovementSet()
    data.add_movement(
        "p:PROD-1",
        _mov("p:PROD-1", direction="in", qty="100", price="250.00", doc_no="PO-1", day=2),
    )
    data.add_movement(
        "p:PROD-1",
        _mov("p:PROD-1", direction="out", qty="30", doc_no="SO-1", day=5, desc="销售给客户 A"),
    )
    data.add_movement(
        "p:PROD-1", _mov("p:PROD-1", direction="in", qty="50", price="260.00", doc_no="PO-2", day=8)
    )
    data.add_movement(
        "p:PROD-NEG", _mov("p:PROD-NEG", direction="out", qty="5", doc_no="SO-9", day=3)
    )
    data.add_movement(
        "n:น้ำแข็งหลอด",
        _mov("n:น้ำแข็งหลอด", direction="in", qty="10", price="95.00", doc_no="PO-7", day=4),
    )
    data.add_movement(
        "p:PROD-UNK", _mov("p:PROD-UNK", direction="in", qty="5", price=None, doc_no="CN-3", day=6)
    )
    openings = {
        "p:PROD-1": {
            "as_of_date": date(2024, 5, 31),
            "qty": Decimal("10"),
            "unit_cost": Decimal("250.00"),
        }
    }
    return data, openings


class GroupsReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._product_names = mock.patch.object(
            report_svc.mv_svc,
            "product_names",
            return_value={
                "PROD-1": {"name": "WPC 仿木条 2 寸", "unit": "条"},
                "PROD-NEG": {"name": "山牌饮用水 600ml", "unit": "箱"},
            },
        )
        cls._purchase_units = mock.patch.object(
            report_svc.mv_svc, "purchase_units", return_value={"น้ำแข็งหลอด": "ถุง"}
        )
        cls._products_mock = cls._product_names.start()
        cls._units_mock = cls._purchase_units.start()

    @classmethod
    def tearDownClass(cls):
        cls._product_names.stop()
        cls._purchase_units.stop()

    def _groups(self):
        data, openings = _ctx()
        return report_svc.groups(
            None,
            tenant_id="tenant-1",
            workspace_client_id=1,
            date_from=date(2024, 6, 1),
            date_to=date(2024, 6, 30),
            context=(data, openings),
        )

    def test_groups_order_and_keys(self):
        groups = self._groups()
        self.assertEqual(
            [g["product"]["key"] for g in groups],
            ["n:น้ำแข็งหลอด", "p:PROD-1", "p:PROD-NEG", "p:PROD-UNK"],
        )

    def test_product_meta_is_minimal(self):
        for g in self._groups():
            self.assertEqual(set(g["product"].keys()), {"key", "product_id", "name", "unit"})

    def test_product_track_rows_and_totals(self):
        g = next(x for x in self._groups() if x["product"]["key"] == "p:PROD-1")
        self.assertEqual(g["product"]["product_id"], "PROD-1")
        self.assertEqual(g["product"]["name"], "WPC 仿木条 2 寸")
        self.assertEqual(g["product"]["unit"], "条")

        # 第一行是期初结转(合成行,金额/单价为空),后续是期间逐笔。
        opening, *period = g["rows"]
        self.assertEqual(opening["kind"], "open")
        self.assertEqual(opening["qty"], "10")
        self.assertEqual(opening["bal_qty"], "10")
        self.assertEqual(opening["bal_unit_cost"], "250.00")
        self.assertEqual(opening["bal_value"], "2500.00")
        self.assertIsNone(opening["unit_price"])
        self.assertIsNone(opening["amount"])
        self.assertEqual(opening["date"], "2024-06-01")  # 期初行落在所选期间起点

        self.assertEqual([r["kind"] for r in period], ["in", "out", "in"])
        self.assertEqual(period[0]["qty"], "100")
        self.assertEqual(period[0]["bal_qty"], "110")
        self.assertEqual(period[0]["bal_unit_cost"], "250.00")
        self.assertEqual(period[1]["bal_qty"], "80")
        self.assertEqual(period[2]["bal_qty"], "130")
        self.assertEqual(period[2]["bal_unit_cost"], "253.85")
        self.assertEqual(period[2]["bal_value"], "33000.00")

        t = g["totals"]
        self.assertEqual(t["in_qty"], "150")
        self.assertEqual(t["in_amount"], "38000.00")
        self.assertEqual(t["out_qty"], "30")
        self.assertEqual(t["out_amount"], "7500.00")
        self.assertEqual(t["bal_qty"], "130")
        self.assertEqual(t["bal_unit_cost"], "253.85")
        self.assertEqual(t["bal_value"], "33000.00")

    def test_negative_stock_is_honest(self):
        g = next(x for x in self._groups() if x["product"]["key"] == "p:PROD-NEG")
        # 无期初先出库 → 负库存,成本未确立 → 单价/金额留空(不以 0 冒充)。
        self.assertEqual(g["rows"][0]["kind"], "open")
        self.assertEqual(g["rows"][0]["qty"], "0")
        self.assertIsNone(g["rows"][0]["bal_unit_cost"])
        out = g["rows"][1]
        self.assertEqual(out["qty"], "5")
        self.assertEqual(out["bal_qty"], "-5")
        self.assertIsNone(out["amount"])
        self.assertIsNone(out["bal_unit_cost"])
        self.assertIsNone(out["bal_value"])
        self.assertEqual(g["totals"]["bal_qty"], "-5")
        self.assertIsNone(g["totals"]["bal_unit_cost"])
        self.assertIsNone(g["totals"]["bal_value"])

    def test_name_track_has_no_product_id(self):
        g = next(x for x in self._groups() if x["product"]["key"] == "n:น้ำแข็งหลอด")
        self.assertIsNone(g["product"]["product_id"])
        self.assertEqual(g["product"]["name"], "น้ำแข็งหลอด")
        self.assertEqual(g["product"]["unit"], "ถุง")  # 名字轨单位由 purchase_units 带出

    def test_unknown_in_amount_stays_null(self):
        g = next(x for x in self._groups() if x["product"]["key"] == "p:PROD-UNK")
        # 退货入库在成本未确立时金额为 None → 该方向合计也必须是 None,不能拿已知部分顶替。
        self.assertIsNone(g["rows"][1]["amount"])
        self.assertEqual(g["totals"]["in_qty"], "5")
        self.assertIsNone(g["totals"]["in_amount"])

    def test_products_do_not_cross_mix(self):
        groups = self._groups()
        p1 = next(x for x in groups if x["product"]["key"] == "p:PROD-1")
        neg = next(x for x in groups if x["product"]["key"] == "p:PROD-NEG")
        # 各自独立的期末结存:PROD-1 正数且带成均成本,PROD-NEG 负数且成本未知。
        self.assertNotEqual(p1["totals"]["bal_qty"], neg["totals"]["bal_qty"])
        self.assertIsNone(neg["totals"]["bal_unit_cost"])
        self.assertIsNotNone(p1["totals"]["bal_unit_cost"])

    def test_no_n_plus_one_batch_fetches(self):
        # 商品名/名字轨单位是「一次批量取」,不是每个 key 各查一次(反 N+1 红线)。
        before = (self._products_mock.call_count, self._units_mock.call_count)
        self._groups()
        after = (self._products_mock.call_count, self._units_mock.call_count)
        self.assertEqual((after[0] - before[0], after[1] - before[1]), (1, 1))

    def test_product_names_batches_all_ids(self):
        # 商品名一次带上全部 p: 轨 id(跨商品共读一次,不按商品查)。
        self._groups()
        self.assertEqual(
            set(self._products_mock.call_args.kwargs["product_ids"]),
            {"PROD-1", "PROD-NEG", "PROD-UNK"},
        )


if __name__ == "__main__":
    unittest.main()
