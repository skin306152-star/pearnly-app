# -*- coding: utf-8 -*-
"""LINE 待问暂挂池 store(services/line_binding/line_client_pool_store)· D2-S3 契约。

钉死:同票二次 stage 命中 active 唯一约束不重复(幂等回原行)、非法跳转结构化拒
(IllegalTransitionError)、pending→staged 回退合法(推送失败路)、transition 的
CAS 在并发改写下视为跳转失效(latest-wins)、表缺失自愈重试。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_pool_store as s


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


_ROW = {
    "id": 1,
    "tenant_id": "t-1",
    "workspace_client_id": 84,
    "work_order_id": "wo-1",
    "item_id": "item-1",
    "period": "2026-07",
    "question_type": "direction",
    "question_payload": {},
    "status": "staged",
    "batch_id": None,
    "answer_raw": None,
    "resolution": None,
    "created_by": "user:1",
    "created_at": None,
    "sent_at": None,
    "answered_at": None,
    "closed_at": None,
    "updated_at": None,
}


class EnsureTableTests(unittest.TestCase):
    def test_idempotent_rerun_does_not_raise(self):
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("core.rls.apply_tenant_rls") as apply_rls,
        ):
            s.ensure_table()
            s.ensure_table()
        apply_rls.assert_called_with(cur, "line_client_questions")
        self.assertEqual(apply_rls.call_count, 2)


class StageTests(unittest.TestCase):
    def _stage_kwargs(self):
        return dict(
            workspace_client_id=84,
            work_order_id="wo-1",
            item_id="item-1",
            period="2026-07",
            question_type=vocab.QUESTION_DIRECTION,
            created_by="user:1",
        )

    def test_rejects_unknown_question_type(self):
        with self.assertRaises(s.ClientPoolError):
            s.stage("t-1", **{**self._stage_kwargs(), "question_type": "bogus"})

    def test_fresh_insert_returns_new_row(self):
        cur = MagicMock()
        cur.fetchone.return_value = dict(_ROW)
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.stage("t-1", **self._stage_kwargs())
        self.assertEqual(out["status"], vocab.STAGED)
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (tenant_id, work_order_id, item_id)", sql)
        self.assertIn("DO NOTHING", sql)

    def test_duplicate_stage_is_idempotent_not_duplicated(self):
        """同票二次 stage:INSERT 撞 uq_lcq_active_item 空手而归(fetchone None)→
        原样查回既有 active 行,绝不产出第二条。"""
        cur = MagicMock()
        cur.fetchone.side_effect = [None, dict(_ROW)]  # 第一次 INSERT 冲突, 第二次 SELECT 命中
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.stage("t-1", **self._stage_kwargs())
        self.assertEqual(out["id"], 1)
        self.assertEqual(cur.execute.call_count, 2)  # INSERT + 补 SELECT,没有第二条 INSERT

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_client_questions" does not exist'),
            None,
        ]
        cur.fetchone.return_value = dict(_ROW)
        with (
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.stage("t-1", **self._stage_kwargs())
        ensure.assert_called_once()


class TransitionTests(unittest.TestCase):
    def test_illegal_transition_is_rejected_before_update(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"status": vocab.APPLIED}  # 终态
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            with self.assertRaises(s.IllegalTransitionError) as ctx:
                s.transition("t-1", 1, vocab.PENDING)
        self.assertEqual(ctx.exception.from_status, vocab.APPLIED)
        self.assertEqual(ctx.exception.to_status, vocab.PENDING)
        self.assertEqual(cur.execute.call_count, 1)  # 只读了一次,没跑 UPDATE

    def test_pending_to_staged_rollback_is_legal(self):
        """推送失败回退:pending → staged 是唯一允许的"倒退"跳转。"""
        cur = MagicMock()
        cur.fetchone.side_effect = [
            {"status": vocab.PENDING},
            {**_ROW, "status": vocab.STAGED},
        ]
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.transition("t-1", 1, vocab.STAGED)
        self.assertEqual(out["status"], vocab.STAGED)

    def test_manual_review_to_applied_stamps_answered_at(self):
        cur = MagicMock()
        cur.fetchone.side_effect = [
            {"status": vocab.MANUAL_REVIEW},
            {**_ROW, "status": vocab.APPLIED},
        ]
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            s.transition("t-1", 1, vocab.APPLIED, resolution={"decision": "exclude"})
        update_sql = cur.execute.call_args_list[1].args[0]
        self.assertIn("answered_at = now()", update_sql)

    def test_concurrent_write_makes_transition_stale(self):
        """CAS latest-wins:UPDATE ... WHERE status=<期望的当前态> 影响 0 行(被别处抢先改写)
        → 视为跳转失效,报 IllegalTransitionError 而不是静默覆盖。"""
        cur = MagicMock()
        cur.fetchone.side_effect = [{"status": vocab.PENDING}, None]  # UPDATE 没打中任何行
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            with self.assertRaises(s.IllegalTransitionError):
                s.transition("t-1", 1, vocab.APPLIED)

    def test_question_not_found_raises(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            with self.assertRaises(s.ClientPoolError):
                s.transition("t-1", 999, vocab.PENDING)

    def test_unknown_target_status_rejected(self):
        with self.assertRaises(s.ClientPoolError):
            s.transition("t-1", 1, "bogus_status")


class ListForClientTests(unittest.TestCase):
    def test_defaults_to_active_statuses_only(self):
        cur = MagicMock()
        cur.fetchall.return_value = [dict(_ROW)]
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.list_for_client("t-1", 84)
        self.assertEqual(len(out), 1)
        params = cur.execute.call_args.args[1]
        self.assertEqual(set(params[-1]), set(vocab.ACTIVE_STATUSES))


if __name__ == "__main__":
    unittest.main()
