# -*- coding: utf-8 -*-
"""管家写授权闸 + 成本硬封顶(services/steward/authz.py + budget.py · B3 第二段)。

锁四个面:
  ① 执行层物理闸:写工具没批文/批文对不上当前参数 → tools.run 拒,handler 一步不进
     (授权不是前端不显示按钮);
  ② 令牌生命周期:一次性(第二次 used 拒)/过期拒/参数指纹变了拒/跨租户当不存在;
     批准复跑任务、拒绝收 cancelled,决断都留审计(谁在什么时候批了什么);
  ③ 成本封顶:单任务/单会话两级上限,预留-结算两段式 —— 两路并发各自没超但合计超,
     第二路必须被在飞预留拦住;封顶基础设施故障 fail-open 不停全功能;
  ④ 路由权限:批准要 tax.filing.approve,无权 403 且不烧卡(权限先于 token 消费)。
零真 DB:nonce 表 / steward_tasks / 成本台账都是按真 SQL 分支行为仿真的内存假游标。
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from fastapi import HTTPException

from services.agent.contracts import ToolResult
from services.steward import authz, budget, copy, orchestrator, registry, store, tools, worker
from services.steward.registry import StewardTool, ToolContext

_WRITE_TOOL = "erp_push_draft"
_ARGS = {"invoice_no": "INV-9", "amount": "107.00"}


class _World:
    """内存版 nonce 表 + 单条任务行(FakeCur 按真 SQL 的分支语义读写它)。"""

    def __init__(self, task=None):
        self.nonces = {}
        self.task = task


def _task_row(**over):
    row = {
        "id": "task-1",
        "tenant_id": "t-1",
        "session_id": "s-1",
        "title": "推一张草稿进 ERP",
        "status": store.TASK_RUNNING,
        "steps": [{"state": store.STEP_DONE}, {"state": store.STEP_QUEUED}],
        "artifacts": [],
        "payload": {"tool": _WRITE_TOOL, "args": dict(_ARGS), "lang": "zh", "user_id": "u1"},
        "timeout_s": 300,
        "worker_id": None,
        "created_at": None,
        "finished_at": None,
        "error_code": None,
        "error_message": None,
    }
    row.update(over)
    return row


class FakeCur:
    """authz/decide 流程真会跑到的 SQL 各给一个行为分支;认不出的语句直接炸(别静默假绿)。"""

    def __init__(self, world):
        self.world = world
        self._ret = None
        self.rowcount = 0

    def execute(self, sql, params=()):
        w = self.world
        if "INSERT INTO line_action_nonces" in sql:
            token, tid, _ws, uid, ref, ttl = params
            w.nonces[token] = {
                "tenant_id": str(tid),
                "user_id": uid,
                "action_ref": ref,
                "consumed": False,
                "expired": int(ttl) <= 0,
            }
            self._ret = None
        elif "UPDATE line_action_nonces SET consumed_at" in sql:
            token, tid = params
            r = w.nonces.get(token)
            if r and r["tenant_id"] == str(tid) and not r["consumed"] and not r["expired"]:
                r["consumed"] = True
                self._ret = {"action_ref": r["action_ref"], "workspace_client_id": 0,
                             "user_id": r["user_id"]}  # fmt: skip
            else:
                self._ret = None
        elif "SELECT consumed_at" in sql:
            token, tid = params
            r = w.nonces.get(token)
            self._ret = (
                {"consumed_at": 1 if r["consumed"] else None, "action_ref": r["action_ref"],
                 "workspace_client_id": 0, "expired": r["expired"]}  # fmt: skip
                if r and r["tenant_id"] == str(tid)
                else None
            )
        elif "jsonb_set" in sql:
            self._jsonb_update(sql, params)
        elif "finished_at = now()" in sql:
            self._finish(params)
        elif sql.strip().startswith("SELECT") and "FROM steward_tasks" in sql:
            tid, task_id = params
            t = w.task
            hit = t and str(t["tenant_id"]) == str(tid) and str(t["id"]) == str(task_id)
            self._ret = dict(t) if hit else None
        else:
            raise AssertionError(f"unexpected sql: {sql[:80]}")

    def _jsonb_update(self, sql, params):
        w = self.world
        if "make_interval" in sql:  # 批准复跑:waiting_user → running + 认领窗租约
            card, to_status, _grace, tid, task_id, from_status = params
            allowed = (from_status,)
        elif "status = ANY(%s)" in sql:  # 铸卡停靠:running/waiting_user → waiting_user
            card, to_status, tid, task_id, allowed = params
        else:  # 只写卡不动任务态
            card, tid, task_id = params
            to_status, allowed = None, None
        t = w.task
        match = t and str(t["tenant_id"]) == str(tid) and str(t["id"]) == str(task_id)
        if match and (allowed is None or t["status"] in allowed):
            t["payload"] = {**t["payload"], "authorization": json.loads(card)}
            if to_status is not None:
                t["status"] = to_status
            self.rowcount = 1
        else:
            self.rowcount = 0

    def _finish(self, params):
        status, steps, artifacts, error_code, error_message, tid, task_id, allowed = params
        t = self.world.task
        match = t and str(t["tenant_id"]) == str(tid) and str(t["id"]) == str(task_id)
        if match and t["status"] in allowed:
            t.update(
                status=status,
                steps=json.loads(steps),
                artifacts=json.loads(artifacts),
                error_code=error_code,
                error_message=error_message,
            )
            self.rowcount = 1
        else:
            self.rowcount = 0

    def fetchone(self):
        return self._ret


def _grant(args=None, **over):
    grant = {
        "token": "tok",
        "tool": _WRITE_TOOL,
        "risk": registry.RISK_WRITE,
        "args": args or dict(_ARGS),
        "args_fp": authz.args_fingerprint(_WRITE_TOOL, args or dict(_ARGS)),
        "status": store.AUTH_APPROVED,
    }
    grant.update(over)
    return grant


class _WriteToolMixin(unittest.TestCase):
    """把一个假写工具临时挂进闭集(注册表 + 执行器),用完必拆 —— 别污染别的测试。"""

    def setUp(self):
        self.handler_calls = []
        spec = StewardTool(
            name=_WRITE_TOOL,
            desc="推一张草稿进 ERP",
            slots=(),
            handler=_WRITE_TOOL,
            risk=registry.RISK_WRITE,
        )
        registry.TOOLS_BY_NAME[_WRITE_TOOL] = spec
        tools._HANDLERS[_WRITE_TOOL] = lambda _ctx, args: (
            self.handler_calls.append(args) or ToolResult(ok=True, data={"pushed": True})
        )
        self.addCleanup(registry.TOOLS_BY_NAME.pop, _WRITE_TOOL, None)
        self.addCleanup(tools._HANDLERS.pop, _WRITE_TOOL, None)


class ExecutionGateTests(_WriteToolMixin):
    def _ctx(self):
        return ToolContext(user={"id": "u1"}, tenant_id="t-1", user_id="u1")

    def test_write_tool_without_grant_is_physically_refused(self):
        res = tools.run(_WRITE_TOOL, self._ctx(), dict(_ARGS))
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, authz.ERR_AUTHZ_REQUIRED)
        self.assertEqual(self.handler_calls, [])  # handler 一步没进

    def test_unapproved_or_foreign_grant_is_refused(self):
        for bad in (
            {"status": store.AUTH_PENDING},
            {"status": store.AUTH_REJECTED},
            "not-a-dict",
        ):
            grant = _grant(**bad) if isinstance(bad, dict) else bad
            res = tools.run(_WRITE_TOOL, self._ctx(), dict(_ARGS), grant)
            self.assertEqual(res.error_code, authz.ERR_AUTHZ_REQUIRED)
        self.assertEqual(self.handler_calls, [])

    def test_grant_with_changed_args_is_refused(self):
        """批的是 107 推的是 999 → 指纹对不上,物理拒(批的必须就是执行的)。"""
        res = tools.run(_WRITE_TOOL, self._ctx(), {**_ARGS, "amount": "999"}, _grant())
        self.assertEqual(res.error_code, authz.ERR_AUTHZ_MISMATCH)
        self.assertEqual(self.handler_calls, [])

    def test_approved_grant_lets_the_tool_run(self):
        res = tools.run(_WRITE_TOOL, self._ctx(), dict(_ARGS), _grant())
        self.assertTrue(res.ok)
        self.assertEqual(self.handler_calls, [dict(_ARGS)])

    def test_readonly_tools_never_need_a_grant(self):
        spec = registry.get(registry.CLIENT_LOOKUP)
        self.assertIsNone(authz.execution_error(spec, None, tool=spec.name, args={}))


class RegistryRiskTests(unittest.TestCase):
    def test_readonly_derives_from_risk(self):
        write = StewardTool(name="w", desc="d", slots=(), handler="w", risk=registry.RISK_WRITE)
        read = StewardTool(name="r", desc="d", slots=(), handler="r")
        self.assertFalse(write.readonly)
        self.assertTrue(read.readonly)
        self.assertTrue(registry.requires_authorization(write))
        self.assertFalse(registry.requires_authorization(read))

    def test_unknown_risk_level_is_rejected_at_definition(self):
        with self.assertRaises(ValueError):
            StewardTool(name="x", desc="d", slots=(), handler="x", risk="yolo")


class TokenLifecycleTests(_WriteToolMixin):
    """铸卡 → 决断的全流程(内存假游标按真 SQL 分支行为仿真)。"""

    def setUp(self):
        super().setUp()
        self.world = _World(_task_row())
        self.cur = FakeCur(self.world)
        self.audit = mock.patch("services.audit.store.insert_operation_log").start()
        self.addCleanup(mock.patch.stopall)

    def _open(self):
        return authz.open_request(
            self.cur,
            tenant_id="t-1",
            task_id="task-1",
            tool=_WRITE_TOOL,
            args=dict(_ARGS),
            requested_by="u1",
        )

    def test_open_request_parks_task_with_pending_card(self):
        auth = self._open()
        self.assertEqual(self.world.task["status"], store.TASK_WAITING_USER)
        card = self.world.task["payload"]["authorization"]
        self.assertEqual(card["status"], store.AUTH_PENDING)
        self.assertEqual(card["args_fp"], authz.args_fingerprint(_WRITE_TOOL, _ARGS))
        self.assertIn(auth["token"], self.world.nonces)

    def test_approve_consumes_token_resumes_task_and_audits(self):
        auth = self._open()
        out = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=True
        )
        self.assertTrue(out["ok"])
        self.assertEqual(self.world.task["status"], store.TASK_RUNNING)
        card = self.world.task["payload"]["authorization"]
        self.assertEqual(card["status"], store.AUTH_APPROVED)
        self.assertEqual(card["decided_by"], "boss")
        kwargs = self.audit.call_args.kwargs
        self.assertEqual(kwargs["action"], authz.AUDIT_APPROVED)
        self.assertEqual(kwargs["actor_user_id"], "boss")
        self.assertEqual(kwargs["target_id"], "task-1")
        self.assertEqual(kwargs["details"]["tool"], _WRITE_TOOL)

    def test_token_is_single_use(self):
        auth = self._open()
        first = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=True
        )
        second = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=True
        )
        self.assertTrue(first["ok"])
        self.assertEqual(second, {"ok": False, "http": 409, "code": authz.ERR_AUTHZ_USED})

    def test_expired_token_is_refused(self):
        auth = self._open()
        self.world.nonces[auth["token"]]["expired"] = True
        out = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=True
        )
        self.assertEqual(out, {"ok": False, "http": 409, "code": authz.ERR_AUTHZ_EXPIRED})

    def test_cross_tenant_token_is_not_found(self):
        """别家租户拿到 token 也批不动:consume 按 tenant 收窄,统一按不存在,不泄漏存在性。"""
        auth = self._open()
        out = authz.decide(
            self.cur, tenant_id="t-2", token=auth["token"], actor={"id": "spy"}, approve=True
        )
        self.assertEqual(out, {"ok": False, "http": 404, "code": authz.ERR_NOT_FOUND})
        self.assertEqual(self.world.task["status"], store.TASK_WAITING_USER)  # 任务纹丝不动

    def test_changed_args_invalidate_the_old_token(self):
        """铸卡后参数被改 → 指纹对不上,决断拒 + 卡就地标失效(不留活按钮)。"""
        auth = self._open()
        self.world.task["payload"]["authorization"]["args"] = {**_ARGS, "amount": "999"}
        out = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=True
        )
        self.assertEqual(out["code"], authz.ERR_AUTHZ_MISMATCH)
        card = self.world.task["payload"]["authorization"]
        self.assertEqual(card["status"], store.AUTH_EXPIRED)
        self.assertNotEqual(self.world.task["status"], store.TASK_RUNNING)

    def test_reject_cancels_task_without_running_anything(self):
        auth = self._open()
        out = authz.decide(
            self.cur, tenant_id="t-1", token=auth["token"], actor={"id": "boss"}, approve=False
        )
        self.assertTrue(out["ok"])
        self.assertEqual(self.world.task["status"], store.TASK_CANCELLED)
        self.assertEqual(self.world.task["error_code"], authz.ERR_AUTHZ_REJECTED)
        self.assertEqual(
            self.world.task["error_message"], copy.fail_reason(authz.ERR_AUTHZ_REJECTED, "zh")
        )
        self.assertEqual(self.handler_calls, [])
        self.assertEqual(self.audit.call_args.kwargs["action"], authz.AUDIT_REJECTED)

    def test_open_request_refuses_readonly_tool(self):
        with self.assertRaises(ValueError):
            authz.open_request(
                self.cur,
                tenant_id="t-1",
                task_id="task-1",
                tool=registry.CLIENT_LOOKUP,
                args={},
                requested_by="u1",
            )


class PublicCardTests(unittest.TestCase):
    def test_public_task_exposes_card_without_fingerprint(self):
        auth = _grant(status=store.AUTH_PENDING, title="推一张草稿进 ERP",
                      expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat())  # fmt: skip
        row = _task_row(payload={"authorization": auth})
        card = store.public_task(row)["authorization"]
        self.assertEqual(card["status"], store.AUTH_PENDING)
        self.assertEqual(card["tool"], _WRITE_TOOL)
        self.assertNotIn("args_fp", card)

    def test_stale_pending_card_reads_as_expired(self):
        auth = _grant(status=store.AUTH_PENDING,
                      expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())  # fmt: skip
        card = store.public_task(_task_row(payload={"authorization": auth}))["authorization"]
        self.assertEqual(card["status"], store.AUTH_EXPIRED)

    def test_task_without_card_has_no_authorization_key(self):
        self.assertNotIn("authorization", store.public_task(_task_row()))


class MintMinutesTests(unittest.TestCase):
    def test_mint_supports_minute_ttl(self):
        from services.line_binding import line_action_nonce

        executed = []

        class Cur:
            def execute(self, sql, params):
                executed.append((sql, params))

        token = line_action_nonce.mint(
            Cur(), tenant_id="t-1", workspace_client_id=0, action_ref="x", ttl_minutes=5
        )
        self.assertTrue(token)
        sql, params = executed[0]
        self.assertIn("make_interval(mins => %s)", sql)
        self.assertEqual(params[-1], 5)


class _LedgerCur:
    """成本台账假游标:锁行 / 汇总(含未结算预留)/ 占坑 / 结算,四条 SQL 各一分支。"""

    def __init__(self, entries):
        self.entries = entries
        self._ret = None

    def execute(self, sql, params=()):
        if "FOR UPDATE" in sql:
            self._ret = {"id": params[1]}
        elif "SUM(cost_thb)" in sql:
            task_id, tid, sid = params
            rows = [e for e in self.entries if e["tenant_id"] == tid and e["session_id"] == sid]
            self._ret = {
                "session_spent": sum(e["cost_thb"] for e in rows),
                "task_spent": sum(e["cost_thb"] for e in rows if e["task_id"] == task_id),
            }
        elif "INSERT INTO steward_cost_entries" in sql:
            tid, sid, task_id, cost = params
            entry = {"id": f"e{len(self.entries) + 1}", "tenant_id": tid, "session_id": sid,
                     "task_id": task_id, "cost_thb": Decimal(cost), "settled": False}  # fmt: skip
            self.entries.append(entry)
            self._ret = {"id": entry["id"]}
        elif "UPDATE steward_cost_entries" in sql:
            actual, tid, eid = params
            for e in self.entries:
                if e["id"] == eid and e["tenant_id"] == tid:
                    e["settled"] = True
                    if actual is not None:
                        e["cost_thb"] = Decimal(actual)
        else:
            raise AssertionError(f"unexpected sql: {sql[:80]}")

    def fetchone(self):
        return self._ret


class _CurCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.entries = []
        patches = (
            mock.patch.object(budget, "_ensured", True),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(_LedgerCur(self.entries))),
        )
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _env(self, **caps):
        p = mock.patch.dict("os.environ", caps)
        p.start()
        self.addCleanup(p.stop)

    def test_task_over_cap_is_blocked_with_human_ready_numbers(self):
        self._env(STEWARD_TASK_COST_CAP_THB="1", STEWARD_SESSION_COST_CAP_THB="50")
        self.entries.append(
            {"id": "e0", "tenant_id": "t-1", "session_id": "s-1", "task_id": "task-1",
             "cost_thb": Decimal("1.00"), "settled": True}  # fmt: skip
        )
        out = budget.reserve(tenant_id="t-1", session_id="s-1", task_id="task-1")
        self.assertEqual(out["allowed"], False)
        self.assertEqual(out["code"], budget.ERR_TASK)
        self.assertEqual(out["cap_thb"], "1.00")
        self.assertEqual(out["spent_thb"], "1.00")

    def test_concurrent_reservations_share_the_session_cap(self):
        """两条任务各自没超,但在飞预留计入合计 → 第二路被拦(check-then-spend 赛道封死)。"""
        self._env(
            STEWARD_SESSION_COST_CAP_THB="0.15",
            STEWARD_TASK_COST_CAP_THB="0",  # 任务级关闭,只验会话合计
            STEWARD_CALL_COST_RESERVE_THB="0.1",
        )
        first = budget.reserve(tenant_id="t-1", session_id="s-1", task_id="task-a")
        second = budget.reserve(tenant_id="t-1", session_id="s-1", task_id="task-b")
        self.assertTrue(first["allowed"])
        self.assertEqual(second["allowed"], False)
        self.assertEqual(second["code"], budget.ERR_SESSION)

    def test_settle_replaces_reservation_with_actual_cost(self):
        self._env(STEWARD_CALL_COST_RESERVE_THB="0.1")
        out = budget.reserve(tenant_id="t-1", session_id="s-1")
        budget.settle(tenant_id="t-1", entry_id=out["entry_id"], cost_thb=0.021)
        entry = self.entries[0]
        self.assertTrue(entry["settled"])
        self.assertEqual(entry["cost_thb"], Decimal("0.021"))

    def test_settle_without_actual_keeps_the_reservation(self):
        """调用炸了拿不到成本 → 预留额当最终值(保守多计,封顶不放水)。"""
        out = budget.reserve(tenant_id="t-1", session_id="s-1")
        budget.settle(tenant_id="t-1", entry_id=out["entry_id"], cost_thb=None)
        self.assertTrue(self.entries[0]["settled"])
        self.assertEqual(self.entries[0]["cost_thb"], budget.call_reserve_thb())

    def test_infra_error_fails_open_not_closed(self):
        def boom(*a, **k):
            raise RuntimeError("db down")

        with mock.patch("core.db.get_cursor", boom):
            out = budget.reserve(tenant_id="t-1", session_id="s-1")
        self.assertEqual(out, {"allowed": True, "entry_id": None})

    def test_caps_are_decimal_and_disabled_by_nonpositive(self):
        self._env(STEWARD_TASK_COST_CAP_THB="0", STEWARD_SESSION_COST_CAP_THB="2.5")
        self.assertIsNone(budget.task_cap_thb())
        self.assertEqual(budget.session_cap_thb(), Decimal("2.5"))

    def test_decide_prefers_the_narrower_task_cap(self):
        code = budget.decide(
            session_spent=Decimal("9"),
            task_spent=Decimal("1"),
            estimate=Decimal("0.1"),
            session_cap=Decimal("5"),
            task_cap=Decimal("1"),
        )
        self.assertEqual(code, budget.ERR_TASK)


class OrchestratorBudgetTests(unittest.TestCase):
    def _patches(self, gate, plan=None):
        messages = []

        def add_message(_cur, **kw):
            messages.append(kw)
            return {"id": f"m{len(messages)}"}

        return messages, (
            mock.patch.object(budget, "reserve", mock.Mock(return_value=gate)),
            mock.patch.object(budget, "settle", mock.Mock()),
            mock.patch.object(
                orchestrator.planner,
                "plan",
                (
                    mock.Mock(return_value=plan)
                    if plan
                    else mock.Mock(side_effect=AssertionError("超限的轮次一次模型都不许调"))
                ),
            ),
            mock.patch.object(store, "add_message", add_message),
            mock.patch.object(store, "set_title_if_empty", mock.Mock()),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch.object(store, "list_messages", lambda *a, **k: []),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(None)),
        )

    def _ctx(self):
        return ToolContext(user={"id": "u1"}, tenant_id="t-1", user_id="u1", lang="zh")

    def test_blocked_turn_answers_human_and_machine_without_model_call(self):
        gate = {"allowed": False, "code": budget.ERR_SESSION, "cap_thb": "5.00",
                "spent_thb": "5.02"}  # fmt: skip
        messages, patches = self._patches(gate)
        with patches[0], patches[1] as settle, patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7]:  # fmt: skip
            out = orchestrator.handle_message(self._ctx(), session_id="s-1", text="本期谁缺料")
        self.assertEqual(out["budget"], {"code": budget.ERR_SESSION, "cap_thb": "5.00",
                                         "spent_thb": "5.02"})  # fmt: skip
        self.assertIn("5.00", out["reply"])  # 人话提示带上限数
        self.assertNotIn("task_id", out)
        settle.assert_not_called()  # 没占坑就没结算
        self.assertEqual(messages[1]["tool_trace"][0]["error"], budget.ERR_SESSION)

    def test_allowed_turn_settles_with_actual_model_cost(self):
        plan = {"degraded": False, "reason": None, "tool": registry.OUT_OF_SCOPE,
                "args": {}, "message": "", "cost_thb": 0.03}  # fmt: skip
        _messages, patches = self._patches({"allowed": True, "entry_id": "e1"}, plan=plan)
        with patches[0] as reserve, patches[1] as settle, patches[2], patches[3], patches[4], \
                patches[5], patches[6], patches[7]:  # fmt: skip
            orchestrator.handle_message(self._ctx(), session_id="s-1", text="今天天气怎么样")
        self.assertEqual(reserve.call_args.kwargs["session_id"], "s-1")
        self.assertEqual(settle.call_args.kwargs["entry_id"], "e1")
        self.assertEqual(settle.call_args.kwargs["cost_thb"], 0.03)


class WorkerGrantTests(unittest.IsolatedAsyncioTestCase):
    async def test_worker_hands_the_grant_to_the_execution_gate(self):
        grant = _grant()
        row = _task_row(payload={**_task_row()["payload"], "authorization": grant})
        run = mock.Mock(return_value=ToolResult(ok=True, data={}))
        ctx = ToolContext(user={"id": "u1"}, tenant_id="t-1", user_id="u1")
        with (
            mock.patch.object(worker, "_build_context", lambda *a: ctx),
            mock.patch.object(tools, "run", run),
            mock.patch.object(store, "update_steps", mock.Mock(return_value=True)),
            mock.patch.object(store, "finish_task", mock.Mock(return_value=True)),
            mock.patch.object(store, "add_message", mock.Mock(return_value={"id": "m1"})),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(None)),
        ):
            await worker._execute(row)
        self.assertEqual(run.call_args.args[3], grant)


class RoutePermissionTests(unittest.IsolatedAsyncioTestCase):
    def _sr(self):
        from routes import steward_routes as sr

        return sr

    async def test_approve_without_permission_is_403_and_burns_no_token(self):
        sr = self._sr()

        def guard(_request, perm, *, not_found):
            if perm == sr._C_APPROVE:
                raise HTTPException(403, detail="authz.forbidden")
            return {"id": "u1"}, "t-1"

        decide = mock.Mock()
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", side_effect=guard),
            mock.patch.object(sr.authz, "decide", decide),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await sr.approve_authorization(
                    sr.AuthzDecisionIn(token="tok-12345678"), mock.Mock()
                )
        self.assertEqual(ctx.exception.status_code, 403)
        decide.assert_not_called()  # 权限先于 token 消费:无权点批准不烧卡

    async def test_reject_needs_only_view_and_maps_the_envelope(self):
        sr = self._sr()
        seen = []

        def guard(_request, perm, *, not_found):
            seen.append(perm)
            return {"id": "u1"}, "t-1"

        decision = {"ok": True, "task_id": "task-1", "authorization": _grant()}
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", side_effect=guard),
            mock.patch.object(sr.feature_flags, "pearnly_ai_steward_enabled_for", lambda t: True),
            mock.patch.object(store, "ensure_once", mock.Mock()),
            mock.patch.object(sr.authz, "decide", mock.Mock(return_value=decision)),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(None)),
        ):
            out = await sr.reject_authorization(
                sr.AuthzDecisionIn(token="tok-12345678"), mock.Mock()
            )
        self.assertEqual(seen, [sr._C_VIEW])
        self.assertEqual(out["task_id"], "task-1")
        self.assertNotIn("args_fp", out["authorization"])

    async def test_error_envelope_becomes_http_error(self):
        sr = self._sr()
        err = {"ok": False, "http": 409, "code": authz.ERR_AUTHZ_USED}
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=({"id": "u1"}, "t-1")),
            mock.patch.object(sr.feature_flags, "pearnly_ai_steward_enabled_for", lambda t: True),
            mock.patch.object(store, "ensure_once", mock.Mock()),
            mock.patch.object(sr.authz, "decide", mock.Mock(return_value=err)),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(None)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await sr.approve_authorization(
                    sr.AuthzDecisionIn(token="tok-12345678"), mock.Mock()
                )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, authz.ERR_AUTHZ_USED)


if __name__ == "__main__":
    unittest.main()
