# -*- coding: utf-8 -*-
"""管家长任务异步化(services/steward/worker.py + store 队列面 + routes 取消/自愈 · B3)。

锁七件事:①入队即返(POST 消息不跑工具,任务行 running + payload 齐全,应承不冒领);
②轮询面(public_task 暴露失败码/人话原因,进度步骤中途可更新);③worker 成功收尾 done +
主动回话;④失败落错误码与人话原因;⑤超时硬闸落 failed(默认 300s 可配);⑥失联自愈
(租约过期/从没被认领 → failed,不永远转圈);⑦租户隔离(SQL 全部按 tenant 收窄,
作用域快照随任务走)。零真 DB:core.db.get_cursor 与 store 函数是注入点。
"""

from __future__ import annotations

import time
import unittest
from unittest import mock

from services.agent.contracts import ToolResult
from services.steward import budget, copy, orchestrator, registry, store, tools, worker
from services.steward.registry import ToolContext


class _CurCM:
    def __init__(self, cur=None):
        self.cur = cur if cur is not None else object()

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _RecCur:
    """记录型假游标:执行的 SQL/参数留档供断言,fetch 返回预置值。"""

    def __init__(self, fetchone=None, rows=(), rowcount=1):
        self.executed = []
        self._fetchone = fetchone
        self._rows = list(rows)
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return list(self._rows)


def _task_row(**over):
    row = {
        "id": "task-1",
        "tenant_id": "t-1",
        "session_id": "s-1",
        "title": "查本期矩阵",
        "status": store.TASK_RUNNING,
        "steps": copy.build_steps(
            registry.MATRIX_OVERVIEW,
            "zh",
            tool_state=store.STEP_QUEUED,
            summarize=store.STEP_QUEUED,
        ),
        "artifacts": [],
        "payload": {
            "tool": registry.MATRIX_OVERVIEW,
            "args": {},
            "lang": "zh",
            "user_id": "u1",
            "allowed_client_ids": None,
        },
        "timeout_s": 5,
        "worker_id": "w-1",
        "created_at": None,
        "finished_at": None,
    }
    row.update(over)
    return row


def _ctx():
    return ToolContext(user={"id": "u1", "tenant_id": "t-1"}, tenant_id="t-1", user_id="u1")


_MATRIX_DATA = {
    "period": "2569-07",
    "client_count": 3,
    "missing_order": 1,
    "badges": {"missing_materials": 2, "pending_review": 1, "in_progress": 0},
    "attention": [],
}


class EnqueueImmediateReturnTests(unittest.TestCase):
    def test_handle_message_returns_task_without_finishing_it(self):
        """入队即返:响应带 task_id + running,任务收尾绝不发生在请求里(归 worker)。"""
        finish = mock.Mock()
        messages = []

        def add_message(_cur, **kw):
            messages.append(kw)
            return {"id": f"m{len(messages)}"}

        with (
            mock.patch.object(
                orchestrator.planner,
                "plan",
                return_value={
                    "degraded": False,
                    "reason": None,
                    "tool": registry.MATRIX_OVERVIEW,
                    "args": {},
                    "message": "",
                },
            ),
            mock.patch.object(tools, "run", side_effect=AssertionError("must not run inline")),
            mock.patch.object(store, "create_task", lambda _c, **kw: {"id": "task-1", **kw}),
            mock.patch.object(store, "finish_task", finish),
            mock.patch.object(store, "add_message", add_message),
            mock.patch.object(store, "set_title_if_empty", mock.Mock()),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch.object(store, "list_messages", lambda *a, **k: []),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        ):
            out = orchestrator.handle_message(_ctx(), session_id="s-1", text="本期谁缺料")
        finish.assert_not_called()
        self.assertEqual(out["task_id"], "task-1")
        self.assertEqual(out["task_status"], store.TASK_RUNNING)
        self.assertEqual(out["reply"], copy.task_ack("查本期矩阵", "zh"))
        self.assertEqual(messages[1]["task_id"], "task-1")  # 应承消息挂上任务


