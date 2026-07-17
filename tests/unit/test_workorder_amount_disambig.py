# -*- coding: utf-8 -*-
"""确定性读数解歧金标(services/workorder/steps/amount_disambig.py · J-13)。

纯函数、Decimal、零 AI。锁四件事:①真料 IN26-00575(IMG_2647)三数反解出唯一自洽建议;
②本工单其余自洽进项票逐张零建议(无假阳性);③人造多解样例不出建议(宁缺勿滥);
④配置层的存在性论证——生产 9↔0 配置下两个替换解不可能并存(故本工单无假阳性有数学保证)。
真料三数取自 tests/e2e/_artifacts/mc0/01_fresh_order_stuck_detail.json 的 ocr_read 快照。
"""

import unittest
from decimal import Decimal

from services.workorder.steps import amount_disambig


class DisambigGoldenTests(unittest.TestCase):
    def test_img2647_ocr_triple_yields_unique_suggestion(self):
        # 派单书断言 1:IMG_2647 原始 OCR 三数(净 .40 版,净+税≠含税 差 0.05)。
        got = amount_disambig.suggest("58048.40", "4060.05", "62108.40")
        self.assertEqual(
            got,
            {
                "net": Decimal("58129.35"),
                "vat": Decimal("4069.05"),
                "grand": Decimal("62198.40"),
            },
        )

    def test_img2647_real_corpus_triple_yields_same_suggestion(self):
        # 真料快照净读作 .35:净+税=含税(加总恰抵平)却 净×7%≠税——只查加总会漏,必须
        # 两条恒等式都验才认作不自洽。反解建议与 .40 版一致(税/含税各纠 1 位 9↔0)。
        got = amount_disambig.suggest("58048.35", "4060.05", "62108.40")
        self.assertEqual(
            got,
            {
                "net": Decimal("58129.35"),
                "vat": Decimal("4069.05"),
                "grand": Decimal("62198.40"),
            },
        )

    def test_self_consistent_purchase_tickets_yield_no_suggestion(self):
        # 派单书断言 2:本工单其余自洽进项票逐张零建议(真料 ocr_read 快照,净+税=含税 且 净×7%≈税)。
        clean = [
            ("9016.82", "631.18", "9648.00", "57016198"),
            ("63413.83", "4438.97", "67852.80", "IN26-00658"),
            ("54240.00", "3796.80", "58036.80", "HS6905001"),
            ("3557.01", "248.99", "3806.00", "SW02000131"),
            ("6139.25", "429.75", "6569.00", "02000129"),
            ("2549.53", "178.47", "2728.00", "02000133"),
            ("5284.49", "369.91", "5654.40", "IN26-00557"),
            ("186.92", "13.08", "200.00", "02000113"),
        ]
        for net, vat, grand, label in clean:
            with self.subTest(label=label):
                self.assertIsNone(amount_disambig.suggest(net, vat, grand))

    def test_net_only_misread_recovers_via_derivation(self):
        # 税/含税正确、净被读错(整段错也无妨):净由 含税−税 反解,建议纠回真净。
        got = amount_disambig.suggest("11111.11", "4069.05", "62198.40")
        self.assertEqual(got["net"], Decimal("58129.35"))

    def test_no_confusion_fix_yields_no_suggestion(self):
        # 不平但无 9↔0 替换能同时闭合加总与 7% → 无解 → 不出建议(不硬造)。
        self.assertIsNone(amount_disambig.suggest("1000.00", "70.00", "1099.00"))

    def test_malformed_inputs_yield_no_suggestion(self):
        self.assertIsNone(amount_disambig.suggest(None, "70.00", "1070.00"))
        self.assertIsNone(amount_disambig.suggest("abc", "70.00", "1070.00"))


class DisambigMultiSolutionTests(unittest.TestCase):
    """派单书断言 3:多解不出建议。生产 9↔0 配置下多解不可能(见 test_prod_config_*),
    故用注入更宽的混淆表(某位有两个候选)构造真·两解样例,验「多解→不出建议」这条分支真实生效。"""

    def setUp(self):
        self._orig = amount_disambig._CONFUSABLE

    def tearDown(self):
        amount_disambig._CONFUSABLE = self._orig

    def test_two_closing_substitutions_abstain(self):
        # 注入 5→{0,9}:OCR(113.55/7.99/121.00)有两组等改动量替换均闭合(见下),故应不出建议。
        amount_disambig._CONFUSABLE = {"0": ("9",), "9": ("0",), "5": ("0", "9")}
        self.assertIsNone(amount_disambig.suggest("113.55", "7.99", "121.00"))

    def test_prod_config_cannot_produce_two_solutions_on_same_input(self):
        # 存在性论证:同一样例在生产 9↔0 配置下不会多解(此处恰为无解,返 None)——两个「单区段」
        # 替换要同时闭合 净×7%=税,需含税增量≈税增量×15.29,而单位替换增量比恒为 10 的幂,永不
        # 等于 15.29,故生产配置下两解不可能并存(无假阳性的数学保证)。
        self.assertIsNone(amount_disambig.suggest("113.55", "7.99", "121.00"))


if __name__ == "__main__":
    unittest.main()
