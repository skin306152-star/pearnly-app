# -*- coding: utf-8 -*-
"""改写审批流(波4)单测:出卡分流 / 提审 / 选人送达 / 批拒 / 执行诚实。

全 mock(不打库不发 LINE):store/roster/line_client 逐一 patch;执行协程经捕获后
await,断言走「批准人 endpoint + 快照字段」,失败必回炉不谎报。真库/真时序在
_w4 取证舱覆盖,此处守语义与守门。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.line_dms import approval_cards, approval_flow, cards

_BINDING_SALES = {"tenant_id": "T1", "user_id": "sales-1"}
_BINDING_ADMIN = {"tenant_id": "T1", "user_id": "admin-1"}
_LUID = "Lsales"

_REQ = {
    "id": "req-1",
    "tenant_id": "T1",
    "operator_user_id": "sales-1",
    "customer_id": "108",
    "customer_name": "สมชาย",
    "status": "pending",
    "field_diffs": [{"field": "house_no", "old": "1", "new": "9"}],
    "draft": {
        "fields": {"people_id": "1101700230705", "name": "สมชาย", "house_no": "9"},
        "display_diffs": [{"label": "บ้านเลขที่", "old": "1", "new": "9"}],
    },
}

_APPROVERS = [
    {"user_id": "admin-1", "display_name": "มานะ", "line_user_id": "Ladmin1"},
    {"user_id": "admin-2", "display_name": "สมหญิง", "line_user_id": "Ladmin2"},
]


def _btn_actions(card):
    return [b["action"]["data"] for b in card["contents"]["footer"]["contents"]]


_DISPLAY = [{"label": "ชื่อ", "old": "ก", "new": "ข"}]


class ExactDiffCardTests(unittest.TestCase):
    def test_sales_direct_update_with_borrowed_admin(self):
        """2026-07-19 泰方拍板:客户档改写销售不走审批,借到老板 admin 凭据即直写。"""
        with mock.patch.object(
            approval_flow.roster_store, "get_profile", return_value={"dms_role": "sales"}
        ):
            card, approval = approval_flow.exact_diff_card(
                "T1", "sales-1", _DISPLAY, True, "n1", {}
            )
        self.assertFalse(approval)
        self.assertTrue(any("action=update" in a for a in _btn_actions(card)))

    def test_sales_without_admin_creds_gets_setup_hint(self):
        """老板没配管理员凭据组=借不到写权 → 诚实不出更新按钮,也不假装能提审。"""
        with mock.patch.object(
            approval_flow.roster_store, "get_profile", return_value={"dms_role": "sales"}
        ):
            card, approval = approval_flow.exact_diff_card(
                "T1", "sales-1", _DISPLAY, False, "n1", {}
            )
        self.assertFalse(approval)
        self.assertFalse(any("action=update" in a for a in _btn_actions(card)))
        self.assertFalse(any("approval_submit" in a for a in _btn_actions(card)))

    def test_sales_gets_approval_card_when_policy_requires(self):
        """信用授权接口守门:策略登记要审的改动类型,波4 提审链原样接回。"""
        with (
            mock.patch.dict(approval_flow.APPROVAL_POLICY, {"customer_profile": True}),
            mock.patch.object(
                approval_flow.roster_store, "get_profile", return_value={"dms_role": "sales"}
            ),
        ):
            card, approval = approval_flow.exact_diff_card(
                "T1", "sales-1", _DISPLAY, False, "n1", {}
            )
        self.assertTrue(approval)
        self.assertTrue(any("approval_submit" in a for a in _btn_actions(card)))

    def test_unregistered_change_kind_defaults_to_approval(self):
        self.assertTrue(approval_flow.requires_approval("credit_auth"))
        self.assertTrue(approval_flow.requires_approval("future_unknown_kind"))
        self.assertFalse(approval_flow.requires_approval("customer_profile"))

    def test_admin_gets_direct_update(self):
        with mock.patch.object(
            approval_flow.roster_store, "get_profile", return_value={"dms_role": "admin"}
        ):
            card, approval = approval_flow.exact_diff_card(
                "T1", "admin-1", _DISPLAY, False, "n1", {}
            )
        self.assertFalse(approval)
        self.assertTrue(any("action=update" in a for a in _btn_actions(card)))

    def test_no_profile_keeps_legacy_has_admin(self):
        with mock.patch.object(approval_flow.roster_store, "get_profile", return_value=None):
            card, approval = approval_flow.exact_diff_card(
                "T1", "owner-1", _DISPLAY, False, "n1", {}
            )
        self.assertFalse(approval)
        self.assertFalse(any("action=update" in a for a in _btn_actions(card)))


class SubmitTests(unittest.IsolatedAsyncioTestCase):
    _PAYLOAD = {
        "scenario": "exact_diff",
        "approval": True,
        "endpoint_id": "ep-s",
        "customer_id": "108",
        "field_diffs": _REQ["field_diffs"],
        "display_diffs": _REQ["draft"]["display_diffs"],
        "draft": _REQ["draft"]["fields"],
    }

    async def test_submit_creates_request_and_shows_picker(self):
        with (
            mock.patch.object(
                approval_flow.store, "consume_nonce", return_value=dict(self._PAYLOAD)
            ),
            mock.patch.object(approval_flow, "_bound_approvers", return_value=list(_APPROVERS)),
            mock.patch.object(
                approval_flow.approval_store, "create_request", return_value="req-1"
            ) as cr,
            mock.patch.object(approval_flow.store, "clear_session") as clear,
            mock.patch.object(approval_flow.line_client, "reply_messages") as reply_msgs,
        ):
            await approval_flow._submit(_BINDING_SALES, _LUID, "rt", {"nonce": "n1"})
        self.assertEqual(cr.call_args.kwargs["customer_id"], "108")
        self.assertEqual(cr.call_args.kwargs["draft"]["fields"]["people_id"], "1101700230705")
        clear.assert_called_once()
        acts = _btn_actions(reply_msgs.call_args.args[1][0])
        self.assertTrue(any("aid=all" in a for a in acts))
        self.assertTrue(any("aid=admin-2" in a for a in acts))

    async def test_submit_without_approval_flag_rejected(self):
        bad = dict(self._PAYLOAD, approval=False)
        with (
            mock.patch.object(approval_flow.store, "consume_nonce", return_value=bad),
            mock.patch.object(approval_flow, "_reply") as reply,
        ):
            await approval_flow._submit(_BINDING_SALES, _LUID, "rt", {"nonce": "n1"})
        reply.assert_called_once_with("rt", cards.TXT_EXPIRED)

    async def test_submit_no_bound_approvers_honest(self):
        with (
            mock.patch.object(
                approval_flow.store, "consume_nonce", return_value=dict(self._PAYLOAD)
            ),
            mock.patch.object(approval_flow, "_bound_approvers", return_value=[]),
            mock.patch.object(approval_flow.approval_store, "create_request") as cr,
            mock.patch.object(approval_flow, "_reply") as reply,
        ):
            await approval_flow._submit(_BINDING_SALES, _LUID, "rt", {"nonce": "n1"})
        cr.assert_not_called()
        reply.assert_called_once_with("rt", approval_cards.TXT_NO_APPROVERS)


class TargetTests(unittest.IsolatedAsyncioTestCase):
    async def test_target_all_broadcasts_and_waits(self):
        with (
            mock.patch.object(approval_flow.approval_store, "get_request", return_value=dict(_REQ)),
            mock.patch.object(approval_flow, "_bound_approvers", return_value=list(_APPROVERS)),
            mock.patch.object(approval_flow.approval_store, "set_target", return_value=True) as st,
            mock.patch.object(
                approval_flow.roster_store, "get_profile", return_value={"display_name": "อาหมิง"}
            ),
            mock.patch.object(approval_flow.line_client, "push_messages") as push_msgs,
            mock.patch.object(approval_flow.line_client, "reply_messages") as reply_msgs,
        ):
            await approval_flow._target(_BINDING_SALES, _LUID, "rt", {"req": "req-1", "aid": "all"})
        st.assert_called_once_with("T1", "req-1", None)
        self.assertEqual({c.args[0] for c in push_msgs.call_args_list}, {"Ladmin1", "Ladmin2"})
        approve_acts = _btn_actions(push_msgs.call_args.args[1][0])
        self.assertTrue(any("approval_approve" in a for a in approve_acts))
        self.assertEqual(reply_msgs.call_args.args[1][0]["altText"], approval_cards.TXT_SENT_WAIT)

    async def test_target_single_admin_only_one_push(self):
        with (
            mock.patch.object(approval_flow.approval_store, "get_request", return_value=dict(_REQ)),
            mock.patch.object(approval_flow, "_bound_approvers", return_value=list(_APPROVERS)),
            mock.patch.object(approval_flow.approval_store, "set_target", return_value=True) as st,
            mock.patch.object(approval_flow.roster_store, "get_profile", return_value=None),
            mock.patch.object(approval_flow.line_client, "push_messages") as push_msgs,
            mock.patch.object(approval_flow.line_client, "reply_messages"),
        ):
            await approval_flow._target(
                _BINDING_SALES, _LUID, "rt", {"req": "req-1", "aid": "admin-2"}
            )
        st.assert_called_once_with("T1", "req-1", "admin-2")
        self.assertEqual(push_msgs.call_count, 1)
        self.assertEqual(push_msgs.call_args.args[0], "Ladmin2")

    async def test_target_foreign_request_rejected(self):
        foreign = dict(_REQ, operator_user_id="someone-else")
        with (
            mock.patch.object(approval_flow.approval_store, "get_request", return_value=foreign),
            mock.patch.object(approval_flow, "_reply") as reply,
        ):
            await approval_flow._target(_BINDING_SALES, _LUID, "rt", {"req": "req-1", "aid": "all"})
        reply.assert_called_once_with("rt", cards.TXT_EXPIRED)


class DecideTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_approver_rejected(self):
        with (
            mock.patch.object(approval_flow, "_approver_eligible", return_value=False),
            mock.patch.object(approval_flow.approval_store, "claim") as claim,
            mock.patch.object(approval_flow, "_reply") as reply,
        ):
            await approval_flow._decide(
                _BINDING_SALES, "Lsales", "rt", {"req": "req-1"}, approve=True
            )
        claim.assert_not_called()
        reply.assert_called_once_with("rt", approval_cards.TXT_NOT_APPROVER)

    async def test_lost_claim_stale_vs_expired(self):
        for status, expected in (
            ("approved", approval_cards.TXT_REQ_STALE),
            ("expired", approval_cards.TXT_REQ_EXPIRED),
        ):
            with (
                mock.patch.object(approval_flow, "_approver_eligible", return_value=True),
                mock.patch.object(approval_flow.approval_store, "claim", return_value=None),
                mock.patch.object(
                    approval_flow.approval_store,
                    "get_request",
                    return_value=dict(_REQ, status=status),
                ),
                mock.patch.object(approval_flow, "_reply") as reply,
            ):
                await approval_flow._decide(
                    _BINDING_ADMIN, "Ladmin1", "rt", {"req": "req-1"}, approve=True
                )
            reply.assert_called_once_with("rt", expected)

    async def test_reject_finishes_and_notifies_sales(self):
        with (
            mock.patch.object(approval_flow, "_approver_eligible", return_value=True),
            mock.patch.object(
                approval_flow.approval_store, "claim", return_value=dict(_REQ, status="processing")
            ),
            mock.patch.object(approval_flow.approval_store, "finish", return_value=True) as fin,
            mock.patch.object(approval_flow, "_reply") as reply,
            mock.patch.object(
                approval_flow.store,
                "get_binding_by_user",
                return_value={"line_user_id": "Lsales"},
            ),
            mock.patch.object(approval_flow, "_push") as push,
        ):
            await approval_flow._decide(
                _BINDING_ADMIN, "Ladmin1", "rt", {"req": "req-1"}, approve=False
            )
        fin.assert_called_once_with("T1", "req-1", "rejected")
        reply.assert_called_once_with("rt", approval_cards.TXT_REQ_REJECTED_ADMIN)
        push.assert_called_once_with("Lsales", approval_cards.TXT_REQ_REJECTED_SALES)


class ExecuteTests(unittest.IsolatedAsyncioTestCase):
    _EP = {"id": "ep-admin", "adapter": "mrerp_dms", "enabled": True, "config": {}}

    async def test_success_uses_approver_endpoint_and_snapshot(self):
        req = dict(_REQ, status="processing", decided_by="admin-1")
        with (
            mock.patch.object(
                approval_flow._id_ocr, "resolve_dms_endpoint", return_value=self._EP
            ) as res,
            mock.patch.object(
                approval_flow._dms_intake,
                "push_idcard_fields_mrerp_dms",
                return_value={"success": True, "customer_id": "108", "elapsed_ms": 5},
            ) as push_dms,
            mock.patch.object(approval_flow.db, "insert_push_log") as log,
            mock.patch.object(approval_flow.approval_store, "finish", return_value=True) as fin,
            mock.patch.object(approval_flow.line_client, "start_loading"),
            mock.patch.object(
                approval_flow.store,
                "get_binding_by_user",
                return_value={"line_user_id": "Lsales"},
            ),
            mock.patch.object(approval_flow, "_push") as push,
        ):
            await approval_flow._execute_approved(_BINDING_ADMIN, "Ladmin1", req)
        res.assert_called_once_with("admin-1", None)  # 批准人自己的 endpoint
        kw = push_dms.call_args.kwargs
        self.assertEqual(kw["mode"], "overwrite")
        self.assertEqual(kw["customer_id"], "108")
        self.assertEqual(kw["fields"]["house_no"], "9")  # 快照 diff,不依赖会话
        self.assertEqual(kw["fields"]["people_id"], "1101700230705")
        fin.assert_called_once_with("T1", "req-1", "approved")
        self.assertEqual(log.call_args.args[0], "admin-1")  # 台账落批准人名下
        self.assertEqual(log.call_args.args[8]["trigger"], "line_dms_approval")
        texts = [c.args for c in push.call_args_list]
        self.assertIn(("Ladmin1", approval_cards.TXT_REQ_APPROVED_ADMIN), texts)
        self.assertIn(("Lsales", approval_cards.TXT_REQ_APPROVED_SALES), texts)

    async def test_dms_failure_requeues_and_tells_truth(self):
        req = dict(_REQ, status="processing", decided_by="admin-1")
        with (
            mock.patch.object(approval_flow._id_ocr, "resolve_dms_endpoint", return_value=self._EP),
            mock.patch.object(
                approval_flow._dms_intake,
                "push_idcard_fields_mrerp_dms",
                return_value={"success": False, "error_code": "ERR_X", "elapsed_ms": 5},
            ),
            mock.patch.object(approval_flow.db, "insert_push_log"),
            mock.patch.object(approval_flow.approval_store, "finish", return_value=True) as fin,
            mock.patch.object(approval_flow.line_client, "start_loading"),
            mock.patch.object(approval_flow, "_push") as push,
        ):
            await approval_flow._execute_approved(_BINDING_ADMIN, "Ladmin1", req)
        fin.assert_called_once_with("T1", "req-1", "pending")  # 回炉可重试,不谎报已更新
        self.assertIn(approval_cards.TXT_EXEC_FAIL_ADMIN, push.call_args.args[1])

    async def test_approver_without_endpoint_requeues(self):
        req = dict(_REQ, status="processing", decided_by="admin-1")
        with (
            mock.patch.object(approval_flow._id_ocr, "resolve_dms_endpoint", return_value=None),
            mock.patch.object(approval_flow.approval_store, "finish", return_value=True) as fin,
            mock.patch.object(approval_flow.line_client, "start_loading"),
            mock.patch.object(approval_flow, "_push") as push,
        ):
            await approval_flow._execute_approved(_BINDING_ADMIN, "Ladmin1", req)
        fin.assert_called_once_with("T1", "req-1", "pending")
        push.assert_called_once_with("Ladmin1", approval_cards.TXT_APPROVER_NO_ENDPOINT)


class FlowWiringTests(unittest.IsolatedAsyncioTestCase):
    """接线守门:flow 必须真持有 approval_flow 引用并在 exact_diff/postback 走到它。

    血泪:import 行被 black 折行后 sed 落空,单测直调 approval_flow 全绿,真链 NameError
    才现形——此处从 flow 侧穿透断言,杜绝同类脱线。"""

    def test_flow_holds_approval_flow_reference(self):
        from services.line_dms import flow

        self.assertIs(flow.approval_flow, approval_flow)

    async def test_postback_routes_approval_action_via_flow(self):
        from services.line_dms import flow

        with (
            mock.patch.object(flow.store, "get_session", return_value=None),
            mock.patch.object(flow.approval_flow, "handle_postback") as h,
        ):
            await flow.handle_postback(
                _BINDING_ADMIN, "Ladmin1", "rt", {"data": "action=approval_approve&req=req-1"}
            )
        h.assert_awaited_once()
        self.assertEqual(h.call_args.args[3], cards.ACT_APPROVAL_APPROVE)


if __name__ == "__main__":
    unittest.main()
