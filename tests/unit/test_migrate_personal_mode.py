# -*- coding: utf-8 -*-
"""个人模式 → 个人主体迁移脚本单测(scripts/migrate_personal_mode_to_subject.py)。

锁定:候选识别 → 建 personal 主体 → 回填 NULL-workspace 历史(不丢)· dry-run 零写 ·
幂等(无候选/已有主体 → 不重复建)· 名称兜底。全用脚本化 FakeCursor,不打真实 DB。
"""

import importlib.util
import os
import unittest

_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "migrate_personal_mode_to_subject.py"
)
_spec = importlib.util.spec_from_file_location("migrate_personal_mode_to_subject", _PATH)
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)


class ScriptedCursor:
    """按 SQL 子串分流返回的假游标(migrate 全程吃 cur · 不连库)。"""

    def __init__(
        self,
        tenant_candidates=None,
        user_candidates=None,
        owners=None,
        existing_personal=None,
        insert_id=500,
        backfill_count=0,
    ):
        self.tenant_candidates = tenant_candidates or []
        self.user_candidates = user_candidates or []
        self.owners = owners or {}
        self.existing_personal = existing_personal
        self._insert_id = insert_id
        self.backfill_count = backfill_count
        self.executed = []
        self._last = ""
        self._last_params = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last = sql
        self._last_params = params
        if "UPDATE ocr_history" in sql:
            self.rowcount = self.backfill_count

    def fetchall(self):
        if "GROUP BY oh.tenant_id" in self._last:
            return [dict(r) for r in self.tenant_candidates]
        if "GROUP BY oh.user_id" in self._last:
            return [dict(r) for r in self.user_candidates]
        return []

    def fetchone(self):
        s = self._last
        if "FROM users" in s:
            return self.owners.get(self._last_params[0])
        if "SELECT id FROM workspace_clients" in s and "subject_type = 'personal'" in s:
            return {"id": self.existing_personal} if self.existing_personal else None
        if "INSERT INTO workspace_clients" in s:
            return {"id": self._insert_id}
        return None

    def all_sql(self):
        return " | ".join(e[0] for e in self.executed)


class NameTests(unittest.TestCase):
    def test_personal_name_fallback_chain(self):
        self.assertEqual(mig.personal_name({"company_name": "Acme"}), "Acme")
        self.assertEqual(mig.personal_name({"company_name": "", "email": "bob@x.com"}), "bob")
        self.assertEqual(
            mig.personal_name({"company_name": "", "email": ""}), mig.DEFAULT_PERSONAL_NAME
        )
        self.assertEqual(mig.personal_name(None), mig.DEFAULT_PERSONAL_NAME)


class DryRunTests(unittest.TestCase):
    def test_dry_run_reports_but_writes_nothing(self):
        cur = ScriptedCursor(tenant_candidates=[{"tenant_id": "T1", "null_ocr_count": 3}])
        report = mig.migrate(cur, apply=False)
        self.assertEqual(report["tenant_candidates"], 1)
        self.assertEqual(report["subjects_created"], 0)
        self.assertNotIn("INSERT INTO workspace_clients", cur.all_sql())
        self.assertNotIn("UPDATE ocr_history", cur.all_sql())


class ApplyTests(unittest.TestCase):
    def test_creates_personal_subject_and_backfills_history(self):
        cur = ScriptedCursor(
            tenant_candidates=[{"tenant_id": "T1", "null_ocr_count": 3}],
            owners={"T1": {"id": "U1", "company_name": "Acme", "email": "a@b.com"}},
            existing_personal=None,
            insert_id=500,
            backfill_count=3,
        )
        report = mig.migrate(cur, apply=True)
        self.assertEqual(report["subjects_created"], 1)
        self.assertEqual(report["history_backfilled"], 3)
        self.assertIn("INSERT INTO workspace_clients", cur.all_sql())
        # 回填 UPDATE 用新主体 id 归属该租户仍为 NULL 的历史(不丢)
        updates = [(s, p) for (s, p) in cur.executed if "UPDATE ocr_history" in s]
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0][1][0], 500)  # subject_id 第一个参数
        self.assertEqual(updates[0][1][1], "T1")  # tenant scope

    def test_idempotent_no_candidates_is_noop(self):
        cur = ScriptedCursor(tenant_candidates=[], user_candidates=[])
        report = mig.migrate(cur, apply=True)
        self.assertEqual(report["subjects_created"], 0)
        self.assertEqual(report["history_backfilled"], 0)
        self.assertNotIn("INSERT INTO workspace_clients", cur.all_sql())

    def test_existing_personal_returns_id_without_insert(self):
        cur = ScriptedCursor(existing_personal=77)
        sid = mig.create_personal_subject(cur, user_id="U1", tenant_id="T1", name="X")
        self.assertEqual(sid, 77)
        self.assertNotIn("INSERT INTO workspace_clients", cur.all_sql())

    def test_tenant_candidate_without_owner_is_skipped(self):
        cur = ScriptedCursor(
            tenant_candidates=[{"tenant_id": "T9", "null_ocr_count": 2}], owners={}
        )
        report = mig.migrate(cur, apply=True)
        self.assertEqual(report["subjects_created"], 0)
        self.assertNotIn("INSERT INTO workspace_clients", cur.all_sql())


if __name__ == "__main__":
    unittest.main()