class WorkerExecutionTests(unittest.IsolatedAsyncioTestCase):
    def _patches(self, run, finish=None):
        return (
            mock.patch.object(worker, "_build_context", lambda *a: _ctx()),
            mock.patch.object(tools, "run", run),
            mock.patch.object(store, "update_steps", mock.Mock(return_value=True)),
            mock.patch.object(store, "finish_task", finish or mock.Mock(return_value=True)),
            mock.patch.object(store, "add_message", mock.Mock(return_value={"id": "m1"})),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        )

    async def test_success_finishes_done_and_reports_to_chat(self):
        finish = mock.Mock(return_value=True)
        run = mock.Mock(return_value=ToolResult(ok=True, data=_MATRIX_DATA))
        p = self._patches(run, finish)
        with p[0], p[1], p[2] as update_steps, p[3], p[4] as add_message, p[5], p[6]:
            await worker._execute(_task_row())
        marked = update_steps.call_args.kwargs
        self.assertEqual([s["state"] for s in marked["steps"]], ["done", "running", "queued"])
        done = finish.call_args.kwargs
        self.assertEqual(done["status"], store.TASK_DONE)
        self.assertEqual([s["state"] for s in done["steps"]], ["done", "done", "done"])
        self.assertTrue(any(a["kind"] == "deeplink" for a in done["artifacts"]))
        self.assertIsNone(done["error_code"])
        said = add_message.call_args.kwargs
        self.assertEqual(said["text"], copy.reply(registry.MATRIX_OVERVIEW, _MATRIX_DATA, "zh"))
        self.assertEqual(said["task_id"], "task-1")
        self.assertEqual(said["tool_trace"][0]["ok"], True)

    async def test_tool_failure_lands_error_code_and_human_reason(self):
        finish = mock.Mock(return_value=True)
        result = ToolResult(
            ok=False,
            error_code="steward.client_not_found",
            data={"keyword": "Sis", "candidates": []},
        )
        p = self._patches(mock.Mock(return_value=result), finish)
        with p[0], p[1], p[2], p[3], p[4] as add_message, p[5], p[6]:
            await worker._execute(_task_row())
        failed = finish.call_args.kwargs
        self.assertEqual(failed["status"], store.TASK_FAILED)
        self.assertEqual(failed["error_code"], "steward.client_not_found")
        self.assertIn("Sis", failed["error_message"])  # 人话原因,不是裸码
        self.assertEqual(failed["steps"][1]["state"], store.STEP_FAILED)
        self.assertEqual(add_message.call_args.kwargs["text"], failed["error_message"])

    async def test_timeout_lands_failed_with_reason(self):
        """超时硬闸:工具超过任务行里的 timeout_s 没回来 → failed + steward.timeout。"""
        finish = mock.Mock(return_value=True)
        p = self._patches(lambda *a: time.sleep(0.3), finish)
        with p[0], p[1], p[2], p[3], p[4] as add_message, p[5], p[6]:
            await worker._execute(_task_row(timeout_s=0.05))
        failed = finish.call_args.kwargs
        self.assertEqual(failed["status"], store.TASK_FAILED)
        self.assertEqual(failed["error_code"], worker.ERR_TIMEOUT)
        self.assertEqual(
            failed["error_message"], copy.fail_reason(worker.ERR_TIMEOUT, "zh", seconds=1)
        )
        add_message.assert_called_once()  # 失败也主动回话,不静默

    async def test_late_result_after_cancel_is_dropped(self):
        """取消赛跑:终态没落成(finish 守卫拒收)→ 不往会话冒一条"跑完了"。"""
        finish = mock.Mock(return_value=False)
        p = self._patches(mock.Mock(return_value=ToolResult(ok=True, data=_MATRIX_DATA)), finish)
        with p[0], p[1], p[2], p[3], p[4] as add_message, p[5], p[6]:
            await worker._execute(_task_row())
        add_message.assert_not_called()

    async def test_lost_identity_fails_the_task(self):
        finish = mock.Mock(return_value=True)
        with (
            mock.patch.object(worker, "_build_context", lambda *a: None),
            mock.patch.object(store, "finish_task", finish),
            mock.patch.object(store, "add_message", mock.Mock(return_value={"id": "m1"})),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        ):
            await worker._execute(_task_row())
        self.assertEqual(finish.call_args.kwargs["error_code"], worker.ERR_CONTEXT_LOST)


