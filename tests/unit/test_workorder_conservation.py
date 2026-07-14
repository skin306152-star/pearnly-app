# -*- coding: utf-8 -*-
"""料件守恒纯闸守门测试(services/workorder/steps/conservation.py · 任务包 §5 步 6)。

纯函数、零库:构造混堆 items + 裁决 map,断言核心不变式 Σ桶==N 且每件恰一桶;畸形件
fail-closed 归待裁决;两类方向票无裁决 → 待裁决(G1R2 黑洞);waive → 已豁免桶。
"""

import unittest

from services.workorder.steps import conservation as c


def _item(item_id, kind, status="ok", flag_reason=None, file_ref=None):
    return {
        "id": item_id,
        "kind": kind,
        "status": status,
        "flag_reason": flag_reason,
        "file_ref": file_ref or f"/in/{item_id}.jpg",
    }


def _dec(decision, **extra):
    return {"decision": decision, **extra}


class BucketPartitionTests(unittest.TestCase):
    """每种终态桶都有料的混堆:Σ桶=N、每件恰一桶、桶归属正确。"""

    def _mixed(self):
        items = [
            _item("p_ok", "purchase_invoice", status="ok"),
            _item("p_face", "purchase_invoice", status="flagged", flag_reason="amount_math_fail"),
            _item("p_recalc", "purchase_invoice", status="flagged", flag_reason="amount_math_fail"),
            _item("s1", "sales_summary", status="ok"),
            _item("bank1", "bank_statement", status="pending"),
            _item("edc1", "edc_settlement", status="ok"),
            _item("nt", "non_tax", status="excluded", flag_reason="no_tax_elements:x"),
            _item("dup", "duplicate", status="excluded", flag_reason="duplicate_of:p_ok"),
            _item("p_excl", "purchase_invoice", status="flagged", flag_reason="amount_math_fail"),
            _item("dir_buy", "unknown", status="flagged", flag_reason="direction_ambiguous"),
            _item("dir_sell", "unknown", status="flagged", flag_reason="sales_direction_unhandled"),
            _item("dir_nt", "unknown", status="flagged", flag_reason="direction_ambiguous"),
            _item("waived1", "purchase_invoice", status="flagged", flag_reason="ocr_error:X"),
        ]
        decisions = {
            "p_face": _dec("face_value"),
            "p_recalc": _dec("recalc", values={"vat": "70.00"}),
            "p_excl": _dec("exclude"),
            "dir_buy": _dec("assign_kind", kind="purchase_invoice"),
            "dir_sell": _dec("assign_kind", kind="sales_doc"),
            "dir_nt": _dec("assign_kind", kind="non_tax"),
            "waived1": _dec("waive", reason="client confirmed by LINE, doc lost"),
        }
        return items, decisions

    def test_every_item_lands_in_exactly_one_bucket_sum_equals_n(self):
        items, decisions = self._mixed()
        cons = c.bucket_items(items, decisions)
        self.assertEqual(cons.total, len(items))
        self.assertTrue(cons.conserved(len(items)))
        # 每件恰一桶:并集=全体、两两不相交。
        placed = [it["id"] for bucket in cons.buckets.values() for it in bucket]
        self.assertEqual(sorted(placed), sorted(it["id"] for it in items))
        self.assertEqual(len(placed), len(set(placed)))

    def test_bucket_membership_is_correct_per_terminal_state(self):
        items, decisions = self._mixed()
        b = c.bucket_items(items, decisions).buckets
        ids = {k: {it["id"] for it in v} for k, v in b.items()}
        self.assertEqual(ids[c.INPUT_COUNTED], {"p_ok", "p_face", "p_recalc", "dir_buy"})
        self.assertEqual(ids[c.SALES_MATERIAL], {"s1"})
        self.assertEqual(ids[c.BANK], {"bank1", "edc1"})
        self.assertEqual(ids[c.EXCLUDED], {"nt", "dup", "p_excl", "dir_nt"})
        self.assertEqual(ids[c.SALES_REASSIGNED], {"dir_sell"})
        self.assertEqual(ids[c.WAIVED], {"waived1"})
        self.assertEqual(ids[c.PENDING], set())

    def test_stuck_reasons_empty_when_conserved(self):
        items, decisions = self._mixed()
        cons = c.bucket_items(items, decisions)
        self.assertEqual(c.stuck_reasons(cons, len(items)), [])


