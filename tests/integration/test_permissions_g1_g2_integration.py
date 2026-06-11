#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""权限完善 G1/G2 真库 E2E(docs/permissions/07 §五 V4/V5 · 窗口①)。

env-gated:无 DB / 无测试账号 = clean skip(不让 CI 红)。本地 / staging 跑前:
    export PEARNLY_INTEGRATION_DB=1
    export DATABASE_URL=postgresql://...
    export PEARNLY_E2E_USER=... PEARNLY_E2E_PASS=...

V4 席位:邀请填满 → 422 team.seat_limit → 撤回一个 → 可再邀(全程自清理)。
V5 安全日志:类型筛选结果正确 / 游标分页不重不漏 / CSV 带 BOM 表头(泰文不乱码)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration._helpers import (  # noqa: E402
    auth_header,
    get_test_client,
    login_for_token,
    mock_gmail_smtp,
    require_db,
    require_test_user,
)


class _TeamE2EBase(unittest.TestCase):
    def setUp(self) -> None:
        require_db()
        creds = require_test_user()
        self.client = get_test_client()
        self.token = login_for_token(
            self.client, creds["PEARNLY_E2E_USER"], creds["PEARNLY_E2E_PASS"]
        )
        self.h = auth_header(self.token)
        self._created_invites: list[str] = []

    def tearDown(self) -> None:
        # 自清理:撤回本测试建的全部邀请,恢复席位 / 日志环境
        for iid in getattr(self, "_created_invites", []):
            with mock_gmail_smtp():
                self.client.delete(f"/api/team/invitations/{iid}", headers=self.h)

    def _seat_state(self) -> dict:
        resp = self.client.get("/api/team/members", headers=self.h)
        self.assertEqual(resp.status_code, 200, msg=resp.text[:300])
        return resp.json()

    def _invite(self, target: str) -> "tuple[int, dict]":
        with mock_gmail_smtp():
            resp = self.client.post(
                "/api/team/invitations",
                headers=self.h,
                json={"channel": "email", "target": target, "role_key": "viewer"},
            )
        body = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        if resp.status_code == 200 and body.get("id"):
            self._created_invites.append(body["id"])
        return resp.status_code, body


class SeatLimitE2E(_TeamE2EBase):
    """V4:席位满 422 → 撤回 → 可再邀。"""

    def test_seat_limit_enforced_then_revoke_reinvite(self) -> None:
        state = self._seat_state()
        seats_max = int(state.get("seats_max") or 0)
        if seats_max <= 0 or seats_max >= 999999:
            self.skipTest(f"测试租户席位上限不适合本用例(seats_max={seats_max})")
        used = int(state.get("seats_used") or state.get("total") or 0)
        available = seats_max - used
        if available > 20:
            self.skipTest(f"剩余席位过多({available})· 跳过以免造大量数据")

        # 填满剩余席位
        for i in range(max(0, available)):
            code, _ = self._invite(f"seat-fill-{i}@pearnly.test")
            self.assertEqual(code, 200, msg=f"填席第 {i} 个应成功")

        # 满员:下一个邀请被拦
        code, body = self._invite("seat-over@pearnly.test")
        self.assertEqual(code, 422, msg=f"满员应 422 · 实得 {code}:{body}")
        self.assertEqual(body.get("detail"), "team.seat_limit")

        if not self._created_invites:
            self.skipTest("起始即满且无本测试可撤回的邀请 · 已验 422 拦截")

        # 撤回一个 pending → 释放一席
        freed = self._created_invites.pop()
        del_resp = self.client.delete(f"/api/team/invitations/{freed}", headers=self.h)
        self.assertEqual(del_resp.status_code, 200, msg=del_resp.text[:200])

        # 现在可再邀
        code, body = self._invite("seat-reinvite@pearnly.test")
        self.assertEqual(code, 200, msg=f"撤回后应可再邀 · 实得 {code}:{body}")


class SecurityEventsE2E(_TeamE2EBase):
    """V5:筛选 / 游标分页 / CSV 导出。"""

    def _events(self, query: str = "") -> dict:
        resp = self.client.get(f"/api/team/security-events{query}", headers=self.h)
        self.assertEqual(resp.status_code, 200, msg=resp.text[:300])
        return resp.json()

    def test_filter_paginate_and_csv_export(self) -> None:
        # 造一条 team.* 事件保证非空
        code, _ = self._invite("evt-seed@pearnly.test")
        if code != 200:
            self.skipTest("无法造邀请事件(可能席位满)· 筛选用例跳过")

        # 类型筛选:type=team → 全部 action 以 team. 开头
        data = self._events("?type=team&limit=50")
        self.assertIn("events", data)
        self.assertIn("next_cursor", data)
        self.assertTrue(
            all(str(e.get("action") or "").startswith("team.") for e in data["events"]),
            msg=f"type=team 不应混入他域:{[e.get('action') for e in data['events']]}",
        )

        # 游标分页不重不漏:limit=1 取首页 → 跟随 cursor 取次页 · id 不重叠
        page1 = self._events("?limit=1")
        if page1.get("next_cursor") and page1["events"]:
            page2 = self._events(f"?limit=1&cursor={page1['next_cursor']}")
            ids1 = {e.get("id") for e in page1["events"]}
            ids2 = {e.get("id") for e in page2["events"]}
            self.assertFalse(ids1 & ids2, msg="游标分页出现重复事件")

        # CSV 导出:带 BOM + 表头(Excel 泰文不乱码)
        exp = self.client.get("/api/team/security-events/export?type=team", headers=self.h)
        self.assertEqual(exp.status_code, 200, msg=exp.text[:200])
        self.assertIn("text/csv", exp.headers.get("content-type", ""))
        text = exp.content.decode("utf-8-sig")  # utf-8-sig 吃掉 BOM
        self.assertTrue(exp.content.startswith(b"\xef\xbb\xbf"), msg="CSV 缺 UTF-8 BOM")
        self.assertTrue(text.splitlines()[0].startswith("created_at,action"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
