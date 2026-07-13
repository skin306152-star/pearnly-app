# -*- coding: utf-8 -*-
"""审核队列读模型 + 复核态写动作守门(services/workorder/review.py · MC1-b1)。

脱库:review_queue 喂 FakeCur 假行验分组投影;写动作 patch store/api 验事件与状态。锁四件:
①review_queue 跨客户 × 工单聚合正确(flag_reason 分组 / 到期日 / 客户池 / 返工标 / severity 筛);
②batch_decisions 部分成功逐条诚实返回;③reject_review 落 review_rejected + 重开 reconcile→package
+ 回可跑态;④declare_self_review 落声明事件(幂等 dedupe_key)。
"""

import unittest
from datetime import date, datetime, timezone
from unittest import mock

from services.workorder import api, engine, review


class FakeCur:
    """单查询假游标:execute 存参、fetchall 回预置行(RealDict 风格 dict 行)。"""

    def __init__(self, rows):
        self._rows = rows
        self.params = None

    def execute(self, _sql, params):
        self.params = params

    def fetchall(self):
        return self._rows


def _row(**kw):
    base = {
        "work_order_id": "wo-1",
        "workspace_client_id": 7,
        "period": "2569-05",
        "status": "review",
        "current_step": "review",
        "updated_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "client_name": "Sister Makeup",
        "client_tax_id": "0105551234567",
        "flag_reason": None,
        "flagged_count": 0,
        "next_due_efiling": date(2026, 6, 23),
        "next_due_paper": date(2026, 6, 15),
        "pool_pending": 0,
        "reject_count": 0,
    }
    base.update(kw)
    return base


class ReviewQueueTests(unittest.TestCase):
    def _run(self, rows, **kw):
        cur = FakeCur(rows)
        with mock.patch.object(review.line_client_pool_store, "ensure_table", return_value=None):
            return review.review_queue(cur, tenant_id="t-1", **kw)

    def test_groups_by_client_and_order_with_flag_breakdown(self):
        rows = [
            _row(flag_reason="amount_math_fail", flagged_count=2, pool_pending=3),
            _row(flag_reason="ocr_low_confidence:hi", flagged_count=1, pool_pending=3),
            _row(
                work_order_id="wo-2",
                workspace_client_id=9,
                client_name="Metta",
                flag_reason="direction_ambiguous",
                flagged_count=4,
                reject_count=1,
                next_due_efiling=date(2026, 6, 10),
            ),
        ]
        out = self._run(rows)
        self.assertEqual(out["counts"], {"clients": 2, "orders": 2, "flagged": 7})
        by_client = {c["workspace_client_id"]: c for c in out["clients"]}
        # 客户 7:一张工单,两组 flagged,合计 3,池 pending 3,义务到期日 ISO 化
        c7 = by_client[7]
        self.assertEqual(c7["pool_pending"], 3)
        o1 = c7["orders"][0]
        self.assertEqual(o1["flagged_total"], 3)
        self.assertEqual(len(o1["flagged_groups"]), 2)
        self.assertEqual(o1["next_due_efiling"], "2026-06-23")
        self.assertEqual(o1["top_severity"], "crit")  # 含 amount_math_fail
        self.assertFalse(o1["is_rework"])
        # 客户 9:返工件(reject_count>0)
        self.assertTrue(by_client[9]["orders"][0]["is_rework"])

    def test_order_with_no_flagged_items_still_listed(self):
        out = self._run([_row(flag_reason=None)])
        order = out["clients"][0]["orders"][0]
        self.assertEqual(order["flagged_groups"], [])
        self.assertEqual(order["flagged_total"], 0)
        self.assertIsNone(order["top_severity"])

    def test_severity_filter_drops_nonmatching_groups_and_empty_orders(self):
        rows = [
            _row(flag_reason="amount_math_fail", flagged_count=2),  # crit
            _row(flag_reason="ocr_low_confidence:hi", flagged_count=1),  # warn
            _row(
                work_order_id="wo-2", flag_reason="sales_doc_review", flagged_count=5
            ),  # warn only
        ]
        out = self._run(rows, severity="crit")
        # wo-1 保留仅 crit 组(total=2);wo-2 全 warn → 整条剔除
        self.assertEqual(out["counts"]["orders"], 1)
        order = out["clients"][0]["orders"][0]
        self.assertEqual(order["flagged_total"], 2)
        self.assertTrue(all(g["severity"] == "crit" for g in order["flagged_groups"]))

    def test_query_params_wire_filters(self):
        cur = FakeCur([])
        with mock.patch.object(review.line_client_pool_store, "ensure_table"):
            review.review_queue(cur, tenant_id="t-1", period="2569-05", client_id=7, severity=None)
        # period/client 出现在尾部参数(静态谓词值),tenant 首位
        self.assertEqual(cur.params[0], "t-1")
        self.assertIn("2569-05", cur.params)
        self.assertIn(7, cur.params)


