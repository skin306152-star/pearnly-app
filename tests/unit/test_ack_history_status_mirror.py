# -*- coding: utf-8 -*-
"""ack 把推送终态镜像回 ocr_history 的守门。

原先 ack 只改 erp_push_logs,单据记录那边永远停在入队时的 'pending'。真跑实测:
推过的 69 条里 30 条卡 pending,实际早就成功了。后果两条:用户看到"还没推"会再推
一次造重复单;导出的状态列照抄假状态,会计据此去 ERP 删单就删错。
"""

import unittest
from unittest import mock

from services.erp.express_push import agent_store as st


class FakeCursor:
    """只记录 UPDATE 打到哪张表 · 不碰真库。"""

    def __init__(self, log_row):
        self._log = log_row
        self.history_updates = []

    def execute(self, sql, params=None):
        s = " ".join(str(sql).split())
        if "UPDATE ocr_history" in s:
            self.history_updates.append((params[0], str(params[1])))
        self._last = s

    def fetchone(self):
        return self._log

    def fetchall(self):
        return []


class _Ctx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def _run(outcome, *, status="pending", attempt=1, history_id="hid-1", success=False):
    log = {
        "id": "log-1",
        "status": status,
        "attempt": attempt,
        "lease_owner": "owner-1",
        "response_body": None,
        "history_id": history_id,
    }
    cur = FakeCursor(log)
    with mock.patch("core.db.get_cursor", return_value=_Ctx(cur)):
        res = st.ack("ep-1", "log-1", "owner-1", success, outcome=outcome, express_docnum="D1")
    return res, cur


class MirrorTests(unittest.TestCase):
    def test_success_mirrors_to_history(self):
        res, cur = _run("success", success=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(cur.history_updates, [("success", "hid-1")])

    def test_needs_review_mirrors_manual(self):
        res, cur = _run("needs_review")
        self.assertEqual(res["status"], "manual")
        self.assertEqual(cur.history_updates, [("manual", "hid-1")])

    def test_needs_mapping_mirrors_manual(self):
        _res, cur = _run("needs_mapping")
        self.assertEqual(cur.history_updates, [("manual", "hid-1")])

    def test_waiting_lock_does_not_mirror(self):
        """Express 占用账套 → 还会重领,记录确实还在排队。写成失败是撒谎。"""
        res, cur = _run("waiting_lock")
        self.assertEqual(res["status"], "pending")
        self.assertEqual(cur.history_updates, [])

    def test_retryable_failure_does_not_mirror(self):
        """第 1 次失败还会重试 —— 保持 pending 才诚实。"""
        res, cur = _run("failed", attempt=1)
        self.assertEqual(res["status"], "pending")
        self.assertEqual(cur.history_updates, [])

    def test_exhausted_failure_mirrors_manual(self):
        """重试用尽转人工 —— 这才是终态,必须让记录也跟上。"""
        res, cur = _run("failed", attempt=st._MAX_ATTEMPTS)
        self.assertEqual(res["status"], "manual")
        self.assertEqual(cur.history_updates, [("manual", "hid-1")])

    def test_no_history_id_is_a_noop_not_a_crash(self):
        """有些推送不挂单据记录(手工补推等)· 不该因此让 ack 失败。"""
        res, cur = _run("success", success=True, history_id=None)
        self.assertEqual(res["status"], "success")
        self.assertEqual(cur.history_updates, [])


class LoadedColumnsTests(unittest.TestCase):
    def test_owned_log_query_selects_history_id(self):
        """history_id 不在 SELECT 里,镜像就永远拿到 None、一次也不触发(改的时候踩过)。"""
        import inspect

        src = inspect.getsource(st._load_owned_log)
        self.assertIn("history_id", src)


if __name__ == "__main__":
    unittest.main()
