# -*- coding: utf-8 -*-
"""LINE 会话态当前套账:读/回落/模糊匹配/切换写入。"""

import unittest
from unittest.mock import MagicMock

from services.line_binding import line_workspace as lw


def _cur(fetchone=None, fetchall=None, rowcount=1):
    cur = MagicMock()
    cur.fetchone.return_value = fetchone
    cur.fetchall.return_value = fetchall or []
    cur.rowcount = rowcount
    return cur


class TestLineWorkspace(unittest.TestCase):
    def test_current_none_when_unset(self):
        cur = _cur(fetchone={"current_workspace_client_id": None})
        self.assertIsNone(lw.current_workspace_id(cur, line_user_id="U"))

    def test_current_returns_int(self):
        cur = _cur(fetchone={"current_workspace_client_id": 84})
        self.assertEqual(lw.current_workspace_id(cur, line_user_id="U"), 84)

    def test_resolve_falls_back_to_default(self):
        # 未选当前套账 → 回落 default_workspace_id。
        cur = _cur(fetchone={"current_workspace_client_id": None})
        with unittest.mock.patch("core.workspace_context.default_workspace_id", return_value=69):
            self.assertEqual(lw.resolve_write_workspace(cur, tenant_id="t", line_user_id="U"), 69)

    def test_match_by_name_unique_substring(self):
        cur = _cur(
            fetchall=[
                {"id": 84, "name": "บริษัท มานะชัยบริการ จำกัด"},
                {"id": 72, "name": "บริษัท สยามวัสดุก่อสร้าง จำกัด"},
            ]
        )
        hit = lw.match_by_name(cur, tenant_id="t", name="สยาม")
        self.assertEqual(hit["id"], 72)

    def test_match_by_name_ambiguous_returns_none(self):
        cur = _cur(fetchall=[{"id": 1, "name": "Earn A"}, {"id": 2, "name": "Earn B"}])
        self.assertIsNone(lw.match_by_name(cur, tenant_id="t", name="earn"))

    def test_set_current_reports_hit(self):
        cur = _cur(rowcount=1)
        self.assertTrue(lw.set_current(cur, line_user_id="U", workspace_client_id=84))

    def test_set_current_miss_when_no_binding(self):
        cur = _cur(rowcount=0)
        self.assertFalse(lw.set_current(cur, line_user_id="U", workspace_client_id=84))


if __name__ == "__main__":
    unittest.main()