class BatchDecisionsTests(unittest.TestCase):
    def test_partial_success_reports_each_row(self):
        # it-1 成功、it-2 item 不存在、it-3 非法裁决 —— 逐条诚实,不整批失败
        def _rec(cur, *, item_id, **k):
            if item_id == "it-2":
                raise api.WorkOrderApiError("workorder.item_not_found")
            if item_id == "it-3":
                raise api.WorkOrderApiError("workorder.decision_invalid")
            return {"id": 99}

        items = [
            {"item_id": "it-1", "decision": "face_value"},
            {"item_id": "it-2", "decision": "face_value"},
            {"item_id": "it-3", "decision": "bogus"},
        ]
        with mock.patch.object(api, "record_decision", side_effect=_rec):
            out = review.batch_decisions(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", items=items, actor="user:u1"
            )
        self.assertEqual(out["ok_count"], 1)
        self.assertEqual(out["fail_count"], 2)
        self.assertEqual(out["total"], 3)
        r = {x["item_id"]: x for x in out["results"]}
        self.assertTrue(r["it-1"]["ok"])
        self.assertEqual(r["it-1"]["event_id"], 99)
        self.assertFalse(r["it-2"]["ok"])
        self.assertEqual(r["it-2"]["error"], "workorder.item_not_found")
        self.assertEqual(r["it-3"]["error"], "workorder.decision_invalid")

    def test_empty_batch_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            review.batch_decisions(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", items=[], actor="user:u1"
            )
        self.assertEqual(ctx.exception.code, "workorder.batch_empty")

    def test_oversize_batch_rejected(self):
        items = [
            {"item_id": f"it-{i}", "decision": "face_value"} for i in range(review.MAX_BATCH + 1)
        ]
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            review.batch_decisions(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", items=items, actor="user:u1"
            )
        self.assertEqual(ctx.exception.code, "workorder.batch_too_large")


class RejectReviewTests(unittest.TestCase):
    def _patch_store(self, wo_status):
        appended = []

        def _append(cur, **kw):
            appended.append(kw)
            return {"id": len(appended)}

        status_holder = {}

        def _set_status(cur, *, tenant_id, work_order_id, status, current_step=None):
            status_holder["status"] = status
            status_holder["step"] = current_step

        return (
            appended,
            status_holder,
            mock.patch.object(review.store, "get_work_order", return_value={"status": wo_status}),
            mock.patch.object(review.store, "append_event", side_effect=_append),
            mock.patch.object(review.store, "set_status", side_effect=_set_status),
        )

    def test_reject_logs_event_reopens_steps_and_returns_runnable(self):
        appended, status_holder, p1, p2, p3 = self._patch_store("review")
        with p1, p2, p3:
            out = review.reject_review(
                mock.Mock(),
                tenant_id="t-1",
                work_order_id="wo-1",
                actor="user:u2",
                reason="税额可疑",
            )
        types = [(a["step"], a["event_type"]) for a in appended]
        # 一条 review_rejected(step=review)+ 逐步 step_reopened(reconcile/compute/package)
        self.assertIn(("review", review.EVT_REVIEW_REJECTED), types)
        for step in ("reconcile", "compute", "package"):
            self.assertIn((step, engine.EVT_REOPENED), types)
        self.assertEqual(out["reopened_steps"], ["reconcile", "compute", "package"])
        self.assertEqual(status_holder["status"], engine.STATUS_RUNNING)
        self.assertEqual(status_holder["step"], "reconcile")

    def test_reason_required(self):
        _, _, p1, p2, p3 = self._patch_store("review")
        with p1, p2, p3, self.assertRaises(api.WorkOrderApiError) as ctx:
            review.reject_review(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", actor="user:u2", reason="  "
            )
        self.assertEqual(ctx.exception.code, "workorder.reject_reason_required")

    def test_non_review_status_rejected(self):
        _, _, p1, p2, p3 = self._patch_store("stuck")
        with p1, p2, p3, self.assertRaises(api.WorkOrderApiError) as ctx:
            review.reject_review(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", actor="user:u2", reason="x"
            )
        self.assertEqual(ctx.exception.code, "workorder.not_reviewable")


