# -*- coding: utf-8 -*-
"""工单跑批收尾通知会计真库闭环(IN-0c · 本地真库)。

真建工单 + 真 line_bindings 绑定,模拟一次 run 收尾(run_requested → 终态 → run_finished
事件序列,不跑真引擎),验证 notify_run_outcome 走真表连表查询(work_order_events 反查
发起人/卡点 + line_bindings JOIN users 拿语言 + workspace_clients 拿客户名)后,
notification_logs 恰落一行、字段齐(template/event_ref/line_user_id/status)。

跑法(CI 无真库自动 skip):
    PEARNLY_INTEGRATION_DB=1 DATABASE_URL=postgresql://... PGSSLMODE=disable \
    python -m unittest tests.integration.test_workorder_notify_real
"""

from __future__ import annotations

import unittest
import uuid
from unittest import mock

from tests.integration._helpers import require_db


class WorkorderNotifyRealDb(unittest.TestCase):
    def setUp(self):
        require_db()
        from core import db
        from services.notification import store as notif_store
        from services.workorder import engine, runner
        from services.workorder import store as wo_store
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.notif_store, self.engine, self.runner = db, notif_store, engine, runner
        self.wo_store = wo_store

        build_workorder_schema()
        wo_store.ensure_runtime()
        notif_store.ensure_notification_tables()

        self.user_id = str(uuid.uuid4())
        self.tenant = str(uuid.uuid4())
        self.line_user_id = f"Utest{uuid.uuid4().hex[:20]}"
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users(id, username, password_hash, tenant_id, preferred_lang) "
                "VALUES (%s, %s, 'x', %s, 'zh')",
                (self.user_id, f"wo-notify-{self.user_id[:8]}", self.tenant),
            )
            cur.execute(
                "INSERT INTO line_bindings(user_id, line_user_id) VALUES (%s, %s)",
                (self.user_id, self.line_user_id),
            )
            cur.execute(
                "INSERT INTO workspace_clients(tenant_id, user_id, name, tax_id) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (self.tenant, self.user_id, "真库测试客户", "0000000000000"),
            )
            self.ws_id = int(cur.fetchone()["id"])
            wo = wo_store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=self.ws_id, period="2569-06"
            )
            self.wo_id = str(wo["id"])
        self.addCleanup(self._cleanup)

        self.gate = mock.patch(
            "core.feature_flags.pearnly_ai_run_notify_enabled_for", return_value=True
        ).start()
        self.push = mock.patch(
            "services.line_binding.line_reply.push_text_context", return_value=True
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _cleanup(self):
        with self.db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM notification_logs WHERE user_id = %s", (self.user_id,))
            cur.execute("DELETE FROM work_order_events WHERE work_order_id = %s", (self.wo_id,))
            cur.execute("DELETE FROM work_orders WHERE id = %s", (self.wo_id,))
            cur.execute("DELETE FROM workspace_clients WHERE id = %s", (self.ws_id,))
            cur.execute("DELETE FROM line_bindings WHERE user_id = %s", (self.user_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))

    def _simulate_run(self, *, completed: bool):
        """模拟一次 run 收尾(不跑真引擎):落 run_requested(会计发起)→ 工单落终态 →
        run_finished 事件,取回 order + run_event_id 供 notify_run_outcome 直调——同 runner.
        advance() 收尾后 _notify_run_outcome 拿到的两个实参形态。"""
        with self.db.get_cursor(commit=True) as cur:
            self.wo_store.append_event(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                step=self.runner.RUN_STEP,
                event_type=self.runner.EVT_RUN_REQUESTED,
                actor=f"user:{self.user_id}",
            )
            if not completed:
                self.wo_store.append_event(
                    cur,
                    tenant_id=self.tenant,
                    work_order_id=self.wo_id,
                    step="reconcile",
                    event_type=self.engine.EVT_NEEDS,
                    payload={"missing": ["sales_summary"]},
                )
            self.wo_store.set_status(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                status=self.engine.STATUS_REVIEW if completed else self.engine.STATUS_STUCK,
                current_step="package" if completed else "reconcile",
            )
            event = self.wo_store.append_event(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                step=self.runner.RUN_STEP,
                event_type=self.runner.EVT_RUN_FINISHED,
                actor="system:runner",
            )
        with self.db.get_cursor() as cur:
            order = self.wo_store.get_work_order(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
        return order, event["id"]

    def test_run_finished_writes_one_notification_log_row(self):
        from services.notification import workorder_notify

        order, run_event_id = self._simulate_run(completed=True)
        workorder_notify.notify_run_outcome(order, run_event_id)

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT template_code, event_ref, line_user_id, status FROM notification_logs "
                "WHERE user_id = %s",
                (self.user_id,),
            )
            rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["template_code"], workorder_notify.TEMPLATE_DONE)
        self.assertEqual(row["event_ref"], f"{self.wo_id}:{run_event_id}")
        self.assertEqual(row["line_user_id"], self.line_user_id)
        self.assertEqual(row["status"], "sent")
        self.push.assert_called_once()

    def test_stuck_run_writes_stuck_template_and_dedupes_same_run(self):
        from services.notification import workorder_notify

        order, run_event_id = self._simulate_run(completed=False)
        workorder_notify.notify_run_outcome(order, run_event_id)
        workorder_notify.notify_run_outcome(order, run_event_id)  # 同一次 run 重复调用

        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT template_code, status FROM notification_logs WHERE user_id = %s",
                (self.user_id,),
            )
            rows = cur.fetchall()
        self.assertEqual(len(rows), 1, "同一次 run 恰发一条,重复调用不许堆积")
        self.assertEqual(rows[0]["template_code"], workorder_notify.TEMPLATE_STUCK)
        self.assertEqual(rows[0]["status"], "sent")
        self.push.assert_called_once()


if __name__ == "__main__":
    unittest.main()
