# -*- coding: utf-8 -*-
"""管家第一个写工具 erp_push 全链(services/steward/erp_push_tool.py · B4)。

锁的是「派活 → 弹授权卡 → 经桥真写 Express」这条链上每一处会出事的地方:
  ① 派活即铸卡:任务停 waiting_user,卡上一眼看得出对哪个账套做什么、影响几条;桥一次没碰;
  ② 没批准物理进不去 handler(闸在 tools.run,不是前端不显示按钮);拒绝 → 任务 cancelled;
  ③ 批准后真投桥:断言的载荷是 mapper 现产的 express payload v1 —— 形状不由本测试杜撰,
     由 bridge.client.build_write_payload(生产写路的同一道契约闸)当场验一遍;
  ④ 参数/票面在等批的空档被改 → 旧批文一律作废,一步不执行;
  ⑤ 失败面全覆盖:桥不在线 / 桥拒收 / 桥写失败 / 等不到终态(必须报「别重推」并交出作业号);
  ⑥ 跨租户与账套作用域:别人家的票在这条链上一步都走不动。

零真 DB、零真桥:DB 是按真 SQL 分支语义仿真的假游标(复用 test_steward_authz 的那套),
桥只 mock services.erp.bridge.client 的 submit_write/write_status 两个门面函数。
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from unittest import mock

from core import db as _core_db  # noqa: F401 —— 先落 core.db,避免撞 dal_reexports 循环导入
from services.erp.bridge import BridgeRejected, BridgeUnavailable
from services.erp.bridge import client as bridge_client
from services.steward import (
    authz,
    copy,
    erp_push_tool,
    orchestrator,
    registry,
    store,
    tools,
    worker,
)
from services.steward.registry import ToolContext
from tests.unit.test_steward_authz import FakeCur, _CurCM, _World, _task_row

OWN_TAX = "0994000333444"
VENDOR_TAX = "0107561000013"
_ACCOUNT_SET = "DATAT"
_HISTORY_ID = "hist-1"

_CONFIG = {
    "account_set": _ACCOUNT_SET,
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}


def _endpoint(**over):
    cfg = dict(_CONFIG)
    cfg.update(over.pop("config", {}))
    ep = {"id": "ep-1", "adapter": "express", "user_id": "u1", "enabled": True, "config": cfg}
    ep.update(over)
    return ep


def _history(**over):
    """一张真进项票(自家是买方 → 方向按税号锚点判 purchase)· 形状同 /api/erp/push 那条路。"""
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": VENDOR_TAX,
        "buyer_tax": OWN_TAX,
        "subtotal": "375347.20",
        "vat": "26274.30",
        "invoice_number": "RR581231-002",
        "document_type": "tax_invoice",
    }
    row = {
        "id": _HISTORY_ID,
        "filename": "ptt.pdf",
        "invoice_date": "2015-12-31",
        "invoice_no": "RR581231-002",
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "total_amount": 401621.50,
        "confidence": "high",
        "workspace_client_id": 7,
        "pages": [{"fields": fields}],
    }
    row.update(over)
    return row


def _listing_row(**over):
    """识别记录列表里的一行(prepare 按关键词定位那张票时看到的形状)。"""
    row = {
        "id": _HISTORY_ID,
        "filename": "ptt.pdf",
        "invoice_no": "RR581231-002",
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "invoice_date": "2015-12-31",
        "total_amount": 401621.50,
        "workspace_client_id": 7,
        "status": "success",
    }
    row.update(over)
    return row


def _ctx(**over):
    kw = {
        "user": {"id": "u1", "tenant_id": "t-1", "plan": "pro"},
        "tenant_id": "t-1",
        "user_id": "u1",
    }
    kw.update(over)
    return ToolContext(**kw)


class _World3rd:
    """把 erp_push 会碰到的外部世界一次性接管:端点/识别记录/桥/日志/审计。"""

    def __init__(self, test, *, endpoint=None, history=None, listing=None):
        self.endpoint = _endpoint() if endpoint is None else endpoint
        self.history = _history() if history is None else history
        self.listing = [_listing_row()] if listing is None else listing
        self.submit = mock.Mock(return_value="job-1")
        self.status = mock.Mock(return_value={"job_id": "job-1", "status": "done",
                                              "result": {"docnum": "RR6800012"}, "error": None})  # fmt: skip
        self.push_logs = []
        self.audits = []
        patches = (
            mock.patch("core.db.list_erp_endpoints", self._endpoints),
            mock.patch("core.db.get_ocr_history_detail", lambda *_a, **_k: self.history),
            mock.patch("core.db.get_user_tenant_id", lambda *_a, **_k: None),
            mock.patch("core.db.get_workspace_client", lambda *_a, **_k: {"tax_id": OWN_TAX}),
            mock.patch("core.db.get_visible_client_ids_for_user", lambda *_a, **_k: None),
            mock.patch("core.db.insert_push_log", self._log),
            mock.patch("services.ocr_history.queries.list_ocr_history", self._search),
            mock.patch("services.audit.store.insert_operation_log", self._audit),
            mock.patch.object(bridge_client, "submit_write", self.submit),
            mock.patch.object(bridge_client, "write_status", self.status),
            mock.patch.dict("os.environ", {"ERP_PUSH_ENABLED": "1"}),
            mock.patch.object(erp_push_tool, "_POLL_INTERVAL_S", 0),
            mock.patch.object(erp_push_tool, "_POLL_DEADLINE_S", 0.05),
        )
        for p in patches:
            p.start()
            test.addCleanup(p.stop)

    def _endpoints(self, *_a, **_k):
        return [self.endpoint] if self.endpoint else []

    def _search(self, **kwargs):
        return {"items": list(self.listing), "total": len(self.listing), "status_counts": {}}

    def _log(self, **kwargs):
        self.push_logs.append(kwargs)
        return "log-1"

    def _audit(self, **kwargs):
        self.audits.append(kwargs)

    @property
    def payload(self):
        return self.submit.call_args.args[2] if self.submit.call_args else None


class PrepareTests(unittest.TestCase):
    """铸卡前接地:把「那张 PTT 的票」落成一条真记录 + 目标账套 + 票面快照。"""

    def setUp(self):
        self.world = _World3rd(self)

    def test_resolves_one_invoice_into_executable_args(self):
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"})
        self.assertTrue(out.ok)
        self.assertEqual(set(out.args), set(erp_push_tool.ARG_KEYS))
        self.assertEqual(out.args["history_id"], _HISTORY_ID)
        self.assertEqual(out.args["account_set"], _ACCOUNT_SET)
        self.assertEqual(out.args["total_amount"], "401621.50")  # decimal 两位,不是 float
        self.assertEqual(out.workspace_client_id, 7)

    def test_direction_hint_is_normalized_and_optional(self):
        hinted = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT", "direction": "进项"})
        self.assertEqual(hinted.args["direction"], "")  # 认不出的词当没说,交税号锚点判
        typed = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT", "direction": "sales"})
        self.assertEqual(typed.args["direction"], "sales")

    def test_no_invoice_found_asks_instead_of_guessing(self):
        self.world.listing = []
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "不存在的店"})
        self.assertFalse(out.ok)
        self.assertEqual(out.error.error_code, erp_push_tool.ERR_INVOICE_NOT_FOUND)

    def test_ambiguous_keyword_returns_candidates(self):
        self.world.listing = [_listing_row(), _listing_row(id="hist-2", invoice_no="RR-9")]
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"})
        self.assertEqual(out.error.error_code, erp_push_tool.ERR_INVOICE_AMBIGUOUS)
        self.assertEqual(len(out.error.data["candidates"]), 2)
        reply = copy.error(out.error.error_code, out.error.data, "zh")
        self.assertIn("RR-9", reply)  # 候选原样列出来让人挑,不替他选一张

    def test_without_express_connection_it_refuses_early(self):
        self.world.endpoint = None
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"})
        self.assertEqual(out.error.error_code, erp_push_tool.ERR_ENDPOINT_MISSING)

    def test_account_set_the_user_named_must_match_the_connection(self):
        out = tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT", "account_set": "OTHER"})
        self.assertEqual(out.error.error_code, erp_push_tool.ERR_ACCOUNT_SET_MISMATCH)
        self.assertIn("OTHER", copy.error(out.error.error_code, out.error.data, "zh"))


class _ChainTestCase(unittest.IsolatedAsyncioTestCase):
    """派活 → 铸卡 → 决断 → worker 复跑的全链底座(orchestrator/authz/worker/tools 全走真码)。"""

    def setUp(self):
        self.world = _World3rd(self)
        self.db = _World(None)
        self.cur = FakeCur(self.db)

    def _create_task(self, _cur, **kw):
        self.db.task = _task_row(
            status=kw["status"], steps=kw["steps"], payload=kw["payload"], title=kw["title"]
        )
        return self.db.task

    def _enqueue(self, args=None, ctx=None):
        with (
            mock.patch.object(store, "create_task", self._create_task),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(self.cur)),
        ):
            return orchestrator._enqueue(
                ctx or _ctx(), registry.ERP_PUSH, args or {"keyword": "PTT"}, "zh", session_id="s-1"
            )

    async def _run_worker(self):
        with (
            mock.patch.object(worker, "_build_context", lambda *a: _ctx()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(self.cur)),
        ):
            await worker._execute(dict(self.db.task))

    def _approve(self):
        token = self.db.task["payload"]["authorization"]["token"]
        return authz.decide(
            self.cur, tenant_id="t-1", token=token, actor={"id": "boss"}, approve=True
        )


class ConfirmFirstChainTests(_ChainTestCase):
    async def test_dispatch_mints_a_readable_card_and_touches_no_bridge(self):
        out = self._enqueue()
        self.assertEqual(self.db.task["status"], store.TASK_WAITING_USER)
        card = store.public_task(self.db.task)["authorization"]
        self.assertEqual(card["status"], store.AUTH_PENDING)
        self.assertEqual(card["risk"], registry.RISK_WRITE)
        # 标题自证「对哪个账套推几张」;票面明细逐行摆在 args_display 上,用会计的说法,
        # 不是工具槽名(direction=sales / history_id=<uuid> 摆给人签 = 让她闭眼签)。
        for token in ("1 张", _ACCOUNT_SET):
            self.assertIn(token, card["title"])
        rows = {r["label"]: r["value"] for r in card["args_display"]}
        self.assertEqual(rows["票号"], "RR581231-002")
        self.assertEqual(rows["方向"], "方向自动判定")
        self.assertIn("401621.50", rows["金额"])
        self.assertNotIn("purchase", str(card["args_display"]))
        self.assertNotIn(_HISTORY_ID, str(card["args_display"]))
        self.assertEqual(card["args"]["history_id"], _HISTORY_ID)
        self.assertNotIn("args_fp", card)
        self.assertIn(store.STEP_WAITING_AUTH, [s["state"] for s in out["steps"]])
        self.assertEqual(out["task_status"], store.TASK_WAITING_USER)
        self.submit_not_called()

    def submit_not_called(self):
        self.assertEqual(self.world.submit.call_args_list, [])

    async def test_write_task_carries_the_long_timeout(self):
        """经桥写是分钟级:任务超时按工具声明定格,别让 5 分钟的只读口径砍掉在写的活。"""
        self._enqueue()
        create = mock.Mock(side_effect=self._create_task)
        with (
            mock.patch.object(store, "create_task", create),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM(self.cur)),
        ):
            orchestrator._enqueue(_ctx(), registry.ERP_PUSH, {"keyword": "PTT"}, "zh",
                                  session_id="s-1")  # fmt: skip
        self.assertEqual(create.call_args.kwargs["timeout_s"], registry.ERP_PUSH_TIMEOUT_S)

    async def test_approved_run_submits_a_real_express_payload_v1(self):
        self._enqueue()
        self.assertTrue(self._approve()["ok"])
        self.assertEqual(self.db.task["status"], store.TASK_RUNNING)

        await self._run_worker()

        tenant_id, book_id, payload = self.world.submit.call_args.args
        self.assertEqual((tenant_id, book_id), ("t-1", _ACCOUNT_SET))
        # 载荷契约 = mapper 模块头逐字(payload_version / 方向 / 票种 / 佛历日 / 供应商 / 分录)。
        self.assertEqual(payload["payload_version"], 1)
        self.assertEqual(payload["direction"], "purchase")
        self.assertIn(payload["doctype"], ("RR", "HP"))
        self.assertEqual(payload["account_set"], _ACCOUNT_SET)
        self.assertEqual(payload["docdate_be"], "581231")
        self.assertEqual(payload["vat_period_be"], "581201")
        self.assertEqual(payload["ref_no"], "RR581231-002")
        self.assertEqual(payload["base_amount"], "375347.20")
        self.assertEqual(payload["vat_amount"], "26274.30")
        self.assertEqual(payload["total_amount"], "401621.50")
        self.assertEqual(payload["supplier"]["tax_id"], VENDOR_TAX)
        self.assertTrue(payload["supplier"]["supplier_new"])
        self.assertEqual(payload["source"]["history_id"], _HISTORY_ID)
        debit = sum(Decimal(ln["amount"]) for ln in payload["lines"] if ln["side"] == "D")
        credit = sum(Decimal(ln["amount"]) for ln in payload["lines"] if ln["side"] == "C")
        self.assertEqual(debit, credit)
        # 生产写路的同一道形状闸当场验:形状不是本测试杜撰的,是桥真会收的那个。
        bridge_client.build_write_payload(payload, _ACCOUNT_SET)

    async def test_success_reports_docnum_logs_the_push_and_audits(self):
        self._enqueue()
        self._approve()
        await self._run_worker()
        self.assertEqual(self.db.task["status"], store.TASK_DONE)
        reply = self.db.messages[-1]["text"]
        self.assertIn("RR6800012", reply)  # Express 单号如实回,没拿到就不编
        self.assertIn(_ACCOUNT_SET, reply)
        log = self.world.push_logs[-1]
        self.assertEqual((log["status"], log["trigger"]), ("success", "steward"))
        self.assertEqual(log["total_amount"], Decimal("401621.50"))  # 钱走 decimal
        self.assertEqual(self.world.audits[-1]["action"], erp_push_tool.AUDIT_SUBMITTED)
        self.assertEqual(self.world.audits[-1]["details"]["job_id"], "job-1")

    async def test_rejecting_cancels_the_task_and_writes_nothing(self):
        self._enqueue()
        token = self.db.task["payload"]["authorization"]["token"]
        out = authz.decide(
            self.cur, tenant_id="t-1", token=token, actor={"id": "boss"}, approve=False
        )
        self.assertTrue(out["ok"])
        self.assertEqual(self.db.task["status"], store.TASK_CANCELLED)
        self.assertEqual(self.db.task["error_code"], authz.ERR_AUTHZ_REJECTED)
        self.assertEqual(self.world.submit.call_args_list, [])

    async def test_unapproved_task_is_refused_at_the_execution_gate(self):
        """停靠万一失守(pending 任务被当 running 认领)→ 物理拒,桥一次没碰。"""
        self._enqueue()
        self.db.task["status"] = store.TASK_RUNNING
        await self._run_worker()
        self.assertEqual(self.db.task["error_code"], authz.ERR_AUTHZ_REQUIRED)
        self.assertEqual(self.world.submit.call_args_list, [])

    async def test_changed_args_invalidate_the_grant_before_the_bridge(self):
        """批的是这张票、执行时参数被换成另一张 → 指纹对不上,物理拒。"""
        self._enqueue()
        self._approve()
        self.db.task["payload"]["args"]["history_id"] = "hist-999"
        await self._run_worker()
        self.assertEqual(self.db.task["error_code"], authz.ERR_AUTHZ_MISMATCH)
        self.assertEqual(self.world.submit.call_args_list, [])

    async def test_invoice_edited_while_waiting_voids_the_grant(self):
        """参数没变但票面变了(会计在等批的空档改了金额)→ 批文作废,绝不照旧写进去。"""
        self._enqueue()
        self._approve()
        self.world.history = _history(total_amount=999999.00)
        await self._run_worker()
        self.assertEqual(self.db.task["error_code"], erp_push_tool.ERR_INVOICE_CHANGED)
        self.assertEqual(self.world.submit.call_args_list, [])


class BridgeFailureTests(_ChainTestCase):
    """桥侧四种坏天气:不在线 / 拒收 / 写失败 / 等不到终态。每一种都得给人话 + 下一步。"""

    async def _push(self):
        self._enqueue()
        self._approve()
        await self._run_worker()
        return self.db.task

    async def test_offline_bridge_says_where_to_look(self):
        self.world.submit.side_effect = BridgeUnavailable("no write bridge")
        task = await self._push()
        self.assertEqual(task["status"], store.TASK_FAILED)
        self.assertEqual(task["error_code"], erp_push_tool.ERR_BRIDGE_OFFLINE)
        # 主语说「小助手」不说「桥」——会计只认得装在她电脑上的那个;也不许指向产品里
        # 根本没有的那一栏(「集成 · ERP 桥」全仓不存在,照着找找不到)。
        self.assertIn("小助手", task["error_message"])
        self.assertNotIn("桥", task["error_message"])
        self.assertIn(_ACCOUNT_SET, task["error_message"])
        self.assertIn("没有写入", task["error_message"])

    async def test_rejected_payload_is_not_reported_as_written(self):
        self.world.submit.side_effect = BridgeRejected("借贷不平", "bridge.bad_payload")
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_REJECTED)
        self.assertIn("借贷不平", task["error_message"])

    async def test_bridge_failure_carries_the_job_id(self):
        self.world.status.return_value = {"job_id": "job-1", "status": "failed", "result": {},
                                          "error": {"code": "bridge.write_failed",
                                                    "message": "CDX rebuild failed"}}  # fmt: skip
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_FAILED)
        self.assertIn("job-1", task["error_message"])
        self.assertEqual(self.world.push_logs[-1]["status"], "failed")

    async def test_still_writing_never_tells_anyone_to_retry(self):
        """等不到终态 ≠ 没写进去:必须交出作业号并明说别重推(重推 = 双写)。"""
        self.world.status.return_value = {"job_id": "job-1", "status": "leased", "result": {},
                                          "error": None}  # fmt: skip
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_PENDING)
        self.assertIn("job-1", task["error_message"])
        self.assertIn("不要重推", task["error_message"])
        self.assertEqual(self.world.push_logs[-1]["status"], "pending")

    async def test_expired_job_is_reported_as_not_written(self):
        self.world.status.return_value = {"job_id": "job-1", "status": "expired", "result": {},
                                          "error": None}  # fmt: skip
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_EXPIRED)

    async def test_confirmed_write_without_an_ack_is_not_reported_as_not_written(self):
        """同样是 expired,「领了没回执」与「没人来领」必须说两句不同的话。

        确认放行的写单关掉了桥端的幂等闸,系统分不出它写没写。照 ERR_PUSH_EXPIRED 那句
        「多为小助手一直不在线,上线后再说一次」去做,就是账上两张 —— 这里必须落在
        「先去核对再决定」那一支,推送日志也不能记成 failed。
        """
        from services.erp.bridge import write_gate as bridge_write_gate

        self.world.status.return_value = {"job_id": "job-1", "status": "expired", "result": {},
                                          "error": {"code": bridge_write_gate.CONFIRMED_UNACKED_CODE,
                                                    "message": "领了没回结果"}}  # fmt: skip
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_UNCERTAIN)
        self.assertIn("job-1", task["error_message"])
        self.assertNotIn("上线后再说一次", task["error_message"])
        log = self.world.push_logs[-1]
        self.assertEqual(log["status"], "pending")
        # 占位租约必须在:pending 是 Express 旧队列的保留态,不占住,小助手会把这份
        # 带确认位的载荷领走再写一遍。
        self.assertEqual(log["lease_owner"], erp_push_tool._PENDING_LEASE_OWNER)

    async def test_preflight_block_stops_before_the_bridge(self):
        """票过不了推送前体检(这里:账套没配)→ 不投桥,如实说要补什么。"""
        self.world.history = _history(invoice_date=None)
        task = await self._push()
        self.assertEqual(task["error_code"], erp_push_tool.ERR_PUSH_BLOCKED)
        self.assertEqual(self.world.submit.call_args_list, [])


class TenantIsolationTests(unittest.TestCase):
    """跨租户/跨账套:别人家的票在这条链上一步都走不动。"""

    def setUp(self):
        self.world = _World3rd(self)

    def _args(self):
        return dict(tools.prepare(registry.ERP_PUSH, _ctx(), {"keyword": "PTT"}).args)

    def test_other_tenants_history_is_simply_not_found(self):
        args = self._args()
        self.world.history = None  # get_ocr_history_detail 按 tenant 收窄 → 查无
        res = erp_push_tool.erp_push(_ctx(tenant_id="t-2"), args)
        self.assertEqual(res.error_code, erp_push_tool.ERR_INVOICE_NOT_FOUND)
        self.assertEqual(self.world.submit.call_args_list, [])

    def test_client_scope_keeps_assigned_members_off_other_books(self):
        args = self._args()
        res = erp_push_tool.erp_push(_ctx(allowed_client_ids=frozenset({99})), args)
        self.assertEqual(res.error_code, erp_push_tool.ERR_INVOICE_NOT_FOUND)
        self.assertEqual(self.world.submit.call_args_list, [])

    def test_connection_switched_account_set_after_minting(self):
        args = self._args()
        self.world.endpoint = _endpoint(config={"account_set": "OTHER"})
        res = erp_push_tool.erp_push(_ctx(), args)
        self.assertEqual(res.error_code, erp_push_tool.ERR_ACCOUNT_SET_MISMATCH)
        self.assertEqual(self.world.submit.call_args_list, [])

    def test_bridge_call_is_scoped_to_the_callers_tenant(self):
        res = erp_push_tool.erp_push(_ctx(), self._args())
        self.assertTrue(res.ok)
        self.assertEqual(self.world.submit.call_args.args[0], "t-1")


class WriteToolCopyTests(unittest.TestCase):
    def test_timeout_copy_for_write_tools_forbids_a_blind_retry(self):
        """同一个「超时」,只读工具可以叫人再说一次,写工具说这句就是在教人双写。"""
        read = copy.fail_reason("steward.timeout", "zh", seconds=30, tool=registry.CLIENT_LOOKUP)
        write = copy.fail_reason("steward.timeout", "zh", seconds=900, tool=registry.ERP_PUSH)
        self.assertIn("再说一次", read)
        self.assertNotIn("再说一次", write)
        self.assertIn("不要重推", write)

    def test_every_write_error_code_has_thai_and_chinese_copy(self):
        from services.steward import copy_erp_push

        for code, table in copy_erp_push.ERRORS.items():
            self.assertEqual(set(table), {"zh", "th"}, code)
            self.assertTrue(all(v.strip() for v in table.values()), code)

    def test_capability_line_admits_the_write_tool(self):
        """产品不许撒谎:注册表里有写工具,能力清单就不能还写着「只查不改」。"""
        for lang in ("zh", "th"):
            self.assertIn("Express", copy.out_of_scope(lang))


if __name__ == "__main__":
    unittest.main()
