# -*- coding: utf-8 -*-
"""跨渠道关联(services.sales_agg.linker):settlement 匹配 / 交叉核对不平 / 重叠疑似。"""

import unittest
from datetime import date
from decimal import Decimal

from services.sales_agg.linker import (
    edc_internal_conflicts,
    link_settlements,
    overlap_suspects,
)
from services.sales_agg.model import BankCredit, EdcSettlement, SalesDoc


def _edc(ref, day, gross, fee=None, net=None, batch="B1"):
    return EdcSettlement(
        ref=ref,
        day=day,
        gross=Decimal(gross) if gross is not None else None,
        fee=Decimal(fee) if fee is not None else None,
        net=Decimal(net) if net is not None else None,
        batch_no=batch,
        terminal_id="T1",
    )


def _credit(ref, day, amount, tx_id=""):
    return BankCredit(
        ref=ref, day=day, amount=Decimal(amount), description="EDC KBANK", tx_id=tx_id
    )


class TestLinkSettlements(unittest.TestCase):
    def test_match_on_net(self):
        edc = _edc("e1", date(2026, 5, 15), "10700.00", fee="160.50", net="10539.50")
        credit = _credit("b1", date(2026, 5, 16), "10539.50")
        links, conflicts, matched_bank, matched_edc = link_settlements([edc], [credit])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["matched_on"], "net")
        self.assertEqual(links[0]["date_diff_days"], 1)
        self.assertEqual(links[0]["kind"], "settlement_of")
        self.assertEqual(matched_bank, {"b1"})
        self.assertEqual(matched_edc, {"e1"})
        self.assertEqual(conflicts, [])

    def test_match_on_gross_minus_fee_when_net_missing(self):
        edc = _edc("e1", date(2026, 5, 15), "10700.00", fee="160.50")
        credit = _credit("b1", date(2026, 5, 17), "10539.50")
        links, _, _, _ = link_settlements([edc], [credit])
        self.assertEqual(links[0]["matched_on"], "gross_minus_fee")

    def test_outside_date_window_not_matched(self):
        edc = _edc("e1", date(2026, 5, 15), "10700.00", net="10539.50")
        credit = _credit("b1", date(2026, 5, 18), "10539.50")
        links, _, matched_bank, _ = link_settlements([edc], [credit])
        self.assertEqual(links, [])
        self.assertEqual(matched_bank, set())

    def test_crosscheck_imbalance_named(self):
        # 到账按净额匹配上,但 净+手续费 ≠ 毛额(单据读错/异常扣款)→ 点名不静默。
        edc = _edc("e1", date(2026, 5, 15), "10700.00", fee="100.00", net="10539.50")
        credit = _credit("b1", date(2026, 5, 16), "10539.50")
        links, conflicts, _, _ = link_settlements([edc], [credit])
        self.assertEqual(len(links), 1)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["kind"], "settlement_crosscheck_imbalance")
        self.assertEqual(conflicts[0]["refs"], ["b1", "e1"])

    def test_one_to_one_greedy_smallest_date_diff_first(self):
        # 两张同额结算单、两笔同额到账:按日期差最近配对,不许一对多。
        e1 = _edc("e1", date(2026, 5, 15), "1070.00", net="1050.00", batch="B1")
        e2 = _edc("e2", date(2026, 5, 16), "1070.00", net="1050.00", batch="B2")
        b1 = _credit("b1", date(2026, 5, 16), "1050.00")
        b2 = _credit("b2", date(2026, 5, 17), "1050.00")
        links, _, matched_bank, matched_edc = link_settlements([e1, e2], [b1, b2])
        self.assertEqual(len(links), 2)
        self.assertEqual(matched_bank, {"b1", "b2"})
        self.assertEqual(matched_edc, {"e1", "e2"})
        pairs = {(ln["bank_ref"], ln["edc_ref"]) for ln in links}
        self.assertIn(("b1", "e2"), pairs)  # 同日 0 天差优先于跨 1 天

    def test_tolerance_is_one_satang(self):
        edc = _edc("e1", date(2026, 5, 15), "10700.00", net="10539.50")
        near = _credit("b1", date(2026, 5, 15), "10539.51")
        far = _credit("b2", date(2026, 5, 15), "10539.60")
        links, _, matched_bank, _ = link_settlements([edc], [near, far])
        self.assertEqual(len(links), 1)
        self.assertEqual(matched_bank, {"b1"})


class TestEdcInternalConflicts(unittest.TestCase):
    def test_imbalance_named(self):
        bad = _edc("e1", date(2026, 5, 15), "10700.00", fee="160.50", net="10500.00")
        ok = _edc("e2", date(2026, 5, 16), "10700.00", fee="160.50", net="10539.50")
        conflicts = edc_internal_conflicts([bad, ok])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["kind"], "edc_internal_imbalance")
        self.assertEqual(conflicts[0]["refs"], ["e1"])

    def test_missing_fee_not_guessed(self):
        self.assertEqual(edc_internal_conflicts([_edc("e1", date(2026, 5, 15), "100.00")]), [])


class TestOverlapSuspects(unittest.TestCase):
    def test_doc_on_edc_day_named_not_auto_deduped(self):
        doc = SalesDoc(
            ref="d1",
            day=date(2026, 5, 15),
            net=Decimal("1000.00"),
            vat=Decimal("70.00"),
            gross=Decimal("1070.00"),
            invoice_no="INV-001",
        )
        out = overlap_suspects([doc], {date(2026, 5, 15)})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "doc_edc_overlap_suspect")
        self.assertEqual(out[0]["refs"], ["d1"])
        self.assertEqual(overlap_suspects([doc], {date(2026, 5, 16)}), [])


if __name__ == "__main__":
    unittest.main()