class WorkerModelBudgetTests(unittest.IsolatedAsyncioTestCase):
    """识别类工具是管家里唯一会自己烧模型的动作,而它落在 worker 的单工具路上 ——
    请求侧对附件轮次明确跳过了 reserve(「一次模型都不调」对请求侧成立,对这里不成立)。"""

    def _file_task(self):
        payload = {
            "tool": registry.FILE_CONVERT,
            "args": {},
            "lang": "zh",
            "user_id": "u1",
            "allowed_client_ids": None,
            "attachment_ids": ["a-1"],
        }
        return _task_row(payload=payload, title="转成 Excel")

    def _patches(self, run, finish):
        return (
            mock.patch.object(worker, "_build_context", lambda *a: _ctx()),
            mock.patch.object(tools, "run", run),
            mock.patch.object(store, "update_steps", mock.Mock(return_value=True)),
            mock.patch.object(store, "finish_task", finish),
            mock.patch.object(store, "add_message", mock.Mock(return_value={"id": "m1"})),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        )

    async def _execute(self, row, run, gate):
        finish = mock.Mock(return_value=True)
        p = self._patches(run, finish)
        with (
            p[0], p[1], p[2], p[3], p[4], p[5], p[6],
            mock.patch.object(worker.budget, "reserve", return_value=gate) as reserve,
            mock.patch.object(worker.budget, "settle") as settle,
        ):  # fmt: skip
            await worker._execute(row)
        return finish, reserve, settle

    async def test_a_model_calling_tool_reserves_and_settles_its_own_budget(self):
        run = mock.Mock(return_value=ToolResult(ok=True, data={"filename": "gl.pdf", "issues": []}))
        finish, reserve, settle = await self._execute(
            self._file_task(), run, {"allowed": True, "entry_id": "e-1"}
        )
        kwargs = reserve.call_args.kwargs
        self.assertEqual(kwargs["task_id"], "task-1")
        self.assertEqual(kwargs["session_id"], "s-1")
        # 逐页栅格化远贵于循环里一步分类,拿同一个 ฿0.25 占坑 = 封顶名存实亡
        self.assertEqual(kwargs["estimate"], worker.budget.file_call_reserve_thb())
        self.assertEqual(settle.call_args.kwargs["entry_id"], "e-1")
        self.assertEqual(finish.call_args.kwargs["status"], store.TASK_DONE)

    async def test_over_the_cap_the_tool_never_runs(self):
        run = mock.Mock(side_effect=AssertionError("capped task must not run the tool"))
        gate = {"allowed": False, "code": budget.ERR_TENANT, "cap_thb": "150.00"}
        finish, _reserve, settle = await self._execute(self._file_task(), run, gate)
        failed = finish.call_args.kwargs
        self.assertEqual(failed["status"], store.TASK_FAILED)
        self.assertEqual(failed["error_code"], budget.ERR_TENANT)
        self.assertIn("150.00", failed["error_message"])  # 人话说清卡在哪条线
        settle.assert_not_called()

    async def test_a_read_only_query_tool_takes_no_budget_at_all(self):
        """只读 DB 查询不产生模型成本;给它占坑会在台账里留一串永不结算的幽灵行。"""
        run = mock.Mock(return_value=ToolResult(ok=True, data=_MATRIX_DATA))
        _finish, reserve, settle = await self._execute(
            _task_row(), run, {"allowed": True, "entry_id": "e-1"}
        )
        reserve.assert_not_called()
        settle.assert_not_called()


