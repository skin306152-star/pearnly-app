# -*- coding: utf-8 -*-
"""守门测试 · 卖方智能分拣 match_workspace_for_seller(Phase 1a · Zihao 2026-05-26)

销项发票卖方 = 账套主体 = workspace_client → 绑定 ERP endpoint。
匹配优先级:① seller_workspace_routes 学习路由 → ② workspace_clients.tax_id 精确
→ ③ workspace_clients.name 精确。判定:assigned / unbound / multi / none。

无 DB · 用按 SQL 关键字返结果的 fake cursor 锁定匹配优先级 + 判定。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 — 先初始化 db 防 services.workspace.store 循环导入
from services.workspace import store


class KeywordCursor:
    """按 SQL 关键字分流返结果(match 内部多条顺序查询)。"""

    def __init__(self, route=None, by_id=None, by_tax=None, by_name=None):
        self.route = route  # seller_workspace_routes fetchone → {'workspace_client_id': N} 或 None
        self.by_id = by_id or []  # workspace_clients WHERE id (路由记忆 load)
        self.by_tax = by_tax or []  # workspace_clients tax_id 精确
        self.by_name = by_name or []  # workspace_clients name 精确
        self._mode = None

    def execute(self, sql, params=None):
        if "seller_workspace_routes" in sql:
            self._mode = "route"
        elif "WHERE id = %s" in sql:
            self._mode = "by_id"
        elif "REPLACE(REPLACE(COALESCE(tax_id" in sql:
            self._mode = "by_tax"
        elif "LOWER(TRIM(name))" in sql:
            self._mode = "by_name"
        else:
            self._mode = None

    def fetchone(self):
        return self.route if self._mode == "route" else None

    def fetchall(self):
        return {"by_id": self.by_id, "by_tax": self.by_tax, "by_name": self.by_name}.get(
            self._mode, []
        )


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def _patch(cur):
    return mock.patch.object(store.db, "get_cursor", lambda *a, **k: _CM(cur))


WS_BOUND = {"id": 10, "name": "卖方A", "erp_endpoint_id": "ep-A"}
WS_UNBOUND = {"id": 11, "name": "卖方B", "erp_endpoint_id": None}


class MatchWorkspaceForSellerTests(unittest.TestCase):
    def _match(self, cur, tax="0105500000001", name="卖方A"):
        with _patch(cur):
            return store.match_workspace_for_seller(tax, name, user_id="u1", tenant_id="t1")

    def test_route_memory_hit_assigned(self):
        # 路由记忆命中 → 载入该 workspace(已绑 endpoint)→ assigned
        cur = KeywordCursor(route={"workspace_client_id": 10}, by_id=[WS_BOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["workspace_client_id"], 10)
        self.assertEqual(d["endpoint_id"], "ep-A")
        self.assertEqual(d["match_source"], "route_memory")

    def test_route_memory_points_to_deleted_ws_falls_through_to_tax(self):
        # 记忆指向的 workspace 已删/停用(by_id 空)→ 退回税号直配
        cur = KeywordCursor(route={"workspace_client_id": 99}, by_id=[], by_tax=[WS_BOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["match_source"], "seller_tax")

    def test_tax_exact_unique_bound_assigned(self):
        cur = KeywordCursor(by_tax=[WS_BOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["endpoint_id"], "ep-A")

    def test_tax_unique_unbound_endpoint(self):
        # 唯一命中但 workspace 没绑 ERP → unbound 异常(不能推)
        cur = KeywordCursor(by_tax=[WS_UNBOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "unbound")
        self.assertEqual(d["workspace_client_id"], 11)
        self.assertIsNone(d["endpoint_id"])

    def test_tax_multi_candidate(self):
        cur = KeywordCursor(by_tax=[WS_BOUND, WS_UNBOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "multi")
        self.assertIsNone(d["workspace_client_id"])

    def test_name_exact_when_no_tax_match(self):
        # 税号不命中 → 名字精确命中
        cur = KeywordCursor(by_tax=[], by_name=[WS_BOUND])
        d = self._match(cur)
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["match_source"], "seller_name")

    def test_no_match_none(self):
        cur = KeywordCursor()
        d = self._match(cur)
        self.assertEqual(d["action"], "none")

    def test_invalid_tax_skips_tax_layer(self):
        # 税号非法(短)→ 不走税号 · 名字命中
        cur = KeywordCursor(by_name=[WS_BOUND])
        with _patch(cur):
            d = store.match_workspace_for_seller("123", "卖方A", user_id="u1", tenant_id="t1")
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["match_source"], "seller_name")


class RouteAssignsWorkspaceTests(unittest.TestCase):
    """归属覆盖决策(persist 用):命中具体主体才覆盖;none/multi 不覆盖(保留 insert 归属·不清 NULL)。

    回归 2026-06-22 真机事故:采购票卖方≠自家 → match=none → 旧码用 None 回写清空
    workspace_client_id → Express 方向判定失锚 → direction_unknown。
    """

    def test_assigned_returns_id(self):
        self.assertEqual(
            store.route_assigns_workspace({"action": "assigned", "workspace_client_id": 10}), 10
        )

    def test_unbound_returns_id(self):
        self.assertEqual(
            store.route_assigns_workspace({"action": "unbound", "workspace_client_id": 11}), 11
        )

    def test_none_returns_none_no_clobber(self):
        # 没命中 → None → 调用方保留 insert 归属,绝不回写 NULL
        self.assertIsNone(store.route_assigns_workspace({"action": "none"}))

    def test_multi_returns_none_no_clobber(self):
        self.assertIsNone(
            store.route_assigns_workspace({"action": "multi", "workspace_client_id": None})
        )

    def test_empty_or_missing_action_returns_none(self):
        self.assertIsNone(store.route_assigns_workspace(None))
        self.assertIsNone(store.route_assigns_workspace({}))


if __name__ == "__main__":
    unittest.main()
