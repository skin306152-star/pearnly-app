# -*- coding: utf-8 -*-
"""工单事件流 → 银行对账候选适配器测试(E1 · services/recon/workorder_recon_adapter.py)。

纯函数、零副作用:构造 item_classified/human_decision 事件 + 银行流水行,验证
候选字段映射、方向裁决覆盖、逐笔对平分桶(自动/人审/缺票/未达)与两张清单金额结算。
打分引擎(bank_recon_scoring)一行不改,这里只验适配层。
"""

import unittest
from decimal import Decimal

from services.recon import workorder_recon_adapter as adapter
from services.recon.bank_recon_types import StatementRow


def _classified(item_id, *, kind="purchase_invoice", total, date=None, inv=None, vendor=None):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": kind,
            "status": "ok",
            "money": {
                "subtotal": None,
                "vat": None,
                "total_amount": total,
                "invoice_number": inv,
                "seller_tax": "0735527000289",
                "invoice_date": date,
                "vendor": vendor,
            },
        },
    }


def _assign(item_id, kind):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": "assign_kind", "kind": kind},
    }


def _out(amount, *, date=None, desc="payment"):
    return adapter.tx_from_gt_entry(
        {"withdrawal": amount, "deposit": "", "transaction_date": date, "description": desc}
    )


class CandidateMappingTests(unittest.TestCase):
    def test_maps_money_fields_to_candidate(self):
        events = [
            _classified(
                "p1", total="752.00", date="2026-06-07", inv="INV-26-001", vendor="Supplier"
            )
        ]
        cands = adapter.candidates_from_events(events)
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertEqual(c["id"], "p1")
        self.assertEqual(c["amount_total"], "752.00")
        self.assertEqual(c["invoice_date"], "2026-06-07")
        self.assertEqual(c["invoice_no"], "INV-26-001")
        self.assertEqual(c["vendor"], "Supplier")
        self.assertEqual(c["category_tag"], "purchase")

    def test_skips_items_without_money(self):
        events = [
            {
                "event_type": "item_classified",
                "payload": {"item_id": "s1", "kind": "sales_summary", "status": "ok"},
            }
        ]
        self.assertEqual(adapter.candidates_from_events(events), [])

    def test_latest_classified_wins(self):
        events = [
            _classified("p1", total="100.00"),
            _classified("p1", total="200.00"),
        ]
        cands = adapter.candidates_from_events(events)
        self.assertEqual(cands[0]["amount_total"], "200.00")

    def test_assign_kind_overrides_direction_category(self):
        events = [
            _classified("d1", kind="unknown", total="500.00"),
            _assign("d1", "sales_doc"),
        ]
        cands = adapter.candidates_from_events(events)
        self.assertEqual(cands[0]["category_tag"], "sales")

    def test_assign_non_tax_excludes_candidate(self):
        events = [
            _classified("d1", kind="unknown", total="500.00"),
            _assign("d1", "non_tax"),
        ]
        self.assertEqual(adapter.candidates_from_events(events), [])


class StatementRowMappingTests(unittest.TestCase):
    def test_withdrawal_row_is_out(self):
        import datetime

        row = StatementRow(datetime.date(2026, 6, 7), "Supplier INV", 752.0, 0.0, 1000.0)
        tx = adapter.tx_from_statement_row(row)
        self.assertEqual(tx["direction"], "OUT")
        self.assertEqual(tx["amount"], 752.0)
        self.assertEqual(tx["tx_date"], "2026-06-07")

    def test_deposit_row_is_in(self):
        import datetime

        row = StatementRow(datetime.date(2026, 6, 5), "Customer", 0.0, 655.0, 1655.0)
        tx = adapter.tx_from_statement_row(row)
        self.assertEqual(tx["direction"], "IN")
        self.assertEqual(tx["amount"], 655.0)

    def test_tx_id_is_row_hash_and_stable_on_reparse(self):
        # MC1-b3:statement_tx_id 是内容指纹(row_hash),同一行重解析恒定不变,是人审
        # 裁决落库的落点身份——不是随机 uuid,不需要额外持久化映射表。
        import datetime

        row_a = StatementRow(datetime.date(2026, 6, 7), "Supplier INV", 752.0, 0.0, 1000.0)
        row_b = StatementRow(datetime.date(2026, 6, 7), "Supplier INV", 752.0, 0.0, 1000.0)
        tx_a = adapter.tx_from_statement_row(row_a)
        tx_b = adapter.tx_from_statement_row(row_b)
        self.assertEqual(tx_a["_tx_id"], row_a.row_hash)
        self.assertEqual(tx_a["_tx_id"], tx_b["_tx_id"])
        self.assertTrue(tx_a["_tx_id"])