class SalesDocBucketTests(unittest.TestCase):
    """自动判本方销项票(kind=sales_doc · MC1-c.1)的终态归属。"""

    def test_flagged_sales_doc_without_decision_is_pending(self):
        # 拍板①:自动判 sales_doc 后 flagged 留一次人工过目 → 无裁决落待裁决桶(配 MC1-b 批量确认)。
        items = [_item("sd", "sales_doc", status="flagged", flag_reason="sales_doc_review")]
        cons = c.bucket_items(items, {})
        self.assertEqual([it["id"] for it in cons.pending], ["sd"])
        self.assertFalse(cons.conserved(1))

    def test_confirmed_sales_doc_goes_to_sales_reassigned(self):
        # 人工按 S(assign_kind sales_doc)确认销项 → 归销项侧桶,不再待裁决。
        items = [_item("sd", "sales_doc", status="flagged", flag_reason="sales_doc_review")]
        decs = {"sd": _dec("assign_kind", kind="sales_doc")}
        b = c.bucket_items(items, decs).buckets
        self.assertEqual({it["id"] for it in b[c.SALES_REASSIGNED]}, {"sd"})
        self.assertEqual(b[c.PENDING], [])

    def test_reassigned_sales_doc_to_purchase_counts_as_input(self):
        # 客户拍错票兜底:改判进项 → 计入 R1 桶(与方向票 assign_kind 同 _ASSIGN_BUCKET 口径)。
        items = [_item("sd", "sales_doc", status="flagged", flag_reason="sales_doc_review")]
        decs = {"sd": _dec("assign_kind", kind="purchase_invoice")}
        b = c.bucket_items(items, decs).buckets
        self.assertEqual({it["id"] for it in b[c.INPUT_COUNTED]}, {"sd"})

    def test_ok_sales_doc_reassigned_without_decision(self):
        # MC1-c.2 放宽自动 ok 后:status=ok 的 sales_doc 免裁直接归销项侧,不卡待裁决。
        items = [_item("sd", "sales_doc", status="ok")]
        b = c.bucket_items(items, {}).buckets
        self.assertEqual({it["id"] for it in b[c.SALES_REASSIGNED]}, {"sd"})


class FailClosedTests(unittest.TestCase):
    """畸形/未裁决件一律 fail-closed 归待裁决,守恒违例被逐件点名。"""

    def test_sales_direction_unhandled_without_decision_is_pending(self):
        # G1R2 黑洞:自家==卖方的方向票无裁决,过去照样出包;现在必须落待裁决桶。
        items = [_item("x", "unknown", status="flagged", flag_reason="sales_direction_unhandled")]
        cons = c.bucket_items(items, {})
        self.assertEqual([it["id"] for it in cons.pending], ["x"])
        self.assertFalse(cons.conserved(1))

    def test_direction_ambiguous_without_decision_is_pending(self):
        items = [_item("d", "unknown", status="flagged", flag_reason="direction_ambiguous")]
        cons = c.bucket_items(items, {})
        self.assertEqual([it["id"] for it in cons.pending], ["d"])

    def test_flagged_purchase_without_decision_is_pending(self):
        items = [_item("p", "purchase_invoice", status="flagged", flag_reason="amount_math_fail")]
        cons = c.bucket_items(items, {})
        self.assertEqual([it["id"] for it in cons.pending], ["p"])

    def test_malformed_unknown_kind_falls_to_pending_not_dropped(self):
        # 缺任何一桶归属的畸形件(未知 kind / pending 状态)→ 不丢,归待裁决,Σ 仍=N。
        items = [
            _item("weird", "some_future_kind", status="ok"),
            _item("stillpending", "unknown", status="pending"),
        ]
        cons = c.bucket_items(items, {})
        self.assertEqual(cons.total, 2)  # 一件不漏
        self.assertEqual({it["id"] for it in cons.pending}, {"weird", "stillpending"})

    def test_stuck_reasons_names_each_pending_ticket_by_file(self):
        items = [
            _item("ok1", "purchase_invoice", status="ok"),
            _item(
                "x",
                "unknown",
                status="flagged",
                flag_reason="sales_direction_unhandled",
                file_ref="/in/IMG_6d001f06.jpg",
            ),
        ]
        cons = c.bucket_items(items, {})
        reasons = c.stuck_reasons(cons, len(items))
        self.assertEqual(len(reasons), 1)
        self.assertIn("IMG_6d001f06.jpg", reasons[0])
        self.assertIn("sales_direction_unhandled", reasons[0])

    def test_conservation_violation_appended_when_total_mismatch(self):
        # 防御性:若 N 传错(> 实际件数),守恒违例条目现身(Σ桶≠N)。
        items = [_item("p", "purchase_invoice", status="ok")]
        cons = c.bucket_items(items, {})
        reasons = c.stuck_reasons(cons, 5)
        self.assertTrue(any("conservation_violation" in r for r in reasons))


class WaivePrecedenceTests(unittest.TestCase):
    def test_waive_wins_over_otherwise_pending_direction_ticket(self):
        items = [_item("x", "unknown", status="flagged", flag_reason="sales_direction_unhandled")]
        cons = c.bucket_items(items, {"x": _dec("waive", reason="lost original")})
        self.assertEqual([it["id"] for it in cons.buckets[c.WAIVED]], ["x"])
        self.assertEqual(cons.pending, [])
        self.assertTrue(cons.conserved(1))


if __name__ == "__main__":
    unittest.main()