class RejectAndRerunTests(unittest.TestCase):
    """MC2-A1 ②:驳回翻状态与抢租约同一事务(收进 request_run 的 lease 闭包),消灭
    「running + 租约 NULL」孤儿窗口;抢不到租约驳回不落 → run_in_progress。"""

    class _FakeCM:
        def __enter__(self):
            return mock.Mock()

        def __exit__(self, *a):
            return False

    class _FakeDB:
        def get_cursor(self, commit=False):
            return RejectAndRerunTests._FakeCM()

    def _wire(self, *, acquire=True, wo_status="review"):
        from services.workorder import runner

        self.appended = []
        self.acquired = []
        self.spawned = []

        def _append(cur, **kw):
            self.appended.append(kw)
            return {"id": len(self.appended)}

        def _acquire(cur, *, tenant_id, work_order_id, owner, ttl_seconds):
            self.acquired.append(owner)
            return acquire

        return (
            mock.patch.object(runner, "db", self._FakeDB()),
            mock.patch.object(
                runner, "_spawn_advance", lambda t, w, o: self.spawned.append((t, w, o))
            ),
            mock.patch.object(review.store, "ensure_runtime", return_value=None),
            mock.patch.object(review.store, "acquire_run_lease", side_effect=_acquire),
            mock.patch.object(review.store, "get_work_order", return_value={"status": wo_status}),
            mock.patch.object(review.store, "append_event", side_effect=_append),
            mock.patch.object(review.store, "set_status", return_value=None),
        )

    def _enter_all(self, stack, patches):
        for p in patches:
            stack.enter_context(p)

    def test_reject_and_requeue_share_one_transaction(self):
        import contextlib

        with contextlib.ExitStack() as stack:
            self._enter_all(stack, self._wire())
            out = review.reject_and_rerun(
                tenant_id="t-1", work_order_id="wo-1", actor="user:u2", reason="税额可疑"
            )
        self.assertEqual(out["status"], engine.STATUS_RUNNING)
        types = [a["event_type"] for a in self.appended]
        # 同一事务序:review_rejected → step_reopened×3 → run_requested(租约已在手)。
        self.assertEqual(types[0], review.EVT_REVIEW_REJECTED)
        self.assertEqual(types[-1], "run_requested")
        self.assertEqual(types.count(engine.EVT_REOPENED), 3)
        self.assertEqual(len(self.acquired), 1)
        self.assertEqual(self.spawned, [("t-1", "wo-1", self.acquired[0])])

    def test_lease_busy_raises_run_in_progress_without_reject(self):
        import contextlib

        with contextlib.ExitStack() as stack:
            self._enter_all(stack, self._wire(acquire=False))
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                review.reject_and_rerun(
                    tenant_id="t-1", work_order_id="wo-1", actor="user:u2", reason="x"
                )
        self.assertEqual(ctx.exception.code, "workorder.run_in_progress")
        self.assertEqual(self.appended, [])  # 驳回不落,工单还是 review
        self.assertEqual(self.spawned, [])

    def test_validation_error_propagates_and_nothing_scheduled(self):
        import contextlib

        with contextlib.ExitStack() as stack:
            self._enter_all(stack, self._wire(wo_status="stuck"))
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                review.reject_and_rerun(
                    tenant_id="t-1", work_order_id="wo-1", actor="user:u2", reason="x"
                )
        self.assertEqual(ctx.exception.code, "workorder.not_reviewable")
        self.assertEqual(self.spawned, [])


class SelfReviewDeclareTests(unittest.TestCase):
    def test_declares_event_with_dedupe_key(self):
        captured = {}

        def _append(cur, **kw):
            captured.update(kw)
            return {"id": 7}

        with (
            mock.patch.object(review.store, "get_work_order", return_value={"status": "review"}),
            mock.patch.object(review.store, "append_event", side_effect=_append),
        ):
            out = review.declare_self_review(
                mock.Mock(), tenant_id="t-1", work_order_id="wo-1", actor="user:u1"
            )
        self.assertTrue(out["ok"])
        self.assertEqual(captured["event_type"], review.EVT_SELF_REVIEW_DECLARED)
        self.assertEqual(captured["dedupe_key"], "self_review:wo-1:user:u1")

    def test_only_review_status(self):
        with mock.patch.object(review.store, "get_work_order", return_value={"status": "archive"}):
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                review.declare_self_review(
                    mock.Mock(), tenant_id="t-1", work_order_id="wo-1", actor="user:u1"
                )
        self.assertEqual(ctx.exception.code, "workorder.not_reviewable")


if __name__ == "__main__":
    unittest.main()
