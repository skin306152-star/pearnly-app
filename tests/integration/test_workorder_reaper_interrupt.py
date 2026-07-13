# -*- coding: utf-8 -*-
"""部署中断工单自愈真复现(MC2-0 验收命门 · 本地真库)。

剧本 = 事故 2514dc65 的还原:真库起跑批(子进程走生产路径 runner.advance,OCR 慢速桩)
→ classify 中途硬杀子进程(TerminateProcess,模拟部署重启,无 finally)→ 断言事故现场
(status=running + 未过期租约 + 无收尾事件 = UI 说谎窗口)→ 拨快时钟令租约过期(杀是
真的,只是不为 TTL 干等 30 分钟)→ 模拟重启(reaper.reap_dead_runs,与 startup 钩子/
巡检 tick 同一实现)→ 断言:run_failed(interrupted)认账 → run_requested(auto)自动
续跑 → 跑到自然停点(缺销项 → needs/stuck,状态诚实)→ 已完成件 OCR 零重烧(按本进程
OCR 桩调用计数 + item_classified 事件计数双口径)。

跑法(CI 无真库自动 skip):
    PEARNLY_INTEGRATION_DB=1 DATABASE_URL=postgresql://... PGSSLMODE=disable \
    python -m unittest tests.integration.test_workorder_reaper_interrupt
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from tests.integration._helpers import require_db

_CHILD = Path(__file__).with_name("_reaper_crash_child.py")
_OWN_TAX = "0105561000013"
_N_ITEMS = 6


def _events(cur, store, tenant, wo_id):
    return store.list_events(cur, tenant_id=tenant, work_order_id=wo_id)


def _count(events, event_type):
    return sum(1 for e in events if e["event_type"] == event_type)


class ReaperInterruptIntegration(unittest.TestCase):
    """真杀进程 → 收尸 → 续跑闭环(每个用例独立租户/工单,互不串)。"""

    def setUp(self):
        require_db()
        from core import db
        from services.workorder import store
        from services.workorder.steps import classify
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.store = db, store
        build_workorder_schema()
        store.ensure_runtime()
        self._neutralize_stray_dead_runs()

        # 本进程(=「重启后的服务」)的 OCR 桩:计数即重烧监视器。resolver 一并替换,
        # 收尸续跑绝不触达真 OCR/真 workspace 查询。
        self.ocr_calls = []
        stub_fields = {
            "document_type": "tax_invoice",
            "buyer_tax": _OWN_TAX,
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
        }

        def counting_ocr(path):
            self.ocr_calls.append(path)
            seq = "".join(ch for ch in Path(path).stem if ch.isdigit()) or "0"
            return dict(stub_fields, seller_tax=f"1{int(seq):012d}", invoice_number=f"INV-{seq}")

        for name, repl in (
            ("_ocr_image", counting_ocr),
            ("_resolve_own_tax_id", lambda ctx: _OWN_TAX),
            ("_resolve_own_name", lambda ctx: None),
            ("_resolve_own_names", lambda ctx: []),
            ("_m1_enabled", lambda ctx: False),
        ):
            self.addCleanup(setattr, classify, name, getattr(classify, name))
            setattr(classify, name, repl)

        self.tenant = str(uuid.uuid4())
        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=1, period="2569-06"
            )
        self.wo_id = str(wo["id"])

    def _neutralize_stray_dead_runs(self):
        """共享本地库可能残留别的测试留下的死单——收尸人是全局扫描,先把它们摘出判据,
        保证本用例的 OCR 计数/事件断言不被无关工单污染。"""
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE work_orders SET run_lease_owner = NULL, run_lease_expires_at = NULL "
                "WHERE status = 'running' AND run_lease_expires_at < now()"
            )

    def _register_materials(self, n=_N_ITEMS):
        """建 n 份假票图(唯一字节)并按补料端点同款路径登记成 items。"""
        from services.workorder import engine
        from services.workorder.steps import intake

        tmp = tempfile.mkdtemp(prefix="wo-reaper-")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        with self.db.get_cursor(commit=True) as cur:
            ctx = engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            for i in range(n):
                p = Path(tmp) / f"item{i}.jpg"
                p.write_bytes(f"fake-jpeg-{uuid.uuid4()}".encode())
                intake.register_file(ctx, p, "upload")

    def _expire_lease(self):
        """拨快时钟:杀是真的,只是不为 30 分钟 TTL 干等——判据本身(过期)一字不动。"""
        with self.db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE work_orders SET run_lease_expires_at = now() - interval '1 second' "
                "WHERE id = %s",
                (self.wo_id,),
            )

    def _poll(self, predicate, timeout, interval=0.2, desc=""):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.db.get_cursor() as cur:
                got = predicate(cur)
            if got:
                return got
            time.sleep(interval)
        self.fail(f"等待超时({timeout}s): {desc}")

    def _spawn_child(self):
        env = dict(
            os.environ,
            WO_TENANT=self.tenant,
            WO_ID=self.wo_id,
            WO_OWN_TAX=_OWN_TAX,
            WO_OCR_DELAY="0.8",
            PEARNLY_WORKORDER_OCR_CONCURRENCY="1",
        )
        return subprocess.Popen(
            [sys.executable, str(_CHILD)],
            env=env,
            cwd=str(_CHILD.parents[2]),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_killed_run_is_reaped_acknowledged_and_resumed_without_ocr_reburn(self):
        self._register_materials()
        proc = self._spawn_child()
        try:
            # 等子进程真跑起来且至少 2 件已提交(逐件检查点),再硬杀——正中 classify 步中段。
            def _classified(cur):
                if proc.poll() is not None:
                    self.fail(f"子进程提前退出:\n{proc.stdout.read()[-2000:]}")
                evts = _events(cur, self.store, self.tenant, self.wo_id)
                return len(evts) if _count(evts, "item_classified") >= 2 else None

            self._poll(_classified, timeout=120, desc="子进程 classify 逐件提交")
        finally:
            proc.kill()
            proc.wait(timeout=30)
            proc.stdout.close()

        # 事故现场 = MC2-0 立案的谎言窗口:status=running、租约未过期、无任何收尾事件。
        with self.db.get_cursor() as cur:
            wo = self.store.get_work_order(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            holder = self.store.run_lease_holder(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
            evts = _events(cur, self.store, self.tenant, self.wo_id)
        self.assertEqual(wo["status"], "running")
        self.assertIsNotNone(holder, "被杀进程的租约应仍未过期(收尸判据的另一半)")
        self.assertEqual(_count(evts, "run_finished"), 0)
        self.assertEqual(_count(evts, "run_failed"), 0)
        classified_before = _count(evts, "item_classified")
        boundary_id = max(e["id"] for e in evts)
        self.assertGreaterEqual(classified_before, 2)
        self.assertLess(classified_before, _N_ITEMS, "杀早了/杀晚了都测不到续跑,调 WO_OCR_DELAY")

        # 模拟部署重启后的服务:租约过期 → 收尸(startup 钩子与巡检 tick 同一实现)。
        self._expire_lease()
        from services.workorder import reaper

        stats = reaper.reap_dead_runs()
        self.assertEqual(stats["resumed"], 1)

        self._poll(
            lambda cur: _count(_events(cur, self.store, self.tenant, self.wo_id), "run_finished")
            or None,
            timeout=120,
            desc="收尸后自动续跑收尾",
        )

        with self.db.get_cursor() as cur:
            wo = self.store.get_work_order(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            holder = self.store.run_lease_holder(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
            evts = _events(cur, self.store, self.tenant, self.wo_id)

        # 认账 → 自动续跑 → 收尾,事件序全部落在杀点之后且次序正确。
        tail = [e for e in evts if e["id"] > boundary_id]
        failed = next(e for e in tail if e["event_type"] == "run_failed")
        self.assertEqual(failed["actor"], reaper.ACTOR_REAPER)
        self.assertEqual(failed["payload"]["reason"], reaper.REASON_INTERRUPTED)
        requested = next(e for e in tail if e["event_type"] == "run_requested")
        self.assertEqual(requested["actor"], reaper.ACTOR_REAPER)
        self.assertEqual(requested["payload"], {"auto_resume": 1})
        started = next(e for e in tail if e["event_type"] == "run_started")
        finished = next(e for e in tail if e["event_type"] == "run_finished")
        self.assertLess(failed["id"], requested["id"])
        self.assertLess(requested["id"], started["id"])
        self.assertLess(started["id"], finished["id"])

        # 自然停点:全部票已归堆,缺销项汇总 → needs/stuck。UI 不再说谎(不是 running)。
        self.assertEqual(wo["status"], "stuck")
        needs = [e for e in tail if e["event_type"] == "step_needs"]
        self.assertTrue(needs and "sales_summary" in needs[-1]["payload"]["missing"])
        self.assertIsNone(holder, "续跑收尾必须释放租约")

        # OCR 零重烧:续跑只烧未完成件;每件恰一条 item_classified,无双计。
        self.assertEqual(len(self.ocr_calls), _N_ITEMS - classified_before)
        classified = [e for e in evts if e["event_type"] == "item_classified"]
        self.assertEqual(len(classified), _N_ITEMS)
        self.assertEqual(len({e["payload"]["item_id"] for e in classified}), _N_ITEMS)

    def test_breaker_halts_after_auto_resume_budget_spent(self):
        # 毒丸工单(每次重跑都被杀)烧满 3 次自动预算 → 只认账不再爬:置 stuck + 释放租约 +
        # 零 OCR。真库版熔断验证,补单测的 SQL 盲区。
        from services.workorder import reaper, runner

        with self.db.get_cursor(commit=True) as cur:
            for i in range(reaper.AUTO_RESUME_LIMIT):
                self.store.append_event(
                    cur,
                    tenant_id=self.tenant,
                    work_order_id=self.wo_id,
                    step=runner.RUN_STEP,
                    event_type=runner.EVT_RUN_REQUESTED,
                    payload={"auto_resume": i + 1},
                    actor=reaper.ACTOR_REAPER,
                )
            self.store.set_status(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                status="running",
                current_step="classify",
            )
            cur.execute(
                "UPDATE work_orders SET run_lease_owner = 'run:dead', "
                "run_lease_expires_at = now() - interval '1 minute' WHERE id = %s",
                (self.wo_id,),
            )

        stats = reaper.reap_dead_runs()
        self.assertEqual(stats["halted"], 1)

        with self.db.get_cursor() as cur:
            wo = self.store.get_work_order(cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            evts = _events(cur, self.store, self.tenant, self.wo_id)
            holder = self.store.run_lease_holder(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
        self.assertEqual(wo["status"], "stuck")
        self.assertIsNone(holder)
        self.assertEqual(len(self.ocr_calls), 0)
        failed = [e for e in evts if e["event_type"] == "run_failed"]
        self.assertTrue(failed and failed[-1]["payload"]["auto_resume_exhausted"])
        stuck = [e for e in evts if e["event_type"] == "step_stuck"]
        self.assertIn(reaper.REASON_EXHAUSTED, stuck[-1]["payload"]["reasons"][0])
        # 超限后不再自动入跑:run_requested 仍是预置那 3 条。
        self.assertEqual(_count(evts, "run_requested"), reaper.AUTO_RESUME_LIMIT)
        # 收尸后判据不再命中,下一轮巡检不重复收这张单。
        self.assertEqual(reaper.reap_dead_runs()["reaped"], 0)

    def test_claim_is_single_winner_on_real_rows(self):
        # 幂等抢占真 SQL 验证:同一死单,先到者赢,后到者条件不再成立抢不到。
        from services.workorder import reaper, runner

        with self.db.get_cursor(commit=True) as cur:
            self.store.set_status(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                status="running",
                current_step="classify",
            )
            cur.execute(
                "UPDATE work_orders SET run_lease_owner = 'run:dead', "
                "run_lease_expires_at = now() - interval '1 minute' WHERE id = %s",
                (self.wo_id,),
            )
        kw = dict(
            tenant_id=self.tenant,
            work_order_id=self.wo_id,
            ttl_seconds=runner.run_lease_ttl_seconds(),
            status="running",
        )
        with self.db.get_cursor(commit=True) as cur:
            self.assertTrue(self.store.claim_dead_run(cur, owner="reaper:a", **kw))
        with self.db.get_cursor(commit=True) as cur:
            self.assertFalse(self.store.claim_dead_run(cur, owner="reaper:b", **kw))


if __name__ == "__main__":
    unittest.main()
