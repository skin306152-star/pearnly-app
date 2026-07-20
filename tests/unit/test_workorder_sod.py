# -*- coding: utf-8 -*-
"""职责分离(SoD)判定守门(services/workorder/sod.py · C3 · 拍板3)。

纯函数,零 DB/框架依赖:制单集回放(裁决 + 人工填销项,run_requested 机械触发不计入)、
复核/授权闸判定(enforced=False 恒放行 = 一人所全兼零特判)。三拒场景(复核=制单人 /
无签批冻结 / 授权=制单人)是 C3 验收硬项,逐条钉在这里。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from services.workorder import sod


def _decision(actor):
    return {"event_type": "human_decision", "actor": actor, "payload": {"item_id": "a"}}


def _sales_summary(actor):
    return {
        "event_type": "item_classified",
        "actor": actor,
        "payload": {"kind": "sales_summary", "status": "ok"},
    }


def _classified_purchase(actor):
    return {
        "event_type": "item_classified",
        "actor": actor,
        "payload": {"kind": "purchase_invoice", "status": "ok"},
    }


def _run_requested(actor):
    return {"event_type": "run_requested", "actor": actor, "payload": {}}


def _review_signoff(actor):
    return {"event_type": "review_signoff", "actor": actor, "payload": {"role": "reviewer"}}


class PreparerActorsTests(unittest.TestCase):
    def test_decision_actor_counts(self):
        events = [_decision("user:1")]
        self.assertEqual(sod.preparer_actors(events), {"user:1"})

    def test_manual_sales_summary_counts(self):
        events = [_sales_summary("user:2")]
        self.assertEqual(sod.preparer_actors(events), {"user:2"})

    def test_direct_read_classify_not_counted(self):
        # 非人工填销项(无 kind=sales_summary 或 status 直读)不算制单判断。
        events = [_classified_purchase("user:3")]
        self.assertEqual(sod.preparer_actors(events), set())

    def test_run_requested_mechanical_not_counted(self):
        events = [_run_requested("user:4")]
        self.assertEqual(sod.preparer_actors(events), set())

    def test_dedup_across_multiple_events(self):
        events = [_decision("user:1"), _decision("user:1"), _sales_summary("user:1")]
        self.assertEqual(sod.preparer_actors(events), {"user:1"})

    def test_multiple_preparers(self):
        events = [_decision("user:1"), _sales_summary("user:2")]
        self.assertEqual(sod.preparer_actors(events), {"user:1", "user:2"})


class ReviewerActorsTests(unittest.TestCase):
    def test_collects_signoff_actors(self):
        events = [_review_signoff("user:9")]
        self.assertEqual(sod.reviewer_actors(events), {"user:9"})

    def test_non_signoff_events_ignored(self):
        events = [_decision("user:1")]
        self.assertEqual(sod.reviewer_actors(events), set())


class ReviewerViolationTests(unittest.TestCase):
    def test_flag_off_always_passes(self):
        events = [_decision("user:1")]
        self.assertIsNone(sod.reviewer_violation(events, "user:1", enforced=False))

    def test_flag_on_reviewer_is_preparer_rejected(self):
        events = [_decision("user:1")]
        self.assertEqual(
            sod.reviewer_violation(events, "user:1", enforced=True),
            sod.REVIEWER_IS_PREPARER,
        )

    def test_flag_on_distinct_reviewer_passes(self):
        events = [_decision("user:1")]
        self.assertIsNone(sod.reviewer_violation(events, "user:2", enforced=True))


class ApproverViolationTests(unittest.TestCase):
    def test_flag_off_always_passes(self):
        events = [_decision("user:1")]
        self.assertIsNone(sod.approver_violation(events, "user:1", enforced=False))

    def test_flag_on_approver_is_preparer_rejected(self):
        events = [_decision("user:1"), _review_signoff("user:2")]
        self.assertEqual(
            sod.approver_violation(events, "user:1", enforced=True),
            sod.APPROVER_IS_PREPARER,
        )

    def test_flag_on_no_signoff_rejected(self):
        events = [_decision("user:1")]
        self.assertEqual(
            sod.approver_violation(events, "user:2", enforced=True),
            sod.REVIEW_REQUIRED,
        )

    def test_flag_on_signoff_by_preparer_does_not_count(self):
        # 复核人若同时也在制单集里,那条签批不算「有效」复核——不能自审自签绕过闸。
        events = [_decision("user:1"), _review_signoff("user:1")]
        self.assertEqual(
            sod.approver_violation(events, "user:2", enforced=True),
            sod.REVIEW_REQUIRED,
        )

    def test_flag_on_valid_three_actor_chain_passes(self):
        # 制单人 user:1、复核人 user:2(≠制单人)、授权人 user:3(≠制单人)→ 放行。
        events = [_decision("user:1"), _review_signoff("user:2")]
        self.assertIsNone(sod.approver_violation(events, "user:3", enforced=True))


def _self_review(actor):
    return {"event_type": "self_review_declared", "actor": actor, "payload": {}}


class SelfReviewEscapeTests(unittest.TestCase):
    """单人所自审逃生门(方案决策 5 · 声明制不豁免制):授权人本人声明自审 → 放行,但留痕可审。"""

    def test_declared_by_actor_detected(self):
        events = [_decision("user:1"), _self_review("user:1")]
        self.assertTrue(sod.self_review_declared_by(events, "user:1"))
        self.assertFalse(sod.self_review_declared_by(events, "user:2"))

    def test_self_declared_approver_is_allowed_despite_being_preparer(self):
        # 单人所:制单=授权=user:1,本会因 approver_is_preparer 被拒;自审声明后放行。
        events = [_decision("user:1")]
        self.assertEqual(
            sod.approver_violation(events, "user:1", enforced=True), sod.APPROVER_IS_PREPARER
        )
        events_declared = events + [_self_review("user:1")]
        self.assertIsNone(sod.approver_violation(events_declared, "user:1", enforced=True))

    def test_declaration_does_not_bypass_when_flag_off_is_moot(self):
        # 闸关本就放行,声明与否不改变(逐字节维持单人流)。
        events = [_decision("user:1"), _self_review("user:1")]
        self.assertIsNone(sod.approver_violation(events, "user:1", enforced=False))


def _signoff(actor="user:rev", note="", at="2026-06-01T10:00:00+00:00"):
    return {
        "event_type": "review_signoff",
        "actor": actor,
        "payload": {"note": note},
        "created_at": at,
    }


def _rejected():
    return {"event_type": "review_rejected", "actor": "user:rev", "payload": {"reason": "税额可疑"}}


def _run_finished():
    return {"event_type": "run_finished", "actor": "system:runner", "payload": {"status": "review"}}


class SignoffProjectionTests(unittest.TestCase):
    """P0-1:签批投影四态——无签 None / 签后 fresh / 签后重跑 stale / 签后驳回作废 /
    重签恢复 fresh。事件按落库序(id 升序)入参,与两读模型取库口径一致。"""

    def test_no_signoff_returns_none(self):
        self.assertIsNone(sod.signoff_projection([_decision("user:1"), _run_finished()]))

    def test_empty_events_returns_none(self):
        self.assertIsNone(sod.signoff_projection([]))

    def test_signoff_fresh(self):
        proj = sod.signoff_projection([_run_finished(), _signoff(note="核对无误")])
        self.assertEqual(proj["actor"], "user:rev")
        self.assertEqual(proj["note"], "核对无误")
        self.assertEqual(proj["at"], "2026-06-01T10:00:00+00:00")
        self.assertFalse(proj["stale"])

    def test_signoff_then_run_finished_is_stale(self):
        # 裁决触发的正常重跑:复核后数字重生,需重签。
        proj = sod.signoff_projection([_signoff(), _run_finished()])
        self.assertTrue(proj["stale"])
        self.assertEqual(proj["actor"], "user:rev")

    def test_signoff_then_rejected_returns_none(self):
        # 驳回打回工单,旧签批作废。
        self.assertIsNone(sod.signoff_projection([_signoff(), _rejected()]))

    def test_resign_after_stale_restores_fresh(self):
        proj = sod.signoff_projection([_signoff(), _run_finished(), _signoff(actor="user:rev2")])
        self.assertEqual(proj["actor"], "user:rev2")
        self.assertFalse(proj["stale"])

    def test_resign_after_reject_restores_fresh(self):
        proj = sod.signoff_projection(
            [_signoff(), _rejected(), _run_finished(), _signoff(actor="user:rev3")]
        )
        self.assertEqual(proj["actor"], "user:rev3")
        self.assertFalse(proj["stale"])

    def test_multiple_run_finished_after_signoff_stays_stale(self):
        self.assertTrue(
            sod.signoff_projection([_signoff(), _run_finished(), _run_finished()])["stale"]
        )

    def test_datetime_created_at_serialized_to_iso(self):
        evt = _signoff()
        evt["created_at"] = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(sod.signoff_projection([evt])["at"], "2026-06-01T10:00:00+00:00")

    def test_missing_note_defaults_empty(self):
        evt = {
            "event_type": "review_signoff",
            "actor": "user:rev",
            "payload": {},
            "created_at": None,
        }
        proj = sod.signoff_projection([evt])
        self.assertEqual(proj["note"], "")
        self.assertIsNone(proj["at"])


if __name__ == "__main__":
    unittest.main()
