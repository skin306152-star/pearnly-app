#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_route_contract_fakes.py

工单路由契约测试的假件四件套(照 _workorder_fakes.py 先例,下划线文件名不进 unittest
discovery):FakeCur(execute 吞参,fetchone/fetchall 回预置)+ CurCM(with 语义)+
FakeDB(get_cursor 恒回同一游标)+ route_set(router 注册面快照)。此前
test_workorder_routes_contract / test_workorder_review_routes_contract /
test_workorder_financials_routes_contract / test_workorder_deliverable_filename_contract
四个文件各抄一份,收到这里;文件级特殊需求(如 get_workspace_client 桩)由子类补。
"""

from __future__ import annotations

_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


class FakeCur:
    """契约测试假游标:fetch 是 fetchone 的固定返回(None = 归属查询落空),rows 喂 fetchall。"""

    def __init__(self, fetch=(1,), rows=()):
        self._fetch = fetch
        self._rows = list(rows)

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._fetch

    def fetchall(self):
        return list(self._rows)


class CurCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class FakeDB:
    def __init__(self, cur=None):
        self._cur = cur if cur is not None else FakeCur()

    def get_cursor(self, commit=False):
        return CurCM(self._cur)


def route_set(router):
    """router 的 (method, path) 注册面快照,供契约测试断言端点齐全。"""
    out = set()
    for r in router.routes:
        for m in getattr(r, "methods", set()) or set():
            if m in _METHODS:
                out.add((m, r.path))
    return out
