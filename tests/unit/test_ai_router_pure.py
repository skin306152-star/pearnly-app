#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_router_pure.py

导航三门 P0-2(全站深链丢账期)守门测试:ai-router.js 的 buildClientHash 第三参 period
往返 parseHash 拿得回来;缺省 period 不追加查询串(不破坏一路吃 "#/client/<id>/<view>"
形状的既有调用点);其余路由(dashboard/clients/reports 等)不受 P0-2 的查询串切分影响。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_ROUTER = json.dumps(str(AI_DIR / "ai-router.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BuildClientHashPeriodTests(unittest.TestCase):
    def test_period_appends_query_string(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify(r.buildClientHash('42', 'wo', '2569-06')));
            """)
        self.assertEqual(out, "#/client/42/wo?period=2569-06")

    def test_missing_period_keeps_bare_hash(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify([
                r.buildClientHash('42', 'wo'),
                r.buildClientHash('42', 'wo', ''),
                r.buildClientHash('42', 'wo', null),
            ]));
            """)
        self.assertEqual(out, ["#/client/42/wo", "#/client/42/wo", "#/client/42/wo"])

    def test_period_survives_special_characters(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify(r.buildClientHash('42', 'wo', '2569-06&x=1')));
            """)
        self.assertEqual(out, "#/client/42/wo?period=2569-06%26x%3D1")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ParseHashPeriodRoundtripTests(unittest.TestCase):
    def test_build_then_parse_recovers_period(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            const hash = r.buildClientHash('42', 'wo', '2569-06');
            process.stdout.write(JSON.stringify(r.parseHash(hash)));
            """)
        self.assertEqual(
            out, {"name": "client", "clientId": "42", "view": "wo", "period": "2569-06"}
        )

    def test_no_period_parses_to_null_not_swallowing_view(self):
        # P0-2 根因回归:切分查询串之前,view 段的正则会把 "wo?period=x" 整段当非法值
        # 落回默认 view——这里锁住"没带 period 时 view 仍精确解析"。
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify(r.parseHash('#/client/42/review')));
            """)
        self.assertEqual(
            out, {"name": "client", "clientId": "42", "view": "review", "period": None}
        )

    def test_other_routes_unaffected_by_query_split(self):
        out = _run_node(f"""
            const r = require({_ROUTER});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/clients'), r.parseHash('#/reports'), r.parseHash('#/'),
            ]));
            """)
        self.assertEqual(
            out,
            [{"name": "clients"}, {"name": "reports"}, {"name": "dashboard", "sub": "matrix"}],
        )


if __name__ == "__main__":
    unittest.main()
