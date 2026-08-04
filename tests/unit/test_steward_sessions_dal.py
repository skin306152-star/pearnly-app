# -*- coding: utf-8 -*-
"""会话列表/改名/删除与消息游标分页 DAL(services/steward/sessions_dal.py)。

锁:①列表 SQL 过滤零消息空会话且带 (tenant, user) 双锚;②改名/删除只认本人且
rowcount 说了算;③删除先收 file_ref 再删行(文件删除在提交后,由路由层执行);
④分页取 limit+1 判 has_more、升序返回、坏游标按无游标处理不报错。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from services.steward import sessions_dal


class RecordingCur:
    """记录 execute 的 SQL 与参数;fetch 序列按调用顺序弹出。"""

    def __init__(self, results=None, rowcount=1):
        self.calls = []
        self._results = list(results or [])
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def _pop(self):
        return self._results.pop(0) if self._results else []

    def fetchall(self):
        return self._pop()

    def fetchone(self):
        rows = self._pop()
        return rows[0] if rows else None


def _msg(i, ts):
    return {"id": f"m{i}", "created_at": ts, "role": "user", "text": f"t{i}"}


class ListSessionsTests(unittest.TestCase):
    def test_sql_filters_empty_sessions_and_scopes_to_owner(self):
        cur = RecordingCur(results=[[{"id": "s1", "title": "对账"}]])
        rows = sessions_dal.list_sessions(cur, tenant_id="t-1", user_id="u1", limit=10)
        sql, params = cur.calls[0]
        self.assertIn("EXISTS", sql)
        self.assertIn("steward_messages", sql)
        self.assertIn("ORDER BY s.last_active_at DESC", sql)
        self.assertEqual(params, ("t-1", "u1", 10))
        self.assertEqual(rows[0]["id"], "s1")


class RenameDeleteTests(unittest.TestCase):
    def test_rename_clamps_to_120_and_reports_rowcount(self):
        cur = RecordingCur(rowcount=1)
        ok = sessions_dal.rename_session(
            cur, tenant_id="t-1", session_id="s-1", user_id="u1", title="标" * 200
        )
        self.assertTrue(ok)
        _sql, params = cur.calls[0]
        self.assertEqual(len(params[0]), 120)
        self.assertEqual(params[1:], ("t-1", "s-1", "u1"))

    def test_rename_missing_session_is_false(self):
        cur = RecordingCur(rowcount=0)
        self.assertFalse(
            sessions_dal.rename_session(
                cur, tenant_id="t-1", session_id="s-x", user_id="u1", title="改名"
            )
        )

    def test_delete_collects_file_refs_before_deleting_rows(self):
        cur = RecordingCur(results=[[{"file_ref": "/a/1.bin"}, {"file_ref": ""}]], rowcount=1)
        refs = sessions_dal.delete_session(cur, tenant_id="t-1", session_id="s-1", user_id="u1")
        self.assertEqual(refs, ["/a/1.bin"])
        select_sql = cur.calls[0][0]
        delete_sql = cur.calls[1][0]
        self.assertIn("SELECT file_ref", select_sql)
        self.assertIn("DELETE FROM steward_sessions", delete_sql)
        self.assertEqual(cur.calls[1][1], ("t-1", "s-1", "u1"))

    def test_delete_someone_elses_session_returns_none(self):
        cur = RecordingCur(results=[[]], rowcount=0)
        self.assertIsNone(
            sessions_dal.delete_session(cur, tenant_id="t-1", session_id="s-1", user_id="u2")
        )


class MessagesPageTests(unittest.TestCase):
    _TS = datetime(2026, 8, 5, 3, 0, tzinfo=timezone.utc)

    def test_first_page_returns_ascending_and_reports_more(self):
        # DESC 取回 limit+1 行 = 还有更早的;返回按时间升序、多取的那行不外泄。
        rows = [_msg(3, self._TS), _msg(2, self._TS), _msg(1, self._TS)]
        cur = RecordingCur(results=[rows])
        page, has_more = sessions_dal.list_messages_page(
            cur, tenant_id="t-1", session_id="s-1", limit=2
        )
        self.assertTrue(has_more)
        self.assertEqual([m["id"] for m in page], ["m2", "m3"])
        sql, params = cur.calls[0]
        self.assertIn("ORDER BY created_at DESC, id DESC", sql)
        self.assertEqual(params[-1], 3)  # limit + 1

    def test_last_page_has_no_more(self):
        cur = RecordingCur(results=[[_msg(1, self._TS)]])
        page, has_more = sessions_dal.list_messages_page(
            cur, tenant_id="t-1", session_id="s-1", limit=2
        )
        self.assertFalse(has_more)
        self.assertEqual(len(page), 1)

    def test_cursor_anchors_on_created_at_and_id(self):
        anchor = [{"created_at": self._TS, "id": "m5"}]
        cur = RecordingCur(results=[anchor, [_msg(4, self._TS)]])
        sessions_dal.list_messages_page(
            cur, tenant_id="t-1", session_id="s-1", before_id="m5", limit=2
        )
        sql, params = cur.calls[1]
        self.assertIn("(created_at, id) < (%s, %s)", sql)
        self.assertEqual(params[2], self._TS)
        self.assertEqual(params[3], "m5")

    def test_broken_cursor_falls_back_to_latest_page(self):
        # 游标指向不存在的消息(被删/伪造):按无游标处理,不报错。
        cur = RecordingCur(results=[[], [_msg(1, self._TS)]])
        page, has_more = sessions_dal.list_messages_page(
            cur, tenant_id="t-1", session_id="s-1", before_id="ghost", limit=2
        )
        self.assertFalse(has_more)
        sql, _params = cur.calls[1]
        self.assertNotIn("(created_at, id) <", sql)


class PublicSessionTests(unittest.TestCase):
    def test_projection_keeps_empty_title_empty(self):
        # title 还没落(建了会话没说话):给空串,由前端按「新对话」词条显示。
        ts = datetime(2026, 8, 5, 3, 0, tzinfo=timezone.utc)
        out = sessions_dal.public_session({"id": "s1", "title": None, "last_active_at": ts})
        self.assertEqual(out, {
            "session_id": "s1",
            "title": "",
            "last_active_at": ts.isoformat(),
        })  # fmt: skip


if __name__ == "__main__":
    unittest.main()
