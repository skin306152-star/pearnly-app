# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/recon_jobs/store.py 行为单测(recon 异步任务队列 DAL · 不涉扣费)

补真实行为/边界/错误分支(原仅 submit contract · 行为覆盖 ~29%):
ensure_table / _norm(纯) / enqueue(含 job_type 校验 + 自愈建表)/ claim_next / update_progress /
finish / set_needs_review / set_needs_mapping / set_failed / fail / reclaim_stale / get(归属校验)/ gc_old
的 SQL 形状 + 参数 + 返回 + rowcount 真假 + 异常吞咽兜底。
全部 FakeCursor mock(隔离确定 · 不打真实 DB · 队列纯记录·无扣费)。
"""

import unittest
from unittest import mock

import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.recon_jobs import store as rj


class FakeDT:
    def isoformat(self):
        return "2026-05-29T00:00:00"


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur)

    return mock.patch.object(rj, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(rj, "get_cursor", factory)


class NormTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(rj._norm(None))

    def test_stringifies_ids_and_isoformats_dates(self):
        out = rj._norm(
            {"id": 123, "user_id": 7, "tenant_id": None, "created_at": FakeDT(), "x": "y"}
        )
        self.assertEqual(out["id"], "123")
        self.assertEqual(out["user_id"], "7")
        self.assertIsNone(out["tenant_id"])  # None 不转
        self.assertEqual(out["created_at"], "2026-05-29T00:00:00")
        self.assertEqual(out["x"], "y")


class EnsureTableTests(unittest.TestCase):
    def test_success_runs_ddl_and_returns_true(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(rj.ensure_table())
        self.assertIn("CREATE TABLE IF NOT EXISTS recon_jobs", cur.all_sql())
        self.assertIn("CREATE EXTENSION IF NOT EXISTS pgcrypto", cur.all_sql())

    def test_ddl_failure_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.ensure_table())  # pgcrypto+DDL 都 raise → False(pgcrypto 吞掉)


class EnqueueTests(unittest.TestCase):
    def test_invalid_job_type_raises(self):
        with self.assertRaises(ValueError):
            rj.enqueue("bogus", "u1", "t1")

    def test_with_job_id_inserts_id_and_returns(self):
        cur = FakeCursor(fetchone={"id": "JOB-1"})
        with patch_cursor(cur):
            out = rj.enqueue("bank", "u1", "t1", params={"a": 1}, job_id="JOB-1")
        self.assertEqual(out, "JOB-1")
        self.assertIn("INSERT INTO recon_jobs (id, job_type", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_without_job_id_uses_default(self):
        cur = FakeCursor(fetchone={"id": "GEN-1"})
        with patch_cursor(cur):
            out = rj.enqueue("glvat", "u1", None)
        self.assertEqual(out, "GEN-1")
        self.assertNotIn("INSERT INTO recon_jobs (id,", cur.last_sql)  # 无显式 id 列

    def test_generic_exception_returns_none(self):
        with patch_cursor_raises(RuntimeError("connection reset")):
            self.assertIsNone(rj.enqueue("bank", "u1", "t1"))

    def test_self_heal_table_missing_then_ensure_fails(self):
        # 首次 _insert 报『表不存在』→ 触发 ensure_table;mock ensure_table 返 False → 不重试 → None
        with patch_cursor_raises(RuntimeError('relation "recon_jobs" does not exist')):
            with mock.patch.object(rj, "ensure_table", return_value=False) as ens:
                self.assertIsNone(rj.enqueue("bank", "u1", "t1"))
                ens.assert_called_once()


class ClaimNextTests(unittest.TestCase):
    def test_claims_and_norms(self):
        cur = FakeCursor(fetchone={"id": 5, "user_id": 1, "status": "running"})
        with patch_cursor(cur):
            out = rj.claim_next("worker-1", lease_seconds=300)
        self.assertEqual(out["id"], "5")
        self.assertIn("FOR UPDATE SKIP LOCKED", cur.last_sql)
        self.assertEqual(cur.last_params, ("worker-1", 300))

    def test_no_job_returns_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(rj.claim_next("w"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(rj.claim_next("w"))


class UpdateProgressTests(unittest.TestCase):
    def test_rowcount_true_and_running_guard(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(rj.update_progress("j1", {"pct": 50}))
        self.assertIn("status = 'running'", cur.last_sql)

    def test_rowcount_zero_false(self):
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(rj.update_progress("j1", {}))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.update_progress("j1", {}))


class FinishTests(unittest.TestCase):
    def test_finish_done(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(rj.finish("j1", "vat_reports", 42, progress={"done": True}))
        self.assertIn("status = 'done'", cur.last_sql)
        self.assertEqual(cur.last_params[1], "42")  # result_id → str

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.finish("j1", "t", 1))


class NeedsReviewTests(unittest.TestCase):
    def test_wraps_payload_under_review(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(rj.set_needs_review("j1", {"rows": [1, 2]}))
        self.assertIn("status = 'needs_review'", cur.last_sql)
        self.assertIn('"review"', cur.last_params[0])

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.set_needs_review("j1", {}))


class NeedsMappingTests(unittest.TestCase):
    def test_maps_payload_fields(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = rj.set_needs_mapping(
                "j1", {"mapping": {"col": "x"}, "result_table": "rt", "result_id": 9}
            )
        self.assertTrue(ok)
        self.assertIn("status = 'needs_mapping'", cur.last_sql)
        self.assertIn('"mapping"', cur.last_params[0])
        self.assertEqual(cur.last_params[2], "9")  # result_id → str

    def test_default_error_code(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            rj.set_needs_mapping("j1", {})
        self.assertEqual(cur.last_params[3], "needs_mapping")  # 默认 error_code

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.set_needs_mapping("j1", {}))


class SetFailedTests(unittest.TestCase):
    def test_terminal_failed(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(rj.set_failed("j1", "ERR_PARSE", result_table="diag", result_id=3))
        self.assertIn("status = 'failed'", cur.last_sql)
        self.assertEqual(cur.last_params[0], "ERR_PARSE")

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.set_failed("j1", "E"))


class FailTests(unittest.TestCase):
    def test_returns_true_when_row(self):
        cur = FakeCursor(fetchone={"status": "queued"})
        with patch_cursor(cur):
            self.assertTrue(rj.fail("j1", "ERR"))
        self.assertIn("attempts < max_attempts", cur.last_sql)  # 重试 vs 终态 CASE

    def test_no_row_false(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertFalse(rj.fail("j1", "ERR"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(rj.fail("j1", "ERR"))


class ReclaimStaleTests(unittest.TestCase):
    def test_returns_reclaimed_list(self):
        cur = FakeCursor(fetchall=[{"id": 1, "status": "queued"}, {"id": 2, "status": "failed"}])
        with patch_cursor(cur):
            out = rj.reclaim_stale()
        self.assertEqual(out, [{"id": "1", "status": "queued"}, {"id": "2", "status": "failed"}])
        self.assertIn("lease_until < now()", cur.last_sql)

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(rj.reclaim_stale(), [])


class GetTests(unittest.TestCase):
    def test_user_and_tenant_scope(self):
        cur = FakeCursor(fetchone={"id": 1, "user_id": 2})
        with patch_cursor(cur):
            rj.get("j1", user_id="u1", tenant_id="t1")
        self.assertIn("user_id = %s::uuid OR tenant_id = %s::uuid", cur.last_sql)

    def test_user_only_scope(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(rj.get("j1", user_id="u1"))
        self.assertIn("user_id = %s::uuid", cur.last_sql)
        self.assertNotIn("tenant_id = %s::uuid", cur.last_sql)

    def test_no_scope_just_id(self):
        cur = FakeCursor(fetchone={"id": 9})
        with patch_cursor(cur):
            out = rj.get("j1")
        self.assertEqual(out["id"], "9")

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(rj.get("j1"))


class GcOldTests(unittest.TestCase):
    def test_returns_rowcount_and_passes_days(self):
        cur = FakeCursor(rowcount=5)
        with patch_cursor(cur):
            self.assertEqual(rj.gc_old(done_days=3, failed_days=10), 5)
        self.assertEqual(cur.last_params, (3, 10))

    def test_exception_zero(self):
        with patch_cursor_raises():
            self.assertEqual(rj.gc_old(), 0)


if __name__ == "__main__":
    unittest.main()
