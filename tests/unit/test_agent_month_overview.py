# -*- coding: utf-8 -*-
"""本月聚合数据层(_ov)+ 共用可见性谓词(owner_visibility_where)。"""

import unittest
from unittest.mock import MagicMock, patch

from services.ocr_history import agent_overview
from services.ocr_history import list_status as ls

_ov = agent_overview.docs_overview


class TestOwnerVisibilityWhere(unittest.TestCase):
    def test_tenant_scope(self):
        where, params = ls.owner_visibility_where("u1", "t1", None, None)
        self.assertIn("user_id IN (SELECT id FROM users WHERE tenant_id = %s)", where[0])
        self.assertEqual(params, ["t1"])
        self.assertIn("staged = FALSE", where)

    def test_self_scope_no_tenant(self):
        where, params = ls.owner_visibility_where("u1", None, None, None)
        self.assertEqual(where[0], "user_id = %s")
        self.assertEqual(params, ["u1"])

    def test_workspace_and_restrict(self):
        where, params = ls.owner_visibility_where("u1", "t1", 9, [3, 4])
        joined = " ".join(where)
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", joined)
        self.assertIn("client_id = ANY(%s::bigint[])", joined)
        self.assertIn(9, params)
        self.assertIn([3, 4], params)

    def test_restrict_empty_only_own_unassigned(self):
        where, _ = ls.owner_visibility_where("u1", "t1", None, [])
        self.assertIn("(user_id = %s AND client_id IS NULL)", " ".join(where))

    def test_excludes_workorder_ledger_rows_from_aggregations(self):
        # MC2-A2 ②:工单台账行(source=workorder_classify)不进主站识别聚合(月报/概览/画像/
        # 提醒/召回共用此谓词)。黑名单只挡工单行,NULL/其它 source 全放行(IS DISTINCT FROM)。
        where, _ = ls.owner_visibility_where("u1", "t1", 9, None)
        self.assertIn("source IS DISTINCT FROM 'workorder_classify'", where)


class TestMonthOverview(unittest.TestCase):
    def _cursor(self, fetchone, fetchall=None):
        cur = MagicMock()
        cur.fetchone.return_value = fetchone
        cur.fetchall.return_value = fetchall or []
        return cur

    @patch("services.ocr_history.agent_overview.db")
    def test_aggregates_count_sum_categories(self, db):
        cur = self._cursor(
            {"doc_count": 5, "amount_total": 1500.5},
            [{"category_tag": "fuel", "c": 3}, {"category_tag": "food", "c": 2}],
        )
        db.get_cursor_rls.return_value.__enter__.return_value = cur
        out = _ov("u1", "t1")
        self.assertEqual(out["doc_count"], 5)
        self.assertEqual(out["amount_total"], 1500.5)
        self.assertEqual(out["by_category"], [("fuel", 3), ("food", 2)])

    @patch("services.ocr_history.agent_overview.db")
    def test_include_categories_false_skips_group_query(self, db):
        cur = self._cursor({"doc_count": 2, "amount_total": 0})
        db.get_cursor_rls.return_value.__enter__.return_value = cur
        out = _ov("u1", "t1", include_categories=False)
        self.assertEqual(out["by_category"], [])
        cur.fetchall.assert_not_called()

    @patch("services.ocr_history.agent_overview.db")
    def test_zero_docs_skips_group_query(self, db):
        cur = self._cursor({"doc_count": 0, "amount_total": 0})
        db.get_cursor_rls.return_value.__enter__.return_value = cur
        out = _ov("u1", "t1")
        self.assertEqual(out["by_category"], [])
        cur.fetchall.assert_not_called()

    def test_retention_zero_returns_empty_without_db(self):
        # 不可查历史(retention==0)→ 不碰 DB,返空。
        out = _ov("u1", "t1", retention_days=0)
        self.assertEqual(out, {"doc_count": 0, "amount_total": 0.0, "by_category": []})

    @patch("services.ocr_history.agent_overview.db")
    def test_db_error_degrades_to_empty(self, db):
        db.get_cursor_rls.side_effect = RuntimeError("boom")
        out = _ov("u1", "t1")
        self.assertEqual(out["doc_count"], 0)
        self.assertEqual(out["by_category"], [])


if __name__ == "__main__":
    unittest.main()