class ReconcileBucketsTests(unittest.TestCase):
    """逐笔对平:唯一高分自动 / 多候选人审 / 缺票 / 未达,差额手算一致。"""

    def _events(self):
        return [
            # p1:与 tx752 精确同额同日同描述 → 自动匹配(≥85)。
            _classified(
                "p1", total="752.00", date="2026-06-07", inv="INV-26-001", vendor="Supplier"
            ),
            # p2:与 tx500 同额、无日期 → 分 65 落人审区(60~85)。
            _classified("p2", total="500.00", inv="IVX", vendor=None),
            # p3:无任何对应流水 → 未达清单。
            _classified("p3", total="300.00", inv="IVZ", vendor=None),
        ]

    def test_full_reconcile(self):
        txs = [
            _out("752.00", date="2026-06-07", desc="Supplier INV-26-001"),
            _out("500.00", desc="payment"),
            _out("999.00", desc="unknown payee"),
        ]
        cands = adapter.candidates_from_events(self._events())
        r = adapter.reconcile_workorder(txs, cands)

        self.assertEqual(len(r.auto_matched), 1)
        self.assertEqual(r.auto_matched[0]["candidate_id"], "p1")
        self.assertEqual(r.auto_matched[0]["score"], 100.0)

        self.assertEqual(len(r.review), 1)
        review_ids = {c["candidate_id"] for c in r.review[0]["candidates"]}
        self.assertIn("p2", review_ids)

        self.assertEqual(len(r.missing_invoice), 1)
        self.assertEqual(r.missing_invoice[0]["amount"], "999.00")

        self.assertEqual(len(r.unmatched_invoice), 1)
        self.assertEqual(r.unmatched_invoice[0]["candidate_id"], "p3")
        self.assertEqual(r.unmatched_invoice[0]["amount"], "300.00")

        # 差额手算:缺票 999.00,未达 300.00,净差 699.00。
        self.assertEqual(r.diff["missing_invoice_total"], "999.00")
        self.assertEqual(r.diff["unmatched_invoice_total"], "300.00")
        self.assertEqual(r.diff["net"], "699.00")
        self.assertEqual(
            Decimal(r.diff["missing_invoice_total"]) - Decimal(r.diff["unmatched_invoice_total"]),
            Decimal(r.diff["net"]),
        )

    def test_two_high_candidates_go_to_review_not_auto(self):
        # 两张候选都精确同额同日 → 不唯一,不自动定,交人审(避免误配)。
        events = [
            _classified("a", total="752.00", date="2026-06-07", vendor="X"),
            _classified("b", total="752.00", date="2026-06-07", vendor="Y"),
        ]
        cands = adapter.candidates_from_events(events)
        r = adapter.reconcile_workorder([_out("752.00", date="2026-06-07", desc="pay")], cands)
        self.assertEqual(len(r.auto_matched), 0)
        self.assertEqual(len(r.review), 1)

    def test_empty_inputs_yield_zero_diff(self):
        r = adapter.reconcile_workorder([], [])
        self.assertEqual(r.diff["net"], "0")
        self.assertEqual(r.as_gate_payload()["missing_invoice_count"], 0)

    def test_review_bucket_carries_statement_tx_id_for_decide_endpoint(self):
        # MC1-b3:review 桶的 tx 视图要带 statement_tx_id,前端裁决卡才有落点可传给
        # POST .../bank-recon/decide。用真 StatementRow(非 gt_entry)喂,拿到真 row_hash。
        import datetime

        from services.recon.bank_recon_types import StatementRow

        row = StatementRow(datetime.date(2026, 6, 7), "payment", 500.0, 0.0, 1000.0)
        tx = adapter.tx_from_statement_row(row)
        cands = adapter.candidates_from_events(
            [_classified("p2", total="500.00", inv="IVX", vendor=None)]
        )
        r = adapter.reconcile_workorder([tx], cands)
        self.assertEqual(len(r.review), 1)
        self.assertEqual(r.review[0]["tx"]["statement_tx_id"], row.row_hash)


if __name__ == "__main__":
    unittest.main()
