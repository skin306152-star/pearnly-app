# -*- coding: utf-8 -*-
"""services/ocr/jobs/store.py 行为单测(缺口④ 网页 OCR 异步队列 DAL)。

镜像 test_recon_jobs_store_behavior 的 FakeCursor 套路(隔离确定 · 不打真 DB)。
重点新增:begin_charge 扣费幂等闸(rowcount 真假)+ finish 落 result/history_ids。
真表 RLS 隔离另见 tests/integration/test_ocr_jobs_rls_real_tables.py。
"""

import contextlib
import unittest
from unittest import mock

from core import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.ocr.jobs import store as oj


class FakeDT:
    def isoformat(self):
        return "2026-06-30T00:00:00"


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


@contextlib.contextmanager
def _patch_both(factory):
    with (
        mock.patch.object(oj, "get_cursor", factory),
        mock.patch.object(oj, "get_cursor_rls", factory),
    ):
        yield


def patch_cursor(cur):
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur)

    return _patch_both(factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return _patch_both(factory)


class NormTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(oj._norm(None))

    def test_stringifies_ids_and_isoformats_dates(self):
        out = oj._norm(
            {"id": 1, "user_id": 7, "tenant_id": None, "created_at": FakeDT(), "result": {"a": 1}}
        )
        self.assertEqual(out["id"], "1")
        self.assertEqual(out["user_id"], "7")
        self.assertIsNone(out["tenant_id"])
        self.assertEqual(out["created_at"], "2026-06-30T00:00:00")
        self.assertEqual(out["result"], {"a": 1})  # JSONB dict 不动


class EnsureTableTests(unittest.TestCase):
    def test_success_runs_ddl_and_returns_true(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(oj.ensure_table())
        self.assertIn("CREATE TABLE IF NOT EXISTS ocr_jobs", cur.all_sql())
        self.assertIn("result", cur.all_sql())  # 同形响应结果列在 DDL

    def test_ddl_failure_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(oj.ensure_table())


class EnqueueTests(unittest.TestCase):
    def test_invalid_job_type_raises(self):
        with self.assertRaises(ValueError):
            oj.enqueue("u1", "t1", job_type="bogus")

    def test_with_job_id_inserts_id_and_returns(self):
        cur = FakeCursor(fetchone={"id": "JOB-1"})
        with patch_cursor(cur):
            out = oj.enqueue("u1", "t1", params={"a": 1}, job_id="JOB-1")
        self.assertEqual(out, "JOB-1")
        self.assertIn("INSERT INTO ocr_jobs (id, job_type", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_without_job_id_uses_default(self):
        cur = FakeCursor(fetchone={"id": "GEN-1"})
        with patch_cursor(cur):
            out = oj.enqueue("u1", None)
        self.assertEqual(out, "GEN-1")
        self.assertNotIn("INSERT INTO ocr_jobs (id,", cur.last_sql)

    def test_generic_exception_returns_none(self):
        with patch_cursor_raises(RuntimeError("connection reset")):
            self.assertIsNone(oj.enqueue("u1", "t1"))

    def test_self_heal_table_missing_then_ensure_fails(self):
        with patch_cursor_raises(RuntimeError('relation "ocr_jobs" does not exist')):
            with mock.patch.object(oj, "ensure_table", return_value=False) as ens:
                self.assertIsNone(oj.enqueue("u1", "t1"))
                ens.assert_called_once()


class ClaimNextTests(unittest.TestCase):
    def test_claims_and_norms(self):
        cur = FakeCursor(fetchone={"id": 5, "user_id": 1, "status": "running"})
        with patch_cursor(cur):
            out = oj.claim_next("worker-1", lease_seconds=300)
        self.assertEqual(out["id"], "5")
        self.assertIn("FOR UPDATE SKIP LOCKED", cur.last_sql)
        self.assertEqual(cur.last_params, ("worker-1", 300))

    def test_no_job_returns_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(oj.claim_next("w"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(oj.claim_next("w"))


class UpdateProgressTests(unittest.TestCase):
    def test_rowcount_true_and_running_guard(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(oj.update_progress("j1", {"page": 2, "total": 5}))
        self.assertIn("status = 'running'", cur.last_sql)

    def test_rowcount_zero_false(self):
        with patch_cursor(FakeCursor(rowcount=0)):
            self.assertFalse(oj.update_progress("j1", {}))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(oj.update_progress("j1", {}))


class FinishTests(unittest.TestCase):
    def test_finish_done_with_result(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = oj.finish("j1", result={"pages": []}, history_ids=["h1", "h2"])
        self.assertTrue(ok)
        self.assertIn("status = 'done'", cur.last_sql)
        self.assertIn('"pages"', cur.last_params[0])  # result JSON
        self.assertIn("h1", cur.last_params[1])  # history_ids JSON

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(oj.finish("j1"))


class FailTests(unittest.TestCase):
    def test_returns_true_when_row(self):
        cur = FakeCursor(fetchone={"status": "queued"})
        with patch_cursor(cur):
            self.assertTrue(oj.fail("j1", "ERR"))
        self.assertIn("attempts < max_attempts", cur.last_sql)

    def test_no_row_false(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertFalse(oj.fail("j1", "ERR"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(oj.fail("j1", "ERR"))


class SetFailedTests(unittest.TestCase):
    def test_terminal_failed(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(oj.set_failed("j1", "ERR_CORRUPT"))
        self.assertIn("status = 'failed'", cur.last_sql)
        self.assertEqual(cur.last_params[0], "ERR_CORRUPT")

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(oj.set_failed("j1", "E"))


class ReclaimStaleTests(unittest.TestCase):
    def test_returns_reclaimed_list(self):
        cur = FakeCursor(fetchall=[{"id": 1, "status": "queued"}, {"id": 2, "status": "failed"}])
        with patch_cursor(cur):
            out = oj.reclaim_stale()
        self.assertEqual(out, [{"id": "1", "status": "queued"}, {"id": "2", "status": "failed"}])
        self.assertIn("lease_until < now()", cur.last_sql)

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(oj.reclaim_stale(), [])


class GetTests(unittest.TestCase):
    def test_user_and_tenant_scope(self):
        cur = FakeCursor(fetchone={"id": 1, "user_id": 2})
        with patch_cursor(cur):
            oj.get("j1", user_id="u1", tenant_id="t1")
        self.assertIn("user_id = %s::uuid OR tenant_id = %s::uuid", cur.last_sql)

    def test_user_only_scope(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(oj.get("j1", user_id="u1"))
        self.assertIn("user_id = %s::uuid", cur.last_sql)
        self.assertNotIn("tenant_id = %s::uuid", cur.last_sql)

    def test_no_scope_just_id(self):
        cur = FakeCursor(fetchone={"id": 9})
        with patch_cursor(cur):
            self.assertEqual(oj.get("j1")["id"], "9")

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(oj.get("j1"))


class GetStatusMapTests(unittest.TestCase):
    """ENC-c janitor 用:批量取暂存目录名(job_id)对应的 status。镜像 recon_jobs 同名测试。"""

    def test_empty_ids_short_circuits_without_db(self):
        with patch_cursor_raises():
            self.assertEqual(oj.get_status_map([]), {})

    def test_dedupes_and_returns_map(self):
        cur = FakeCursor(
            fetchall=[{"id": "j1", "status": "done"}, {"id": "j2", "status": "running"}]
        )
        with patch_cursor(cur):
            out = oj.get_status_map(["j1", "j1", "j2"])
        self.assertEqual(out, {"j1": "done", "j2": "running"})
        self.assertIn("ANY(%s::uuid[])", cur.last_sql)

    def test_missing_ids_absent_from_result(self):
        cur = FakeCursor(fetchall=[{"id": "j1", "status": "done"}])
        with patch_cursor(cur):
            out = oj.get_status_map(["j1", "orphan-id"])
        self.assertEqual(out, {"j1": "done"})

    def test_exception_returns_empty_dict(self):
        with patch_cursor_raises():
            self.assertEqual(oj.get_status_map(["j1"]), {})


class GcOldTests(unittest.TestCase):
    def test_returns_rowcount_and_passes_days(self):
        cur = FakeCursor(rowcount=4)
        with patch_cursor(cur):
            self.assertEqual(oj.gc_old(done_days=3, failed_days=14), 4)
        self.assertEqual(cur.last_params, (3, 14))

    def test_exception_zero(self):
        with patch_cursor_raises():
            self.assertEqual(oj.gc_old(), 0)


if __name__ == "__main__":
    unittest.main()
