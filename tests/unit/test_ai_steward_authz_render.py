#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_steward_authz_render.py

智能管家(B3 · 前端)写授权卡 + 成本封顶纯函数守门:
  1. 卡状态四值闭集 → B1 色族(pending 橙 / approved 绿 / rejected 红 / expired 灰),
     契约外落空白族;风险二值,契约外按 danger 兜底(淡化风险 = 放行风险)。
  2. 倒计时:remainingMs 对过期/垃圾输入一律钳 0,countdownLabel 出 m:ss。
  3. 参数行:平面对象按键序展开成字符串行,非对象输入回空(不渲染半张假表)。
  4. 决断错误码 → 词条闭集(404/403/409 六码各有各的话,未知落 err_generic)。
  5. 预算 code 判别:只认契约两码;会话级才有「开新会话」出口。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_AUTHZ = json.dumps(str(AI_DIR / "ai-steward-authz-render.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AuthzCardPureTests(unittest.TestCase):
    def test_status_families_match_contract_and_unknown_falls_to_empty(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify({{
                pairs: a.AUTHZ_STATUSES.map((s) => [s, a.authzFamily(s)]),
                unknown: a.authzFamily('bogus'),
                keys: [a.authzStatusKey('pending'), a.authzStatusKey('bogus')],
            }}));
            """)
        self.assertEqual(
            out["pairs"],
            [["pending", "warn"], ["approved", "ok"], ["rejected", "err"], ["expired", "off"]],
        )
        self.assertEqual(out["unknown"], "empty")
        self.assertEqual(out["keys"], ["stw_authz_pending", "stw_authz_unknown"])

    def test_risk_defaults_to_danger_when_out_of_contract(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify([
                a.riskFamily('write'), a.riskKey('write'),
                a.riskFamily('danger'), a.riskKey('danger'),
                a.riskFamily('bogus'), a.riskKey(undefined),
            ]));
            """)
        # 未知风险按 danger 兜底:写授权卡上宁可吓人,不给一张被淡化的卡。
        self.assertEqual(
            out,
            [
                "warn",
                "stw_authz_risk_write",
                "err",
                "stw_authz_risk_danger",
                "err",
                "stw_authz_risk_danger",
            ],
        )

    def test_remaining_ms_clamps_past_and_garbage_to_zero(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            const now = Date.parse('2026-07-27T10:00:00+00:00');
            process.stdout.write(JSON.stringify([
                a.remainingMs('2026-07-27T10:04:59+00:00', now),
                a.remainingMs('2026-07-27T09:59:00+00:00', now),
                a.remainingMs('not-a-date', now),
                a.remainingMs(null, now),
            ]));
            """)
        self.assertEqual(out, [299000, 0, 0, 0])

    def test_countdown_label_is_minutes_colon_seconds(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify([
                a.countdownLabel(299000), a.countdownLabel(61000),
                a.countdownLabel(0), a.countdownLabel(-5), a.countdownLabel(NaN),
            ]));
            """)
        self.assertEqual(out, ["4:59", "1:01", "0:00", "0:00", "0:00"])

    def test_arg_entries_flatten_object_and_reject_non_objects(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify([
                a.argEntries({{ client: 'SM', period: '2569-06', n: 3 }}),
                a.argEntries(null), a.argEntries('x'), a.argEntries([1]),
            ]));
            """)
        self.assertEqual(
            out[0],
            [
                {"k": "client", "v": "SM"},
                {"k": "period", "v": "2569-06"},
                {"k": "n", "v": "3"},
            ],
        )
        self.assertEqual(out[1:], [[], [], []])

    def test_decide_error_codes_map_to_their_own_copy(self):
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify([
                a.decideErrKey('steward.authz_expired'), a.decideErrKey('steward.authz_used'),
                a.decideErrKey('steward.authz_stale'), a.decideErrKey('steward.authz_mismatch'),
                a.decideErrKey('authz.forbidden'), a.decideErrKey('steward.not_found'),
                a.decideErrKey('something-else'), a.decideErrKey(undefined),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "stw_authz_err_expired",
                "stw_authz_err_used",
                "stw_authz_err_stale",
                "stw_authz_err_mismatch",
                "stw_authz_err_forbidden",
                "stw_authz_err_notfound",
                "err_generic",
                "err_generic",
            ],
        )

    def test_budget_codes_closed_set_and_session_only_gets_exit(self):
        # 租户日额级也进数字块闭集,但「开新会话」出口只属于会话级 —— 新会话绕不过日额顶。
        out = _run_node(f"""
            const a = require({_AUTHZ});
            process.stdout.write(JSON.stringify([
                a.isBudgetCode('steward.budget_session_exceeded'),
                a.isBudgetCode('steward.budget_task_exceeded'),
                a.isBudgetCode('steward.budget_tenant_exceeded'),
                a.isBudgetCode('steward.timeout'), a.isBudgetCode(undefined),
                a.isSessionBudget('steward.budget_session_exceeded'),
                a.isSessionBudget('steward.budget_task_exceeded'),
                a.isSessionBudget('steward.budget_tenant_exceeded'),
            ]));
            """)
        self.assertEqual(out, [True, True, True, False, False, True, False, False])


if __name__ == "__main__":
    unittest.main()