class WorkerContextTests(unittest.TestCase):
    def test_context_rejects_cross_tenant_user(self):
        """租户对不上不跑:入队后用户换了租户,旧任务不得以任务租户身份执行。"""
        user = {"id": "u1", "tenant_id": "t-OTHER"}
        with mock.patch("services.auth.user_lookup.find_user_by_id", return_value=user):
            self.assertIsNone(worker._build_context({"user_id": "u1"}, "t-1"))

    def test_context_restores_scope_snapshot(self):
        user = {"id": "u1", "tenant_id": "t-1"}
        payload = {"user_id": "u1", "allowed_client_ids": [3, 7], "lang": "th"}
        with mock.patch("services.auth.user_lookup.find_user_by_id", return_value=user):
            ctx = worker._build_context(payload, "t-1")
        self.assertEqual(ctx.allowed_client_ids, frozenset({3, 7}))
        self.assertEqual(ctx.lang, "th")


class StaleHealTests(unittest.TestCase):
    def test_heal_marks_claimed_and_unclaimed_differently(self):
        """失联两类各给各的码:认领过 = worker_lost,从没被认领 = queue_stalled;
        原因按任务语言落人话,没跑完的步骤如实标失败。"""
        claimed = _task_row(worker_id="w-9", payload={"lang": "th"})
        unclaimed = _task_row(id="task-2", worker_id=None)
        finish = mock.Mock(return_value=True)
        with (
            mock.patch.object(store, "list_stale_tasks", return_value=[claimed, unclaimed]),
            mock.patch.object(store, "finish_task", finish),
        ):
            healed = worker.heal_stale(object(), tenant_id="t-1")
        self.assertEqual(healed, 2)
        first, second = (c.kwargs for c in finish.call_args_list)
        self.assertEqual(first["error_code"], worker.ERR_WORKER_LOST)
        self.assertEqual(first["error_message"], copy.fail_reason(worker.ERR_WORKER_LOST, "th"))
        self.assertEqual(second["error_code"], worker.ERR_QUEUE_STALLED)
        self.assertEqual(first["status"], store.TASK_FAILED)
        patched = first["steps"]
        self.assertEqual(patched[0]["state"], store.STEP_DONE)  # 跑完的不抹
        self.assertEqual(patched[1]["state"], store.STEP_FAILED)
        self.assertEqual(patched[1]["detail"], first["error_message"])

    def test_heal_passes_scope_to_store(self):
        listing = mock.Mock(return_value=[])
        with mock.patch.object(store, "list_stale_tasks", listing):
            worker.heal_stale(object(), tenant_id="t-1", task_id="task-1")
        self.assertEqual(listing.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(listing.call_args.kwargs["task_id"], "task-1")


class StoreQueueSqlTests(unittest.TestCase):
    """队列 SQL 的隔离与守卫面:租户收窄 / SKIP LOCKED / 终态守卫,漂了就是越权或假绿。"""

    def test_update_steps_is_tenant_scoped_and_running_only(self):
        cur = _RecCur(rowcount=0)
        self.assertFalse(store.update_steps(cur, tenant_id="t-1", task_id="task-1", steps=[]))
        sql, params = cur.executed[0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("t-1", params)
        self.assertIn(store.TASK_RUNNING, params)

    def test_finish_task_guards_terminal_states(self):
        cur = _RecCur(rowcount=1)
        ok = store.finish_task(
            cur, tenant_id="t-1", task_id="task-1", status=store.TASK_DONE, steps=[]
        )
        self.assertTrue(ok)
        sql, params = cur.executed[0]
        self.assertIn("status = ANY(%s)", sql)
        self.assertIn([store.TASK_RUNNING, store.TASK_WAITING_USER], params)
        self.assertIn("tenant_id = %s", sql)

    def test_cancel_task_only_touches_running(self):
        cur = _RecCur(fetchone=None)
        self.assertIsNone(store.cancel_task(cur, tenant_id="t-1", task_id="task-1", steps=[]))
        sql, params = cur.executed[0]
        self.assertIn(store.TASK_CANCELLED, params)
        self.assertIn(store.TASK_RUNNING, params)
        self.assertIn("tenant_id = %s", sql)

    def test_claim_next_task_skips_locked_and_claimed(self):
        cur = _RecCur(fetchone=None)
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(cur)):
            self.assertIsNone(store.claim_next_task("w-1"))
        sql, _params = cur.executed[0]
        self.assertIn("worker_id IS NULL", sql)
        self.assertIn("FOR UPDATE SKIP LOCKED", sql)

    def test_list_stale_tasks_scopes_and_locks(self):
        cur = _RecCur(rows=[])
        store.list_stale_tasks(cur, tenant_id="t-1", task_id="task-1")
        sql, params = cur.executed[0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("lease_until", sql)
        self.assertIn("FOR UPDATE SKIP LOCKED", sql)
        self.assertIn("t-1", params)

    def test_fail_steps_keeps_done_and_carries_reason_once(self):
        steps = [{"state": "done"}, {"state": "running"}, {"state": "queued"}]
        out = store.fail_steps(steps, "原因")
        self.assertEqual([s["state"] for s in out], ["done", "failed", "failed"])
        self.assertEqual(out[1]["detail"], "原因")
        self.assertNotIn("detail", out[2])

    def test_default_timeout_is_env_configurable(self):
        with mock.patch.dict("os.environ", {"STEWARD_TASK_TIMEOUT_S": "120"}):
            self.assertEqual(store.default_timeout_s(), 120)
        with mock.patch.dict("os.environ", {"STEWARD_TASK_TIMEOUT_S": "not-a-number"}):
            self.assertEqual(store.default_timeout_s(), 300)

    def test_public_task_exposes_failure_but_not_payload(self):
        row = _task_row(
            status=store.TASK_FAILED,
            error_code=worker.ERR_TIMEOUT,
            error_message="跑了超过 300 秒还没有结果",
        )
        out = store.public_task(row)
        self.assertEqual(out["error_code"], worker.ERR_TIMEOUT)
        self.assertIn("300", out["error_reason"])
        self.assertNotIn("payload", out)
        self.assertNotIn("worker_id", out)
        self.assertNotIn("error_code", store.public_task(_task_row()))


class CancelRouteTests(unittest.IsolatedAsyncioTestCase):
    def _base_patches(self):
        from routes import steward_common as sc
        from routes import steward_routes as sr

        return sr, (
            # 业务端点的门收口在 routes/steward_common(S1),鉴权桩打在那边。
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=({"id": "u1"}, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
            mock.patch.object(store, "ensure_once", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        )

    async def test_cancel_running_task_returns_cancelled(self):
        sr, patches = self._base_patches()
        running = _task_row()
        done = _task_row(status=store.TASK_CANCELLED)
        cancel = mock.Mock(return_value=done)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            mock.patch.object(store, "get_task", return_value=running),
            mock.patch.object(store, "cancel_task", cancel),
        ):
            out = await sr.cancel_task("task-1", mock.Mock())
        self.assertEqual(out["status"], store.TASK_CANCELLED)
        kwargs = cancel.call_args.kwargs
        self.assertEqual(kwargs["tenant_id"], "t-1")
        self.assertEqual(kwargs["steps"][1]["state"], store.STEP_FAILED)

    async def test_cancel_terminal_task_is_idempotent(self):
        sr, patches = self._base_patches()
        cancel = mock.Mock()
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            mock.patch.object(store, "get_task", return_value=_task_row(status=store.TASK_DONE)),
            mock.patch.object(store, "cancel_task", cancel),
        ):
            out = await sr.cancel_task("task-1", mock.Mock())
        cancel.assert_not_called()
        self.assertEqual(out["status"], store.TASK_DONE)

    async def test_get_task_heals_stale_before_answering(self):
        """轮询自愈:GET 任务先过失联收口 —— worker 死了,轮询的人也看得到诚实的 failed。"""
        sr, patches = self._base_patches()
        heal = mock.Mock(return_value=0)
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            mock.patch.object(sr.worker, "heal_stale", heal),
            mock.patch.object(store, "get_task", return_value=_task_row()),
        ):
            await sr.get_task("task-1", mock.Mock())
        self.assertEqual(heal.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(heal.call_args.kwargs["task_id"], "task-1")


if __name__ == "__main__":
    unittest.main()
