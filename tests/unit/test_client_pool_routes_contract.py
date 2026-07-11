# -*- coding: utf-8 -*-
"""LINE 待问客户池会计端路由契约(routes/client_pool_routes.py · D2-S8+S9)。

锁定:①四端点按 path+method 注册且挂进 app;②M1 闸 / client_pool 闸任一关 → 404
(fail-closed,不泄漏端点存在性);③stage 校验工单+item 归属、question_type 未知 → 422;
④list 按 workspace_client_id 过滤或缺省逐客户枚举(零问题客户不占版面);⑤push-batch
薄封装 line_client_pool_push,原样透传结构化四态返回;⑥decide 只认 manual_review 态,
成功后落 human_decision 事件 + 转 applied,非法跳转 → 409。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes.client_pool_routes import router as client_pool_router
from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_pool_store as pool_store


def _route_set(router):
    out = set()
    for r in router.routes:
        for m in getattr(r, "methods", set()) or set():
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                out.add((m, r.path))
    return out


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(client_pool_router)
        expected = {
            ("POST", "/api/ai/client-pool/stage"),
            ("GET", "/api/ai/client-pool"),
            ("POST", "/api/ai/client-pool/push-batch"),
            ("POST", "/api/ai/client-pool/questions/{question_id}/decide"),
        }
        self.assertEqual(rs, expected)


class RouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/ai/client-pool/stage", paths)
        self.assertIn("/api/ai/client-pool/questions/{question_id}/decide", paths)


class _Cur:
    def __init__(self, fetchone_value=(1,)):
        self._fetchone = fetchone_value

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._fetchone


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _FakeDB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return _CM(self._cur)


_USER = {"id": "u1", "tenant_id": "t-1"}


class _GatedRouteCase(unittest.IsolatedAsyncioTestCase):
    """两闸 + 权限 + 归属校验的共用桩(照 test_workorder_routes_contract 先例,用
    enterContext 逐个挂上,3.11 支持)。子类调用 self._wire(cpr, ...) 后即可直调路由函数。"""

    def _wire(self, mod, *, m1=True, pool=True, owns=True):
        patches = (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=m1),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=pool),
            mock.patch.object(mod, "check_workspace_scope", return_value=None),
            mock.patch.object(mod, "db", _FakeDB(_Cur(fetchone_value=(1,) if owns else None))),
        )
        for p in patches:
            self.enterContext(p)


class GateClosedTests(_GatedRouteCase):
    async def test_m1_gate_closed_hides_route_as_404(self):
        from routes import client_pool_routes as cpr

        self.enterContext(
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER)
        )
        self.enterContext(
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False)
        )
        with self.assertRaises(HTTPException) as ctx:
            await cpr.list_client_pool(mock.Mock(), workspace_client_id=None)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_client_pool_gate_closed_hides_route_as_404(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr, pool=False)
        with self.assertRaises(HTTPException) as ctx:
            await cpr.list_client_pool(mock.Mock(), workspace_client_id=None)
        self.assertEqual(ctx.exception.status_code, 404)


class StageTests(_GatedRouteCase):
    async def test_stage_returns_question_shape(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        wo = {"workspace_client_id": 7, "period": "2569-05"}
        item = {"id": "item-1"}
        question = {
            "id": 1,
            "workspace_client_id": 7,
            "work_order_id": "wo-1",
            "item_id": "item-1",
            "period": "2569-05",
            "question_type": vocab.QUESTION_DIRECTION,
            "question_payload": {},
            "status": vocab.STAGED,
            "batch_id": None,
            "answer_raw": None,
            "resolution": None,
            "created_at": None,
            "sent_at": None,
            "answered_at": None,
            "closed_at": None,
        }
        self.enterContext(mock.patch.object(cpr.wo_store, "get_work_order", return_value=wo))
        self.enterContext(mock.patch.object(cpr.wo_store, "get_item", return_value=item))
        self.enterContext(mock.patch.object(cpr.pool_store, "stage", return_value=question))

        out = await cpr.stage_question(
            cpr.StageIn(
                work_order_id="wo-1", item_id="item-1", question_type=vocab.QUESTION_DIRECTION
            ),
            mock.Mock(),
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["question"]["status"], vocab.STAGED)

    async def test_unknown_question_type_is_422(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        with self.assertRaises(HTTPException) as ctx:
            await cpr.stage_question(
                cpr.StageIn(work_order_id="wo-1", item_id="item-1", question_type="bogus"),
                mock.Mock(),
            )
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_work_order_not_found_is_404(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        self.enterContext(mock.patch.object(cpr.wo_store, "get_work_order", return_value=None))
        with self.assertRaises(HTTPException) as ctx:
            await cpr.stage_question(
                cpr.StageIn(
                    work_order_id="wo-x", item_id="item-1", question_type=vocab.QUESTION_DIRECTION
                ),
                mock.Mock(),
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_item_not_belonging_to_order_is_404(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        wo = {"workspace_client_id": 7, "period": "2569-05"}
        self.enterContext(mock.patch.object(cpr.wo_store, "get_work_order", return_value=wo))
        self.enterContext(mock.patch.object(cpr.wo_store, "get_item", return_value=None))
        with self.assertRaises(HTTPException) as ctx:
            await cpr.stage_question(
                cpr.StageIn(
                    work_order_id="wo-1", item_id="item-x", question_type=vocab.QUESTION_DIRECTION
                ),
                mock.Mock(),
            )
        self.assertEqual(ctx.exception.status_code, 404)


class ListPoolTests(_GatedRouteCase):
    async def test_single_client_filter_builds_one_group(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        rows = [
            {
                "id": 1,
                "workspace_client_id": 7,
                "work_order_id": "wo-1",
                "item_id": "item-1",
                "period": "2569-05",
                "question_type": vocab.QUESTION_DIRECTION,
                "question_payload": {},
                "status": vocab.STAGED,
                "batch_id": None,
                "answer_raw": None,
                "resolution": None,
                "created_at": None,
                "sent_at": None,
                "answered_at": None,
                "closed_at": None,
            }
        ]
        self.enterContext(mock.patch.object(cpr.pool_store, "list_for_client", return_value=rows))
        self.enterContext(
            mock.patch.object(cpr.line_client_contact, "get_contact", return_value=None)
        )
        self.enterContext(
            mock.patch.object(
                cpr.workspace_store, "get_workspace_client", return_value={"name": "Sister Makeup"}
            )
        )
        out = await cpr.list_client_pool(mock.Mock(), workspace_client_id=7)
        self.assertEqual(len(out["groups"]), 1)
        group = out["groups"][0]
        self.assertEqual(group["workspace_client_id"], 7)
        self.assertEqual(group["name"], "Sister Makeup")
        self.assertFalse(group["bound"])
        self.assertEqual(len(group["questions"][vocab.STAGED]), 1)

    async def test_missing_workspace_id_enumerates_only_nonempty_clients(self):
        from routes import client_pool_routes as cpr

        self.enterContext(
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER)
        )
        self.enterContext(
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True)
        )
        self.enterContext(mock.patch.object(route_helpers, "require_perm", return_value=_USER))
        self.enterContext(
            mock.patch("core.feature_flags.pearnly_ai_client_pool_enabled_for", return_value=True)
        )
        clients = [{"id": 7}, {"id": 8}]

        def _list_for(_tenant, ws_id, statuses=None):
            return (
                [
                    {
                        "id": 1,
                        "workspace_client_id": ws_id,
                        "work_order_id": "wo-1",
                        "item_id": "item-1",
                        "period": "2569-05",
                        "question_type": vocab.QUESTION_DIRECTION,
                        "question_payload": {},
                        "status": vocab.STAGED,
                        "batch_id": None,
                        "answer_raw": None,
                        "resolution": None,
                        "created_at": None,
                        "sent_at": None,
                        "answered_at": None,
                        "closed_at": None,
                    }
                ]
                if ws_id == 7
                else []
            )

        self.enterContext(
            mock.patch.object(cpr.workspace_store, "list_workspace_clients", return_value=clients)
        )
        self.enterContext(
            mock.patch.object(cpr.pool_store, "list_for_client", side_effect=_list_for)
        )
        self.enterContext(
            mock.patch.object(cpr.line_client_contact, "get_contact", return_value=None)
        )
        out = await cpr.list_client_pool(mock.Mock(), workspace_client_id=None)
        self.assertEqual([g["workspace_client_id"] for g in out["groups"]], [7])


class PushBatchTests(_GatedRouteCase):
    async def test_delegates_to_push_batch_for_client(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        result = {"ok": False, "reason": "not_bound"}
        call = self.enterContext(
            mock.patch.object(cpr.pool_push, "push_batch_for_client", return_value=result)
        )
        out = await cpr.push_batch(cpr.PushBatchIn(workspace_client_id=7), mock.Mock())
        self.assertEqual(out, result)
        call.assert_called_once()
        self.assertEqual(call.call_args.args[1], 7)


class DecideTests(_GatedRouteCase):
    def _manual_review_row(self):
        return {
            "id": 5,
            "workspace_client_id": 7,
            "work_order_id": "wo-1",
            "item_id": "item-1",
            "period": "2569-05",
            "question_type": vocab.QUESTION_DROP,
            "question_payload": {},
            "status": vocab.MANUAL_REVIEW,
            "batch_id": "b-1",
            "answer_raw": "ไม่แน่ใจ",
            "resolution": None,
            "created_at": None,
            "sent_at": None,
            "answered_at": None,
            "closed_at": None,
        }

    async def test_decide_applies_and_transitions(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        row = self._manual_review_row()
        applied = dict(row, status=vocab.APPLIED)
        self.enterContext(mock.patch.object(cpr.pool_store, "list_for_client", return_value=[row]))
        self.enterContext(
            mock.patch.object(cpr.wo_api, "record_decision", return_value={"id": "evt-1"})
        )
        trans = self.enterContext(
            mock.patch.object(cpr.pool_store, "transition", return_value=applied)
        )
        out = await cpr.decide_question(
            5, cpr.DecideIn(workspace_client_id=7, decision="exclude"), mock.Mock()
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["question"]["status"], vocab.APPLIED)
        trans.assert_called_once()
        self.assertEqual(trans.call_args.args[2], vocab.APPLIED)

    async def test_question_not_in_manual_review_is_404(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        self.enterContext(mock.patch.object(cpr.pool_store, "list_for_client", return_value=[]))
        with self.assertRaises(HTTPException) as ctx:
            await cpr.decide_question(
                99, cpr.DecideIn(workspace_client_id=7, decision="exclude"), mock.Mock()
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_illegal_transition_is_409(self):
        from routes import client_pool_routes as cpr

        self._wire(cpr)
        row = self._manual_review_row()
        self.enterContext(mock.patch.object(cpr.pool_store, "list_for_client", return_value=[row]))
        self.enterContext(
            mock.patch.object(cpr.wo_api, "record_decision", return_value={"id": "evt-1"})
        )
        self.enterContext(
            mock.patch.object(
                cpr.pool_store,
                "transition",
                side_effect=pool_store.IllegalTransitionError(vocab.APPLIED, vocab.APPLIED),
            )
        )
        with self.assertRaises(HTTPException) as ctx:
            await cpr.decide_question(
                5, cpr.DecideIn(workspace_client_id=7, decision="exclude"), mock.Mock()
            )
        self.assertEqual(ctx.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
