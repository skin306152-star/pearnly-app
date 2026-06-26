# -*- coding: utf-8 -*-
"""dispatch_auto_push · adapter-aware 入队分流守门。

已归属(client_id)票推所有自动端点;未归属(现金/散客)票只推 Express,绝不发给
MR.ERP(会 ERR_NO_CLIENT)。锁住放宽后不误伤 MR.ERP、且现金票能自动推。
"""

import unittest
from unittest import mock

from services.ocr.recognize import autopush


def _ep(eid, adapter):
    return {"id": eid, "adapter": adapter, "auto_push": True, "enabled": True}


class DispatchAutoPushTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = {"id": "u1"}
        self.plan = {}
        self._p_perms = mock.patch.object(
            autopush, "_plan_permissions", return_value={"can_auto_push_erp": True}
        )
        self._p_tid = mock.patch.object(autopush, "_tid", return_value=None)
        self._p_routing = mock.patch.object(
            autopush, "_erp_seller_routing_enabled", return_value=False
        )
        self._p_hist = mock.AsyncMock()
        self._p_smart = mock.AsyncMock()
        self._patch_hist = mock.patch.object(autopush, "_auto_push_history", self._p_hist)
        self._patch_smart = mock.patch.object(autopush, "_auto_push_smart_routed", self._p_smart)
        for p in (self._p_perms, self._p_tid, self._p_routing, self._patch_hist, self._patch_smart):
            p.start()
            self.addCleanup(p.stop)

    def _detail(self, mapping):
        def _f(_uid, hid, tenant_id=None):
            cid = mapping.get(hid)
            return {"id": hid, "client_id": cid}

        return _f

    async def _run(self, history_ids, endpoints, detail_map):
        import asyncio

        with (
            mock.patch.object(autopush.db, "list_erp_endpoints", return_value=endpoints),
            mock.patch.object(
                autopush.db, "get_ocr_history_detail", side_effect=self._detail(detail_map)
            ),
        ):
            res = autopush.dispatch_auto_push(
                history_ids=history_ids, plan=self.plan, user=self.user
            )
            await asyncio.sleep(0)  # 让 create_task 排的协程跑完
        return res

    async def test_unassigned_cash_goes_to_express_not_mrerp(self):
        eps = [_ep("ex1", "express"), _ep("mr1", "mrerp")]
        res = await self._run(["h1"], eps, {"h1": None})
        self.assertTrue(res)
        # 只发给 Express,且只带 express 端点
        self.assertEqual(self._p_hist.await_count, 1)
        _, hid, sent_eps = self._p_hist.await_args.args
        self.assertEqual(hid, "h1")
        self.assertEqual([e["adapter"] for e in sent_eps], ["express"])

    async def test_unassigned_skipped_when_no_express_endpoint(self):
        eps = [_ep("mr1", "mrerp")]
        res = await self._run(["h1"], eps, {"h1": None})
        self.assertFalse(res)
        self._p_hist.assert_not_awaited()

    async def test_assigned_goes_to_all_endpoints(self):
        eps = [_ep("ex1", "express"), _ep("mr1", "mrerp")]
        res = await self._run(["h1"], eps, {"h1": 42})
        self.assertTrue(res)
        _, hid, sent_eps = self._p_hist.await_args.args
        self.assertEqual(hid, "h1")
        self.assertEqual({e["adapter"] for e in sent_eps}, {"express", "mrerp"})

    async def test_mixed_batch_routes_each_correctly(self):
        eps = [_ep("ex1", "express"), _ep("mr1", "mrerp")]
        res = await self._run(["h_assigned", "h_cash"], eps, {"h_assigned": 7, "h_cash": None})
        self.assertTrue(res)
        by_hid = {c.args[1]: c.args[2] for c in self._p_hist.await_args_list}
        self.assertEqual({e["adapter"] for e in by_hid["h_assigned"]}, {"express", "mrerp"})
        self.assertEqual([e["adapter"] for e in by_hid["h_cash"]], ["express"])


if __name__ == "__main__":
    unittest.main()
